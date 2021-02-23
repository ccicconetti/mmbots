#!/usr/bin/env python3
# -*- coding: iso-8859-1 -*-

"""
Select a random element from a set.

Modified from:

    https://github.com/bitbackofen/slash-server-for-mattermost

Mattermost documentation:

    http://docs.mattermost.com/developer/slash-commands.html
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
import json
import argparse
import random
import re

from mattermostrequest import MattermostRequest

token = None

# guarantee unicode string
_u = lambda t: t.decode("UTF-8", "replace") if isinstance(t, str) else t

DIGITS = {
    "0": ":zero:",
    "1": ":one:",
    "2": ":two:",
    "3": ":three:",
    "4": ":four:",
    "5": ":five:",
    "6": ":six:",
    "7": ":seven:",
    "8": ":eight:",
    "9": ":nine:",
}


class PostHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Respond to a POST request."""

        # Extract the contents of the POST
        length = int(self.headers["Content-Length"])
        post_data = parse_qs(self.rfile.read(length).decode("utf-8"))

        # Get POST data and initialize MattermostRequest object
        request = MattermostRequest(post_data)

        data = {}

        if request.command[0] != "/cerino" or request.token[0] != token:
            data["text"] = "invalid request"
            self.send_response(401)
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        if not request.text:
            responsetext = cerino("help")
        else:
            assert len(request.text) == 1
            responsetext = cerino(request.text[0])

        # Send response HTTP 200 (OK) to MM server
        data["response_type"] = "ephemeral" if responsetext[1] else "in_channel"
        data["text"] = responsetext[0]
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))


def digitToEmoji(num: int) -> str:
    ret = ""
    for digit in str(num):
        ret += DIGITS[digit]
    return ret


def cerino(text):
    """Return the response to be returned to the MM server and whether it should be private"""

    tokens = text.split(" ")
    assert len(tokens) > 0

    response = None
    error = False

    if len(tokens) == 1:
        if tokens[0] == "help":
            response = "Return a random element from a set"
            error = True
        elif tokens[0] == "die":
            response = (
                f"The roll of a :game_die: gave: {digitToEmoji(random.randint(1, 6))}"
            )
        elif tokens[0] == "coin":
            response = f"The toss of a coin gave: {random.choice(['head', 'tail'])}"
        elif tokens[0][0:2].upper() == "U(":
            try:
                subtokens = re.split(r"[U(),]", tokens[0], flags=re.IGNORECASE)
                A = None
                B = None
                for tok in subtokens:
                    if tok == "":
                        continue
                    if A is None:
                        A = int(tok)
                    elif B is None:
                        B = int(tok)
                    else:
                        raise RuntimeError(f"Invalid input: {tokens[0]}")
                if A is None or B is None:
                    raise RuntimeError(f"Invalid input: {tokens[0]}")
                response = f"Drawing a random number in [{A},{B}] gave: {digitToEmoji(random.randint(A, B))}"
            except Exception as e:
                error = True
                response = f"Error in request: {e}"
        elif tokens[0] == "bingo":
            response = f"The following number was called: {digitToEmoji(random.randint(1, 90))}"
        else:
            response = f"Invalid command: {tokens[0]}"
            error = True

    else:
        response = (
            f"Out of the following candidates: {','.join(tokens)}\n"
            f"CerinoBot has selected: {random.choice(tokens)}"
        )

    # else:
    #     error = True
    #     response = "Invalid command"

    # Return the error / correct response

    if error:
        return [
            (
                f"{response}\n"
                "\n"
                "Commands:\n"
                "- `/cerino help`:"
                "shows this help\n"
                "- `/cerino X Y Z ...`: "
                "return one random element from those passed\n"
                "- `/cerino die`: "
                "return a random number from 1 to 6\n"
                "- `/cerino coin`: "
                "return the outcome of a coin toss\n"
                "- `/cerino U(A,B)`: "
                "return an integer between `A` and `B`\n"
                "- `/cerino bingo`: "
                "return an integer between 1 and 90\n"
            ),
            True,
        ]

    return [response, False]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "Mattermost handle slash command to return a random element from a set",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--host", type=str, default="localhost", help="Host to bind.")
    parser.add_argument("--port", type=int, default=10000, help="Host to bind.")
    parser.add_argument("--token", type=str, default="", help="Token to match.")
    args = parser.parse_args()

    token = args.token

    with HTTPServer((args.host, args.port), PostHandler) as server:
        print(f"Starting HTTP server at {args.host}:{args.port}, use <Ctrl-C> to stop")
        server.serve_forever()
