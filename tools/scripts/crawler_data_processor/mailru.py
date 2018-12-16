import re
import csv
from common import is_valid_text

re_tags = re.compile(r'<[^>]+>')

def remove_tags(text):
    return re_tags.sub("", text)

def process_file(path, args):
    idx = 0
    with open(path, newline='\r\n', encoding="utf8") as f:
        reader = csv.reader(f, delimiter=";", quotechar='"')
        for row in reader:

            if len(row) != 3:
                print("Wrong data:")
                print(row)
                continue

            q = row[1]
            a = row[2]

            if not q or not a:
                continue
            t1 = remove_tags(q)
            t2 = remove_tags(a)

            if (t1 is not t2 and is_valid_text(t1, args) and is_valid_text(t2, args)):
                yield (t1, t2)
            