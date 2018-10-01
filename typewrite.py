#!/usr/bin/python3
# coding=utf-8

from __future__ import print_function, unicode_literals

import sys
import dandan
import random
import colorama

colorama.init(autoreset=True)


class TypeWrite(object):
    pairs = {
        '1': 'A',
        '2': 'S',
        '3': 'D',
        '4': 'F',
        '5': 'F',
        '6': 'J',
        '7': 'J',
        '8': 'K',
        '9': 'L',
        '0': ';',
    }

    def __init__(self):
        self.char = None
        self.chars = []
        self.chars.extend([chr(var) for var in range(ord('0'), ord('9') + 1)])
        self.chars.extend([chr(var) for var in range(ord('A'), ord('Z') + 1)])
        # self.chars.extend(['4', '5', '6', '5', '6', '7'] * 100)
        # self.chars.extend(['6', '5', 'T', 'Y', 'G', 'H', 'B', 'N'] * 200)
        self.chars.extend(['5', 'T', 'Y', '6'])
        # self.chars.extend(['5'] * 10)

    def show(self):
        sys.stdout.write(colorama.Back.YELLOW + colorama.Fore.BLACK + self.char)

    def next(self):
        self.char = random.choice(self.chars)
        self.show()
        while not self.validate():
            pass

    def validate(self):
        var = dandan.system.getch()
        if var == "|":
            print(colorama.Back.GREEN + "Bye!")
            exit(0)
        if var.upper() != self.char:
            sys.stdout.write("\b" + colorama.Back.RED + self.char)
            return False
        sys.stdout.write("\b" + colorama.Back.GREEN + self.char)
        return True

    def init(self):
        self.char = self.pairs[self.char]
        self.show()
        while not self.validate():
            pass

    def run(self):
        while True:
            self.next()


def main():
    TypeWrite().run()


if __name__ == '__main__':
    main()
