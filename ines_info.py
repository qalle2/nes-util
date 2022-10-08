import os, struct, sys

def decode_ines_header(handle):
    # parse iNES ROM header
    # does not support VS System or PlayChoice-10 flags or NES 2.0 header
    # return: None on error, otherwise a dict with the following keys:
    #    trainerStart: trainer address
    #    trainerSize:  trainer size
    #    prgStart:     PRG ROM address
    #    prgSize:      PRG ROM size
    #    chrStart:     CHR ROM address
    #    chrSize:      CHR ROM size
    #    mapper:       iNES mapper number (0x00-0xff)
    #    mirroring:    name table mirroring ('h'=horizontal, 'v'=vertical,
    #                  'f'=four-screen)
    #    extraRam:     does the game have extra RAM? (bool)
    # see https://www.nesdev.org/wiki/INES

    fileSize = handle.seek(0, 2)
    if fileSize < 16:
        return None

    handle.seek(0)
    (id_, prgSize, chrSize, flags6, flags7) \
    = struct.unpack("4s4B8x", handle.read(16))

    prgSize = (prgSize if prgSize else 256) * 16 * 1024  # 0 = 256
    chrSize = chrSize * 8 * 1024
    trainerSize = bool(flags6 & 0b100) * 512

    if id_ != b"NES\x1a" or fileSize < 16 + trainerSize + prgSize + chrSize:
        return None

    if flags6 & 0b1000:
        mirroring = "four-screen"
    elif flags6 & 0b1:
        mirroring = "vertical"
    else:
        mirroring = "horizontal"

    return {
        "trainerSize": trainerSize,
        "prgSize":     prgSize,
        "chrSize":     chrSize,
        "mapper":      (flags7 & 0b11110000) | (flags6 >> 4),
        "mirroring":   mirroring,
        "extraRam":    bool(flags6 & 0b10),
    }

def main():
    # parse command line arguments
    if len(sys.argv) != 2:
        sys.exit("Print information of an iNES ROM file (.nes).")
    inputFile = sys.argv[1]
    if not os.path.isfile(inputFile):
        sys.exit("File not found.")

    # get info
    try:
        with open(inputFile, "rb") as handle:
            fileInfo = decode_ines_header(handle)
    except OSError:
        sys.exit("Error reading the file.")
    if fileInfo is None:
        sys.exit("Invalid iNES ROM file.")

    # print info
    print("trainer size:", fileInfo["trainerSize"])
    print("PRG ROM size:", fileInfo["prgSize"])
    print("CHR ROM size:", fileInfo["chrSize"])
    print("iNES mapper number:", fileInfo["mapper"])
    print("name table mirroring:", fileInfo["mirroring"])
    print("has extra RAM at $6000-$7fff:", ("no", "yes")[fileInfo["extraRam"]])

main()
