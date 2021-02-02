"""Encode and decode NES Game Genie codes."""

import sys
import nesgenielib

def main():
    if len(sys.argv) == 2:
        # decode Game Genie code
        values = nesgenielib.decode_code(sys.argv[1])
        if values is None:
            sys.exit("Invalid Game Genie code.")
        # reencode to get canonical form
        code = nesgenielib.encode_code(*values)
    elif 3 <= len(sys.argv) <= 4:
        # encode Game Genie code
        try:
            values = [int(n, 16) for n in sys.argv[1:]]
        except ValueError:
            sys.exit("Invalid hexadecimal integers.")
        code = nesgenielib.encode_code(*values)
        if code is None:
            sys.exit("Hexadecimal integers out of range.")
        # redecode to get canonical form
        values = nesgenielib.decode_code(code)
    else:
        sys.exit(
            "Encode and decode NES Game Genie codes. Argument: six-letter code, eight-letter "
            "code, AAAA RR or AAAA RR CC (AAAA = address in hexadecimal, RR = replacement value "
            "in hexadecimal, CC = compare value in hexadecimal)."
        )

    comp = "none" if values[2] is None else f"0x{values[2]:02x}"
    print(
        f"{code}: CPU address = 0x{values[0]:04x}, replace value = 0x{values[1]:02x}, "
        f"compare value = {comp}"
    )

if __name__ == "__main__":
    main()
