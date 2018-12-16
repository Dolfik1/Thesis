import pickle

def make_grams(chars_list, n):
    result = []
    def make_g(n, prefix):
        if n == 0:
            return prefix

        n -= 1
        gram = prefix
        for c in chars_list:
            gram += c
            if n == 0:
                result.append(gram)
                gram = prefix
            else:
                make_g(n, prefix + c)

    make_g(n, "")
    return result


def generate_vocab(allowed_chars, n):
    chars_list = []
    for allowed in allowed_chars:
        if type(allowed) is int:
            chars_list.append(chr(allowed))
        elif type(allowed) is tuple:
            start, end = allowed
            chars_list += [chr(i) for i in range(start,end)]

    if n == 1:
        return chars_list

    return make_grams(chars_list, n)