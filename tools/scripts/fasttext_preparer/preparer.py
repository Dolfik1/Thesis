import os 

import argparse
from os import listdir, makedirs
from os.path import isfile, join, dirname

def safe_open_w(file):
    ''' Open "path" for writing, creating any parent directories as needed.
    '''
    makedirs(dirname(file), exist_ok=True)
    return open(file, 'w', encoding="utf-8")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=str,
                       help="directory with files to be processed")
    parser.add_argument("--output_file", type=str, default="./output/result.txt",
                       help="output files directory")
    args = parser.parse_args()
    start(args)

def start(args):
    files = [join(args.data_dir, f) for f in listdir(args.data_dir) if isfile(join(args.data_dir, f))]

    file_number = 1
    total_lines = 0

    with safe_open_w(args.output_file) as fwrite:
        for f in files:
            print(f)
            with open(f, "r", encoding="utf8") as rfile:
                for line in rfile:
                    fwrite.write(line.strip("\r\n>").strip() + " ")

    print("Done!")

if __name__ == "__main__":
        main()