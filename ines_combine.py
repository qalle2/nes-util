import argparse, os, sys
import qneslib  # qalle's NES library, https://github.com/qalle2/nes-util

def parse_arguments():
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
        "outputFile", help="iNES ROM file (.nes) to write."
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

def main():
    args = parse_arguments()

    # read input files
    try:
        # PRG ROM
        with open(args.prg_rom, "rb") as handle:
            handle.seek(0)
            prgData = handle.read()
        # CHR ROM
        if args.chr_rom is not None:
            with open(args.chr_rom, "rb") as handle:
                handle.seek(0)
                chrData = handle.read()
        else:
            chrData = b""
    except OSError:
        sys.exit("Error reading input files.")

    # create iNES header
    header = qneslib.ines_header_encode(
        prgSize=len(prgData),
        chrSize=len(chrData),
        mapper=args.mapper,
        mirroring=args.mirroring,
        extraRam=args.extra_ram
    )
    if header is None:
        sys.exit("Invalid PRG/CHR ROM size.")

    # write output file
    try:
        with open(args.outputFile, "wb") as target:
            target.seek(0)
            target.write(header)
            target.write(prgData)
            target.write(chrData)
    except OSError:
        sys.exit("Error writing output file.")

main()
