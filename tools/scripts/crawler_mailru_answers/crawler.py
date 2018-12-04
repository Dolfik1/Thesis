import time
import json
import sys
import argparse
import os
import pickle
import requests

def mkdir_p(path):
    os.makedirs(path, exist_ok=True)

API_URL = "https://otvet.mail.ru/api/v2/question?qid={}"
CONFIG_PATH = "./config.pkl"

class Config:
    def __init__(self, last_question_id):
        self.last_question_id = last_question_id

def safe_open_w(file, mode):
    ''' Open "path" for writing, creating any parent directories as needed.
    '''
    mkdir_p(os.path.dirname(file))
    return open(file, mode)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', type=str, default='data',
                       help='directory to save parsed data')
    parser.add_argument('--starts_with', type=int, default=10000,
                       help='question id start')
    parser.add_argument('--delay', type=float, default=3,
                       help='delay between requests')
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

def save_config(config):
    with safe_open_w(CONFIG_PATH, "wb") as cf:
        pickle.dump(config, cf)

def make_request(question_id):
    return requests.get(API_URL.format(question_id)).json()

def append_json_entry_to_file(entry, fname):
    if not os.path.isfile(fname):
        with open(fname, mode="w", encoding="utf-8") as f:
            f.write("[]")
        append_json_entry_to_file(entry, fname)
    else:
        with open(fname, mode="r+", encoding="utf-8") as f:
            current_pos = f.seek(0, os.SEEK_END) - 1
            if current_pos != 1:
                f.seek(current_pos)
                f.write(",")
                current_pos += 1
            f.seek(current_pos)
            jstr = json.dumps(entry)
            f.write(jstr)
            f.write("]")

def start(args):
    dirname = os.path.dirname(__file__)
    save_path = os.path.join(dirname, args.data_dir, "result.json")

    current_question_id = args.starts_with
    if os.path.isfile(CONFIG_PATH):
        with open(CONFIG_PATH, "rb") as cf:
            config = pickle.load(cf)
    else:
        config = Config(last_question_id = current_question_id)
        save_config(config)
    
    
    if args.starts_with > config.last_question_id:
        config.last_question_id = args.starts_with
        save_config(config)
    
    current_question_id = config.last_question_id
    
    loop = True
    while loop:
        try:
            print("Processing question {}...".format(current_question_id))
            result = make_request(current_question_id)
            append_json_entry_to_file(result, save_path)
            
            config.last_question_id = current_question_id
            save_config(config)

            current_question_id += 1
            time.sleep(args.delay)
        except Exception as e:
            print(e)
            print("Unknown exception, waiting 60 seconds.")
            time.sleep(60)
        except KeyboardInterrupt:
            print("Finishing...")
            loop = False
    print("Done")


if __name__ == '__main__':
    main()