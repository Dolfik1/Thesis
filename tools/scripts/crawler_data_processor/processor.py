import os 

os.environ["PATH"] += ";{0}".format(os.getcwd())

import argparse
from common import prepare_text, chars_list, prepare_badwords_regex, safe_open_w
from os import listdir
from os.path import isfile, join
import telegram
import mailru

def string_to_result_line(text):
    return "> {}".format(prepare_text(text))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=str, default="./data/telegram",
                       help="directory with files to be processed")
    parser.add_argument("--output_dir", type=str, default="./output",
                       help="output files directory")
    parser.add_argument("--output_file_lines", type=int, default=250000,
                       help="count lines in data file")
    parser.add_argument("--allow_emoji", type=bool, default=True,
                       help="emoji allowed when set true")
    parser.add_argument("--allow_new_lines", type=bool, default=False,
                       help="new lines allowed when set true")
    parser.add_argument("--max_text_length", type=int, default=300,
                       help="max message length")
    parser.add_argument("--badwords_file", type=str, required=False,
                       help="path to file that contains bad words separated by new line")
    parser.add_argument("--allowed_chars", type=chars_list, default=[(0, 128), (1024, 1151)],
                       help="ranges of allowed chars 0-128 1024-1151")
    parser.add_argument("--input", type=str, default="telegram",
                       help="input file type, telegram or mailru")
    args = parser.parse_args()
    start(args)

def start(args):
    files = [f for f in listdir(args.data_dir) if isfile(join(args.data_dir, f))]
    prepare_badwords_regex(args)

    file_number = 1
    total_lines = 0

    def open_file():
        fpath = join(args.output_dir, "{0}{1}.txt".format(args.input, file_number))
        return safe_open_w(fpath)

    f = open_file()

    for fdata in files:
        print("Processing {}...".format(fdata))
        fdata = join(args.data_dir, fdata)

        if args.input == "telegram":
            process_file = telegram.process_file
        elif args.input == "mailru":
            process_file = mailru.process_file
        else:
            raise Exception("Unsupported input type: {}".format(args.input)) 

        for pair in process_file(fdata, args):
            reply, message = pair
            f.write(string_to_result_line(reply))
            f.write("\n")
            f.write(string_to_result_line(message))
            total_lines += 2

            if total_lines >= args.output_file_lines:
                f.close()
                total_lines = 0
                file_number += 1
                f = open_file()
            else:
                f.write("\n")


    if not f.closed:
        f.close()

    print("Done!")

if __name__ == "__main__":
        main()