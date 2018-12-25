from __future__ import print_function

from chatbot import Chatbot, add_args
import argparse


def process_user_command(chatbot, user_input):
    user_command_entered = True
    try:
        if user_input.startswith('--temperature '):
            temperature = max(0.001, float(user_input[len('--temperature '):]))
            chatbot.set_config(temperature=temperature)
            print("[Temperature set to {}]".format(temperature))
        elif user_input.startswith('--relevance '):
            user_command_entered = True
            new_relevance = float(user_input[len('--relevance '):])
            chatbot.set_config(relevance=new_relevance)
            relevance = chatbot.relevance
            print("[Relevance disabled]" if relevance <=
                  0. else "[Relevance set to {}]".format(relevance))
        elif user_input.startswith('--topn '):
            topn = int(user_input[len('--topn '):])
            chatbot.set_config(topn=topn)
            print("[Top-n filtering disabled]" if topn <=
                  0 else "[Top-n filtering set to {}]".format(topn))
        elif user_input.startswith('--beam_width '):
            beam_width = max(1, int(user_input[len('--beam_width '):]))
            chatbot.set_config(beam_width=beam_width)
            print("[Beam width set to {}]".format(beam_width))
        elif user_input.startswith('--reset'):
            chatbot.reset()
            print("[Model state reset]")
        else:
            user_command_entered = False
    except ValueError:
        print("[Value error with provided argument.]")

    return user_command_entered


def main():
    parser = argparse.ArgumentParser()
    add_args(parser)
    args = parser.parse_args()
    chatbot = Chatbot(save_dir=args.save_dir, n=args.n, prime=args.prime,
                      beam_width=args.beam_width,
                      temperature=args.temperature, topn=args.topn,
                      relevance=args.relevance)
    chatbot.start()
    while True:
        user_input = input('\n> ')
        user_command_entered = process_user_command(chatbot, user_input)
        if not user_command_entered:
            text = chatbot.say(user_input)
            print(text, end='', flush=True)
    chatbot.stop()


if __name__ == '__main__':
    main()
