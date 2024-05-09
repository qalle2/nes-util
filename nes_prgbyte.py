import os, struct, sys

def ines_header_decode(handle):
    # parse the header of an iNES ROM file;
    # see https://www.nesdev.org/wiki/INES
    # does not support VS System or PlayChoice-10 flags or NES 2.0 header;
    # handle: iNES ROM file;
    # return: tuple: (PRG_ROM_address, PRG_ROM_size)

    fileSize = handle.seek(0, 2)
    if fileSize < 16:
        sys.exit("Not an iNES ROM file.")

    # get fields from header
    handle.seek(0)
    (id_, prgSize, chrSize, flags6, flags7) = struct.unpack(
        "4s4B8x", handle.read(16)
    )
    if id_ != b"NES\x1a":
        sys.exit("Not an iNES ROM file.")

    # get PRG ROM and trainer size (PRG ROM size 0 -> 256)
    prgSize = (prgSize if prgSize else 256) * 16 * 1024
    trainerSize = bool(flags6 & 0b00000100) * 512

    # validate file size
    if fileSize < 16 + trainerSize + prgSize:
        sys.exit("Unexpected end of iNES ROM file.")

    return (16 + trainerSize, prgSize)

def main():
    # parse arguments
    if len(sys.argv) != 3:
        sys.exit(
            "Get byte value at specified PRG ROM address in an iNES ROM file "
            "(.nes). Arguments: file address_in_hexadecimal"
        )
    (filename, prgAddrToGet) = sys.argv[1:]

    # parse address (continue validation later)
    try:
        prgAddrToGet = int(prgAddrToGet, 16)
        if prgAddrToGet < 0:
            raise ValueError
    except ValueError:
        sys.exit("Address must be a nonnegative hexadecimal integer.")

    # read byte from file
    if not os.path.isfile(filename):
        sys.exit("File not found.")
    try:
        with open(filename, "rb") as handle:
            (prgStart, prgSize) = ines_header_decode(handle)
            if prgAddrToGet >= prgSize:
                sys.exit("Address must be smaller than PRG ROM size.")
            handle.seek(prgStart + prgAddrToGet)
            value = handle.read(1)[0]
    except OSError:
        sys.exit("Error reading the file.")

    print(f"0x{value:02x}")

main()
