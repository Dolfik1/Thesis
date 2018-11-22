import time
import json
import sys
import argparse
import emoji
import re
from os import listdir
from os.path import dirname, isfile, join

phone = re.compile(r"[+]*[(]{0,1}[0-9]{1,4}[)]{0,1}[-\s\./0-9]*")
url = re.compile(r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)")
email = re.compile(r"[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*")
username = re.compile(r"@.{3,}")


def text_has_emoji(text):
    for character in text:
        if character in emoji.UNICODE_EMOJI:
            return True
    return False

def chars_list(chars_str):
    for pair in chars_str.split(" "):
        p = pair.split("-")
        if len(p) != 2:
            raise argparse.ArgumentTypeError("%s is an invalid pair." % pair)
        try: 
            p0 = int(p[0])
            p1 = int(p[1])

            if p0 > p1:
                raise argparse.ArgumentTypeError("{0} should be less than {1}.".format(p[0], p[1]))
            return (p0, p1)
        except ValueError:
            raise argparse.ArgumentTypeError("{0} or {1} is not integer.".format(p[0], p[1]))

def is_valid_text(text, args):
    if (len(text) > args.max_text_length
        or (not args.allow_new_lines and "\n" in text)
        or (not args.allow_emoji and text_has_emoji(text))
        or phone.search(text)
        or url.search(text)
        or email.search(text)
        or username.search(text)
        ):
        return False
    
    for c in text:
        cn = ord(c)
        for min, max in args.allowed_chars:
            if cn >= min and cn <= max:
                return True
    return False

def prepare_text(text):
    return text.replace("\n", " ")

def process_file(path, args):
    with open(path) as f:
        messages = list(json.load(f))

    result = []
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
                a, b = prev_pair
                if b['message_id'] == reply_message['message_id']:
                    continue
            prev_pair = (reply_message, message)
            result.append(prev_pair)
    return result

def message_to_string(message):
    return "> {}\n".format(prepare_text(message['text']))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', type=str, default='./data',
                       help='directory with files to be processed')
    parser.add_argument('--output_dir', type=str, default='./output',
                       help='output files directory')
    parser.add_argument('--allow_emoji', type=bool, default='true',
                       help='emoji allowed when set true')
    parser.add_argument('--allow_new_lines', type=bool, default='false',
                       help='new lines allowed when set true')
    parser.add_argument('--max_text_length', type=int, default=300,
                       help='max message length')
    parser.add_argument('--allowed_chars', type=chars_list, default=[(0, 128), (1024, 1151)],
                       help='ranges of allowed chars 0-128 1024-1151')
    args = parser.parse_args()
    start(args)

def start(args):
    files = [f for f in listdir(args.data_dir) if isfile(join(args.data_dir, f))]
    pairs = []
    
    dir = dirname(__file__)

    for f in files:
        print("Processing {}...".format(f))
        f = join(dir, args.data_dir, f)
        pairs += process_file(f, args)

    with open('somefile.txt', 'w', encoding="utf-8") as f:
        for pair in pairs:
            reply, message = pair
            f.write(message_to_string(reply))
            f.write(message_to_string(message))

    print("Done!")

if __name__ == '__main__':
        main()