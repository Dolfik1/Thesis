import json
import os
from common import is_valid_text

os.environ["PATH"] += ";{0}".format(os.getcwd())

def process_file(path, args):
    with open(path) as f:
        messages = list(json.load(f))

    total = len(messages)
    idx = 0

    last_progress = 0
    progress = 0

    print("Total messages: {}".format(total))
    
    indexed_messages = dict()
    for message in messages:
        indexed_messages[message["message_id"]] = message
    
    prev_pair = None

    for message in messages:
        idx += 1
        progress = int((idx / total) * 100)

        if (progress % 10 == 0 and progress != last_progress):
            last_progress = progress
            print("{}%".format(progress))

        reply_message_id = message['reply_message_id']
        if not reply_message_id or not reply_message_id in indexed_messages:
            continue

        reply_message = indexed_messages[reply_message_id]

        t1 = message['text']
        t2 = reply_message['text']
        if (t1 is not t2 and is_valid_text(t1, args) and is_valid_text(t2, args)):
            if prev_pair:
                _, b = prev_pair
                if b['message_id'] == reply_message['message_id']:
                    continue
            prev_pair = (reply_message, message)
            yield (reply_message['text'], message['text'])