#!/usr/bin/env python3
"""
Read a names from a semicolor-separated list in a file and plot (in an ASCII-art table) the result.

Example:

1. create the input file, e.g.:

echo "Einstein;Albert;Genius;22988279600;120" > myexample

2. execute the script as follows:

./hindex-table-scholar.py --input myexample

It will print:

Einstein A. (Genius)  ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 120
"""

import argparse
import random
from operator import itemgetter


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "Plot in ASCII a table of h-index values from Scopus"
    )
    parser.add_argument(
        "--input", type=str, default="names_with_hindex.txt", help="The input file name"
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
                #print(tokens)
                if len(tokens) == 5 and tokens[3]:
                    initials = []
                    for firstname in tokens[1].split(" "):
                        initials.append(firstname[0] + ".")

                    if args.fake:
                        hindex = int(random.expovariate(1 / 20.0))
                    else:
                        hindex = int(tokens[4])

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
