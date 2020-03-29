"""Encodes and decodes NES Game Genie codes."""

import sys
import nesgenielib

def main():
    """The main function."""

    if len(sys.argv) != 2:
        sys.exit(
            "Encodes and decodes NES Game Genie codes. Argument: six-letter code, eight-letter "
            "code, aaaa:rr or aaaa?cc:rr (aaaa = address in hexadecimal, rr = replacement value in "
            "hexadecimal, cc = compare value in hexadecimal)."
        )
    input_ = sys.argv[1]

    # code to decode?
    values = nesgenielib.decode_code(input_)
    if values:
        code = nesgenielib.encode_code(*values)  # re-encode to get canonical code
        print(code, "=", nesgenielib.stringify_values(*values))
        sys.exit()

    # hexadecimal values to encode?
    values = nesgenielib.parse_values(input_)
    if values:
        code = nesgenielib.encode_code(*values)  # encode values to code
        values = nesgenielib.decode_code(code)  # re-decode to get canonical values
        print(nesgenielib.stringify_values(*values), "=", code)
        sys.exit()

    sys.exit("Invalid input.")

if __name__ == "__main__":
    main()
