"""qalle's NES library (Nintendo Entertainment System stuff)."""

import struct

# NES master palette
# key=index, value=(red, green, blue); source: FCEUX (fceux.pal)
PALETTE = {
    0x00: (0x74, 0x74, 0x74),
    0x01: (0x24, 0x18, 0x8c),
    0x02: (0x00, 0x00, 0xa8),
    0x03: (0x44, 0x00, 0x9c),
    0x04: (0x8c, 0x00, 0x74),
    0x05: (0xa8, 0x00, 0x10),
    0x06: (0xa4, 0x00, 0x00),
    0x07: (0x7c, 0x08, 0x00),
    0x08: (0x40, 0x2c, 0x00),
    0x09: (0x00, 0x44, 0x00),
    0x0a: (0x00, 0x50, 0x00),
    0x0b: (0x00, 0x3c, 0x14),
    0x0c: (0x18, 0x3c, 0x5c),
    0x0d: (0x00, 0x00, 0x00),
    0x0e: (0x00, 0x00, 0x00),
    0x0f: (0x00, 0x00, 0x00),
    0x10: (0xbc, 0xbc, 0xbc),
    0x11: (0x00, 0x70, 0xec),
    0x12: (0x20, 0x38, 0xec),
    0x13: (0x80, 0x00, 0xf0),
    0x14: (0xbc, 0x00, 0xbc),
    0x15: (0xe4, 0x00, 0x58),
    0x16: (0xd8, 0x28, 0x00),
    0x17: (0xc8, 0x4c, 0x0c),
    0x18: (0x88, 0x70, 0x00),
    0x19: (0x00, 0x94, 0x00),
    0x1a: (0x00, 0xa8, 0x00),
    0x1b: (0x00, 0x90, 0x38),
    0x1c: (0x00, 0x80, 0x88),
    0x1d: (0x00, 0x00, 0x00),
    0x1e: (0x00, 0x00, 0x00),
    0x1f: (0x00, 0x00, 0x00),
    0x20: (0xfc, 0xfc, 0xfc),
    0x21: (0x3c, 0xbc, 0xfc),
    0x22: (0x5c, 0x94, 0xfc),
    0x23: (0xcc, 0x88, 0xfc),
    0x24: (0xf4, 0x78, 0xfc),
    0x25: (0xfc, 0x74, 0xb4),
    0x26: (0xfc, 0x74, 0x60),
    0x27: (0xfc, 0x98, 0x38),
    0x28: (0xf0, 0xbc, 0x3c),
    0x29: (0x80, 0xd0, 0x10),
    0x2a: (0x4c, 0xdc, 0x48),
    0x2b: (0x58, 0xf8, 0x98),
    0x2c: (0x00, 0xe8, 0xd8),
    0x2d: (0x78, 0x78, 0x78),
    0x2e: (0x00, 0x00, 0x00),
    0x2f: (0x00, 0x00, 0x00),
    0x30: (0xfc, 0xfc, 0xfc),
    0x31: (0xa8, 0xe4, 0xfc),
    0x32: (0xc4, 0xd4, 0xfc),
    0x33: (0xd4, 0xc8, 0xfc),
    0x34: (0xfc, 0xc4, 0xfc),
    0x35: (0xfc, 0xc4, 0xd8),
    0x36: (0xfc, 0xbc, 0xb0),
    0x37: (0xfc, 0xd8, 0xa8),
    0x38: (0xfc, 0xe4, 0xa0),
    0x39: (0xe0, 0xfc, 0xa0),
    0x3a: (0xa8, 0xf0, 0xbc),
    0x3b: (0xb0, 0xfc, 0xcc),
    0x3c: (0x9c, 0xfc, 0xf0),
    0x3d: (0xc4, 0xc4, 0xc4),
    0x3e: (0x00, 0x00, 0x00),
    0x3f: (0x00, 0x00, 0x00),
}

# Smallest supported PRG ROM bank sizes for iNES mappers, in KiB (32 if no bankswitching).
# Source: http://wiki.nesdev.com/w/index.php/List_of_mappers
# Only includes mappers used by at least three games among my verified good dumps ("[!]").
_MIN_PRG_BANK_SIZES = {
    0:   32,  # NROM
    1:   16,  # SxROM, MMC1
    2:   16,  # UxROM
    3:   32,  # CNROM
    4:   8,   # TxROM, MMC3, MMC6
    5:   8,   # ExROM, MMC5
    7:   32,  # AxROM
    9:   8,   # PxROM, MMC2
    10:  16,  # FxROM, MMC4
    11:  32,  # Color Dreams
    15:  8,   # 100-in-1 Contra Function 16
    16:  16,  # some Bandai FCG boards
    18:  8,   # Jaleco SS8806
    19:  8,   # Namco 163
    23:  8,   # VRC2b, VRC4e
    25:  8,   # VRC4b, VRC4d
    33:  8,   # Taito TC0190
    34:  32,  # BNROM, NINA-001
    64:  8,   # RAMBO-1
    66:  32,  # GxROM, MxROM
    69:  8,   # FME-7, Sunsoft 5B
    70:  16,  # (unnamed)
    71:  16,  # Camerica/Codemasters
    75:  8,   # VRC1
    79:  32,  # NINA-003/NINA-006
    80:  8,   # Taito X1-005
    83:  8,   # Cony/Yoko
    87:  32,  # (unnamed)
    88:  8,   # (unnamed)
    90:  8,   # J.Y. Company ASIC
    91:  8,   # (unnamed)
    99:  8,   # (used by Vs. System games)
    112: 8,   # (unnamed)
    113: 32,  # NINA-003/NINA-006??
    115: 16,  # Kasheng SFC-02B/-03/-004
    118: 8,   # TxSROM, MMC3
    119: 8,   # TQROM, MMC3
    139: 32,  # Sachen 8259
    141: 32,  # Sachen 8259
    146: 32,  # NINA-003-006
    148: 32,  # Sachen SA-008-A / Tengen 800008
    150: 32,  # Sachen SA-015/SA-630
    163: 32,  # Nanjing
    185: 32,  # CNROM with protection diodes
    196: 8,   # MMC3 variant
    209: 8,   # Jingtai / J.Y. Company ASIC
    232: 16,  # Camerica/Codemasters Quattro
    234: 32,  # Maxi 15 multicart
    243: 32,  # Sachen SA-020A
}

_INES_ID = b"NES\x1a"

GAME_GENIE_LETTERS = "APZLGITYEOXUKSVN"
_GAME_GENIE_DECODE_KEY = (3, 5, 2, 4, 1, 0, 7, 6)  # at 0x0eb6 in Game Genie PRG ROM

class QneslibError(Exception):
    pass

# -------------------------------------------------------------------------------------------------

def min_prg_bank_size_for_mapper(mapper):
    """Get the smallest PRG ROM bank size supported by the mapper.
    mapper: iNES mapper number (0x00-0xff)
    return: 8_192/16_384/32_768 (8_192 if unknown mapper)"""

    return _MIN_PRG_BANK_SIZES.get(mapper, 8) * 1024

def min_prg_bank_size(prgSize, mapper):
    """Get the smallest PRG ROM bank size a game may use.
    prgSize: PRG ROM size
    mapper:  iNES mapper number (0x00-0xff)
    return:  8_192/16_384/32_768 (8_192 if unknown mapper)"""

    return min(min_prg_bank_size_for_mapper(mapper), prgSize)

def is_prg_bankswitched(prgSize, mapper):
    """Does the game use PRG ROM bankswitching? (May give false positives, especially if the
    mapper is unknown. Should not give false negatives.)
    prgSize: PRG ROM size
    mapper:  iNES mapper number (0x00-0xff)
    return:  bool"""

    return min_prg_bank_size_for_mapper(mapper) < prgSize

def is_mapper_known(mapper):
    """Is the mapper known by this program? (If not, mapper functions are more likely to return
    incorrect info.)
    mapper: iNES mapper number (0x00-0xff)
    return: bool"""

    return mapper in _MIN_PRG_BANK_SIZES

def address_prg_to_cpu(prgAddr, prgBankSize):
    """Convert a PRG ROM address into possible CPU ROM addresses.
    prgAddr:     PRG ROM address
    prgBankSize: PRG ROM bank size (8_192/16_384/32_768)
    generate:    CPU ROM addresses (0x8000-0xffff)"""

    offset = prgAddr & (prgBankSize - 1)  # within each bank
    yield from (origin | offset for origin in range(0x8000, 0x10000, prgBankSize))

def address_cpu_to_prg(cpuAddr, prgBankSize, prgSize):
    """Convert a CPU ROM address into possible PRG ROM addresses.
    cpuAddr:     CPU ROM address (0x8000-0xffff)
    prgBankSize: PRG ROM bank size (8_192/16_384/32_768)
    prgSize:     PRG ROM size
    generate:    PRG ROM addresses"""

    offset = cpuAddr & (prgBankSize - 1)  # within each bank
    yield from range(offset, prgSize, prgBankSize)

def tile_slice_decode(loByte, hiByte):
    """Decode 8*1 pixels of one tile of CHR data.
    loByte: low bitplane (0x00-0xff)
    hiByte: high bitplane (0x00-0xff)
    return: eight 2-bit ints"""

    pixels = []
    for i in range(8):
        pixels.append((loByte & 1) | ((hiByte & 1) << 1))
        loByte >>= 1
        hiByte >>= 1
    return pixels[::-1]

def tile_slice_encode(pixels):
    """Encode 8*1 pixels of one tile of CHR data.
    pixels: eight 2-bit ints
    return: (low_bitplane, high_bitplane); both 0x00-0xff"""

    loByte = hiByte = 0
    for pixel in pixels:
        loByte = (loByte << 1) | (pixel &  1)
        hiByte = (hiByte << 1) | (pixel >> 1)
    return (loByte, hiByte)

# -------------------------------------------------------------------------------------------------

def ines_header_decode(handle):
    """Parse the header of an iNES ROM file.
    handle: iNES ROM file
    return: None on error, otherwise a dict with the following keys:
        trainerStart: trainer address
        trainerSize:  trainer size
        prgStart:     PRG ROM address
        prgSize:      PRG ROM size
        chrStart:     CHR ROM address
        chrSize:      CHR ROM size
        mapper:       iNES mapper number (0x00-0xff)
        mirroring:    name table mirroring ('h'=horizontal, 'v'=vertical, 'f'=four-screen)
        extraRam:     does the game have extra RAM? (bool)"""

    fileSize = handle.seek(0, 2)

    if fileSize < 16:
        return None

    # get fields from header
    handle.seek(0)
    (id_, prgSize, chrSize, flags6, flags7) = struct.unpack("4s4B8x", handle.read(16))

    # PRG ROM / CHR ROM / trainer size in bytes (note: PRG ROM size 0 -> 256)
    prgSize = (prgSize if prgSize else 256) * 16 * 1024
    chrSize = chrSize * 8 * 1024
    trainerSize = bool(flags6 & 0x04) * 512

    # validate id and file size (note: accept files that are too large)
    if id_ != _INES_ID or fileSize < 16 + trainerSize + prgSize + chrSize:
        return None

    # type of name table mirroring
    if flags6 & 0x08:
        mirroring = "f"
    elif flags6 & 0x01:
        mirroring = "v"
    else:
        mirroring = "h"

    return {
        "trainerStart": 16,
        "trainerSize": trainerSize,
        "prgStart": 16 + trainerSize,
        "prgSize": prgSize,
        "chrStart": 16 + trainerSize + prgSize,
        "chrSize": chrSize,
        "mapper": (flags7 & 0xf0) | (flags6 >> 4),
        "mirroring": mirroring,
        "extraRam": bool(flags6 & 0x02),
    }

def ines_header_encode(prgSize, chrSize, mapper=0, mirroring="h", extraRam=False):
    """Create an iNES file header.
    prgSize:   PRG ROM size
    chrSize:   CHR ROM size
    mapper:    iNES mapper number (0x00-0xff)
    mirroring: name table mirroring ('h'=horizontal, 'v'=vertical, 'f'=four-screen)
    extraRam:  does the game have extra RAM? (bool)
    return:    16 bytes
    raise:     QneslibError on error"""

    # get PRG ROM size in 16-KiB units (note: 256 -> 0)
    (prgSize, remainder) = divmod(prgSize, 16 * 1024)
    if remainder or not 1 <= prgSize <= 256:
        raise QneslibError("invalid PRG ROM size")
    prgSize %= 256

    # get CHR ROM size in 8-KiB units
    (chrSize, remainder) = divmod(chrSize, 8 * 1024)
    if remainder or chrSize > 255:
        raise QneslibError("invalid CHR ROM size")

    # encode flags
    flags6 = (mapper & 0x0f) << 4
    flags6 |= {"h": 0x00, "v": 0x01, "f": 0x08}[mirroring]
    if extraRam:
        flags6 |= 0x02
    flags7 = mapper & 0xf0

    return struct.pack("4s4B8s", _INES_ID, prgSize, chrSize, flags6, flags7, 8 * b"\x00")

# -------------------------------------------------------------------------------------------------

def game_genie_decode(code):
    """Decode a Game Genie code.
    code: 6 or 8 letters from GAME_GENIE_LETTERS
    return:
        if invalid code: None
        otherwise:       (cpu_address, replacement_value, compare_value):
            cpu_address:       0x8000-0xffff
            replacement_value: 0x00-0xff
            compare_value:     None if 6-letter code, 0x00-0xff if 8-letter code"""

    # see http://nesdev.com/nesgg.txt

    # validate
    if len(code) not in (6, 8) or not set(code.upper()).issubset(set(GAME_GENIE_LETTERS)):
        return None
    # convert letters into integers (0x0-0xf)
    code = [GAME_GENIE_LETTERS.index(letter) for letter in code.upper()]
    # combine integers to a 24/32-bit integer according to _GAME_GENIE_DECODE_KEY
    # (16 bits for CPU address, 8 for replacement value, optionally 8 for compare value)
    bigint = 0
    for loPos in _GAME_GENIE_DECODE_KEY[:len(code)]:
        hiPos = (loPos - 1) % len(code)
        bigint = (bigint << 4) | (code[hiPos] & 8) | (code[loPos] & 7)
    # split integer and set MSB of CPU address
    (bigint, comp) = (bigint, None) if len(code) == 6 else (bigint >> 8, bigint & 0xff)
    (addr, repl) = (bigint >> 8, bigint & 0xff)
    return (addr | 0x8000, repl, comp)

assert game_genie_decode("baaaaa")   is None
assert game_genie_decode("aaaaan")   == (0x8700, 0x08, None)
assert game_genie_decode("aaaana")   == (0x8807, 0x00, None)
assert game_genie_decode("aaanaa")   == (0xf008, 0x00, None)
assert game_genie_decode("aayaaa")   == (0x8070, 0x00, None)
assert game_genie_decode("anaaaa")   == (0x8080, 0x70, None)
assert game_genie_decode("naaaaa")   == (0x8000, 0x87, None)
assert game_genie_decode("naeaaaaa") == (0x8000, 0x87, 0x00)
assert game_genie_decode("aneaaaaa") == (0x8080, 0x70, 0x00)
assert game_genie_decode("aanaaaaa") == (0x8070, 0x00, 0x00)
assert game_genie_decode("aaenaaaa") == (0xf008, 0x00, 0x00)
assert game_genie_decode("aaeanaaa") == (0x8807, 0x00, 0x00)
assert game_genie_decode("aaeaanaa") == (0x8700, 0x00, 0x08)
assert game_genie_decode("aaeaaana") == (0x8000, 0x00, 0x87)
assert game_genie_decode("aaeaaaan") == (0x8000, 0x08, 0x70)

def game_genie_encode(addr, repl, comp=None):
    """Encode a Game Genie code.
    addr: CPU address (0x0000-0xffff; MSB ignored)
    repl: replacement value (0x00-0xff)
    comp: compare value (0x00-0xff/None)
    return:
        if invalid arguments: None
        if comp is None     : 6-letter code
        if comp is not None : 8-letter code"""

    # see http://nesdev.com/nesgg.txt

    # validate
    if not 0 <= addr <= 0xffff or not 0 <= repl <= 0xff \
    or comp is not None and not 0 <= comp <= 0xff:
        return None
    # combine args into a 24/32-bit integer; clear/set MSB of address to get correct 3rd letter
    # later (one of APZLGITY for 6-letter codes, one of EOXUKSVN for 8-letter codes)
    if comp is None:
        codeLen = 6
        addr &= 0x7fff
        bigint = (addr << 8) | repl
    else:
        codeLen = 8
        addr |= 0x8000
        bigint = (addr << 16) | (repl << 8) | comp
    # convert the 24/32-bit int into 4-bit ints according to _GAME_GENIE_DECODE_KEY
    encoded = codeLen * [0]
    for loPos in _GAME_GENIE_DECODE_KEY[codeLen-1::-1]:
        hiPos = (loPos - 1) % codeLen
        encoded[loPos] |= bigint & 0x7
        encoded[hiPos] |= bigint & 0x8
        bigint >>= 4
    # convert 4-bit ints into letters
    return "".join(GAME_GENIE_LETTERS[i] for i in encoded)

assert game_genie_encode(-1,     0x00)       is None
assert game_genie_encode(0x8000, 0x87)       == "NAAAAA"
assert game_genie_encode(0x8070, 0x00)       == "AAYAAA"
assert game_genie_encode(0x8080, 0x70)       == "ANAAAA"
assert game_genie_encode(0x8700, 0x08)       == "AAAAAN"
assert game_genie_encode(0x8807, 0x00)       == "AAAANA"
assert game_genie_encode(0xf008, 0x00)       == "AAANAA"
assert game_genie_encode(0x8000, 0x87, 0x00) == "NAEAAAAA"
assert game_genie_encode(0x8080, 0x70, 0x00) == "ANEAAAAA"
assert game_genie_encode(0x8070, 0x00, 0x00) == "AANAAAAA"
assert game_genie_encode(0xf008, 0x00, 0x00) == "AAENAAAA"
assert game_genie_encode(0x8807, 0x00, 0x00) == "AAEANAAA"
assert game_genie_encode(0x8700, 0x00, 0x08) == "AAEAANAA"
assert game_genie_encode(0x8000, 0x00, 0x87) == "AAEAAANA"
assert game_genie_encode(0x8000, 0x08, 0x70) == "AAEAAAAN"
