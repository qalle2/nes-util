"""Converts a 6-letter NES Game Genie code into 8 letters using the iNES ROM file (.nes)."""

import sys
try:
    import nesgenielib
except ImportError:
    sys.exit("Module nesgenielib not found. Get it from https://github.com/qalle2/nesgenie")

# smallest possible PRG ROM bank sizes for mappers in KiB (32 = no bankswitching);
# http://wiki.nesdev.com/w/index.php/List_of_mappers
# these are the mappers used by at least three games among my 1951 verified good dumps ("[!]"),
# except that mapper 215 is omitted because I'm not sure about it
MIN_PRG_BANK_SIZES_KIB = {
    0: 32,  # NROM
    1: 16,  # SxROM, MMC1
    2: 16,  # UxROM
    3: 32,  # CNROM
    4: 8,  # TxROM, MMC3, MMC6
    5: 8,  # ExROM, MMC5
    7: 32,  # AxROM
    9: 8,  # PxROM, MMC2
    10: 16,  # FxROM, MMC4
    11: 32,  # Color Dreams
    15: 8,  # 100-in-1 Contra Function 16
    16: 16,  # some Bandai FCG boards
    18: 8,  # Jaleco SS8806
    19: 8,  # Namco 163
    23: 8,  # VRC2b, VRC4e
    25: 8,  # VRC4b, VRC4d
    33: 8,  # Taito TC0190
    34: 32,  # BNROM, NINA-001
    64: 8,  # RAMBO-1
    66: 32,  # GxROM, MxROM
    69: 8,  # FME-7, Sunsoft 5B
    70: 16,  # (unnamed)
    71: 16,  # Camerica/Codemasters
    75: 8,  # VRC1
    79: 32,  # NINA-003/NINA-006
    80: 8,  # Taito X1-005
    83: 8,  # Cony/Yoko
    87: 32,  # (unnamed)
    88: 8,  # (unnamed)
    90: 8,  # J.Y. Company ASIC
    91: 8,  # (unnamed)
    99: 8,  # (used by Vs. System games)
    112: 8,  # (unnamed)
    113: 32,  # NINA-003/NINA-006??
    115: 16,  # Kasheng SFC-02B/-03/-004
    118: 8,  # TxSROM, MMC3
    119: 8,  # TQROM, MMC3
    139: 32,  # Sachen 8259
    141: 32,  # Sachen 8259
    146: 32,  # NINA-003-006
    148: 32,  # Sachen SA-008-A / Tengen 800008
    150: 32,  # Sachen SA-015/SA-630
    163: 32,  # Nanjing
    185: 32,  # CNROM with protection diodes
    196: 8,  # MMC3 variant
    209: 8,  # Jingtai / J.Y. Company ASIC
    232: 16,  # Camerica/Codemasters Quattro
    234: 32,  # Maxi 15 multicart
    243: 32,  # Sachen SA-020A
}

def read_iNES_header(handle):
    """Read the header of an iNES ROM file. Return (PRG_ROM_size, mapper)."""

    fileSize = handle.seek(0, 2)
    if fileSize < 16:
        sys.exit("The file is smaller than an iNES header.")

    # read the header, split to fields
    handle.seek(0)
    header = handle.read(16)
    (id_, PRGSize16KiB, flags6, flags7) = (header[0:4], header[4], header[6], header[7])

    # validate and decode fields
    if id_ != b"NES\x1a":
        sys.exit("Not an iNES ROM file (.nes).")
    PRGSize = (PRGSize16KiB if PRGSize16KiB else 256) * 16 * 1024
    if fileSize < 16 + PRGSize:
        sys.exit("The file is smaller than header plus PRG ROM.")
    mapper = (flags7 & 0xf0) | (flags6 >> 4)

    return (PRGSize, mapper)

def get_PRG_bank_size(mapper, PRGSize):
    """Get the smallest PRG ROM bank size this mapper supports."""

    PRGBankSizeKiB = MIN_PRG_BANK_SIZES_KIB.get(mapper)
    if PRGBankSizeKiB is None:
        print(f"Unknown mapper {mapper:d}; you may get more codes than necessary.", file=sys.stderr)
        PRGBankSizeKiB = 8
    PRGBankSize = PRGBankSizeKiB * 1024
    if PRGBankSize >= PRGSize:
        sys.exit("There is no reason to use eight-letter codes with this game.")
    return PRGBankSize

def get_compare_values(handle, PRGSize, PRGBankSize, address):
    """Get possible compare values from the PRG ROM. Yield one value per call."""

    # get offset within each bank by ignoring the most significant bits of the address
    offset = address & (PRGBankSize - 1)
    # for each bank, read the byte at that offset
    for PRGPos in range(offset, PRGSize, PRGBankSize):
        handle.seek(16 + PRGPos)
        yield handle.read(1)[0]

def main():
    """The main function."""

    if sys.version_info[0] != 3:
        print("Warning: possibly incompatible Python version.", file=sys.stderr)

    # read args
    if len(sys.argv) != 3:
        sys.exit(
            "Convert a 6-letter NES Game Genie code into 8 letters using the iNES ROM file (.nes). "
            "Args: file code"
        )
    (file, code) = (sys.argv[1], sys.argv[2])  # pylint complains about [1:]

    # validate and decode the code
    decoded = nesgenielib.decode_code(code)
    if decoded is None or len(decoded) == 3:
        sys.exit("Invalid six-letter Game Genie code.")
    (address, replacement) = decoded

    try:
        with open(file, "rb") as handle:
            (PRGSize, mapper) = read_iNES_header(handle)
            PRGBankSize = get_PRG_bank_size(mapper, PRGSize)
            compareValues = set(get_compare_values(handle, PRGSize, PRGBankSize, address))
    except OSError:
        sys.exit("Error reading the file.")

    # ignore a compare value that equals the replacement value
    compareValues.discard(replacement)

    if compareValues:
        print("Try each of these eight-letter codes instead of your six-letter code:")
        codes = (nesgenielib.encode_code(address, replacement, comp) for comp in compareValues)
        for code in sorted(codes):
            print(code)
    else:
        print("No eight-letter codes found.")

if __name__ == "__main__":
    main()
