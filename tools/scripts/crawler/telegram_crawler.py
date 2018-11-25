import time
import json
import sys
import argparse
import os

from pyrogram import Client
from pyrogram.api.errors import FloodWait, UsernameNotOccupied

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', type=str, default='data',
                       help='directory to save parsed data')
    parser.add_argument('--chats', nargs='+',
                       required=True,
                       help='chats list to dump messages')
    parser.add_argument('--delay', type=float, default=1,
                       help='delay between get_history requests')
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

def start(args):
    app = Client("account")
    dirname = os.path.dirname(__file__)

    with app:
        for target in args.chats:

            print("@{} processing...".format(target))

            save_result_path = os.path.join(dirname, args.data_dir, "{}.json".format(target))
            messages = []  # List that will contain all the messages of the target chat
            offset_id = 0  # ID of the last message of the chunk
            while True:
                try:
                    m = app.get_history(target, offset_id=offset_id)
                    time.sleep(args.delay)
                except FloodWait as e:  # For very large chats the method call can raise a FloodWait
                    print("waiting {}".format(e.x))
                    time.sleep(e.x)  # Sleep X seconds before continuing
                    continue
                except UsernameNotOccupied as e:
                    print(e)
                except Exception as e:
                    print(e)
                    print("Unknown exception, waiting 60 seconds.")
                    time.sleep(60)
                    continue
                if not m.messages:
                    break

                offset_id = m.messages[-1].message_id
                messages += map(message_to_dict, m.messages)
                print("Messages: {}".format(len(messages)))

            print("Saving to {}".format(save_result_path))
            messages = list(filter_messages(messages))
            messages.reverse()
            with open(save_result_path, "w") as outfile:
                json.dump(messages, outfile)
            print("Saved!")
    print("Done")


if __name__ == '__main__':
    main()
