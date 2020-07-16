#!/usr/bin/env python3
# -*- coding: iso-8859-1 -*-

"""
Retrieve the h-index of a scholar using the Scopus APIs (requires token and subscription).

Modified from:

    https://github.com/bitbackofen/slash-server-for-mattermost

Mattermost documentation:

    http://docs.mattermost.com/developer/slash-commands.html
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
import json
import argparse

from persdic import PersDic
from mattermostrequest import MattermostRequest
from hindex import Hindex

token = None
memes = None

# guarantee unicode string
_u = lambda t: t.decode('UTF-8', 'replace') if isinstance(t, str) else t

class PostHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Respond to a POST request."""

        # Extract the contents of the POST
        length = int(self.headers['Content-Length'])
        post_data = parse_qs(self.rfile.read(length).decode('utf-8'))

        # Get POST data and initialize MattermostRequest object
        request = MattermostRequest(post_data)

        data = {}

        if request.command[0] != u'/hindex' or request.token[0] != token:
            data['text'] = 'invalid request'
            self.send_response(401)
            self.wfile.write(json.dumps(data).encode('utf-8'))
            return

        if not request.text:
            responsetext = gethindex('help')
        else:
            assert len(request.text) == 1
            responsetext = gethindex(request.text[0])

        # Send response HTTP 200 (OK) to MM server
        data['response_type'] = 'ephemeral' if responsetext[1] else 'in_channel'
        data['text'] = responsetext[0]
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

def gethindex(text):
    """Return the response to be returned to the MM server and whether it should be private"""

    tokens = text.split(' ')
    assert len(tokens) > 0

    response = None
    error = False
    private = True

    if tokens[0] == "help":
        response = 'Retrieve the h-index of a scholar via Scopus'
        error = True

    elif tokens[0] == "get":
        if len(tokens) == 2:
            hindex = Hindex().get_by_eid(tokens[1])
            islist = False
        elif len(tokens) == 3:
            hindex, islist = Hindex().get_by_name(tokens[1], tokens[2])
        else:
            error = True
            response = 'Invalid get command'

        if not error:
            if not hindex:
                response = 'Author not found'
            else:
                if not islist:
                    private = False
                    response = f'h-index {hindex}'
                else:
                    response = ('| EID | Affiliation | Town | Country |\n'
                                '|:----|:------------|:-----|:--------|\n')
                    for row in hindex:
                        response += f'| {row[0]} | {row[1]} | {row[2]} | {row[3]} |\n'

    else:
        error = True
        response = 'Invalid command'

    # Return the error / correct response

    if error:
        return [(f"{response}\n"
               "\n"
               "Commands:\n"
               "- `/hindex help`\n"
               "shows this help\n"
               "- `/hindex get EID`\n"
               "return the h-index of a scholar by EID\n"
               "- `/hindex get first last`\n"
               "return the h-index of a scholar by first and last name\n"),
               True]

    return [response, private]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        "Mattermost handle slash command to retrieve the h-index of a scholar via Scopus",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--host", type=str, default="localhost",
                        help="Host to bind.")
    parser.add_argument("--port", type=int, default=10000,
                        help="Host to bind.")
    parser.add_argument("--token", type=str, default="",
                        help="Token to match.")
    args = parser.parse_args()

    token = args.token

    with HTTPServer((args.host, args.port), PostHandler) as server:
        print(f'Starting HTTP server at {args.host}:{args.port}, use <Ctrl-C> to stop')
        server.serve_forever()
