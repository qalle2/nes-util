"""Swap colors in the graphics data (CHR ROM) of an iNES ROM file (.nes)."""

import argparse
import os
import sys
import qneslib  # qalle's NES library, https://github.com/qalle2/nes-util

def parse_arguments():
    """Parse command line arguments using argparse."""

    parser = argparse.ArgumentParser(
        description="Swap colors in the graphics data (CHR ROM) of an iNES ROM file (.nes)."
    )

    parser.add_argument(
        "-c", "--colors", nargs=4, type=int, choices=range(4), default=(0, 2, 3, 1),
        help="Change original colors 0...3 to these colors. Four colors (each 0...3) "
        "separated by spaces. Default: 0 2 3 1"
    )
    parser.add_argument(
        "-f", "--first-tile", type=int, default=0,
        help="First tile to change (0 or greater, default=0)."
    )
    parser.add_argument(
        "-n", "--tile-count", type=int, default=0,
        help="Number of tiles to change. 0 (default) = all starting from --first-tile."
    )
    parser.add_argument(
        "input_file",
        help="iNES ROM file (.nes) to read."
    )
    parser.add_argument(
        "output_file",
        help="iNES ROM file (.nes) to write."
    )

    args = parser.parse_args()

    if args.first_tile < 0:
        sys.exit("--first-tile must be 0 or greater.")
    if args.tile_count < 0:
        sys.exit("--tile-count must be 0 or greater.")

    if not os.path.isfile(args.input_file):
        sys.exit("Input file not found.")
    if os.path.exists(args.output_file):
        sys.exit("Target file already exists.")

    return args

def read_file_slice(handle, bytesLeft):
    """Generate bytesLeft bytes from file in chunks."""

    while bytesLeft:
        chunkSize = min(bytesLeft, 2 ** 20)
        yield handle.read(chunkSize)
        bytesLeft -= chunkSize

def swap_colors(chunk, colors):
    """Replace colors 0...3 in NES CHR data chunk with new colors."""

    chunk = bytearray(chunk)

    for charPos in range(0, len(chunk), 16):
        for y in range(8):
            # process 8*1 pixels of one tile
            # position of low/high bitplane (byte)
            loPos = charPos + y
            hiPos = charPos + 8 + y
            # decode pixels, replace colors, reencode pixels
            (chunk[loPos], chunk[hiPos]) = qneslib.tile_slice_encode(
                colors[color] for color
                in qneslib.tile_slice_decode(chunk[loPos], chunk[hiPos])
            )

    return chunk

def create_output_data(source, args):
    """Read input file, modify specified tiles, generate output data as chunks."""

    fileInfo = qneslib.ines_header_decode(source)

    # length of address range to modify and ranges before/after it
    beforeLen = fileInfo["chrStart"] + args.first_tile * 16
    modifyLen = args.tile_count * 16 if args.tile_count else fileInfo["chrSize"]
    afterLen = fileInfo["chrSize"] - modifyLen

    source.seek(0)

    # data before tiles to modify
    yield from read_file_slice(source, beforeLen)
    # tiles to modify
    for chunk in read_file_slice(source, modifyLen):
        yield swap_colors(chunk, args.colors)
    # data after tiles to modify
    yield from read_file_slice(source, afterLen)

def main():
    args = parse_arguments()

    try:
        with open(args.input_file, "rb") as source:
            fileInfo = qneslib.ines_header_decode(source)
            if fileInfo is None:
                sys.exit("Invalid iNES ROM file.")

            chrSize = fileInfo["chrSize"]

            if chrSize == 0:
                sys.exit("Input file has no CHR ROM.")
            if args.first_tile * 16 >= chrSize:
                sys.exit("--first-tile is too large.")
            if args.tile_count and (args.first_tile + args.tile_count) * 16 > chrSize:
                sys.exit("Sum of --first-tile and --tile-count is too large.")

            # copy input file to output file
            try:
                with open(args.output_file, "wb") as target:
                    target.seek(0)
                    for chunk in create_output_data(source, args):
                        target.write(chunk)
            except OSError:
                sys.exit("Error copying data.")
    except OSError:
        sys.exit("Error reading input file.")

if __name__ == "__main__":
    main()
