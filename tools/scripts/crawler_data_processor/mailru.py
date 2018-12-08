import ijson.backends.yajl2_cffi as ijson
#import ijson
import re
from common import is_valid_text

re_tags = re.compile(r'<[^>]+>')

def remove_tags(text):
    return re_tags.sub("", text)

def process_file(path, args):
    idx = 0
    with open(path, mode="rb") as f:
        answers = ijson.items(f, "item")
        for answer in answers:

            if idx % 10000 == 0:
                print("{} records processed...".format(idx))

            idx += 1
            if answer.get("errid") or not answer.get("qtext") or not answer.get("best"):
                continue
            t1 = remove_tags(answer.get("qtext"))
            t2 = remove_tags(answer.get("best").get("atext"))

            if (t1 is not t2 and is_valid_text(t1, args) and is_valid_text(t2, args)):
                yield (t1, t2)