"""Extract PRG ROM and/or CHR ROM data from an iNES ROM file (.nes)."""

import argparse
import os
import sys

def parse_arguments():
    """Parse command line arguments using argparse."""

    parser = argparse.ArgumentParser(
        description="Extract PRG ROM and/or CHR ROM data from an iNES ROM file (.nes).",
        epilog="Specify at least one output file."
    )

    parser.add_argument("-p", "--prg", help="The file to extract PRG ROM data to (16-4096 KiB).")
    parser.add_argument("-c", "--chr", help="The file to extract CHR ROM data to (8-2040 KiB).")
    parser.add_argument("input_file", help="The iNES ROM file (.nes) to read.")

    args = parser.parse_args()

    # input file
    if not os.path.isfile(args.input_file):
        sys.exit("The input file does not exist.")

    # output files
    if args.prg is None and args.chr is None:
        sys.exit("Nothing to do (specify at least one output file).")
    if args.prg is not None and os.path.exists(args.prg):
        sys.exit("The PRG ROM file already exists.")
    if args.chr is not None and os.path.exists(args.chr):
        sys.exit("The CHR ROM file already exists.")

    return args

def get_PRG_and_CHR_size(handle):
    """Parse the iNES header in a file. Return (PRG_ROM_size, CHR_ROM_size).
    http://wiki.nesdev.com/w/index.php/INES"""

    if handle.seek(0, 2) < 16:
        sys.exit("The input file is smaller than an iNES header.")

    handle.seek(0)
    header = handle.read(16)
    (id_, PRGSize16KiB, CHRSize8KiB) = (header[0:4], header[4], header[5])

    if id_ != b"NES\x1a":
        sys.exit("The input file is not an iNES ROM file.")
    PRGSize16KiB = PRGSize16KiB if PRGSize16KiB else 256  # 0 = 256

    return (PRGSize16KiB * 16 * 1024, CHRSize8KiB * 8 * 1024)

def read_file_slice(inputHandle, bytesLeft):
    """Read bytesLeft bytes from current position in inputHandle. Yield one chunk per call."""

    while bytesLeft:
        chunkSize = min(bytesLeft, 2 ** 20)
        yield inputHandle.read(chunkSize)
        bytesLeft -= chunkSize

def main():
    """The main function."""

    args = parse_arguments()
    try:
        with open(args.input_file, "rb") as source:
            # get PRG ROM and CHR ROM size
            (PRGSize, CHRSize) = get_PRG_and_CHR_size(source)
            if source.seek(0, 2) < 16 + PRGSize + CHRSize:
                sys.exit("The input file is smaller than specified by the iNES header.")
            if args.prg is not None:
                # extract PRG ROM
                source.seek(16)
                with open(args.prg, "wb") as target:
                    target.seek(0)
                    for chunk in read_file_slice(source, PRGSize):
                        target.write(chunk)
            if args.chr is not None:
                # extract CHR ROM
                if CHRSize == 0:
                    print("Warning: the input file has no CHR ROM.", file=sys.stderr)
                else:
                    source.seek(16 + PRGSize)
                    with open(args.chr, "wb") as target:
                        target.seek(0)
                        for chunk in read_file_slice(source, CHRSize):
                            target.write(chunk)
    except OSError:
        sys.exit("Error reading/writing files.")

if __name__ == "__main__":
    main()
