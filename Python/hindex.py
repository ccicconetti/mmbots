#!/usr/bin/env python3

import argparse

import pandas as pd
from pybliometrics.scopus import AuthorRetrieval, AuthorSearch

class Hindex(object):
    def get_by_eid(self, eid):
        """Return the h-index of an author by a EID if found, None otherwise.
        """

        au = AuthorSearch('AU-ID({})'.format(eid))
        if au.get_results_size() == 0:
            return None

        assert au.get_results_size() == 1
        res = AuthorRetrieval(au.authors[0][0])
        return res.h_index

    def get_by_name(self, first, last):
        """Return the h-index of an author if there is only one matching, None if none is
        found, or a table with EID, affiliation, town, country otherwise.
        """

        au = AuthorSearch('AUTHLAST({}) and AUTHFIRST({})'.format(last, first))

        if au.get_results_size() == 0:
            return [ None, False ]

        elif au.get_results_size() == 1:
            res = AuthorRetrieval(au.authors[0][0])
            return [ res.h_index, False ]

        else:
            df = pd.DataFrame(au.authors)
            ret = []
            for x in zip(df['eid'], df['affiliation'], df['city'], df['country']):
                tokens = x[0].split('-')
                ret.append([tokens[-1], x[1], x[2], x[3]])
            return [ ret, True ]

if __name__ == '__main__':
    parser = argparse.ArgumentParser("Retrieve h-index from Scopus")
    parser.add_argument("--firstname", type=str, default="",
                        help="First name of the author")
    parser.add_argument("--lastname", type=str, default="",
                        help="Last name of the author")
    parser.add_argument("--eid", type=str, default="",
                        help="Author identifier")
    args = parser.parse_args()

    try:
        if (not args.firstname or not args.lastname) and not args.eid:
            raise Exception("You must specify the first name and last name of the author, or the EID")

        hindex = Hindex()

        firstname = args.firstname
        lastname = args.lastname
        value = None
        islist = None

        if args.eid:
            value = hindex.get_by_eid(args.eid)
        else:
            value, islist = hindex.get_by_name(firstname, lastname)

        if not value:
            if args.eid:
                raise Exception("No author found with first name '{}' and last name '{}'".format(
                    firstname, lastname))
            else:
                raise Exception("No author found with EID '{}'".format(args.eid))

        if islist:
            for x in value:
                print(f'{x[0]} {x[1]} {x[2]} {x[3]}');

        else:
            print(f'h-index: {value}');

    except Exception as err:
        print(f'Error: {err}')
