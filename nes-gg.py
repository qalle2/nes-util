import re
import sys

HELP_TEXT = """\
NES Game Genie code decoder/encoder by Kalle
(http://qalle.net, http://github.com/qalle2)

=== Decoding ===

The command line argument is a Game Genie code, i.e., six or eight of the
following letters: A, P, Z, L, G, I, T, Y, E, O, X, U, K, S, V, N
The argument is case insensitive.
Examples: "IGZALP", "NVXEUOSK"

The output:
    - the code in its canonical form (for six-letter codes, the third
      letter will be one of A, P, Z, L, G, I, T, Y; for eight-letter
      codes, one of E, O, X, U, K, S, V, N)
    - the decoded values in hexadecimal:
        - for six-letter codes:
            - the CPU address (8000-FFFF)
            - a colon (":")
            - the replacement value (00-FF)
        - for eight-letter codes:
            - the CPU address (8000-FFFF)
            - a question mark ("?")
            - the compare value (00-FF)
            - a colon (":")
            - the replacement value (00-FF)

=== Encoding ===

To create a six-letter code, the command line argument consists of:
    - the CPU address in hexadecimal (8000-FFFF, but 0000 is equivalent
      to 8000, 0001 to 8001, etc.)
    - a colon (":")
    - the replacement value in hexadecimal (00-FF)

To create an eight-letter code, the command line argument consists of:
    - the CPU address in hexadecimal (8000-FFFF, but 0000 is equivalent
      to 8000, 0001 to 8001, etc.)
    - a question mark ("?")
    - the compare value in hexadecimal (00-FF)
    - a colon (":")
    - the replacement value in hexadecimal (00-FF)

The argument is case insensitive.
Examples: "8123:45", "89AB?CD:EF"

The output:
    - the hexadecimal values in their canonical forms
    - the Game Genie code (six or eight letters)\
"""

GAME_GENIE_LETTERS = "APZLGITYEOXUKSVN"
GAME_GENIE_DECODE_KEY = (3, 5, 2, 4, 1, 0, 7, 6)

def decode_main(code):
    """Decode a Game Genie code to an integer (a six-letter code to a 24-bit
    integer or an eight-letter code to a 32-bit integer)."""

    if not isinstance(code, str):
        raise TypeError
    if len(code) not in (6, 8):
        raise ValueError

    # convert each letter to a four-bit integer
    letterValues = [
        GAME_GENIE_LETTERS.index(letter) for letter in code.upper()
    ]

    # descramble the code
    decodedNumber = 0x0
    for pos in GAME_GENIE_DECODE_KEY[:len(code)]:
        # get the three least-significant bits from a letter's value
        valueLow = letterValues[pos] & 0b0111
        # get the most significant bit from the previous letter's value
        posHi = (pos + len(code) - 1) % len(code)
        valueHigh = letterValues[posHi] & 0b1000
        # append the decoded four-bit value to the decoded number
        decodedNumber = (decodedNumber << 4) | (valueLow | valueHigh)

    return decodedNumber

def decode_short(code):
    """Decode a six-letter Game Genie code."""

    # decode to one 24-bit number
    decodedNumber = decode_main(code)
    # split to address and replacement value
    address = decodedNumber >> 8
    replacement = decodedNumber & 0xff
    # set the most significant bit of the address
    address |= 0x8000
    # return the values in the AAAA:RR format
    return "{:04X}:{:02X}".format(address, replacement)

def decode_long(code):
    """Decode an eight-letter Game Genie code."""

    # decode to one 32-bit number
    decodedNumber = decode_main(code)
    # split decoded number to address, replacement value and compare value
    address = decodedNumber >> 16
    replacement = (decodedNumber >> 8) & 0xff
    compare = decodedNumber & 0xff
    # set the most significant bit of the address
    address |= 0x8000
    # return the values in the AAAA?CC:RR format
    return "{:04X}?{:02X}:{:02X}".format(address, compare, replacement)

def encode_main(number):
    """Encode an integer to a Game Genie code (24 bits to six letters or
    32 bits to eight letters)."""

    if not isinstance(number, int):
        raise TypeError
    if not 0 <= number < 1 << 32:
        raise ValueError

    # eight-letter codes have the most significant bit of the address set
    codeLength = 8 if number & (1 << 31) else 6

    # set up output (indexes to GAME_GENIE_LETTERS)
    letterValues = codeLength * [0x0]
    # use the same key as when decoding
    for targetPosLow in GAME_GENIE_DECODE_KEY[codeLength-1::-1]:
        # assign the three least significant bits to the current letter
        letterValues[targetPosLow] |= number & 0b0111
        # assign the fourth-least significant bit to the previous letter
        targetPosHigh = (targetPosLow + codeLength - 1) % codeLength
        letterValues[targetPosHigh] |= number & 0b1000
        # move on to the next four least-significant input bits
        number >>= 4
    # convert output to Game Genie letters
    return "".join(GAME_GENIE_LETTERS[value] for value in letterValues)

def encode_short(address, replacement):
    """Encode a six-letter Game Genie code."""

    # convert the values from hexadecimal strings to integers;
    # also clear the most significant bit of the address
    # to make the third letter of the code be one of A/P/Z/L/G/I/T/Y
    address = int(address, 16) & 0x7fff
    replacement = int(replacement, 16)
    # combine the numbers to one 24-bit number and encode it
    return encode_main((address << 8) | replacement)

def encode_long(address, replacement, compare):
    """Encode an eight-letter Game Genie code."""

    # convert the values from hexadecimal strings to integers;
    # also set the most significant bit of the address
    # to make the third letter of the code be one of E/O/X/U/K/S/V/N
    address = int(address, 16) | 0x8000
    replacement = int(replacement, 16)
    compare = int(compare, 16)
    # combine the numbers to one 32-bit number and encode it
    return encode_main((address << 16) | (replacement << 8) | compare)

def convert_input(argument):
    """Detect the type of the argument and convert it."""

    # six-letter code?
    match = re.search(r"^([APZLGITYEOXUKSVN]{6})$", argument, re.IGNORECASE)
    if match is not None:
        return decode_short(match.group(1))

    # eight-letter code?
    match = re.search(r"^([APZLGITYEOXUKSVN]{8})$", argument, re.IGNORECASE)
    if match is not None:
        return decode_long(match.group(1))

    # address and replace value?
    match = re.search(r"^([0-9A-F]{1,4}):([0-9A-F]{1,2})$", argument, re.IGNORECASE)
    if match is not None:
        return encode_short(match.group(1), match.group(2))

    # address, compare value and replacement value?
    match = re.search(r"^([0-9A-F]{1,4})\?([0-9A-F]{1,2}):([0-9A-F]{1,2})$", argument, re.IGNORECASE)
    if match is not None:
        return encode_long(match.group(1), match.group(3), match.group(2))

    exit("Error: invalid input.")

def main():
    if len(sys.argv) != 2:
        exit(HELP_TEXT)

    # print input in canonical format and output
    output = convert_input(sys.argv[1])
    print(convert_input(output), "=", output)

# tests - decode six-letter code
assert convert_input("aaaaaa") == "8000:00"
assert convert_input("AAAAAA") == "8000:00"
assert convert_input("AAEAAA") == "8000:00"
assert convert_input("NNYNNN") == "FFFF:FF"
assert convert_input("NAAAAA") == "8000:87"
assert convert_input("ANAAAA") == "8080:70"
assert convert_input("AAYAAA") == "8070:00"
assert convert_input("AAANAA") == "F008:00"
assert convert_input("AAAANA") == "8807:00"
assert convert_input("AAAAAN") == "8700:08"

# tests - decode eight-letter code
assert convert_input("aaaaaaaa") == "8000?00:00"
assert convert_input("AAAAAAAA") == "8000?00:00"
assert convert_input("AAEAAAAA") == "8000?00:00"
assert convert_input("NNNNNNNN") == "FFFF?FF:FF"
assert convert_input("NAEAAAAA") == "8000?00:87"
assert convert_input("ANEAAAAA") == "8080?00:70"
assert convert_input("AANAAAAA") == "8070?00:00"
assert convert_input("AAENAAAA") == "F008?00:00"
assert convert_input("AAEANAAA") == "8807?00:00"
assert convert_input("AAEAANAA") == "8700?08:00"
assert convert_input("AAEAAANA") == "8000?87:00"
assert convert_input("AAEAAAAN") == "8000?70:08"

# tests - encode six-letter code
assert convert_input("0000:00") == "AAAAAA"
assert convert_input("8000:00") == "AAAAAA"
assert convert_input("ffff:ff") == "NNYNNN"
assert convert_input("FFFF:FF") == "NNYNNN"
assert convert_input("8000:87") == "NAAAAA"
assert convert_input("8080:70") == "ANAAAA"
assert convert_input("8070:00") == "AAYAAA"
assert convert_input("F008:00") == "AAANAA"
assert convert_input("8807:00") == "AAAANA"
assert convert_input("8700:08") == "AAAAAN"

# tests - encode eight-letter code
assert convert_input("0000?00:00") == "AAEAAAAA"
assert convert_input("8000?00:00") == "AAEAAAAA"
assert convert_input("ffff?ff:ff") == "NNNNNNNN"
assert convert_input("FFFF?FF:FF") == "NNNNNNNN"
assert convert_input("8000?00:87") == "NAEAAAAA"
assert convert_input("8080?00:70") == "ANEAAAAA"
assert convert_input("8070?00:00") == "AANAAAAA"
assert convert_input("F008?00:00") == "AAENAAAA"
assert convert_input("8807?00:00") == "AAEANAAA"
assert convert_input("8700?08:00") == "AAEAANAA"
assert convert_input("8000?87:00") == "AAEAAANA"
assert convert_input("8000?70:08") == "AAEAAAAN"

if __name__ == "__main__":
    main()
