"""Extract world maps from Blaster Master US ROM to PNGs.
TODO: clean up (pylint complains)"""

import argparse
import itertools
import os
import sys
from PIL import Image
import neslib

# addresses of maps: (16-KiB PRG ROM bank, pointer offset within PRG ROM bank, 4-KiB CHR ROM bank)
MAP_DATA_ADDRESSES = (
    # area 1-8 side view
    (0, 0 * 4, 8),
    (0, 1 * 4, 9),
    (0, 2 * 4, 10),
    (0, 3 * 4, 11),
    (0, 4 * 4, 12),
    (1, 0 * 4, 13),
    (1, 1 * 4, 14),
    (1, 2 * 4, 15),
    # area 1-8 top view
    (1, 3 * 4, 17),
    (2, 1 * 4, 19),
    (1, 4 * 4, 18),
    (2, 4 * 4, 20),
    (2, 0 * 4, 18),
    (2, 2 * 4, 19),
    (2, 5 * 4, 20),
    (2, 3 * 4, 17),
)

def parse_arguments():
    """Parse command line arguments using argparse."""

    parser = argparse.ArgumentParser(
        description="Extract world maps from NES Blaster Master to PNG files."
    )

    parser.add_argument(
        "-m", "--map", type=int, default=0,
        help="Map to extract: 0-7=side view of area 1-8, 8-15=top view of area 1-8. Default=0."
    )
    parser.add_argument("--usb", help="Save ultra-subblocks as a PNG file (256*256 px).")
    parser.add_argument(
        "input_file", help="The Blaster Master ROM file in iNES format (.nes, US version)."
    )
    parser.add_argument("output_file", help="The PNG image file to write.")

    args = parser.parse_args()

    if not 0 <= args.map <= 15:
        sys.exit("Invalid map number.")
    if args.usb is not None and os.path.exists(args.usb):
        sys.exit("USB output file already exists.")
    if not os.path.isfile(args.input_file):
        sys.exit("Input file not found.")
    if os.path.exists(args.output_file):
        sys.exit("Output file already exists.")

    return args

def decode_character_slice(LSBs, MSBs):
    """Decode 8*1 pixels of one character.
    LSBs: integer with 8 less significant bits
    MSBs: integer with 8 more significant bits
    return: iterable with 8 2-bit big-endian integers"""

    MSBs <<= 1
    return (((LSBs >> shift) & 1) | ((MSBs >> shift) & 2) for shift in range(7, -1, -1))

def decode_tile(data):
    """Decode an NES tile. Return a tuple of 64 2-bit integers."""

    decodedData = []
    for (bitplane0, bitplane1) in zip(data[0:8], data[8:16]):
        decodedData.extend(decode_character_slice(bitplane0, bitplane1))
    return tuple(decodedData)

def decode_offset(bytes_):
    """Decode address, convert into offset within bank."""

    addr = bytes_[0] + bytes_[1] * 0x100  # decode little-endian unsigned short
    if not 0x8000 <= addr <= 0xbfff:
        sys.exit("Invalid offset within bank.")
    return addr & 0x3fff  # convert into offset

def create_USBs_image(USBData, USBAttrData, tileData, worldPalette):
    """Return a Pillow Image with up to 16 * 16 ultra-subblocks, each 16 * 16 px."""

    image = Image.new("P", (16 * 16, 16 * 16), 0)  # indexed color
    imagePalette = sorted(set(neslib.PALETTE[color] for color in worldPalette))
    image.putpalette(itertools.chain.from_iterable(imagePalette))  # RGBRGB...
    worldPalToImgPal = tuple(imagePalette.index(neslib.PALETTE[color]) for color in worldPalette)

    # for each USB, draw 2 * 2 tiles with correct palette
    for (USBIndex, USBTiles) in enumerate(USBData):  # index bits: UUUUuuuu
        worldSubPal = USBAttrData[USBIndex] & 3
        for (tileIndex, tile) in enumerate(USBTiles):  # index bits: Tt
            for pixel in range(8 * 8):  # bits: PPPppp
                targetY = USBIndex & 0xf0 | tileIndex << 2 & 0x08 | pixel >> 3         # UUUUTPPP
                targetX = USBIndex << 4 & 0xf0 | tileIndex << 3 & 0x08 | pixel & 0x07  # uuuutppp
                worldPalColor = worldSubPal << 2 | tileData[tile][pixel]
                image.putpixel((targetX, targetY), worldPalToImgPal[worldPalColor])
    return image

# TODO: continue optimization from here

def create_map_image(mapData, blockData, SBData, USBsImg, worldPalette):
    """Return an image of the entire map with 32 * 32 blocks, each 64 * 64 pixels."""

    outImg = Image.new("P", (2048, len(mapData) * 2), 0)  # indexed color
    RGBPalette = sorted(set(neslib.PALETTE[color] for color in worldPalette))
    outImg.putpalette(itertools.chain.from_iterable(RGBPalette))  # RGBRGB...
    # copy subblocks from the image we created earlier
    for (blockIndex, block) in enumerate(mapData):  # world = len(mapData) blocks
        SBs = blockData[block]
        for (SBIndex, SB) in enumerate(SBs):  # block = 2 * 2 subblocks
            USBs = SBData[SB]
            for (USBIndex, USB) in enumerate(USBs):  # subblock = 2 * 2 ultra-subblocks
                inX = USB % 16 * 16
                inY = USB // 16 * 16
                inImg = USBsImg.crop((inX, inY, inX + 16, inY + 16))
                outX = blockIndex % 32 * 64 + SBIndex % 2 * 32 + USBIndex % 2 * 16
                outY = blockIndex // 32 * 64 + SBIndex // 2 * 32 + USBIndex // 2 * 16
                outImg.paste(inImg, (outX, outY))
    return outImg

def convert_map(source, args):
    """Convert one map into PNG. See http://bck.sourceforge.net/blastermaster.txt"""

    if source.seek(0, 2) != 16 + 256 * 1024:
        sys.exit("Incorrect input file size.")

    (PRGBank, worldPtr, CHRBank) = MAP_DATA_ADDRESSES[args.map]
    scrollPtr = worldPtr + 2

    print(f"Banks: PRG (16 KiB) = {PRGBank:d}, CHR (4 KiB) = {CHRBank:d}")
    print(f"Pointer offsets within PRG bank: world=0x{worldPtr:04x}, scroll=0x{scrollPtr:04x}")

    # read PRG ROM bank from file
    source.seek(16 + PRGBank * 16 * 1024)
    PRGBankData = source.read(16 * 1024)

    # After the pointers, the order of data sections varies.
    # The first ones are always: palette, USBs, subblocks, blocks, map.
    # The last two are USB attributes and scroll, in either order.

    worldAddr = decode_offset(PRGBankData[worldPtr:worldPtr+2])
    scrollAddr = decode_offset(PRGBankData[scrollPtr:scrollPtr+2])
    print(f"Data offsets within PRG ROM bank: world=0x{worldAddr:04x}, scroll=0x{scrollAddr:04x}")

    palAddr = decode_offset(PRGBankData[worldAddr+0:worldAddr+0+2])
    USBAttrAddr = decode_offset(PRGBankData[worldAddr+2:worldAddr+2+2])
    USBAddr = decode_offset(PRGBankData[worldAddr+4:worldAddr+4+2])
    SBAddr = decode_offset(PRGBankData[worldAddr+6:worldAddr+6+2])
    blockAddr = decode_offset(PRGBankData[worldAddr+8:worldAddr+8+2])
    mapAddr = decode_offset(PRGBankData[worldAddr+10:worldAddr+10+2])

    print(
        "World data section offsets within PRG bank: "
        f"palette=0x{palAddr:04x}, "
        f"ultra-subblocks=0x{USBAddr:04x}, "
        f"subblocks=0x{SBAddr:04x}, "
        f"blocks=0x{blockAddr:04x}, "
        f"map=0x{mapAddr:04x}, "
        f"ultra-subblock attributes = 0x{USBAttrAddr:04x}"
    )

    # read this world's palette (always 4*4 bytes, contains duplicate NES colors)
    worldPalette = PRGBankData[palAddr:palAddr+16]

    # read ultra-subblock data
    USBDataLen = SBAddr - USBAddr
    if not 4 <= USBDataLen <= 256 * 4 or USBDataLen % 4:
        sys.exit("Invalid ultra-subblock data size.")
    USBData = tuple(PRGBankData[i:i+4] for i in range(USBAddr, USBAddr + USBDataLen, 4))

    # read subblock data
    SBDataLen = blockAddr - SBAddr
    if not 4 <= SBDataLen <= 256 * 4 or SBDataLen % 4:
        sys.exit("Invalid subblock data size.")
    SBData = tuple(PRGBankData[i:i+4] for i in range(SBAddr, SBAddr + SBDataLen, 4))
    if max(itertools.chain.from_iterable(SBData)) >= len(USBData):
        sys.exit("Invalid ultra-subblock index in subblock data.")

    # read block data
    blockDataLen = mapAddr - blockAddr
    if not 4 <= blockDataLen <= 256 * 4 or blockDataLen % 4:
        sys.exit("Invalid block data size.")
    blockData = tuple(PRGBankData[i:i+4] for i in range(blockAddr, blockAddr + blockDataLen, 4))
    if max(itertools.chain.from_iterable(blockData)) >= len(SBData):
        sys.exit("Invalid subblock index in block data.")

    # read map data (up to 32 * 32 blocks)
    mapDataLen = min(USBAttrAddr, scrollAddr) - mapAddr
    if not 32 <= mapDataLen <= 32 * 32 or mapDataLen % 32:
        sys.exit("Invalid map data size.")
    mapData = PRGBankData[mapAddr:mapAddr+mapDataLen]
    if max(mapData) >= len(blockData):
        sys.exit("Invalid block index in map data.")

    # read ultra-subblock attribute data (1 byte/ultra-subblock)
    if not (scrollAddr < USBAttrAddr or scrollAddr == USBAttrAddr + len(USBData)):
        sys.exit("Invalid ultra-subblock attribute or scroll data address.")
    USBAttrData = PRGBankData[USBAttrAddr:USBAttrAddr+len(USBData)]

    print(
        "Counts: "
        f"ultra-subblocks={len(USBData):d}, subblocks={len(SBData):d}, blocks={len(blockData):d}"
    )
    print("Map size (blocks):", len(mapData))

    # read and decode tile data
    source.seek(16 + 128 * 1024 + CHRBank * 4 * 1024)
    CHRBankData = source.read(4 * 1024)
    tileData = tuple(decode_tile(CHRBankData[i*16:(i+1)*16]) for i in range(256))

    # create image with ultra subblocks, optionally save
    USBsImg = create_USBs_image(USBData, USBAttrData, tileData, worldPalette)
    if args.usb is not None:
        with open(args.usb, "wb") as target:
            USBsImg.save(target)

    # create main output image and save it
    mapImg = create_map_image(mapData, blockData, SBData, USBsImg, worldPalette)
    with open(args.output_file, "wb") as target:
        target.seek(0)
        mapImg.save(target)

def main():
    """The main function."""

    args = parse_arguments()
    try:
        with open(args.input_file, "rb") as source:
            convert_map(source, args)
    except OSError:
        sys.exit("Error reading/writing files.")

if __name__ == "__main__":
    main()
