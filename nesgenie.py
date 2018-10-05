import re
import sys

GENIE_LETTERS = "APZLGITYEOXUKSVN"
GENIE_DECODE_KEY = (3, 5, 2, 4, 1, 0, 7, 6)

def decode_main(code):
    """Decode a Game Genie code to an integer
    (6 letters to 24 bits, 8 letters to 32 bits)."""

    code = code.upper()
    decoded = 0
    for pos in GENIE_DECODE_KEY[:len(code)]:
        decoded <<= 4
        decoded |= GENIE_LETTERS.index(code[pos]) & 0b0111
        prevPos = (pos - 1) % len(code)
        decoded |= GENIE_LETTERS.index(code[prevPos]) & 0b1000
    return decoded

def decode_short(code):
    """Decode a six-letter Game Genie code."""

    n = decode_main(code)
    address = n >> 8
    address |= 0x8000  # set MSB (CPU ROM starts at 0x8000)
    replacement = n & 0xff
    return "{:04x}:{:02x}".format(address, replacement)

def decode_long(code):
    """Decode an eight-letter Game Genie code."""

    n = decode_main(code)
    address = n >> 16
    address |= 0x8000  # set MSB (CPU ROM starts at 0x8000)
    replacement = (n >> 8) & 0xff
    compare = n & 0xff
    return "{:04x}?{:02x}:{:02x}".format(address, compare, replacement)

def encode_main(n):
    """Encode an integer to a Game Genie code
    (24 bits to 6 letters, 32 bits to 8 letters)."""

    codeLength = 6 if n <= 0x7fff_ff else 8
    letterValues = codeLength * [0]
    for pos in GENIE_DECODE_KEY[codeLength-1::-1]:
        letterValues[pos] |= n & 0b0111
        prevPos = (pos - 1) % codeLength
        letterValues[prevPos] |= n & 0b1000
        n >>= 4
    return "".join(GENIE_LETTERS[value] for value in letterValues)

def encode_short(address, replacement):
    """Encode a six-letter Game Genie code."""

    address = int(address, 16)
    address &= 0x7fff  # clear MSB to make 3rd letter A/P/Z/L/G/I/T/Y
    replacement = int(replacement, 16)
    combined = (address << 8) | replacement
    return encode_main(combined)

def encode_long(address, replacement, compare):
    """Encode an eight-letter Game Genie code."""

    address = int(address, 16)
    address |= 0x8000  # set MSB to make 3rd letter E/O/X/U/K/S/V/N
    replacement = int(replacement, 16)
    compare = int(compare, 16)
    combined = (address << 16) | (replacement << 8) | compare
    return encode_main(combined)

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
    match = re.search(
        r"^([0-9A-F]{1,4}):([0-9A-F]{1,2})$", argument, re.IGNORECASE
    )
    if match is not None:
        return encode_short(match.group(1), match.group(2))

    # address, compare value and replacement value?
    match = re.search(
        r"^([0-9A-F]{1,4})\?([0-9A-F]{1,2}):([0-9A-F]{1,2})$",
        argument, re.IGNORECASE
    )
    if match is not None:
        return encode_long(match.group(1), match.group(3), match.group(2))

    exit("Error: invalid input. See the readme file.")

def main():
    if len(sys.argv) != 2:
        exit("Error: invalid number of arguments. See the readme file.")

    # print input in canonical format and output
    output = convert_input(sys.argv[1])
    print(convert_input(output), "=", output)

# tests - decode six-letter code
assert convert_input("aaaaaa") == "8000:00"
assert convert_input("aaaaaa") == "8000:00"
assert convert_input("aaeaaa") == "8000:00"
assert convert_input("nnynnn") == "ffff:ff"
assert convert_input("naaaaa") == "8000:87"
assert convert_input("anaaaa") == "8080:70"
assert convert_input("aayaaa") == "8070:00"
assert convert_input("aaanaa") == "f008:00"
assert convert_input("aaaana") == "8807:00"
assert convert_input("aaaaan") == "8700:08"

# tests - decode eight-letter code
assert convert_input("aaaaaaaa") == "8000?00:00"
assert convert_input("aaaaaaaa") == "8000?00:00"
assert convert_input("aaeaaaaa") == "8000?00:00"
assert convert_input("nnnnnnnn") == "ffff?ff:ff"
assert convert_input("naeaaaaa") == "8000?00:87"
assert convert_input("aneaaaaa") == "8080?00:70"
assert convert_input("aanaaaaa") == "8070?00:00"
assert convert_input("aaenaaaa") == "f008?00:00"
assert convert_input("aaeanaaa") == "8807?00:00"
assert convert_input("aaeaanaa") == "8700?08:00"
assert convert_input("aaeaaana") == "8000?87:00"
assert convert_input("aaeaaaan") == "8000?70:08"

# tests - encode six-letter code
assert convert_input("0000:00") == "AAAAAA"
assert convert_input("8000:00") == "AAAAAA"
assert convert_input("ffff:ff") == "NNYNNN"
assert convert_input("ffff:ff") == "NNYNNN"
assert convert_input("8000:87") == "NAAAAA"
assert convert_input("8080:70") == "ANAAAA"
assert convert_input("8070:00") == "AAYAAA"
assert convert_input("f008:00") == "AAANAA"
assert convert_input("8807:00") == "AAAANA"
assert convert_input("8700:08") == "AAAAAN"

# tests - encode eight-letter code
assert convert_input("0000?00:00") == "AAEAAAAA"
assert convert_input("8000?00:00") == "AAEAAAAA"
assert convert_input("ffff?ff:ff") == "NNNNNNNN"
assert convert_input("ffff?ff:ff") == "NNNNNNNN"
assert convert_input("8000?00:87") == "NAEAAAAA"
assert convert_input("8080?00:70") == "ANEAAAAA"
assert convert_input("8070?00:00") == "AANAAAAA"
assert convert_input("f008?00:00") == "AAENAAAA"
assert convert_input("8807?00:00") == "AAEANAAA"
assert convert_input("8700?08:00") == "AAEAANAA"
assert convert_input("8000?87:00") == "AAEAAANA"
assert convert_input("8000?70:08") == "AAEAAAAN"

if __name__ == "__main__":
    main()
