# MatterMost bots

## sushibot

Splits a discount on a shared cost, with optional delivery fee.

### Example

On one terminal run:

./sushibot --token TOKEN

On another run:

echo "token=TOKEN&text=claudio+1+discount+0.5" | curl -XPOST http://localhost:6500/ -d@-

The output is:

{"response_type":"in_channel","text":"claudio: 0.500000, total: 0.500000, rounding: 0.000000, _bon appetit_"}

## Dependencies

Requires C++-14 support.
Uses uiiitrest (https://bitbucket.org/ccicconetti/rest) and JSON for Modern C++ (https://nlohmann.github.io/json/)
Tested on Mac OS X and Linux.
