import argparse, itertools, os, sys
from PIL import Image  # Pillow, https://python-pillow.org
import qneslib  # qalle's NES library, https://github.com/qalle2/nes-util

def decode_color_code(color):
    # decode a hexadecimal RRGGBB color code into (red, green, blue)

    if len(color) != 6:
        sys.exit("Each color code must be 6 hexadecimal digits.")
    try:
        color = int(color, 16)
    except ValueError:
        sys.exit("Color codes must be hexadecimal.")
    return (color >> 16, (color >> 8) & 0xff, color & 0xff)

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Convert NES CHR (graphics) data into a PNG file."
    )
    parser.add_argument(
        "-p", "--palette", nargs=4, default=("000000", "555555", "aaaaaa", "ffffff"),
        help="Output palette (which image colors correspond to CHR colors 0-3). Four hexadecimal "
        "RRGGBB color codes separated by spaces. Default: 000000 555555 aaaaaa ffffff"
    )
    parser.add_argument(
        "input_file",
        help="File to read. An iNES ROM file (.nes) or raw CHR data. The size of a raw CHR data "
        "file must be a multiple of 256 bytes (16 tiles)."
    )
    parser.add_argument(
        "output_file", help="PNG file to write. Always 128 pixels (16 tiles) wide."
    )
    args = parser.parse_args()

    [decode_color_code(c) for c in args.palette]  # validate
    if not os.path.isfile(args.input_file):
        sys.exit("Input file not found.")
    if os.path.exists(args.output_file):
        sys.exit("Output file already exists.")

    return args

def get_chr_addr_and_size(handle):
    # detect file type and get (address, size) of CHR ROM data

    inesInfo = qneslib.ines_header_decode(handle)
    if inesInfo is not None:
        # iNES ROM file
        if inesInfo["chrSize"] == 0:
            sys.exit("The input file is an iNES ROM file but has no CHR ROM.")
        return (inesInfo["chrStart"], inesInfo["chrSize"])
    else:
        fileSize = handle.seek(0, 2)
        if fileSize == 0 or fileSize % 256:
            sys.exit("The input file is neither an iNES ROM file nor a raw CHR data file.")
        # raw CHR data file
        return (0, fileSize)

def decode_pixel_rows(handle, charRowCount):
    # generate 128*1 pixels (two-bit ints) per call from NES CHR data;
    # note: a tile is 8*8 pixels and 2 bitplanes, or 16 bytes; first low bitplane from top to
    # bottom, then high bitplane from top to bottom; 1 byte is 8*1 pixels of one bitplane

    pixelRow = []
    for i in range(charRowCount):
        charRow = handle.read(16 * 16)  # 16*1 tiles (128*8 pixels), 16 bytes/tile
        for y in range(8):
            pixelRow.clear()
            for x in range(16):
                # decode 2 bytes (8 bytes apart) into 8*1 pixels
                pixelRow.extend(qneslib.tile_slice_decode(charRow[x*16+y], charRow[x*16+y+8]))
            yield pixelRow

def chr_data_to_image(handle, args):
    # read CHR data from a file, return a Pillow image

    (chrAddr, chrSize) = get_chr_addr_and_size(handle)
    charRowCount = chrSize // (16 * 16)  # 16 bytes/tile, 16 tiles/row

    # create indexed image; get palette from command line argument
    image = Image.new("P", (16 * 8, charRowCount * 8))
    image.putpalette(itertools.chain.from_iterable(decode_color_code(c) for c in args.palette))

    # convert CHR data into image data
    handle.seek(chrAddr)
    for (y, pixelRow) in enumerate(decode_pixel_rows(handle, charRowCount)):
        for (x, colorIndex) in enumerate(pixelRow):
            image.putpixel((x, y), colorIndex)

    return image

def main():
    args = parse_arguments()

    # convert CHR data into an image
    try:
        with open(args.input_file, "rb") as handle:
            image = chr_data_to_image(handle, args)
    except OSError:
        sys.exit("Error reading input file.")

    # save image
    try:
        with open(args.output_file, "wb") as handle:
            handle.seek(0)
            image.save(handle, "png")
    except OSError:
        sys.exit("Error writing output file.")

main()
