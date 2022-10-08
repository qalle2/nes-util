import argparse, os, struct, sys

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Create an iNES ROM file (.nes)."
    )

    parser.add_argument(
        "-p", "--prg-rom", required=True,
        help="PRG ROM data file to read. Required. Size: 16-4096 KiB and a "
        "multiple of 16 KiB."
    )
    parser.add_argument(
        "-c", "--chr-rom",
        help="CHR ROM data file to read. Size: 0-2040 KiB and a multiple of "
        "8 KiB."
    )
    parser.add_argument(
        "-m", "--mapper", type=int, default=0,
        help="iNES mapper number (0-255). Default=0 (NROM)."
    )
    parser.add_argument(
        "-n", "--mirroring", choices=("h", "v", "f"), default="h",
        help="Type of name table mirroring: h=horizontal (default), "
        "v=vertical, f=four-screen."
    )
    parser.add_argument(
        "-x", "--extra-ram", action="store_true",
        help="The game contains extra RAM at $6000-$7fff."
    )
    parser.add_argument("outputFile", help="iNES ROM file (.nes) to write.")

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

def encode_ines_header(prgSize, chrSize, mapper, mirroring, extraRam):
    # create an iNES header
    # does not support VS System or PlayChoice-10 flags or NES 2.0 header
    # see https://www.nesdev.org/wiki/INES

    (prgSize, remainder) = divmod(prgSize, 16 * 1024)
    if remainder or not 1 <= prgSize <= 256:
        sys.exit("Invalid PRG ROM size.")
    prgSize %= 256  # 256 = 0

    (chrSize, remainder) = divmod(chrSize, 8 * 1024)
    if remainder or chrSize > 255:
        sys.exit("Invalid CHR ROM size.")

    flags6 = (mapper & 0b1111) << 4
    flags6 |= {"h": 0b0, "v": 0b1, "f": 0b1000}[mirroring]
    if extraRam:
        flags6 |= 0b10
    flags7 = mapper & 0b11110000

    return struct.pack(
        "4s4B8s", b"NES\x1a", prgSize, chrSize, flags6, flags7, 8 * b"\x00"
    )

def main():
    args = parse_arguments()

    # read PRG ROM file
    try:
        with open(args.prg_rom, "rb") as handle:
            handle.seek(0)
            prgData = handle.read()
    except OSError:
        sys.exit("Error reading PRG ROM file.")

    # read CHR ROM file
    if args.chr_rom is not None:
        try:
            with open(args.chr_rom, "rb") as handle:
                handle.seek(0)
                chrData = handle.read()
        except OSError:
            sys.exit("Error reading CHR ROM file.")
    else:
        chrData = b""

    # create iNES header
    header = encode_ines_header(
        prgSize=len(prgData),
        chrSize=len(chrData),
        mapper=args.mapper,
        mirroring=args.mirroring,
        extraRam=args.extra_ram
    )

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
