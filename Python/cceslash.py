#!/usr/bin/env python3
# -*- coding: iso-8859-1 -*-

"""
Respond to a /cce command by posting a URL.

Modified from:

    https://github.com/bitbackofen/slash-server-for-mattermost

Mattermost documentation:

    http://docs.mattermost.com/developer/slash-commands.html
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
import json
import argparse

from mattermostrequest import MattermostRequest

token = None
names = set()

# guarantee unicode string
_u = lambda t: t.decode("UTF-8", "replace") if isinstance(t, str) else t


class PostHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Respond to a POST request."""

        # Extract the contents of the POST
        length = int(self.headers["Content-Length"])
        post_data = parse_qs(self.rfile.read(length).decode("utf-8"))

        # Get POST data and initialize MattermostRequest object
        request = MattermostRequest(post_data)

        data = {}

        if request.command[0] != "/cce" or request.token[0] != token:
            data["text"] = "invalid request"
            self.send_response(401)
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        if not request.text:
            responsetext = getcce("help")
        else:
            assert len(request.text) == 1
            responsetext = getcce(request.text[0])

        # Send response HTTP 200 (OK) to MM server
        data["response_type"] = "ephemeral" if responsetext[1] else "in_channel"
        data["text"] = responsetext[0]
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))


def getcce(text):
    """Return the response to be returned to the MM server and whether it should be private"""

    tokens = text.split(" ")
    assert len(tokens) > 0

    response = None
    error = False
    private = True

    if tokens[0] == "help" or len(tokens) != 1:
        response = "Show the picture of an IIT member"
        error = True

    else:
        for candidate in names:
            if tokens[0].lower() in candidate:
                response = f"![](https://www.iit.cnr.it/wp-content/themes/cnr/foto_personali_400/{candidate}.jpg)"
                private = False

        if response is None:
            response = f"Could not find an IIT member matching: {tokens[0]}"

    # Return the error / correct response

    if error:
        return [
            (
                f"{response}\n"
                "\n"
                "Commands:\n"
                "- `/meme help`\n"
                "shows this help\n"
                "- `/cce PERSON`\n"
                "shows the picture of PERSON\n"
            ),
            True,
        ]

    return [response, private]


def loadNames(filename: str):
    with open(filename, "r") as infile:
        for line in infile:
            names.add(line.rstrip().lower())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "Mattermost handle slash command to post meme URLs",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--host", type=str, default="localhost", help="Host to bind.")
    parser.add_argument("--port", type=int, default=10000, help="Host to bind.")
    parser.add_argument("--token", type=str, default="", help="Token to match.")
    parser.add_argument(
        "--names",
        type=str,
        default="",
        help="Name of the file containing name and surnames.",
    )
    args = parser.parse_args()

    token = args.token
    loadNames(args.names)

    with HTTPServer((args.host, args.port), PostHandler) as server:
        print(f"Starting HTTP server at {args.host}:{args.port}, use <Ctrl-C> to stop")
        server.serve_forever()
