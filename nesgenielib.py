"""Decode and encode Nintendo Entertainment System (NES) Game Genie codes.
See http://nesdev.com/nesgg.txt"""

CODE_LETTERS = "APZLGITYEOXUKSVN"
_DECODE_KEY = (3, 5, 2, 4, 1, 0, 7, 6)

def decode_code(code):
    """Decode a Game Genie code.
    code: 6 or 8 letters from CODE_LETTERS
    return:
        if invalid  code: None
        if 6-letter code: (CPU_address, replacement_value, None)
        if 8-letter code: (CPU_address, replacement_value, compare_value)"""

    # validate
    if not (len(code) in (6, 8) and set(code.upper()).issubset(set(CODE_LETTERS))):
        return None
    # convert letters into 4-bit ints
    code = [CODE_LETTERS.index(letter) for letter in code.upper()]
    # combine to a 24/32-bit integer according to _DECODE_KEY
    # (16 bits for CPU address, 8 for replacement value, optionally 8 for compare value)
    n = 0
    for loPos in _DECODE_KEY[:len(code)]:
        hiPos = (loPos - 1) % len(code)
        n = (n << 4) | (code[hiPos] & 8) | (code[loPos] & 7)
    # split and set MSB of CPU address
    (n, comp) = (n, None) if len(code) == 6 else (n >> 8, n & 0xff)
    (addr, repl) = (n >> 8, n & 0xff)
    return (addr | 0x8000, repl, comp)

assert decode_code("apapa")     is None
assert decode_code("apapapa")   is None
assert decode_code("apapapapa") is None
assert decode_code("dapapa")    is None
assert decode_code("dapapapa")  is None

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

def encode_code(addr, repl, comp=None):
    """Encode a Game Genie code.
    addr: CPU address (0...0xffff; MSB ignored)
    repl: replacement value (0...0xff)
    comp: compare value (0...0xff or None)
    return:
        if invalid arguments  : None
        if compare is None    : 6-letter code
        if compare is not None: 8-letter code"""

    # validate
    if not (
        0 <= addr <= 0xffff and 0 <= repl <= 0xff and (comp is None or 0 <= comp <= 0xff)
    ):
        return None
    # combine args into a 24/32-bit integer; clear/set MSB of address to get correct 3rd
    # letter later (one of APZLGITY for 6-letter codes, one of EOXUKSVN for 8-letter codes)
    if comp is None:
        codeLen = 6
        addr &= 0x7fff
        n = (addr << 8) | repl
    else:
        codeLen = 8
        addr |= 0x8000
        n = (addr << 16) | (repl << 8) | comp
    # convert 24/32-bit int into 4-bit ints according to _DECODE_KEY
    encoded = codeLen * [0]
    for loPos in _DECODE_KEY[codeLen-1::-1]:
        hiPos = (loPos - 1) % codeLen
        encoded[loPos] |= n & 7
        encoded[hiPos] |= n & 8
        n >>= 4
    # convert 4-bit ints into letters
    return "".join(CODE_LETTERS[i] for i in encoded)

assert encode_code(0x10000, 0x00)       is None
assert encode_code(0xffff, 0x100)       is None
assert encode_code(0xffff, 0xff, 0x100) is None

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
