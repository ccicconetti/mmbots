#!/usr/bin/env python3
"""Simple thread-safe dictionary persistent on file"""

import argparse
import json
from threading import Lock

class PersDic(object):
    def __init__(self, filename):

        self._lock = Lock()
        self.filename = filename
        self._content = dict()
        try:
            with open(filename, 'r') as pers_file:
                self._content = json.load(pers_file)
        except FileNotFoundError:
            pass

    def get_all(self):
        """Return the full dictionary"""

        with self._lock:
            return self._content

    def get(self, key):
        """Return one value from the dictionary"""

        with self._lock:
            return self._content.get(key)

    def add(self, key, value):
        """Add a new entry and save to file.

        Parameters
        ----------

        key : str
            The key of the pair to be added
        value : str
            The value of the pair to be added
        """

        with self._lock:
            if self._content.get(key) == value:
                return
            self._content[key] = value
            with open(self.filename, 'w') as pers_file:
                json.dump(self._content, pers_file)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        "Command-line interface to manipulate the dictionary",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--show", action="store_true", default=False,
                        help="Show the content.")
    parser.add_argument("--file", type=str, default="persistence.json",
                        help="File to use.")
    parser.add_argument("--add", type=str, default="",
                        help="Entry to be added (key:value).")
    parser.add_argument("--get", type=str, default="",
                        help="Return the value for this entry.")
    args = parser.parse_args()

    pers_dic = PersDic(args.file)
    
    if args.add:
        key, value = args.add.split(':')
        pers_dic.add(key, value)

    if args.get:
        print(pers_dic.get(args.get))

    if args.show:
        for k, v in pers_dic.get_all().items():
            print(f'{k} -> {v}')
