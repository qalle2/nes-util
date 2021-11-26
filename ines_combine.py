import argparse, os, sys
import qneslib  # qalle's NES library, https://github.com/qalle2/nes-util

def parse_arguments():
    """Parse command line arguments using argparse."""

    parser = argparse.ArgumentParser(
        description="Create an iNES ROM file (.nes)."
    )
    parser.add_argument(
        "-p", "--prg-rom", required=True,
        help="PRG ROM data file to read. Required. Size: 16-4096 KiB and a multiple of 16 KiB."
    )
    parser.add_argument(
        "-c", "--chr-rom",
        help="CHR ROM data file to read. Size: 0-2040 KiB and a multiple of 8 KiB."
    )
    parser.add_argument(
        "-m", "--mapper", type=int, default=0, help="iNES mapper number (0-255). Default=0 (NROM)."
    )
    parser.add_argument(
        "-n", "--mirroring", choices=("h", "v", "f"), default="h",
        help="Type of name table mirroring: h=horizontal (default), v=vertical, f=four-screen."
    )
    parser.add_argument(
        "-x", "--extra-ram", action="store_true",
        help="The game contains extra RAM at $6000-$7fff."
    )
    parser.add_argument(
        "outputFile", help="The iNES ROM file (.nes) to write."
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

def copy_file(source, target):
    # copy source file to current position in target file
    bytesLeft = source.seek(0, 2)
    source.seek(0)
    while bytesLeft:
        chunkSize = min(bytesLeft, 2 ** 20)
        target.write(source.read(chunkSize))
        bytesLeft -= chunkSize

def main():
    args = parse_arguments()

    # get PRG/CHR ROM size
    try:
        prgSize = os.path.getsize(args.prg_rom)
        chrSize = 0 if args.chr_rom is None else os.path.getsize(args.chr_rom)
    except OSError:
        sys.exit("Error getting PRG/CHR ROM file size.")

    # create iNES header
    header = qneslib.ines_header_encode(
        prgSize=prgSize, chrSize=chrSize, mapper=args.mapper, mirroring=args.mirroring,
        extraRam=args.extra_ram
    )
    if header is None:
        sys.exit("Invalid PRG/CHR ROM size.")

    # write header and PRG/CHR ROM data to output file
    try:
        with open(args.outputFile, "wb") as target:
            target.seek(0)
            target.write(header)
            with open(args.prg_rom, "rb") as source:
                copy_file(source, target)
            if chrSize:
                with open(args.chr_rom, "rb") as source:
                    copy_file(source, target)
    except OSError:
        sys.exit("Error reading/writing files.")

if __name__ == "__main__":
    main()
