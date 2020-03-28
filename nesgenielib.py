"""A library for decoding and encoding NES Game Genie codes. See http://nesdev.com/nesgg.txt"""

import re
import sys

_GENIE_LETTERS = "APZLGITYEOXUKSVN"
_GENIE_DECODE_KEY = (3, 5, 2, 4, 1, 0, 7, 6)

# --- decoding -------------------------------------------------------------------------------------

def _decode_lowlevel(code):
    """Decode a Game Genie code (the low-level stuff).
    6 letters to a 24-bit int (16 for address, 8 for replacement value)
    8 letters to a 32-bit int (16 for address, 8 for replacement value, 8 for compare value)"""

    # decode each letter into a four-bit int
    code = tuple(_GENIE_LETTERS.index(letter) for letter in code.upper())
    # construct four decoded bits per round by copying bits from two letters
    decoded = 0
    for lowBitsLetterPos in _GENIE_DECODE_KEY[:len(code)]:
        highBitLetterPos = (lowBitsLetterPos - 1) % len(code)
        decoded <<= 4
        decoded |= code[lowBitsLetterPos] & 0b0111
        decoded |= code[highBitLetterPos] & 0b1000
    return decoded

def decode_code(code):
    """Decode a Game Genie code.
    If an eight-letter code, return (address, replacement_value, compare_value).
    If a six-letter code, return (address, replacement_value).
    If an invalid code, return None."""

    # validate code
    if len(code) not in (6, 8) or not all(char in _GENIE_LETTERS for char in code.upper()):
        return None
    # decode the code into an integer (6 letters to 24 bits, 8 letters to 32 bits)
    n = _decode_lowlevel(code)
    # extract values from the integer
    if len(code) == 6:
        values = [n >> 8, n & 0xff]
    else:
        values = [n >> 16, (n >> 8) & 0xff, n & 0xff]
    # set most significant bit of address (NES CPU ROM starts at 0x8000)
    values[0] |= 0x8000
    return tuple(values)

def stringify_values(address, replacement, compare=None):
    """Convert the address, replacement value and compare value into a hexadecimal representation
    ('aaaa:rr' or 'aaaa?cc:rr')."""

    return f"{address:04x}" + ("" if compare is None else f"?{compare:02x}") + f":{replacement:02x}"

# --- encoding -------------------------------------------------------------------------------------

def parse_values(input_):
    """Parse 'aaaa:rr' or 'aaaa?cc:rr' where aaaa = address in hexadecimal, rr = replacement value
    in hexadecimal, cc = compare value in hexadecimal. Return the values as a tuple of integers,
    with the replacement value before the compare value, or None if the input matches neither."""

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
        return None
    groups = tuple(int(n, 16) for n in match.groups())
    return groups if len(groups) == 2 else (groups[0], groups[2], groups[1])

def _encode_lowlevel(n, codeLen):
    """Encode a Game Genie code (the low-level stuff).
    If codeLen=6, n must be a 24-bit int (16 for address, 8 for replacement value).
    If codeLen=8, n must be a 32-bit int (16 for address, 8 for replacement value, 8 for compare
    value)."""

    # code letters as indexes to _GENIE_LETTERS
    code = codeLen * [0]
    # copy bits from n to two code positions specified by _GENIE_DECODE_KEY
    for pos in _GENIE_DECODE_KEY[codeLen-1::-1]:
        prevPos = (pos - 1) % codeLen
        code[pos] |= n & 0b0111
        code[prevPos] |= n & 0b1000
        n >>= 4
    # encode code letters from indexes to letters
    return "".join(_GENIE_LETTERS[i] for i in code)

def encode_code(address, replacement, compare=None):
    """Encode a Game Genie code.
    address: 16-bit int, replacement/compare: replacement value and compare value (8-bit ints)"""

    if not 0x0000 <= address <= 0xffff:
        sys.exit("Invalid address.")
    if not 0x00 <= replacement <= 0xff:
        sys.exit("Invalid replacement value.")

    if compare is None:
        # six-letter code
        codeLen = 6
        address &= 0x7fff  # clear MSB to make the third letter one of A/P/Z/L/G/I/T/Y
        n = (address << 8) | replacement
    else:
        # eight-letter code
        if not 0x00 <= compare <= 0xff:
            sys.exit("Invalid compare value.")
        codeLen = 8
        address |= 0x8000  # set MSB to make the third letter one of E/O/X/U/K/S/V/N
        n = (address << 16) | (replacement << 8) | compare
    return _encode_lowlevel(n, codeLen)

# --- tests ----------------------------------------------------------------------------------------

assert decode_code("dapapa") is None
assert decode_code("papapap") is None
assert decode_code("dananana") is None

assert parse_values("abcde:ff") is None
assert parse_values("abcd:eff") is None
assert parse_values("abcd?fff:ff") is None

assert stringify_values(*decode_code("aaaaaa")) == "8000:00"
assert stringify_values(*decode_code("aaaaan")) == "8700:08"
assert stringify_values(*decode_code("aaaana")) == "8807:00"
assert stringify_values(*decode_code("aaanaa")) == "f008:00"
assert stringify_values(*decode_code("aaeaaa")) == "8000:00"  # canonical: aaaaaa
assert stringify_values(*decode_code("aayaaa")) == "8070:00"
assert stringify_values(*decode_code("anaaaa")) == "8080:70"
assert stringify_values(*decode_code("naaaaa")) == "8000:87"
assert stringify_values(*decode_code("nnnnnn")) == "ffff:ff"  # canonical: nnynnn
assert stringify_values(*decode_code("nnynnn")) == "ffff:ff"

assert stringify_values(*decode_code("aaaaaaaa")) == "8000?00:00"  # canonical: aaeaaaaa
assert stringify_values(*decode_code("aaeaaaaa")) == "8000?00:00"
assert stringify_values(*decode_code("aaeaaaan")) == "8000?70:08"
assert stringify_values(*decode_code("aaeaaana")) == "8000?87:00"
assert stringify_values(*decode_code("aaeaanaa")) == "8700?08:00"
assert stringify_values(*decode_code("aaeanaaa")) == "8807?00:00"
assert stringify_values(*decode_code("aaenaaaa")) == "f008?00:00"
assert stringify_values(*decode_code("aanaaaaa")) == "8070?00:00"
assert stringify_values(*decode_code("aneaaaaa")) == "8080?00:70"
assert stringify_values(*decode_code("naeaaaaa")) == "8000?00:87"
assert stringify_values(*decode_code("nnnnnnnn")) == "ffff?ff:ff"
assert stringify_values(*decode_code("nnynnnnn")) == "ffff?ff:ff"  # canonical: nnnnnnnn

assert encode_code(*parse_values("0000:00")) == "AAAAAA"  # canonical: 8000:00
assert encode_code(*parse_values("7fff:ff")) == "NNYNNN"  # canonical: ffff:ff
assert encode_code(*parse_values("8000:00")) == "AAAAAA"
assert encode_code(*parse_values("8000:87")) == "NAAAAA"
assert encode_code(*parse_values("8070:00")) == "AAYAAA"
assert encode_code(*parse_values("8080:70")) == "ANAAAA"
assert encode_code(*parse_values("8700:08")) == "AAAAAN"
assert encode_code(*parse_values("8807:00")) == "AAAANA"
assert encode_code(*parse_values("f008:00")) == "AAANAA"
assert encode_code(*parse_values("ffff:ff")) == "NNYNNN"

assert encode_code(*parse_values("0000?00:00")) == "AAEAAAAA"  # canonical: 8000?00:00
assert encode_code(*parse_values("7fff?ff:ff")) == "NNNNNNNN"  # canonical: ffff?ff:ff
assert encode_code(*parse_values("8000?00:00")) == "AAEAAAAA"
assert encode_code(*parse_values("8000?00:87")) == "NAEAAAAA"
assert encode_code(*parse_values("8000?70:08")) == "AAEAAAAN"
assert encode_code(*parse_values("8000?87:00")) == "AAEAAANA"
assert encode_code(*parse_values("8070?00:00")) == "AANAAAAA"
assert encode_code(*parse_values("8080?00:70")) == "ANEAAAAA"
assert encode_code(*parse_values("8700?08:00")) == "AAEAANAA"
assert encode_code(*parse_values("8807?00:00")) == "AAEANAAA"
assert encode_code(*parse_values("f008?00:00")) == "AAENAAAA"
assert encode_code(*parse_values("ffff?ff:ff")) == "NNNNNNNN"
