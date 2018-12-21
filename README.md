# MatterMost bots

## sushibot

Splits a discount on a shared cost, with optional delivery fee.

### Example

Assume Alice and Bob ordered a meal together. Alice bought a 10$ pizza and Bob the same plus a 5$ beer, and they must pay a 1$ delivery fee, but use a 20% discount coupon. In MatterMost the slack command is:

    /sushi Alice 10 Bob 10 5 discount 0.2 delivery 1

The bot response renders as:

    ![Bot response](/path/to/image.jpg)

If you want to try without installing on MatterMost, on one terminal run:

    ./sushibot --token TOKEN

On another run:

    echo "token=TOKEN&text=alice+10+bob+10+5+discount+0.2+delivery+1" | \
    curl -XPOST http://localhost:6500/ -d@-

The output is:

    {"response_type":"in_channel","text":"| Who | How much |\n| - | - |\n| alice | 8.50 |\n| bob | 12.50 |\n| ** Total ** | ** 21.00 ** |\n_Bon appetit!_"}

## Dependencies

Requires C++-14 support.
Uses uiiitrest (https://bitbucket.org/ccicconetti/rest) and JSON for Modern C++ (https://nlohmann.github.io/json/)
Tested on Mac OS X and Linux.
