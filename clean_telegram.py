"""Prepare training data from telegram chats"""

import json
from pathlib import Path
import csv

# Datatypes: photos, stickers, links

chatfile = Path('result.json')

train_output = Path('train.csv')
validation_output = Path('validation.csv')


def main(validation=0.01):
    """Write out to csv"""
    messages = get_messages(chatfile)
    msg_length = len(messages)

    # Mark for validation and training
    train_validation_split = round((1 - validation) * msg_length)
    training = messages[:train_validation_split]
    validation = messages[train_validation_split:]

    # Create files if necessary
    train_output.touch(exist_ok=False)
    validation_output.touch(exist_ok=False)

    # Output
    with train_output.open(mode='w', encoding='utf-8') as csv_file:
        fieldnames = ['text']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({'text': ''.join(training)})

    with validation_output.open(mode='w', encoding='utf-8') as csv_file:
        fieldnames = ['text']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({'text': ''.join(validation)})


def get_messages(chat: Path):
    # Load chats from JSON
    messages = json.load(chat.open(encoding='utf8'))['messages']
    output = []
    for msg in messages:
        # Ignore calls
        if msg['type'] != 'message':
            continue

        # Ignore blank messages (see process_msg)
        if not (text := process_msg(msg)):
            continue

        date = msg['date']
        msg_from = msg['from']
        output.append(f'{msg_from}: {text}\n\n')
    return output


def process_msg(msg):
    """
    Extract text from telegram message if there is any
    Will return blanks for some message types e.g. file, photo, location_information
    """
    # Text is in the message - could have a photo/video/file as well
    # Types of messages where text could be empty: file, photo, location_information
    if 'text' in msg and type(msg['text']) is str:
        return msg['text']

    # Sticker
    if 'media_type' in msg and msg['media_type'] == 'sticker':
        if 'sticker_emoji' not in msg:
            return ''
        return msg['sticker_emoji']

    # Links
    if type(msg['text']) is list:
        return process_links(msg['text'])

    # Unknown
    raise ValueError(f'Unknown message: {msg}')


def process_links(text: list):
    """Strip object formatting from messages with embedded links."""
    if type(text) is not list:
        raise ValueError(f'Expected list but got {type(text)}')

    texts = []
    for t in text:
        if type(t) is str:
            texts.append(t)
            continue
        else:
            texts.append(t['text'])
    return ''.join(texts)


if __name__ == '__main__':
    main()
