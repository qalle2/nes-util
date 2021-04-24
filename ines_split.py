"""Extract PRG ROM and/or CHR ROM data from an iNES ROM file (.nes)."""

import argparse, os, sys
import qneslib  # qalle's NES library, https://github.com/qalle2/nes-util

def parse_arguments():
    # parse command line arguments using argparse

    parser = argparse.ArgumentParser(
        description="Extract PRG ROM and/or CHR ROM data from an iNES ROM file (.nes)."
    )

    parser.add_argument(
        "-p", "--prg", help="File to write PRG ROM data to."
    )
    parser.add_argument(
        "-c", "--chr", help="File to write CHR ROM data to. Not written if there is no data."
    )
    parser.add_argument(
        "input_file", help="iNES ROM file (.nes) to read."
    )

    args = parser.parse_args()

    if not os.path.isfile(args.input_file):
        sys.exit("Input file does not exist.")
    if args.prg is not None and os.path.exists(args.prg):
        sys.exit("PRG ROM file already exists.")
    if args.chr is not None and os.path.exists(args.chr):
        sys.exit("CHR ROM file already exists.")

    return args

def copy_file_slice(source, bytesLeft, target):
    # copy bytesLeft bytes from one file to another
    while bytesLeft:
        chunkSize = min(bytesLeft, 2 ** 20)
        target.write(source.read(chunkSize))
        bytesLeft -= chunkSize

args = parse_arguments()

try:
    with open(args.input_file, "rb") as source:
        fileInfo = qneslib.ines_header_decode(source)
        if fileInfo is None:
            sys.exit("Invalid iNES ROM file.")

        if args.prg is not None:
            # copy PRG ROM data
            with open(args.prg, "wb") as target:
                source.seek(fileInfo["prgStart"])
                target.seek(0)
                copy_file_slice(source, fileInfo["prgSize"], target)

        if args.chr is not None and fileInfo["chrSize"]:
            # copy CHR ROM data
            with open(args.chr, "wb") as target:
                source.seek(fileInfo["chrStart"])
                target.seek(0)
                copy_file_slice(source, fileInfo["chrSize"], target)
except OSError:
    sys.exit("Error reading/writing files.")
