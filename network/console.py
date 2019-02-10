from __future__ import print_function
from t2t.chatbot import Chatbot, add_args
import argparse

def main():
  parser = argparse.ArgumentParser()
  add_args(parser)
  args = parser.parse_args()
  chatbot = Chatbot(args)
  chatbot.start()
  print('Enter q to stop dialog.')
  user_input = ''
  while user_input != 'q':
    user_input = input('\n> ')
    text = chatbot.say(user_input)
    print(text.strip("\n"), end='', flush=True)
  chatbot.stop()


if __name__ == "__main__":
  main()
