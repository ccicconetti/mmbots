#!/usr/bin/env python3
"""
Read a names from a semicolor-separated list in a file and queries
Elsevier Scopus via HTTP APIs to retrieve and plot (in an ASCII-art table)
the result.

Example:

1. create the input file, e.g.:

echo "Einstein;Albert;Genius;22988279600" > myexample

2. execute the script as follows:

./hindex-table.py --input myexample

It will print:

Einstein A. (Genius)  ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 41
"""

import argparse
import random
from operator import itemgetter

import pandas as pd
from pybliometrics.scopus import AuthorRetrieval, AuthorSearch

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "Plot in ASCII a table of h-index values from Scopus"
    )
    parser.add_argument(
        "--input", type=str, default="names", help="The input file name"
    )
    parser.add_argument("--fake", action="store_true", help="Use random numbers")
    args = parser.parse_args()

    try:
        names = []
        largest_name = 0
        largest_title = 0
        with open(args.input, "r") as infile:
            for line in infile:
                tokens = line.rstrip().split(";")
                if len(tokens) == 4 and tokens[3]:
                    initials = []
                    for firstname in tokens[1].split(" "):
                        initials.append(firstname[0] + ".")

                    hindex = 0
                    if args.fake:
                        hindex = int(random.expovariate(1 / 20.0))
                    else:
                        au = AuthorSearch(f"AU-ID({tokens[3]})")
                        if au.get_results_size() > 0:
                            assert au.get_results_size() == 1
                            hindex = int(AuthorRetrieval(au.authors[0][0]).h_index)

                    fullname = tokens[0] + " " + " ".join(initials)
                    largest_name = max(largest_name, len(fullname))
                    largest_title = max(largest_title, len(tokens[2]))

                    names.append([fullname, tokens[2], hindex])

        for name in sorted(names, key=itemgetter(2), reverse=True):
            print(
                f'{name[0] + " " * (largest_name - len(name[0]))} ({name[1]}) {" " * (largest_title - len(name[1]))} {"▇" * name[2]} {name[2]}'
            )

    except Exception as err:
        print(f"Error: {err}")
