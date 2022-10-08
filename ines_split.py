import argparse, os, struct, sys

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Extract PRG ROM and/or CHR ROM data from an iNES ROM "
        "file (.nes)."
    )
    parser.add_argument("-p", "--prg", help="File to write PRG ROM data to.")
    parser.add_argument(
        "-c", "--chr",
        help="File to write CHR ROM data to. Not written if there is no data."
    )
    parser.add_argument("input_file", help="iNES ROM file (.nes) to read.")
    args = parser.parse_args()

    if not os.path.isfile(args.input_file):
        sys.exit("Input file not found.")
    if args.prg is not None and os.path.exists(args.prg):
        sys.exit("PRG ROM file already exists.")
    if args.chr is not None and os.path.exists(args.chr):
        sys.exit("CHR ROM file already exists.")
    if args.prg is None and args.chr is None:
        sys.exit("Specify at least one of --prg and --chr.")

    return args

def decode_ines_header(handle):
    # parse iNES ROM header
    # does not support VS System or PlayChoice-10 flags or NES 2.0 header
    # return: None on error, otherwise a dict with PRG/CHR ROM address/size
    # see https://www.nesdev.org/wiki/INES

    fileSize = handle.seek(0, 2)
    if fileSize < 16:
        return None

    handle.seek(0)
    (id_, prgSize, chrSize, flags6) = struct.unpack("4s3B", handle.read(7))

    prgSize = (prgSize if prgSize else 256) * 16 * 1024  # 0 = 256
    chrSize = chrSize * 8 * 1024
    trainerSize = bool(flags6 & 0b00000100) * 512

    if id_ != b"NES\x1a" or fileSize < 16 + trainerSize + prgSize + chrSize:
        return None

    return {
        "prgStart": 16 + trainerSize,
        "prgSize":  prgSize,
        "chrStart": 16 + trainerSize + prgSize,
        "chrSize":  chrSize,
    }

def main():
    args = parse_arguments()

    # read input file
    try:
        with open(args.input_file, "rb") as handle:
            # header
            inesInfo = decode_ines_header(handle)
            if inesInfo is None:
                sys.exit("Invalid iNES ROM file.")
            # PRG ROM
            if args.prg is not None:
                handle.seek(inesInfo["prgStart"])
                prgData = handle.read(inesInfo["prgSize"])
            # CHR ROM
            if args.chr is not None and inesInfo["chrSize"]:
                handle.seek(inesInfo["chrStart"])
                chrData = handle.read(inesInfo["chrSize"])
    except OSError:
        sys.exit("Error reading input file.")

    # write output files
    try:
        # PRG ROM
        if args.prg is not None:
            with open(args.prg, "wb") as handle:
                handle.seek(0)
                handle.write(prgData)
        # CHR ROM
        if args.chr is not None and inesInfo["chrSize"]:
            with open(args.chr, "wb") as handle:
                handle.seek(0)
                handle.write(chrData)
    except OSError:
        sys.exit("Error writing output file(s).")

main()
