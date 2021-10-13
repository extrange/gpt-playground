import json
import logging
import queue
import re
import threading

import requests
from dotenv import dotenv_values
from telegram.ext import CommandHandler, MessageHandler, Filters
from telegram.ext import Updater
from telegram.message import Message
from tinydb import TinyDB, Query
from pathlib import Path

script_path = Path(__file__)
config = dotenv_values(script_path.parent / '.env')
token = config['BOT_API_TOKEN']
server_ip = config['SERVER_IP']

# Setup tinydb store
db = TinyDB(script_path.parent / 'db.json')

# TODO Make requests cancelleable when new ones come in

# Maps usernames to those the model was trained on
mapping: dict = json.loads(config['USERNAME_MAPPING'])

updater = Updater(token=token)
dispatcher = updater.dispatcher

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

def get_other_user(username):
    for k in mapping.keys():
        if username != k:
            return k
        continue


def format_chat_history(chat_history: list):
    """Assumes chat_history is already sorted chronologically"""
    return '\n\n'.join([f'{x["from_user_modelname"]}: {x["message"]}' for x in chat_history])


def determine_user_to_emulate(message: Message):
    """Returns the other user in the mapping"""
    from_username = message.from_user.username

    if from_username not in mapping:
        raise Exception(f'User \'{message.from_user.username}\' is not in the mapping ({mapping})')
    return mapping[get_other_user(from_username)]


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=f'Hello {update.message.from_user.username}, I\'m {determine_user_to_emulate(update.message)}! Tell me what you think about me?')


def echo(update, context):
    from_username = update.message.from_user.username
    msg_text = update.message.text
    logging.info(f'Message from {from_username}: {msg_text}')

    # Save chat to DB
    timestamp = update.message.date.timestamp()
    db.insert({'username': from_username,
               'from_user_modelname': mapping[from_username],
               'timestamp': timestamp,
               'message': update.message.text})

    # Notify bot
    Bot.notify(username=from_username, chat_id=update.effective_chat.id)


class Bot:
    thread = {}
    debounce_interval = 0  # seconds
    last_message_time = {}
    api_queue = queue.Queue()

    @classmethod
    def add_username_to_queue(cls, username, chat_id):
        # Clear debounce queue
        cls.thread.pop(username, None)

        cls.api_queue.put((username, chat_id))

    @classmethod
    def notify(cls, username, chat_id):
        """
        Called when a message is sent to this bot.
        Will debounce calls before batching to api, uniquely for each user.
        """

        # Clear timer if already present for this username
        if username in cls.thread:
            cls.thread[username].cancel()

        # Create timer for this username
        cls.thread[username] = threading.Timer(interval=cls.debounce_interval,
                                               function=cls.add_username_to_queue,
                                               args=[username, chat_id])
        cls.thread[username].start()

    @classmethod
    def consume_api_queue(cls):
        """Retrieve chat history for a username, and prepare a call to the API"""
        while True:
            username, chat_id = cls.api_queue.get()
            try:
                other_user_modelname = mapping[get_other_user(username)]

                # Show 'typing...' status
                # Weird error after ~10mins: Exception: urllib3 HTTPError ('Connection aborted.', ConnectionResetError(10054, 'An existing connection was forcibly closed by the remote host', None, 10054, None))
                try:
                    updater.bot.send_chat_action(chat_id=chat_id, action='typing')
                except Exception as e:
                    logging.error(f'HTTP Error while sending typing status: {e}')

                # Retrieve chat history, sorted chronologically
                chat_history = sorted(db.search(Query().username == username), key=lambda x: x['timestamp'])

                # Format the history and send to API
                formatted_chat_history = format_chat_history(chat_history)
                time, generated_messages = cls.query_api(formatted_chat_history,
                                                         target_username=mapping[get_other_user(username)])
                logging.info(f'Generated text for {username} took {time:.2f}s: {generated_messages}')

                # Reply and save history to DB
                for msg in generated_messages:
                    sent_message = updater.bot.send_message(chat_id=chat_id, text=msg)
                    sent_timestamp = sent_message.date.timestamp()
                    db.insert({'username': username,
                               'from_user_modelname': other_user_modelname,
                               'timestamp': sent_timestamp,
                               'message': sent_message.text})

            except Exception as e:
                updater.bot.send_message(chat_id=chat_id,
                                         text='Oops, encountered an error - try resending your message?')
                logging.error(f'Exception: {e}')

    @classmethod
    def query_api(cls, chat_history, target_username, input_max_length=600):
        """
        Takes `input_max_length` characters, adds `username` and queries the endpoint.
        @:param target_username: the username for which to generate text as
        :return: Extracts only responses with a different username and returns as a list
        """
        cut_history = chat_history[-input_max_length:]

        # Append the model username of OTHER target_username as prompt for model
        cut_history += f'\n\n{target_username}:'  # Trailing spaces mess up the model

        # Get response from api and extract responses (try up to 2 times)
        attempts = 0
        response = None
        while attempts < 2:
            try:
                response = requests.post(f'http://{server_ip}:5555/', json={'text': cut_history}).json()
                break
            except Exception as e:
                logging.error(f'HTTP Error from API: {e}')
                attempts += 1

        generated_text = response['generated']
        generated_responses = cls.extract_responses(generated_text, target_username)
        time_taken = response['time']

        return time_taken, generated_responses

    @classmethod
    def extract_responses(cls, text, target_username):
        """
        Extract only the `target_username` responses from a given text sample
        :return: list of responses for `target_username`
        """
        candidate_text = None
        responses = []

        # Cut off text when username is different from target username
        for match in re.finditer('^(.*?): .*$', text, re.MULTILINE):
            match_str = text[match.start(1):match.end(1)]
            if match_str != target_username:
                candidate_text = text[:match.start(1)].strip()
                break

        # If text was not cutoff, the entire chunk is valid output
        if candidate_text is None:
            candidate_text = text

        # Split candidate_text by username
        [responses.append(x.strip()) for x in re.split(f'\n{target_username}: ', candidate_text)]

        return responses

    @classmethod
    def start(cls):
        api_thread = threading.Thread(target=cls.consume_api_queue, daemon=True)
        api_thread.start()

if __name__ == '__main__':
    echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
    start_handler = CommandHandler('start', start)

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(echo_handler)

    Bot.start()
    updater.start_polling()
