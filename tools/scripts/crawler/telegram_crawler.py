import time
import json
import sys
import argparse
import os

from pyrogram import Client
from pyrogram.api.errors import FloodWait, UsernameNotOccupied

def mkdir_p(path):
    os.makedirs(path, exist_ok=True)

def safe_open_w(file):
    ''' Open "path" for writing, creating any parent directories as needed.
    '''
    mkdir_p(os.path.dirname(file))
    return open(file, 'w', encoding="utf-8")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', type=str, default='data',
                       help='directory to save parsed data')
    parser.add_argument('--chats', nargs='+',
                       required=True,
                       help='chats list to dump messages')
    parser.add_argument('--delay', type=float, default=3,
                       help='delay between get_history requests')
    parser.add_argument('--session_name', type=str, default='account',
                       help='name of session file')
    parser.add_argument('--phone', type=str, required=False,
                       help='phone number')
    parser.add_argument('--code_env', type=str, required=False,
                       help='code environment variable')
    args = parser.parse_args()
    start(args)

def filter_messages(messages):
    for m in messages:
        if m['user_id'] is not None and m['text'] is not None:
            yield m

def message_to_dict(message):
    reply_message_id = None
    if message.reply_to_message:
        reply_message_id = message.reply_to_message.message_id
    return dict(
        message_id=message.message_id,
        date=message.date,
        reply_message_id=reply_message_id,
        user_id= message.from_user.id if message.from_user else None,
        text=message.text
    )

def phone_code_callback(phone_number, env_name):
    print("Please, put code in {0} environment variable...".format(env_name))
    attempts = 0
    code = None
    while code is None:
        if attempts > 5:
            raise Exception("Can't read environment variable {}.".format(env_name))
        print("Waiting for code {0}/5...".format(attempts))

        time.sleep(30)
        code = os.environ.get(env_name)
        attempts += 1

    return code

def start(args):
    def cb(phone_number):
        return phone_code_callback(phone_number, args.code_env)

    app = Client(
        session_name=args.session_name,
        phone_code=None if args.code_env is None else cb,
        phone_number=args.phone
        )

    dirname = os.path.dirname(__file__)
    current = 0
    unknown_exceptions_count = 0
    total_chats = len(args.chats)
    with app:
        for target in args.chats:
            current += 1
            print("@{} processing...".format(target))

            save_result_path = os.path.join(dirname, args.data_dir, "{}.json".format(target))
            messages = []  # List that will contain all the messages of the target chat
            offset_id = 0  # ID of the last message of the chunk
            while True:
                try:
                    m = app.get_history(target, offset_id=offset_id)
                    unknown_exceptions_count = 0
                    time.sleep(args.delay)
                except FloodWait as e:  # For very large chats the method call can raise a FloodWait
                    print("waiting {}".format(e.x))
                    time.sleep(e.x)  # Sleep X seconds before continuing
                    continue
                except UsernameNotOccupied as e:
                    print(e)
                    break
                except Exception as e:
                    print(e)
                    print("Unknown exception, waiting 60 seconds.")
                    unknown_exceptions_count += 1
                    time.sleep(60)
                    continue

                if not m.messages or unknown_exceptions_count >= 10:
                    break

                offset_id = m.messages[-1].message_id
                messages += map(message_to_dict, m.messages)
                print("Messages: {0} | @{1} - {2} of {3}".format(len(messages), target, current, total_chats))

            print("Saving to {}".format(save_result_path))
            messages = list(filter_messages(messages))
            messages.reverse()
            with safe_open_w(save_result_path) as outfile:
                json.dump(messages, outfile)
            print("Saved!")
    print("Done")


if __name__ == '__main__':
    main()
