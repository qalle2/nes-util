"""Create an iNES ROM file (.nes) from PRG ROM and CHR ROM data files."""

import argparse
import os
import struct
import sys

def parse_arguments():
    """Parse command line arguments using argparse."""

    parser = argparse.ArgumentParser(
        description="Create an iNES ROM file (.nes) from PRG ROM and CHR ROM data files."
    )

    parser.add_argument(
        "-p", "--prg-rom", required=True,
        help="PRG ROM data file. Required. Size: 16...4096 KiB and a multiple of 16 KiB."
    )
    parser.add_argument(
        "-c", "--chr-rom",
        help="CHR ROM data file. Optional. Size: 0...2040 KiB and a multiple of 8 KiB."
    )
    parser.add_argument(
        "-m", "--mapper", type=int, default=0,
        help="Mapper number (0...255). Default=0 (NROM)."
    )
    parser.add_argument(
        "-n", "--mirroring", choices=("h", "v", "f"), default="h",
        help="Type of name table mirroring: h=horizontal (default), v=vertical, f=four-screen."
    )
    parser.add_argument(
        "-s", "--save-ram", action="store_true",
        help="The game contains battery-backed PRG RAM at $6000...$7fff."
    )
    parser.add_argument(
        "outputFile",
        help="The iNES ROM file (.nes) to write."
    )

    args = parser.parse_args()

    if not os.path.isfile(args.prg_rom):
        sys.exit("PRG ROM file not found.")
    if args.chr_rom is not None and not os.path.isfile(args.chr_rom):
        sys.exit("CHR ROM file not found.")
    if not 0 <= args.mapper <= 255:
        sys.exit("Invalid mapper number.")
    if os.path.exists(args.outputFile):
        sys.exit("Output file already exists.")

    return args

def create_ines_header(prgSize, chrSize, mapper=0, mirroring="h", saveRam=False):
    """Return a 16-byte iNES header. See https://wiki.nesdev.com/w/index.php/INES
    prgSize: PRG ROM size
    chrSize: CHR ROM size
    mapper: mapper number
    mirroring: name table mirroring ('h'/'v'/'f')
    saveRam: does the game have save RAM"""

    # get PRG ROM size in 16-KiB units; encode 256 as 0
    (prgSize, remainder) = divmod(prgSize, 16 * 1024)
    if remainder or not 1 <= prgSize <= 256:
        sys.exit("Invalid PRG ROM size.")
    prgSize %= 256

    # get CHR ROM size in 8-KiB units
    (chrSize, remainder) = divmod(chrSize, 8 * 1024)
    if remainder or chrSize > 255:
        sys.exit("Invalid CHR ROM size.")

    # encode flags
    flags6 = (mapper & 0x0f) << 4
    if mirroring == "v":
        flags6 |= 0x01
    elif mirroring == "f":
        flags6 |= 0x08
    if saveRam:
        flags6 |= 0x02
    flags7 = mapper & 0xf0

    return struct.pack("4s4B8s", b"NES\x1a", prgSize, chrSize, flags6, flags7, 8 * b"\x00")

def copy_file(source, target):
    """Copy source file to current position in target file in chunks."""

    bytesLeft = source.seek(0, 2)
    source.seek(0)
    while bytesLeft:
        chunkSize = min(bytesLeft, 2 ** 20)
        target.write(source.read(chunkSize))
        bytesLeft -= chunkSize

def main():
    args = parse_arguments()

    try:
        prgSize = os.path.getsize(args.prg_rom)
    except OSError:
        sys.exit("Error getting PRG ROM file size.")

    if args.chr_rom is None:
        chrSize = 0
    else:
        try:
            chrSize = os.path.getsize(args.chr_rom)
        except OSError:
            sys.exit("Error getting CHR ROM file size.")

    header = create_ines_header(
        prgSize=prgSize,
        chrSize=chrSize,
        mapper=args.mapper,
        mirroring=args.mirroring,
        saveRam=args.save_ram,
    )

    try:
        with open(args.outputFile, "wb") as target:
            target.seek(0)
            target.write(header)

            # copy PRG ROM data
            try:
                with open(args.prg_rom, "rb") as source:
                    copy_file(source, target)
            except OSError:
                sys.exit("Error copying PRG ROM data.")

            if chrSize:
                # copy CHR ROM data
                try:
                    with open(args.chr_rom, "rb") as source:
                        copy_file(source, target)
                except OSError:
                    sys.exit("Error copying CHR ROM data.")
    except OSError:
        sys.exit("Error writing output file.")

if __name__ == "__main__":
    main()
