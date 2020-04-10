"""Create an iNES ROM file (.nes) from PRG ROM and CHR ROM data files."""

import argparse
import os
import sys
import ineslib

def parse_arguments():
    """Parse command line arguments using argparse."""

    parser = argparse.ArgumentParser(
        description="Create an iNES ROM file (.nes) from PRG ROM and CHR ROM data files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "-p", "--prg-rom", required=True,
        help="PRG ROM data file; required; the size must be 16-4096 KiB and a multiple of 16 KiB."
    )
    parser.add_argument(
        "-c", "--chr-rom",
        help="CHR ROM data file; the size must be 0-2040 KiB and a multiple of 8 KiB. If the file "
        "is empty or the argument is omitted, the game uses CHR RAM."
    )
    parser.add_argument("-m", "--mapper", type=int, default=0, help="Mapper number (0-255).")
    parser.add_argument(
        "-n", "--mirroring", choices=("h", "v", "f"), default="h",
        help="Type of name table mirroring: h=horizontal, v=vertical, f=four-screen."
    )
    parser.add_argument(
        "-s", "--save-ram", action="store_true",
        help="The game contains battery-backed PRG RAM at $6000-$7fff."
    )
    parser.add_argument("outputFile", help="The iNES ROM file (.nes) to write.")

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

def copy_file(source, target):
    """Copy source file to current position in target file in chunks."""

    bytesLeft = source.seek(0, 2)
    source.seek(0)
    while bytesLeft:
        chunkSize = min(bytesLeft, 2 ** 20)
        target.write(source.read(chunkSize))
        bytesLeft -= chunkSize

def main():
    """The main function."""

    args = parse_arguments()

    # get file sizes
    try:
        PRGSize = os.path.getsize(args.prg_rom)
    except OSError:
        sys.exit("Error getting PRG ROM file size.")
    if args.chr_rom is None:
        CHRSize = 0
    else:
        try:
            CHRSize = os.path.getsize(args.chr_rom)
        except OSError:
            sys.exit("Error getting CHR ROM file size.")

    # create iNES header
    try:
        iNESHeader = ineslib.create_iNES_header(
            PRGSize=PRGSize,
            CHRSize=CHRSize,
            mapper=args.mapper,
            mirroring=args.mirroring,
            saveRAM=args.save_ram,
        )
    except ineslib.iNESError as e:
        sys.exit("Error: " + str(e))

    # write output file
    try:
        with open(args.outputFile, "wb") as target:
            target.seek(0)
            target.write(iNESHeader)
            # copy PRG ROM data
            with open(args.prg_rom, "rb") as source:
                copy_file(source, target)
            if args.chr_rom is not None:
                # copy CHR ROM data
                with open(args.chr_rom, "rb") as source:
                    copy_file(source, target)
    except OSError:
        sys.exit("Error reading/writing files.")

if __name__ == "__main__":
    main()
