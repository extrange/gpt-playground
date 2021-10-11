import logging
import warnings

from styleformer import Styleformer
from telegram.ext import CommandHandler, MessageHandler, Filters
from telegram.ext import Updater

warnings.filterwarnings("ignore")

updater = Updater(token='2019903021:AAEweWr-WjoJmBkREDctiQKiHICHRPfHmps')
dispatcher = updater.dispatcher

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

MY_TELEGRAM_ID = 427380463

# style = [0=Casual to Formal, 1=Formal to Casual, 2=Active to Passive, 3=Passive to Active etc..]
sf = Styleformer(style=0)


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=f'Hello {update.message.from_user.username}!\n\n'
                                  f''
                                  f'I can convert informal speech to formal speech. Some examples you can try:\n\n'
                                  f''
                                  f'Yooo bro how r u\n'
                                  f'Dude, this car\'s dope!\n'
                                  f'She\'s my bestie from college\n'
                                  f'I kinda have a feeling that he has a crush on you.\n'
                                  f'OMG! It\'s finger-lickin\' good.')


def reply(update, context):
    # Send 'typing...' - this helps with URLLIB 3 errors re. timeout
    context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

    msg_text = update.message.text
    styled_text = sf.transfer(msg_text)

    log_msg = f'Message from {update.message.from_user.username}: {msg_text} =>\n{styled_text}'
    logging.info(log_msg)

    # Reply to the person
    if styled_text:
        context.bot.send_message(chat_id=update.effective_chat.id, text=styled_text)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Oops, I couldn\'t paraphrase that! Try another?')

    # Send me as well
    context.bot.send_message(chat_id=MY_TELEGRAM_ID, text=log_msg)


reply_handler = MessageHandler(Filters.text & (~Filters.command), reply)
start_handler = CommandHandler('start', start)

dispatcher.add_handler(start_handler)
dispatcher.add_handler(reply_handler)

updater.start_polling()
