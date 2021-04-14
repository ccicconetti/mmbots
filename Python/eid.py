#!/usr/bin/env python3

import argparse

import pandas as pd
from pybliometrics.scopus import AuthorRetrieval, AuthorSearch


class ScopusEid(object):
    def get_by_name(self, first, last):
        """Return a table of EID, affiliation, town, country otherwise."""

        au = AuthorSearch("AUTHLAST({}) and AUTHFIRST({})".format(last, first))

        if au.get_results_size() == 0:
            return None

        df = pd.DataFrame(au.authors)
        ret = []
        for x in zip(df["eid"], df["affiliation"], df["city"], df["country"]):
            tokens = x[0].split("-")
            ret.append([tokens[-1], x[1], x[2], x[3]])

        return ret


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Retrieve EID of an author from Scopus")
    parser.add_argument(
        "--firstname", type=str, default="", help="First name of the author"
    )
    parser.add_argument(
        "--lastname", type=str, default="", help="Last name of the author"
    )
    args = parser.parse_args()

    try:
        scopus_eid = ScopusEid()

        value = scopus_eid.get_by_name(args.firstname, args.lastname)

        if not value:
            raise Exception(
                "No author found with first name '{}' and last name '{}'".format(
                    firstname, lastname
                )
            )

        for x in value:
            print(f"{x[0]} {x[1]} {x[2]} {x[3]}")

    except Exception as err:
        print(f"Error: {err}")
