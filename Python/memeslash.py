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

token = None

# guarantee unicode string
_u = lambda t: t.decode('UTF-8', 'replace') if isinstance(t, str) else t

class MattermostRequest(object):
    """
    This is what we get from Mattermost
    """
    def __init__(self, response_url=None, text=None, token=None, channel_id=None, team_id=None, command=None,
                 team_domain=None, user_name=None, channel_name=None):
        self.response_url = response_url
        self.text = text
        self.token = token
        self.channel_id = channel_id
        self.team_id = team_id
        self.command = command
        self.team_domain = team_domain
        self.user_name = user_name
        self.channel_name = channel_name

class PostHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Respond to a POST request."""

        # Extract the contents of the POST
        length = int(self.headers['Content-Length'])
        post_data = parse_qs(self.rfile.read(length).decode('utf-8'))

        # Get POST data and initialize MattermostRequest object
        request = MattermostRequest()
        for key, value in post_data.items():
            if key == 'response_url':
                request.response_url = value
            elif key == 'text':
                request.text = value
            elif key == 'token':
                request.token = value
            elif key == 'channel_id':
                request.channel_id = value
            elif key == 'team_id':
                request.team_id = value
            elif key == 'command':
                request.command = value
            elif key == 'team_domain':
                request.team_domain = value
            elif key == 'user_name':
                request.user_name = value
            elif key == 'channel_name':
                request.channel_name = value

        data = {}

        if request.command[0] != u'/meme' or request.token[0] != token:
            data['text'] = 'invalid request'
            self.send_response(401)
            self.wfile.write(json.dumps(data).encode('utf-8'))
            return

        responsetext = getmeme(request.text)

        if responsetext:
            data['response_type'] = 'in_channel'
            data['text'] = 'foo'
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode('utf-8'))

def getmeme(text):
    return text

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
    args = parser.parse_args()

    token = args.token

    with HTTPServer((args.host, args.port), PostHandler) as server:
        print(f'Starting HTTP server at {args.host}:{args.port}, use <Ctrl-C> to stop')
        server.serve_forever()
