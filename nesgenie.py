"""Encodes and decodes NES Game Genie codes."""

import re
import sys
import nesgenielib

class GenieError(Exception):
    """An exception for NES Game Genie related errors."""

def parse_values(input_):
    """Parse a hexadecimal representation of the numbers regarding a Game Genie code.
    input_: must match 'aaaa:rr' or 'aaaa?cc:rr', where:
        aaaa = NES CPU address in hexadecimal
        rr = replacement value in hexadecimal
        cc = compare value in hexadecimal
    on error: raise GenieError
    return: (address, replacement_value, compare_value/None)"""

    # try to match "aaaa:rr"
    match = re.search(
        r"^ ([\da-f]{1,4}) : ([\da-f]{1,2}) $",
        input_,
        re.ASCII | re.IGNORECASE | re.VERBOSE
    )
    if match is None:
        # try to match "aaaa?cc:rr"
        match = re.search(
            r"^ ([\da-f]{1,4}) \? ([\da-f]{1,2}) : ([\da-f]{1,2}) $",
            input_,
            re.ASCII | re.IGNORECASE | re.VERBOSE
        )
    if match is None:
        raise GenieError
    groups = tuple(int(n, 16) for n in match.groups())
    return (groups[0], groups[1], None) if len(groups) == 2 else (groups[0], groups[2], groups[1])

def main():
    """The main function."""

    if len(sys.argv) != 2:
        sys.exit(
            "Encodes and decodes NES Game Genie codes. Argument: six-letter code, eight-letter "
            "code, aaaa:rr or aaaa?cc:rr (aaaa = address in hexadecimal, rr = replacement value in "
            "hexadecimal, cc = compare value in hexadecimal)."
        )
    input_ = sys.argv[1]

    # a code to decode?
    try:
        values = nesgenielib.decode_code(input_)
    except nesgenielib.NESGenieError:
        # hexadecimal values to encode?
        try:
            values = parse_values(input_)
        except GenieError:
            sys.exit("Invalid input.")
        print(nesgenielib.encode_code(*values))
        sys.exit()
    print("CPU address = 0x{:04x}, replace value = 0x{:02x}, compare value = {:s}".format(
        values[0], values[1], "none" if values[2] is None else "0x{:02x}".format(values[2])
    ))

if __name__ == "__main__":
    main()
