"""A library for decoding and encoding NES Game Genie codes.
See http://nesdev.com/nesgg.txt"""

GENIE_LETTERS = "APZLGITYEOXUKSVN"
_GENIE_DECODE_KEY = (3, 5, 2, 4, 1, 0, 7, 6)

class NESGenieError(Exception):
    """An exception for NES Game Genie related errors."""

# --- decoding -------------------------------------------------------------------------------------

def is_valid_code(code):
    """Validate a Game Genie code case-insensitively. Return True if valid, False if invalid."""

    return len(code) in (6, 8) and not set(code.upper()) - set(GENIE_LETTERS)

assert is_valid_code("papapa")
assert is_valid_code("papapapa")
assert not is_valid_code("dapapa")
assert not is_valid_code("papapap")
assert not is_valid_code("dananana")

def _decode_lowlevel(code):
    """Decode a Game Genie code (the low-level stuff).
    code: a valid code, 6 or 8 letters, case insensitive
    Return:
        if code is 6 letters: 24 bits (16 for address, 8 for replacement value)
        if code is 8 letters: 32 bits (16 for address, 8 for replacement value, 8 for compare
        value)"""

    # decode each letter into a four-bit int
    code = tuple(GENIE_LETTERS.index(letter) for letter in code.upper())
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
    code: 6 or 8 letters from GENIE_LETTERS, case insensitive
    return: (address, replacement_value, compare_value/None)
    on error: raise NESGenieError"""

    # validate code
    if not is_valid_code(code):
        raise NESGenieError
    # decode the code into an integer (6 letters to 24 bits, 8 letters to 32 bits)
    n = _decode_lowlevel(code)
    # extract values from the integer
    if len(code) == 6:
        values = [n >> 8, n & 0xff, None]
    else:
        values = [n >> 16, (n >> 8) & 0xff, n & 0xff]
    # set most significant bit of address (NES CPU ROM starts at 0x8000)
    values[0] |= 0x8000
    return tuple(values)

assert decode_code("aaaaaa") == (0x8000, 0x00, None)
assert decode_code("aaeaaa") == (0x8000, 0x00, None)  # canonical: "aaaaaa"
assert decode_code("aaaaan") == (0x8700, 0x08, None)
assert decode_code("aaaana") == (0x8807, 0x00, None)
assert decode_code("aaanaa") == (0xf008, 0x00, None)
assert decode_code("aayaaa") == (0x8070, 0x00, None)
assert decode_code("anaaaa") == (0x8080, 0x70, None)
assert decode_code("naaaaa") == (0x8000, 0x87, None)
assert decode_code("nnynnn") == (0xffff, 0xff, None)
assert decode_code("nnnnnn") == (0xffff, 0xff, None)  # canonical: "nnynnn"

assert decode_code("aaeaaaaa") == (0x8000, 0x00, 0x00)
assert decode_code("aaaaaaaa") == (0x8000, 0x00, 0x00)  # canonical: "aaeaaaaa"
assert decode_code("aaeaaaan") == (0x8000, 0x08, 0x70)
assert decode_code("aaeaaana") == (0x8000, 0x00, 0x87)
assert decode_code("aaeaanaa") == (0x8700, 0x00, 0x08)
assert decode_code("aaeanaaa") == (0x8807, 0x00, 0x00)
assert decode_code("aaenaaaa") == (0xf008, 0x00, 0x00)
assert decode_code("aanaaaaa") == (0x8070, 0x00, 0x00)
assert decode_code("aneaaaaa") == (0x8080, 0x70, 0x00)
assert decode_code("naeaaaaa") == (0x8000, 0x87, 0x00)
assert decode_code("nnnnnnnn") == (0xffff, 0xff, 0xff)
assert decode_code("nnynnnnn") == (0xffff, 0xff, 0xff)  # canonical: "nnnnnnnn"

# --- encoding -------------------------------------------------------------------------------------

def _encode_lowlevel(codeLen, n):
    """Encode a Game Genie code (the low-level stuff).
    codeLen: length of code (6/8)
    n:
        if codeLen=6: 24 bits (16 for address, 8 for replacement value)
        if codeLen=8: 32 bits (16 for address, 8 for replacement value, 8 for compare value)
    return: a Game Genie code of length codeLen"""

    # code letters as indexes to GENIE_LETTERS
    code = codeLen * [0]
    # copy bits from n to two code positions specified by _GENIE_DECODE_KEY
    for pos in _GENIE_DECODE_KEY[codeLen-1::-1]:
        prevPos = (pos - 1) % codeLen
        code[pos] |= n & 0b0111
        code[prevPos] |= n & 0b1000
        n >>= 4
    # encode code letters from indexes to letters
    return "".join(GENIE_LETTERS[i] for i in code)

def encode_code(address, replacement, compare=None):
    """Encode a Game Genie code.
    address: NES CPU address (0x8000-0xffff or equivalently 0x0000-0x7fff)
    replacement: replacement value (0x00-0xff)
    compare: compare value (int, 0x00-0xff) or None
    return:
        if compare is None: a 6-letter code (str)
        if compare is not None: an 8-letter code (str)
    on error: raise NESGenieError"""

    if address & ~0xffff or replacement & ~0xff:
        raise NESGenieError

    if compare is None:
        # six-letter code
        codeLen = 6
        address &= 0x7fff  # clear MSB to make the third letter one of A/P/Z/L/G/I/T/Y
        n = (address << 8) | replacement
    else:
        # eight-letter code
        if compare & ~0xff:
            raise NESGenieError
        codeLen = 8
        address |= 0x8000  # set MSB to make the third letter one of E/O/X/U/K/S/V/N
        n = (address << 16) | (replacement << 8) | compare
    return _encode_lowlevel(codeLen, n)

assert encode_code(0x8000, 0x00) == "AAAAAA"
assert encode_code(0x0000, 0x00) == "AAAAAA"  # canonical: 8000:00
assert encode_code(0x8000, 0x87) == "NAAAAA"
assert encode_code(0x8070, 0x00) == "AAYAAA"
assert encode_code(0x8080, 0x70) == "ANAAAA"
assert encode_code(0x8700, 0x08) == "AAAAAN"
assert encode_code(0x8807, 0x00) == "AAAANA"
assert encode_code(0xf008, 0x00) == "AAANAA"
assert encode_code(0xffff, 0xff) == "NNYNNN"
assert encode_code(0x7fff, 0xff) == "NNYNNN"  # canonical: ffff:ff

assert encode_code(0x8000, 0x00, 0x00) == "AAEAAAAA"
assert encode_code(0x0000, 0x00, 0x00) == "AAEAAAAA"  # canonical: 8000?00:00
assert encode_code(0x8000, 0x87, 0x00) == "NAEAAAAA"
assert encode_code(0x8000, 0x08, 0x70) == "AAEAAAAN"
assert encode_code(0x8000, 0x00, 0x87) == "AAEAAANA"
assert encode_code(0x8070, 0x00, 0x00) == "AANAAAAA"
assert encode_code(0x8080, 0x70, 0x00) == "ANEAAAAA"
assert encode_code(0x8700, 0x00, 0x08) == "AAEAANAA"
assert encode_code(0x8807, 0x00, 0x00) == "AAEANAAA"
assert encode_code(0xf008, 0x00, 0x00) == "AAENAAAA"
assert encode_code(0xffff, 0xff, 0xff) == "NNNNNNNN"
assert encode_code(0x7fff, 0xff, 0xff) == "NNNNNNNN"  # canonical: ffff?ff:ff
