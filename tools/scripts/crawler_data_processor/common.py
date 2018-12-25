import argparse
import emoji
import re
from os import makedirs
from os.path import join, dirname

phone = re.compile(r"[+]*[(]{0,1}[0-9]{1,4}[)]{0,1}[-\s\./0-9]*")
url = re.compile(r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)")
email = re.compile(r"[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*")
username = re.compile(r"@.{3,}")
re_badwords = None

def mkdir_p(path):
    makedirs(path, exist_ok=True)

def safe_open_w(file):
    ''' Open "path" for writing, creating any parent directories as needed.
    '''
    mkdir_p(dirname(file))
    return open(file, 'w', encoding="utf-8")

def text_has_emoji(text):
    for character in text:
        if character in emoji.UNICODE_EMOJI:
            return True
    return False

def is_valid_text(text, args):
    if (len(text) > args.max_text_length
        or (not args.allow_new_lines and "\n" in text)
        or (not args.allow_emoji and text_has_emoji(text))
        or phone.search(text)
        or url.search(text)
        or email.search(text)
        or username.search(text)
        or (re_badwords and re_badwords.search(text))
        ):
        return False
    
    for c in text:
        cn = ord(c)
        for min, max in args.allowed_chars:
            if cn >= min and cn <= max:
                return True
    return False

def prepare_text(text):
    return text.replace("\r\n", " ").replace("\n", " ").replace("  ", " ")

    
def badword_to_regex_str(badword):
    return re.escape(badword.lower().replace("\n", "")).replace("\\?", ".")

def prepare_badwords_regex(args):
    badwords_list = None
    if args.badwords_file:
        with open(args.badwords_file) as f:
            badwords_list = f.readlines()
        rx_str = "|".join(map(badword_to_regex_str, badwords_list))
        global re_badwords
        print(rx_str)
        re_badwords = re.compile(rx_str)


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