"""Encodes and decodes NES Game Genie codes."""

import re
import sys

GENIE_LETTERS = "APZLGITYEOXUKSVN"
GENIE_DECODE_KEY = (3, 5, 2, 4, 1, 0, 7, 6)

# regex for Game Genie codes (6-8 of APZLGITYEOXUKSVN, case insensitive)
GENIE_CODE = re.compile(
    r"^ ([AEGIKLN-PS-VX-Z]{6,8}) $",
    re.IGNORECASE | re.VERBOSE
)
# regex for values to encode (case insensitive):
#     - address (1-4 hexadecimal digits)
#     - optional question mark and compare value (1-2 hexadecimal digits)
#     - colon and replacement value (1-2 hexadecimal digits)
GENIE_VALUES = re.compile(
    r"^ ([\dA-F]{1,4}) (\?([\dA-F]{1,2}))? :([\dA-F]{1,2}) $",
    re.ASCII | re.IGNORECASE | re.VERBOSE
)

def decode_main(code):
    """Decode a Game Genie code (string) to an integer.
    6 letters to 24 bits (16 for address, 8 for replacement value)
    8 letters to 32 bits (16 for address, 8 for replacement value,
    8 for compare value)"""

    # decode code letters to integers
    code = tuple(GENIE_LETTERS.index(letter) for letter in code.upper())
    # decoded integer
    n = 0x00
    # copy bits from two code positions specified by GENIE_DECODE_KEY to n
    for pos in GENIE_DECODE_KEY[:len(code)]:
        prevPos = (pos - 1) % len(code)
        n = (n << 4) | (code[pos] & 0b0111) | (code[prevPos] & 0b1000)
    return n

def decode_6letter(code):
    """Decode a six-letter Game Genie code."""

    n = decode_main(code)
    # set MSB of address (CPU ROM starts at 0x8000)
    address = (n >> 8) | 0x8000
    replacement = n & 0xff
    return "{:04x}:{:02x}".format(address, replacement)

def decode_8letter(code):
    """Decode an eight-letter Game Genie code."""

    n = decode_main(code)
    # set MSB of address (CPU ROM starts at 0x8000)
    address = (n >> 16) | 0x8000
    replacement = (n >> 8) & 0xff
    compare = n & 0xff
    return "{:04x}?{:02x}:{:02x}".format(address, compare, replacement)

def encode_main(n):
    """Encode an integer to a Game Genie code.
    if n is 24 bits (16 for address, 8 for replacement value):
    return 6-letter code
    if n is 32 bits (16 for address (MSB always set), 8 for replacement value,
    8 for compare value): return 8-letter code"""

    # get code length (6 or 8 letters) from MSB
    codeLen = 6 + (n >> 31) * 2
    # code letters as indexes to GENIE_LETTERS
    code = codeLen * [0]
    # copy bits from n to two code positions specified by GENIE_DECODE_KEY
    for pos in GENIE_DECODE_KEY[codeLen-1::-1]:
        prevPos = (pos - 1) % codeLen
        code[pos] |= n & 0b0111
        code[prevPos] |= n & 0b1000
        n >>= 4
    # encode code letters from indexes to letters
    return "".join(GENIE_LETTERS[i] for i in code)

def encode_6letter(args):
    """Encode a six-letter Game Genie code. args:
    - address (hexadecimal, 16 bits)
    - replacement value (hexadecimal, 8 bits)"""

    (addr, repl) = (int(v, 16) for v in args)
    # clear MSB of address to make 3rd letter A/P/Z/L/G/I/T/Y
    return encode_main(((addr & 0x7fff) << 8) | repl)

def encode_8letter(args):
    """Encode an eight-letter Game Genie code. args:
    - address (hexadecimal, 16 bits)
    - replacement value (hexadecimal, 8 bits)
    - compare value (hexadecimal, 8 bits)"""

    (addr, repl, comp) = (int(v, 16) for v in args)
    # set MSB of address to make 3rd letter E/O/X/U/K/S/V/N
    return encode_main(((addr | 0x8000) << 16) | (repl << 8) | comp)

def convert_input(arg):
    """Detect the type of the argument and convert it."""

    # Game Genie code to decode?
    match = GENIE_CODE.search(arg)
    if match is not None:
        if len(match.group(1)) == 6:
            return decode_6letter(match.group(1))
        if len(match.group(1)) == 8:
            return decode_8letter(match.group(1))

    # values to encode?
    match = GENIE_VALUES.search(arg)
    if match is not None:
        if match.group(2) is None:
            return encode_6letter(match.group(1, 4))
        return encode_8letter(match.group(1, 4, 3))

    sys.exit("Invalid command line argument.")

def main():
    """The main function."""

    if sys.version_info[0] != 3:
        print("Warning: possibly incompatible Python version.", file=sys.stderr)

    if len(sys.argv) != 2:
        sys.exit("Invalid number of command line arguments.")

    # print input in canonical format and output
    output = convert_input(sys.argv[1])
    print(convert_input(output), "=", output)

# tests - decode six-letter code
assert convert_input("aaaaaa") == "8000:00"
assert convert_input("aaaaan") == "8700:08"
assert convert_input("aaaana") == "8807:00"
assert convert_input("aaanaa") == "f008:00"
assert convert_input("aaeaaa") == "8000:00"  # canonical: aaaaaa
assert convert_input("aayaaa") == "8070:00"
assert convert_input("anaaaa") == "8080:70"
assert convert_input("naaaaa") == "8000:87"
assert convert_input("nnnnnn") == "ffff:ff"  # canonical: nnynnn
assert convert_input("nnynnn") == "ffff:ff"

# tests - decode eight-letter code
assert convert_input("aaaaaaaa") == "8000?00:00"  # canonical: aaeaaaaa
assert convert_input("aaeaaaaa") == "8000?00:00"
assert convert_input("aaeaaaan") == "8000?70:08"
assert convert_input("aaeaaana") == "8000?87:00"
assert convert_input("aaeaanaa") == "8700?08:00"
assert convert_input("aaeanaaa") == "8807?00:00"
assert convert_input("aaenaaaa") == "f008?00:00"
assert convert_input("aanaaaaa") == "8070?00:00"
assert convert_input("aneaaaaa") == "8080?00:70"
assert convert_input("naeaaaaa") == "8000?00:87"
assert convert_input("nnnnnnnn") == "ffff?ff:ff"
assert convert_input("nnynnnnn") == "ffff?ff:ff"  # canonical: nnnnnnnn

# tests - encode six-letter code
assert convert_input("0000:00") == "AAAAAA"  # canonical: 8000:00
assert convert_input("7fff:ff") == "NNYNNN"  # canonical: ffff:ff
assert convert_input("8000:00") == "AAAAAA"
assert convert_input("8000:87") == "NAAAAA"
assert convert_input("8070:00") == "AAYAAA"
assert convert_input("8080:70") == "ANAAAA"
assert convert_input("8700:08") == "AAAAAN"
assert convert_input("8807:00") == "AAAANA"
assert convert_input("f008:00") == "AAANAA"
assert convert_input("ffff:ff") == "NNYNNN"

# tests - encode eight-letter code
assert convert_input("0000?00:00") == "AAEAAAAA"  # canonical: 8000?00:00
assert convert_input("7fff?ff:ff") == "NNNNNNNN"  # canonical: ffff?ff:ff
assert convert_input("8000?00:00") == "AAEAAAAA"
assert convert_input("8000?00:87") == "NAEAAAAA"
assert convert_input("8000?70:08") == "AAEAAAAN"
assert convert_input("8000?87:00") == "AAEAAANA"
assert convert_input("8070?00:00") == "AANAAAAA"
assert convert_input("8080?00:70") == "ANEAAAAA"
assert convert_input("8700?08:00") == "AAEAANAA"
assert convert_input("8807?00:00") == "AAEANAAA"
assert convert_input("f008?00:00") == "AAENAAAA"
assert convert_input("ffff?ff:ff") == "NNNNNNNN"

if __name__ == "__main__":
    main()
