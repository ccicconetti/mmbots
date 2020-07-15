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

    def get_keys(self):
        """Return the list of keys in the dictionary"""

        with self._lock:
            return self._content.keys()

    def get(self, key, exact = True):
        """Return one value from the dictionary

        Parameters
        ---------
        key : str
            The key to search in the dictionary

        exact : bool
            If true then do an exact search, otherwise return
            the first entry with a partial match

        Returns
        -------
        the value corresponding to the given key or None if
        no match was found
        """

        with self._lock:
            if exact:
                return self._content.get(key)

            for k, v in self._content.items():
                if key in k:
                    return v
            return None

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
            self._serialize()

    def delete(self, key):
        """Delete an entry from directionary and save to file.

        Parameters
        ----------

        key : str
            The key of the pair to be removed
        """

        with self._lock:
            if self._content.pop(key, None):
                self._serialize()

    def _serialize(self):
        """Write the dictionary to file"""

        assert self._lock.locked()
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
    parser.add_argument("--delete", type=str, default="",
                        help="Entry to be deleted, by key.")
    parser.add_argument("--add", type=str, default="",
                        help="Entry to be added (key:value).")
    parser.add_argument("--get_exact", type=str, default="",
                        help="Return the value for this entry (exact match).")
    parser.add_argument("--get_partial", type=str, default="",
                        help="Return a value for this entry (partial match).")
    parser.add_argument("--keys", action="store_true", default=False,
                        help="Return the list of keys.")
    args = parser.parse_args()

    pers_dic = PersDic(args.file)
    
    if args.delete:
        pers_dic.delete(args.delete)

    if args.add:
        key, value = args.add.split(':')
        pers_dic.add(key, value)

    if args.get_exact:
        print(pers_dic.get(args.get_exact, exact=True))

    if args.get_partial:
        print(pers_dic.get(args.get_partial, exact=False))

    if args.show:
        for k, v in pers_dic.get_all().items():
            print(f'{k} -> {v}')

    if args.keys:
        for k in pers_dic.get_keys():
            print(k)
