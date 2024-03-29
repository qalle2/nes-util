# source: "Blaster Master Format Specification",
# http://bck.sourceforge.net/blastermaster.txt
# (I actually figured out most of the info myself before I found that
# document.)

# glossary:
# - USB   = ultra-subblock (2*2 tiles)
# - SB    = subblock (2*2 ultra-subblocks)
# - block = 2*2 subblocks
# - map   = up to 32*32 blocks

import argparse, itertools, os, struct, sys
from PIL import Image  # Pillow, https://python-pillow.org

# addresses of maps: (16-KiB PRG ROM bank, pointer address within PRG ROM bank,
# 4-KiB CHR ROM bank);
# note: JP version uses PRG bank 4 instead of 2
MAP_DATA_ADDRESSES = {
    0:  (0, 0 * 4,  8),
    1:  (0, 1 * 4,  9),
    2:  (0, 2 * 4, 10),
    3:  (0, 3 * 4, 11),
    4:  (0, 4 * 4, 12),
    5:  (1, 0 * 4, 13),
    6:  (1, 1 * 4, 14),
    7:  (1, 2 * 4, 15),
    8:  (1, 3 * 4, 17),
    9:  (2, 1 * 4, 19),
    10: (1, 4 * 4, 18),
    11: (2, 4 * 4, 20),
    12: (2, 0 * 4, 18),
    13: (2, 2 * 4, 19),
    14: (2, 5 * 4, 20),
    15: (2, 3 * 4, 17),
}

# NES master palette; values are (red, green, blue); source: FCEUX (fceux.pal)
NES_PALETTE = {
    0x00: (0x74, 0x74, 0x74),
    0x01: (0x24, 0x18, 0x8c),
    0x02: (0x00, 0x00, 0xa8),
    0x03: (0x44, 0x00, 0x9c),
    0x04: (0x8c, 0x00, 0x74),
    0x05: (0xa8, 0x00, 0x10),
    0x06: (0xa4, 0x00, 0x00),
    0x07: (0x7c, 0x08, 0x00),
    0x08: (0x40, 0x2c, 0x00),
    0x09: (0x00, 0x44, 0x00),
    0x0a: (0x00, 0x50, 0x00),
    0x0b: (0x00, 0x3c, 0x14),
    0x0c: (0x18, 0x3c, 0x5c),
    0x0d: (0x00, 0x00, 0x00),
    0x0e: (0x00, 0x00, 0x00),
    0x0f: (0x00, 0x00, 0x00),
    0x10: (0xbc, 0xbc, 0xbc),
    0x11: (0x00, 0x70, 0xec),
    0x12: (0x20, 0x38, 0xec),
    0x13: (0x80, 0x00, 0xf0),
    0x14: (0xbc, 0x00, 0xbc),
    0x15: (0xe4, 0x00, 0x58),
    0x16: (0xd8, 0x28, 0x00),
    0x17: (0xc8, 0x4c, 0x0c),
    0x18: (0x88, 0x70, 0x00),
    0x19: (0x00, 0x94, 0x00),
    0x1a: (0x00, 0xa8, 0x00),
    0x1b: (0x00, 0x90, 0x38),
    0x1c: (0x00, 0x80, 0x88),
    0x1d: (0x00, 0x00, 0x00),
    0x1e: (0x00, 0x00, 0x00),
    0x1f: (0x00, 0x00, 0x00),
    0x20: (0xfc, 0xfc, 0xfc),
    0x21: (0x3c, 0xbc, 0xfc),
    0x22: (0x5c, 0x94, 0xfc),
    0x23: (0xcc, 0x88, 0xfc),
    0x24: (0xf4, 0x78, 0xfc),
    0x25: (0xfc, 0x74, 0xb4),
    0x26: (0xfc, 0x74, 0x60),
    0x27: (0xfc, 0x98, 0x38),
    0x28: (0xf0, 0xbc, 0x3c),
    0x29: (0x80, 0xd0, 0x10),
    0x2a: (0x4c, 0xdc, 0x48),
    0x2b: (0x58, 0xf8, 0x98),
    0x2c: (0x00, 0xe8, 0xd8),
    0x2d: (0x78, 0x78, 0x78),
    0x2e: (0x00, 0x00, 0x00),
    0x2f: (0x00, 0x00, 0x00),
    0x30: (0xfc, 0xfc, 0xfc),
    0x31: (0xa8, 0xe4, 0xfc),
    0x32: (0xc4, 0xd4, 0xfc),
    0x33: (0xd4, 0xc8, 0xfc),
    0x34: (0xfc, 0xc4, 0xfc),
    0x35: (0xfc, 0xc4, 0xd8),
    0x36: (0xfc, 0xbc, 0xb0),
    0x37: (0xfc, 0xd8, 0xa8),
    0x38: (0xfc, 0xe4, 0xa0),
    0x39: (0xe0, 0xfc, 0xa0),
    0x3a: (0xa8, 0xf0, 0xbc),
    0x3b: (0xb0, 0xfc, 0xcc),
    0x3c: (0x9c, 0xfc, 0xf0),
    0x3d: (0xc4, 0xc4, 0xc4),
    0x3e: (0x00, 0x00, 0x00),
    0x3f: (0x00, 0x00, 0x00),
}

def error(msg):
    sys.exit(f"Error: {msg}.")

def warn(msg):
    print(f"Warning: {msg}.", file=sys.stderr)

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Extract world maps from NES Blaster Master to PNG files."
    )
    parser.add_argument(
        "-j", "--japan", action="store_true",
        help="Input file is Japanese version (Chou-Wakusei Senki - MetaFight)."
    )
    parser.add_argument(
        "-n", "--map-number", type=int, default=0,
        help="Map to extract: 0-7 = side view of area 1-8, 8-15 = overhead "
        "view of area 1-8. Default=0."
    )
    parser.add_argument(
        "-u", "--usb-image",
        help="Save ultra-subblocks (16*16 px each) as PNG file (up to "
        "256*256 px)."
    )
    parser.add_argument(
        "-s", "--sb-image",
        help="Save subblocks (32*32 px each) as PNG file (up to 512*512 px)."
    )
    parser.add_argument(
        "-b", "--block-image",
        help="Save blocks (64*64 px each) as PNG file (up to 1024*1024 px)."
    )
    parser.add_argument(
        "-m", "--map-image",
        help="Save map as PNG file (up to 32*32 blocks or 2048*2048 px)."
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Print more information."
    )
    parser.add_argument(
        "input_file",
        help="Blaster Master ROM file in iNES format (.nes, US/US "
        "prototype/EUR/JP; see also --japan)."
    )
    args = parser.parse_args()

    if not 0 <= args.map_number <= 15:
        error("invalid map number")

    if not os.path.isfile(args.input_file):
        error("input file not found")

    outputFiles = (
        args.usb_image, args.sb_image, args.block_image, args.map_image
    )
    if all(f is None for f in outputFiles):
        warn("no output files specified")
    if any(f is not None and os.path.exists(f) for f in outputFiles):
        error("some of the output files already exist")

    return args

def decode_ines_header(handle):
    # parse iNES ROM header
    # does not support VS System, PlayChoice-10 or trainer flags or NES 2.0
    # header
    # see https://www.nesdev.org/wiki/INES

    fileSize = handle.seek(0, 2)
    if fileSize < 16:
        return None

    handle.seek(0)
    (id_, prgSize, chrSize, flags6, flags7) \
    = struct.unpack("4s4B", handle.read(8))

    prgSize = (prgSize if prgSize else 256) * 16 * 1024  # 0 = 256
    chrSize = chrSize * 8 * 1024

    if id_ != b"NES\x1a" or fileSize < 16 + prgSize + chrSize:
        return None

    return {
        "prgStart": 16,
        "prgSize":  prgSize,
        "chrStart": 16 + prgSize,
        "chrSize":  chrSize,
        "mapper":   (flags7 & 0b11110000) | (flags6 >> 4),
    }

def decode_offset(bytes_):
    # decode address, convert into offset within bank
    addr = struct.unpack("<H", bytes_)[0]  # little-endian unsigned short
    if not 0x8000 <= addr <= 0xbfff:
        error("address not in first CPU PRG bank")
    return addr & 0x3fff

def get_tile_data(handle):
    # read a bank of CHR data; generate tiles (tuples of 64 2-bit ints)
    pixels = []
    for ti in range(256):
        tile = handle.read(16)
        pixels.clear()
        for y in range(8):
            pixels.extend(
                ((tile[y] >> s) & 1) | (((tile[y+8] >> s) & 1) << 1)
                for s in range(7, -1, -1)
            )
        yield tuple(pixels)

def world_pal_to_rgb_pal(palette):
    # NES color numbers -> (R, G, B) tuples
    return tuple(NES_PALETTE[c] for c in palette)

def rgb_pal_to_img_pal(palette):
    # (R, G, B) tuples -> sorted unique (R, G, B) tuples
    return tuple(sorted(set(palette)))

def create_usb_image(usbData, usbAttrData, tileData, worldPal):
    # return image with up to 16*16 USBs
    # worldPal: world palette (16 NES colors)

    image = Image.new("P", (16 * 16, (len(usbData) + 15) // 16 * 16), 0)

    # set image palette, create conversion table
    worldPal = world_pal_to_rgb_pal(worldPal)
    imgPal = rgb_pal_to_img_pal(worldPal)
    image.putpalette(itertools.chain.from_iterable(imgPal))
    worldPalToImgPal = tuple(imgPal.index(color) for color in worldPal)
    del worldPal, imgPal

    # for each USB, draw 2*2 tiles with correct palette
    tileImg = Image.new("P", (8, 8))
    for (ui, usb) in enumerate(usbData):
        palMask = (usbAttrData[ui] & 3) << 2  # subpalette
        for (ti, tile) in enumerate(usb):
            tileImg.putdata(tuple(
                worldPalToImgPal[palMask|pixel] for pixel in tileData[tile]
            ))
            # bits: ui = UUUUuuuu, ti = Tt
            # -> y = UUUUT000, x = uuuut000
            y = (ui & 0xf0)       | ((ti & 2) << 2)
            x = ((ui & 0xf) << 4) | ((ti & 1) << 3)
            image.paste(tileImg, (x, y))
    return image

def create_sb_image(sbData, usbImg, worldPal):
    # return image with up to 16*16 SBs

    outImg = Image.new("P", (16 * 32, (len(sbData) + 15) // 16 * 32), 0)
    outImg.putpalette(itertools.chain.from_iterable(
        rgb_pal_to_img_pal(world_pal_to_rgb_pal(worldPal))
    ))

    # copy USBs from source image to target image
    for (si, usbs) in enumerate(sbData):
        for (ui, usb) in enumerate(usbs):
            # bits: usb = UUUUuuuu -> y = UUUU0000, x = uuuu0000
            y = usb & 0xf0
            x = (usb & 0x0f) << 4
            inImg = usbImg.crop((x, y, x + 16, y + 16))
            # bits: si = SSSSssss, ui = Uu
            # -> y = SSSSU0000, x = ssssu0000
            y = ((si & 0xf0) << 1) | ((ui & 2) << 3)
            x = ((si & 0xf)  << 5) | ((ui & 1) << 4)
            outImg.paste(inImg, (x, y))
    return outImg

def create_block_image(blockData, sbData, usbImg, worldPal):
    # return image with up to 16*16 blocks

    outImg = Image.new("P", (16 * 64, (len(blockData) + 15) // 16 * 64), 0)
    outImg.putpalette(itertools.chain.from_iterable(
        rgb_pal_to_img_pal(world_pal_to_rgb_pal(worldPal))
    ))

    # copy USBs from source image to target image
    for (bi, block) in enumerate(blockData):
        for (si, sb) in enumerate(block):
            for (ui, usb) in enumerate(sbData[sb]):
                # bits: usb = UUUUuuuu -> y = UUUU0000, x = uuuu0000
                y = usb & 0xf0
                x = (usb & 0x0f) << 4
                inImg = usbImg.crop((x, y, x + 16, y + 16))
                # bits: bi = BBBBbbbb, si = Ss, ui = Uu
                # -> y = BBBBSU0000, x = bbbbsu0000
                y = ((bi & 0xf0) << 2) | ((si & 2) << 4) | ((ui & 2) << 3)
                x = ((bi & 0xf)  << 6) | ((si & 1) << 5) | ((ui & 1) << 4)
                outImg.paste(inImg, (x, y))
    return outImg

def create_map_image(mapData, blockData, sbData, usbImg, worldPal):
    # return image with up to 32*32 blocks

    outImg = Image.new("P", (32 * 64, len(mapData) // 32 * 64), 0)
    outImg.putpalette(itertools.chain.from_iterable(
        rgb_pal_to_img_pal(world_pal_to_rgb_pal(worldPal))
    ))

    # copy USBs from source image to target image
    for (bi, block) in enumerate(mapData):
        for (si, sb) in enumerate(blockData[block]):
            for (ui, usb) in enumerate(sbData[sb]):
                # bits: usb = UUUUuuuu -> y = UUUU0000, x = uuuu0000
                y = usb & 0xf0
                x = (usb & 0x0f) << 4
                inImg = usbImg.crop((x, y, x + 16, y + 16))
                # bits: bi = BBBBBbbbbb, si = Ss, ui = Uu
                # -> y = BBBBBSU0000, x = bbbbbsu0000
                y = ((bi & 0x3e0) << 1) | ((si & 2) << 4) | ((ui & 2) << 3)
                x = ((bi & 0x1f)  << 6) | ((si & 1) << 5) | ((ui & 1) << 4)
                outImg.paste(inImg, (x, y))
    return outImg

def extract_map(source, args):
    # extract one USB image, SB image, block image and/or map image from file

    # parse iNES header
    fileInfo = decode_ines_header(source)
    if fileInfo is None:
        error("not a valid iNES ROM file")

    if min(fileInfo["prgSize"], fileInfo["chrSize"]) < 128 * 1024:
        error("not Blaster Master (PRG/CHR ROM too small)")

    if fileInfo["mapper"] != 1 \
    or max(fileInfo["prgSize"], fileInfo["chrSize"]) > 128 * 1024:
        warn("probably not Blaster Master")

    (prgBank, worldPtr, chrBank) = MAP_DATA_ADDRESSES[args.map_number]
    # the only version difference
    prgBank = 4 if prgBank == 2 and args.japan else prgBank
    scrollPtr = worldPtr + 2

    # read PRG bank
    source.seek(fileInfo["prgStart"] + prgBank * 16 * 1024)
    prgBankData = source.read(16 * 1024)

    worldAddr  = decode_offset(prgBankData[worldPtr :worldPtr +2])
    scrollAddr = decode_offset(prgBankData[scrollPtr:scrollPtr+2])

    if args.verbose:
        print(f"Map={args.map_number}, PRG bank={prgBank}, CHR bank={chrBank}")
        print(
            f"World data @ ${worldAddr:04x}, scroll data @ ${scrollAddr:04x}"
        )

    (palAddr, usbAttrAddr, usbAddr, sbAddr, blockAddr, mapAddr) = (
        decode_offset(prgBankData[pos:pos+2])
        for pos in range(worldAddr, worldAddr + 12, 2)
    )
    if args.verbose:
        print(
            f"Palette @ ${palAddr:04x}, "
            f"USBs @ ${usbAddr:04x}, "
            f"SBs @ ${sbAddr:04x}, "
            f"blocks @ ${blockAddr:04x}, "
            f"map @ ${mapAddr:04x}, "
            f"USB attributes @ ${usbAttrAddr:04x}"
        )
    if not worldAddr < palAddr < usbAddr < sbAddr < blockAddr < mapAddr \
    < min(usbAttrAddr, scrollAddr):
        warn("order of data sections seems wrong")

    # palette (4*4 NES color numbers)
    worldPalette = prgBankData[palAddr:palAddr+16]
    if max(worldPalette) > 0x3f:
        error("invalid color in world palette")
    if len(set(worldPalette[i] for i in range(0, 16, 4))) > 1:
        warn("world subpalettes don't have the same background color")

    # USB data
    if sbAddr - usbAddr not in range(4, 257 * 4, 4):
        error("invalid USB data size")
    usbData = tuple(prgBankData[i:i+4] for i in range(usbAddr, sbAddr, 4))

    # SB data
    if blockAddr - sbAddr not in range(4, 257 * 4, 4):
        error("invalid SB data size")
    sbData = tuple(prgBankData[i:i+4] for i in range(sbAddr, blockAddr, 4))
    if max(itertools.chain.from_iterable(sbData)) >= len(usbData):
        warn("SB data uses nonexistent USBs")

    # block data
    if mapAddr - blockAddr not in range(4, 257 * 4, 4):
        error("invalid block data size")
    blockData = tuple(prgBankData[i:i+4] for i in range(blockAddr, mapAddr, 4))
    if max(itertools.chain.from_iterable(blockData)) >= len(sbData):
        warn("block data uses nonexistent SBs")

    # map data
    mapEnd = min(usbAttrAddr, scrollAddr)
    if mapEnd - mapAddr not in range(32, 33 * 32, 32):
        error("invalid map size")
    mapData = prgBankData[mapAddr:mapEnd]
    if max(set(mapData)) >= len(blockData):
        warn("map data uses nonexistent blocks")

    # read USB attribute data (1 byte/USB)
    usbAttrData = prgBankData[usbAttrAddr:usbAttrAddr+len(usbData)]

    # read and decode tile data
    source.seek(fileInfo["chrStart"] + chrBank * 4 * 1024)
    tileData = list(get_tile_data(source))

    # create USB image (needed for creating all other images)
    usbImg = create_usb_image(usbData, usbAttrData, tileData, worldPalette)
    if args.usb_image is not None:
        with open(args.usb_image, "wb") as target:
            usbImg.save(target)

    if args.sb_image is not None:
        sbImg = create_sb_image(sbData, usbImg, worldPalette)
        with open(args.sb_image, "wb") as target:
            sbImg.save(target)

    if args.block_image is not None:
        blockImg = create_block_image(blockData, sbData, usbImg, worldPalette)
        with open(args.block_image, "wb") as target:
            blockImg.save(target)

    if args.map_image is not None:
        mapImg = create_map_image(
            mapData, blockData, sbData, usbImg, worldPalette
        )
        with open(args.map_image, "wb") as target:
            target.seek(0)
            mapImg.save(target)

def main():
    args = parse_arguments()

    try:
        with open(args.input_file, "rb") as handle:
            extract_map(handle, args)
    except OSError:
        error("could not read or write a file")

main()
