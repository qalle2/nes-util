import argparse, os, sys
import qneslib  # qalle's NES library, https://github.com/qalle2/nes-util

def parse_arguments():
    # parse command line arguments using argparse

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
        "input_file", help="iNES ROM file (.nes) to read."
    )
    parser.add_argument(
        "output_file", help="iNES ROM file (.nes) to write."
    )

    args = parser.parse_args()

    if args.first_tile < 0:
        sys.exit("--first-tile must be 0 or greater.")
    if args.tile_count < 0:
        sys.exit("--tile-count must be 0 or greater.")

    if not os.path.isfile(args.input_file):
        sys.exit("Input file not found.")
    if os.path.exists(args.output_file):
        sys.exit("Output file already exists.")

    return args

def read_file_slice(handle, bytesLeft):
    # generate bytesLeft bytes from file
    while bytesLeft:
        chunkSize = min(bytesLeft, 2 ** 20)
        yield handle.read(chunkSize)
        bytesLeft -= chunkSize

def swap_colors(chunk, colors):
    # replace colors 0...3 in NES CHR data chunk (16n bytes) with new colors (four ints)

    chunk = bytearray(chunk)

    for charPos in range(0, len(chunk), 16):
        for pixelY in range(8):
            # process 8*1 pixels of one tile
            # position of low/high bitplane (byte)
            loPos = charPos + pixelY
            hiPos = charPos + 8 + pixelY
            # decode pixels, replace colors, reencode pixels
            (chunk[loPos], chunk[hiPos]) = qneslib.tile_slice_encode(
                colors[color] for color in qneslib.tile_slice_decode(chunk[loPos], chunk[hiPos])
            )

    return chunk

args = parse_arguments()

try:
    with open(args.input_file, "rb") as source:
        fileInfo = qneslib.ines_header_decode(source)
        if fileInfo is None:
            sys.exit("Invalid iNES ROM file.")
        if fileInfo["chrSize"] == 0:
            sys.exit("Input file has no CHR ROM.")

        # length of CHR data before the tiles to modify
        beforeLen = args.first_tile * 16
        if beforeLen >= fileInfo["chrSize"]:
            sys.exit("--first-tile is too large.")

        # length of CHR data at/after the tiles to modify
        if args.tile_count:
            modifyLen = args.tile_count * 16
            afterLen = fileInfo["chrSize"] - beforeLen - modifyLen
            if afterLen < 0:
                sys.exit("Sum of --first-tile and --tile-count is too large.")
        else:
            afterLen = 0
            modifyLen = fileInfo["chrSize"] - beforeLen - afterLen

        # copy input file to output file
        source.seek(0)
        with open(args.output_file, "wb") as target:
            target.seek(0)
            # copy data before/at/after the tiles to be modified
            for chunk in read_file_slice(source, fileInfo["chrStart"] + beforeLen):
                target.write(chunk)
            for chunk in read_file_slice(source, modifyLen):
                target.write(swap_colors(chunk, args.colors))
            for chunk in read_file_slice(source, afterLen):
                target.write(chunk)
except OSError:
    sys.exit("Error reading/writing files.")
