# extract map data from NES Irritating Ship (game by Fiskbit & Trirosmos);
# note: "metatile" = 2*2 tiles in this game
# TODO: checkpoint icons

import os, sys
from PIL import Image  # Pillow, https://python-pillow.org

# PRG ROM address: top left tile index of each metatile, then TR/BL/BR;
# METATILE_CNT bytes each
METATILE_DATA_ADDR = 0x156e
# PRG ROM address: map data upside down; byte = metatile;
# MAP_WIDTH*MAP_HEIGHT bytes
MAP_DATA_ADDR = 0x186e

METATILE_CNT = 192  # unique metatiles
MAP_WIDTH    = 16   # map width in metatiles
MAP_HEIGHT   = 139  # map height in metatiles

# shades of gray (red, green, blue, ...)
IMAGE_PALETTE = (
    0x00,0x00,0x00, 0x55,0x55,0x55, 0xaa,0xaa,0xaa, 0xff,0xff,0xff
)

def decode_pt(chrData):
    # read one pattern table (256 tiles) of CHR data;
    # generate tiles (tuples of 64 2-bit ints);
    # tile = 8*8 2-bit pixels
    pixels = []
    for ti in range(256):
        tile = chrData[ti*16:(ti+1)*16]
        pixels.clear()
        for y in range(8):
            pixels.extend(
                ((tile[y] >> s) & 1) | (((tile[y+8] >> s) & 1) << 1)
                for s in range(7, -1, -1)
            )
        yield tuple(pixels)

def create_tiles_image(chrData):
    # create image with 16*16 tiles (128*128 px) from background pattern table
    # data
    image = Image.new("P", (16 * 8, 16 * 8))
    image.putpalette(IMAGE_PALETTE)
    for (ti, tile) in enumerate(decode_pt(chrData)):
        for (pi, pixel) in enumerate(tile):
            (ty, tx) = divmod(ti, 16)
            (py, px) = divmod(pi, 8)
            image.putpixel((tx * 8 + px, ty * 8 + py), pixel)
    return image

def create_metatiles_image(tileImage, prgData):
    # create image with unique metatiles (256*256 px)

    metatileImage = Image.new("P", (16 * 16, 16 * 16))
    metatileImage.putpalette(IMAGE_PALETTE)

    for tpos in range(4):  # which tile within metatile (TL/TR/BL/BR)
        for mti in range(METATILE_CNT):  # metatile index
            # tile index
            ti = prgData[METATILE_DATA_ADDR+tpos*METATILE_CNT+mti]
            # get tile
            (y, x) = divmod(ti, 16)
            x *= 8
            y *= 8
            tempImage = tileImage.crop((x, y, x + 8, y + 8))
            # paste tile
            (y, x) = divmod(mti, 16)
            x = x * 16 + tpos % 2 * 8
            y = y * 16 + tpos // 2 * 8
            metatileImage.paste(tempImage, (x, y))

    return metatileImage

def create_map_image(prgData, chrData):
    # create image of entire map (MAP_WIDTH*MAP_HEIGHT metatiles)

    # create temporary tile & metatile images
    tilesImage = create_tiles_image(chrData)
    metatilesImage = create_metatiles_image(tilesImage, prgData)

    mapImage = Image.new("P", (MAP_WIDTH * 16, MAP_HEIGHT * 16))
    mapImage.putpalette(IMAGE_PALETTE)

    for mtp in range(MAP_WIDTH * MAP_HEIGHT):  # metatile position
        # metatile index
        mti = prgData[MAP_DATA_ADDR+mtp]
        # get metatile
        (y, x) = divmod(mti, 16)
        metatileImage = metatilesImage.crop((
            x * 16, y * 16, (x + 1) * 16, (y + 1) * 16
        ))
        # paste metatile
        (y, x) = divmod(mtp, 16)
        y = MAP_HEIGHT - y - 1  # upside down
        mapImage.paste(metatileImage, (x*16, y*16))

    return mapImage

def main():
    if len(sys.argv) != 3:
        sys.exit(
            "Extract map data from NES Irritating Ship. Arguments: inputFile "
            "outputFile (inputFile = iNES ROM, outputFile = PNG (will be "
            "overwritten))."
        )

    (inputFile, outputFile) = sys.argv[1:]
    if not os.path.isfile(inputFile):
        sys.exit("Input file not found.")

    try:
        with open(inputFile, "rb") as handle:
            handle.seek(0)
            fileData = handle.read()
    except OSError:
        sys.exit("Error reading input file.")

    # validate input file; see https://www.nesdev.org/wiki/INES
    if len(fileData) != 16 + 40 * 1024 or fileData[:4] != b"NES\x1a":
        sys.exit("Not an iNES ROM file or not Irritating Ship.")

    # read PRG & CHR ROM
    prgData = fileData[16:16+32*1024]
    chrData = fileData[16+32*1024:]

    mapImage = create_map_image(prgData, chrData)

    try:
        with open(outputFile, "wb") as handle:
            handle.seek(0)
            mapImage.save(handle, "png")
    except OSError:
        sys.exit("Error writing output file.")

main()
