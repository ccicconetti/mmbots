#!/usr/bin/env python3
# -*- coding: iso-8859-1 -*-

"""
Respond to commands by posting meme URLs previously configured.

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

token = None
memes = None

# guarantee unicode string
_u = lambda t: t.decode('UTF-8', 'replace') if isinstance(t, str) else t

class MattermostRequest(object):
    """
    This is what we get from Mattermost
    """
    def __init__(self, mmdata):
        """Initialize the MM request with the data from the server.

        Parameters
        ---------
            mmdata : dict
                Dictionary representing the MM fields as read from the JSON in the POST.
        """

        self.response_url = None
        self.text = None
        self.token = None
        self.channel_id = None
        self.team_id = None
        self.command = None
        self.team_domain = None
        self.user_name = None
        self.channel_name = None

        for key, value in mmdata.items():
            if key == 'response_url':
                self.response_url = value
            elif key == 'text':
                self.text = value
            elif key == 'token':
                self.token = value
            elif key == 'channel_id':
                self.channel_id = value
            elif key == 'team_id':
                self.team_id = value
            elif key == 'command':
                self.command = value
            elif key == 'team_domain':
                self.team_domain = value
            elif key == 'user_name':
                self.user_name = value
            elif key == 'channel_name':
                self.channel_name = value

class PostHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Respond to a POST request."""

        # Extract the contents of the POST
        length = int(self.headers['Content-Length'])
        post_data = parse_qs(self.rfile.read(length).decode('utf-8'))

        # Get POST data and initialize MattermostRequest object
        request = MattermostRequest(post_data)

        data = {}

        if request.command[0] != u'/meme' or request.token[0] != token:
            data['text'] = 'invalid request'
            self.send_response(401)
            self.wfile.write(json.dumps(data).encode('utf-8'))
            return

        if not request.text:
            responsetext = getmeme('help')
        else:
            assert len(request.text) == 1
            responsetext = getmeme(request.text[0])

        # Send response HTTP 200 (OK) to MM server
        data['response_type'] = 'ephemeral' if responsetext[1] else 'in_channel'
        data['text'] = responsetext[0]
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

def getmeme(text):
    """Return the response to be returned to the MM server and whether it should be private"""

    tokens = text.split(' ')
    assert len(tokens) > 0

    response = None
    error = False
    private = True

    if tokens[0] == "list":
        meme_keys = memes.get_keys()
        if not meme_keys:
            response = 'No activation phrases available'
        else:
            response = "Activation phrases available:\n{}".format(
                '\n'.join([f'- {x}' for x in meme_keys]))

    elif tokens[0] == "help":
        response = 'Show a configurable response in channel'
        error = True

    elif tokens[0] == "add":
        if len(tokens) != 3:
            error = True
            response = 'Invalid add command'

        else:
            memes.add(tokens[1], tokens[2])
            response = 'OK'

    elif tokens[0] == "del":
        if len(tokens) != 2:
            error = True
            response = 'Invalid del command'

        else:
            response = 'OK' if memes.delete(tokens[1]) else f'Activation phrase `{tokens[1]}` not found'

    else:
        if len(tokens) != 1:
            error = True
            response = 'Invalid command'

        else:
            response = memes.get(tokens[0], exact=False)
            if not response:
                response = f'invalid activation phrase `{tokens[0]}`'
            else:
                private = False

    # Return the error / correct response

    if error:
        return [(f"{response}\n"
               "\n"
               "Commands:\n"
               "- `/meme help`\n"
               "shows this help\n"
               "- `/meme list`\n"
               "shows the list of activation phrases\n"
               "- `/meme add KEY VALUE`\n"
               "add KEY as activation phrase that will show VALUE, possibly overriding a previous entry\n"
               "- `/meme del KEY`\n"
               "delete the activation phase KEY\n"
               "- `/meme PHRASE`\n"
               "show a response partially matching the given PHRASE\n"),
               True]

    return [response, private]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        "Mattermost handle slash command to post meme URLs",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--host", type=str, default="localhost",
                        help="Host to bind.")
    parser.add_argument("--port", type=int, default=10000,
                        help="Host to bind.")
    parser.add_argument("--token", type=str, default="",
                        help="Token to match.")
    parser.add_argument("--persistence", type=str, default="persistence.json",
                        help="Name of the file containing the dictionary of meme URLs.")
    args = parser.parse_args()

    token = args.token
    memes = PersDic(args.persistence)

    with HTTPServer((args.host, args.port), PostHandler) as server:
        print(f'Starting HTTP server at {args.host}:{args.port}, use <Ctrl-C> to stop')
        server.serve_forever()
