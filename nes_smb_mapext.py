# extract map data from NES Super Mario Bros. by Nintendo
# under construction

import os, struct, sys
from PIL import Image  # Pillow, https://python-pillow.org

AREA_TYPES = ("water", "ground", "underground", "castle")

# PRG ROM addresses (not CPU addresses)
METATILE_DATA          = 0x0b08
AREA_DATA_OFFSETS      = 0x1d28
AREA_DATA_ADDRESSES_LO = 0x1d2c
AREA_DATA_ADDRESSES_HI = 0x1d4e

def error(msg):
    sys.exit(f"Error: {msg}")

def decode_ines_header(handle):
    # parse iNES ROM header; return dict or None on error
    # does not support VS System, PlayChoice-10 or trainer flags or NES 2.0
    # header
    # see https://www.nesdev.org/wiki/INES

    fileSize = handle.seek(0, 2)
    if fileSize < 16:
        return None

    handle.seek(0)
    (id_, prgSize, chrSize, flags6, flags7) \
    = struct.unpack("4s4B", handle.read(8))

    prgSize *= 16 * 1024
    chrSize *= 8 * 1024

    if id_ != b"NES\x1a" or fileSize < 16 + prgSize + chrSize:
        return None

    return {
        "prgStart": 16,
        "prgSize":  prgSize,
        "chrStart": 16 + prgSize,
        "chrSize":  chrSize,
        "mapper":   (flags7 & 0b11110000) | (flags6 >> 4),
    }

def decode_pt(handle):
    # read one pattern table (256 tiles) of CHR data;
    # generate tiles (tuples of 64 2-bit ints)
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

def pt_to_image(handle):
    # create image with 16*16 tiles (128*128 px) from background pattern table
    # data; handle must be at correct position
    image = Image.new("P", (16 * 8, 16 * 8))
    image.putpalette((0,0,0, 85,85,85, 170,170,170, 255,255,255))
    for (ti, tile) in enumerate(decode_pt(handle)):
        for (pi, pixel) in enumerate(tile):
            (ty, tx) = divmod(ti, 16)
            (py, px) = divmod(pi, 8)
            image.putpixel((tx * 8 + px, ty * 8 + py), pixel)
    return image

def create_mtile_image(handle, prgStart, tileImage):
    # create image with 16*16 metatiles (256*256 px) from PRG ROM data and
    # tile image; top 16*4 metatiles are for palette 0, etc.
    # prgStart: PRG ROM start address in file
    # note: there's garbage at the end

    # get PRG addresses of metatile data of each palette
    handle.seek(prgStart + METATILE_DATA)
    pointers = handle.read(2 * 4)
    pointers = [
        (pointers[i] + pointers[i+4] * 0x100) & 0x7fff for i in range(4)
    ]

    mtileImage = Image.new("P", (16 * 16, 16 * 16))
    mtileImage.putpalette((0,0,0, 85,85,85, 170,170,170, 255,255,255))

    for palette in range(4):
        # get tile data
        if palette < 3:
            dataEnd = pointers[palette+1]
        else:
            dataEnd = pointers[palette] + 256
        handle.seek(prgStart + pointers[palette])
        tileData = handle.read(dataEnd - pointers[palette])

        for mti in range(len(tileData) // 4):  # metatile index
            for ti in range(4):  # tile index within metatile
                # get tile
                (y, x) = divmod(tileData[mti*4+ti], 16)
                tempImage = tileImage.crop((
                    x * 8, y * 8, (x + 1) * 8, (y + 1) * 8
                ))
                # paste tile
                y = (palette * 4 + mti // 16) * 16 + ti % 2 * 8
                x = mti % 16 * 16 + ti // 2 * 8
                mtileImage.paste(tempImage, (x, y))

    return mtileImage

def get_area_count(areaType, areaDataOffsets):
    # get number of areas for area type;
    # areaDataOffsets: the array at AREA_DATA_OFFSETS
    if areaType < 3:
        return areaDataOffsets[areaType+1] - areaDataOffsets[areaType]
    return AREA_DATA_ADDRESSES_HI \
    - (AREA_DATA_ADDRESSES_LO + areaDataOffsets[areaType])

def parse_area_header(header):
    # parse area data header (2 bytes, bits TTMMMBBB PPSSFFFF)

    timeLimit = header[0] >> 6
    startHeight = (header[0] >> 3) & 0b111
    background = header[0] & 0b111  # initial
    specialPlatform = header[1] >> 6
    scenery = (header[1] >> 4) & 0b11  # initial
    floorPattern = header[1] & 0b1111  # initial
    print(
        f"area-wide data from header: {timeLimit=}, {startHeight=}, "
        f"{specialPlatform=}"
    )
    print(
        f"initial values from header: {background=}, {scenery=}, "
        f"{floorPattern=}"
    )

def get_area_width(areaData):
    # get area width in screens (1-32);
    # areaData: 256 bytes immediately after area data header
    screen = maxScreen = 0
    for i in range(0, len(areaData), 2):
        maxScreen = max(screen, maxScreen)
        block = areaData[i:i+2]
        if block[0] == 0xfd:  # terminator
            break
        elif block[0] & 0b1111 == 13 and not block[1] & 0b1000000:
            screen = block[1] & 0b11111
        elif block[1] >> 7:
            screen += 1
    return maxScreen + 1

AREA_BLK_TYPES1 = {  # has Y & size
    1: "special platform",
    2: "brick row",
    3: "3D block row",
    4: "coin row",
    5: "brick column",
    6: "3D block column",
    7: "vertical pipe",
}
METATILES_TYPE1 = {
    1: 0x16,  # special platform
    2: 0x47,  # brick
    5: 0x47,  # brick
    3: 0x61,  # 3D block
    6: 0x61,  # 3D block
    4: 0xc2,  # coin
    7: 0x10,  # vertical pipe
}

AREA_BLK_TYPES2 = {  # has Y & no size
    0:  "question block with power-up",
    1:  "question block with coin",
    2:  "hidden coin",
    3:  "hidden 1-up",
    4:  "brick with power-up",
    5:  "brick with vine",
    6:  "brick with star",
    7:  "brick with multiple coins",
    8:  "brick with 1-up",
    9:  "used question block",
    10: "horizontal end of pipe",
    11: "jumpspring",
    12: "pipe left & up (variant 1?)",
    13: "flagpole 1",
}
METATILES_TYPE2 = {
    0:  0xc0,  # question block
    1:  0xc0,  # question block
    2:  0xc4,  # used question block
    3:  0xc4,  # used question block
    4:  0x47,  # brick
    5:  0x47,  # brick
    6:  0x47,  # brick
    7:  0x47,  # brick
    8:  0x47,  # brick
    9:  0xc4,  # used question block
    13: 0x24,  # flagpole
}

AREA_BLK_TYPES3 = {  # has size & no Y
    0:  "hole in ground",
    1:  "pulley rope top",
    2:  "bridge at Y=7",
    3:  "bridge at Y=8",
    4:  "bridge at Y=10",
    5:  "water hole in ground",
    6:  "question block row at Y=3",
    7:  "question block row at Y=7",
    8:  "vertical pulley rope 1",
    9:  "vertical pulley rope 2",
    10: "castle",
    11: "ascending staircase",
    12: "pipe left & long up",
}
METATILES_TYPE3 = {
    0:  0x86,  # water
    9:  0x25,  # vertical pulley rope
    10: 0x45,  # castle
    11: 0x61,  # 3D block
}

AREA_BLK_TYPES4 = {  # has no Y or size
    0:  "pipe left & up (variant 2?)",
    1:  "flagpole 2",
    2:  "axe",
    3:  "diagonal chain",
    4:  "Bowser's bridge",
    5:  "warp zone",
    6:  "scroll stop 1",
    7:  "scroll stop 2",
    8:  "generator - red Cheep Cheep",
    9:  "generator - bullet or gray Cheep Cheep",
    10: "generator - stop",
    11: "loop command",
}
METATILES_TYPE4 = {
    1: 0x24,  # flagpole
}

REPL_MTILE = 0x88  # replacement metatile (smiling cloud)

# 47: brick
# 61: 3D block
# c0: question mark
# c2: coin

def get_metatile_from_image(i, mtileImage):
    (y, x) = divmod(i, 16)
    return mtileImage.crop((x * 16, y * 16, (x + 1) * 16, (y + 1) * 16))

def parse_area_block(block, screen, areaImage, mtileImage):
    # parse area data block (object) except terminator
    # (2 bytes, bits XXXXYYYY NTTTSSSS)
    # screen: current screen
    # areaImage: image to draw to
    # mtileImage: 16*16 metatiles
    # return: (current screen, areaImage)

    x = block[0] >> 4
    y = block[0] & 0b1111
    nextScreen = block[1] >> 7
    objType = (block[1] >> 4) & 0b111
    size = block[1] & 0b1111

    if nextScreen:
        screen += 1

    print(f"screen={screen:2}, x={x:2}: ", end="")
    imageX = (screen * 16 + x) * 16

    if y < 12:
        if objType == 0:
            # block with Y but no size
            print(f"{AREA_BLK_TYPES2[size]}, {y=}")

            mtile = get_metatile_from_image(
                METATILES_TYPE2.get(size, REPL_MTILE), mtileImage
            )
            areaImage.paste(mtile, (imageX, y * 16))
        else:
            # block with both Y and size
            if objType == 7:
                (enterable, size) = (size >> 3, size & 0b111)
                print(
                    f"{AREA_BLK_TYPES1[objType]}, {y=}, {enterable=}, {size=}"
                )
            else:
                print(f"{AREA_BLK_TYPES1[objType]}, {y=}, {size=}")

            mtile = get_metatile_from_image(
                METATILES_TYPE1[objType], mtileImage
            )
            if objType <= 4:  # row
                for i in range(size + 1):
                    areaImage.paste(mtile, (imageX + i * 16, y * 16))
            else:  # column
                for i in range(size + 1):
                    areaImage.paste(mtile, (imageX, (y + i) * 16))
    elif y == 12 or y == 15:
        # block with size but no Y
        objType += (8 if y == 15 else 0)
        print(f"{AREA_BLK_TYPES3[objType]}, {size=}")

        mtile = get_metatile_from_image(
            METATILES_TYPE3.get(objType, REPL_MTILE), mtileImage
        )
        for i in range(size + 1):
            for j in range(12):
                areaImage.paste(mtile, (imageX + i * 16, j * 16))
    elif y == 13:
        if block[1] & 0b1000000:
            # block without Y or size
            objType = block[1] & 0b111111
            print(f"{AREA_BLK_TYPES4[objType]}")

            mtile = get_metatile_from_image(
                METATILES_TYPE4.get(objType, REPL_MTILE), mtileImage
            )
            for i in range(12):
                areaImage.paste(mtile, (imageX, i * 16))
        else:
            # skip to screen
            screen = block[1] & 0b11111
            print(f"skip to screen {screen}")
    elif y == 14:
        if block[1] & 0b1000000:
            bg = block[1] & 0b111
            print(f"use background {bg}")
        else:
            scenery = (block[1] >> 4) & 0b11
            floor = block[1] & 0b1111
            print(f"use scenery {scenery} & floor pattern {floor}")
    else:
        error(f"unrecognized block {block.hex()} (this should never happen)")

    return (screen, areaImage)

def extract_map(sourceHnd, areaType, area):
    # return area image

    # parse iNES header
    fileInfo = decode_ines_header(sourceHnd)
    if fileInfo is None:
        error("not a valid iNES ROM file")
    if fileInfo["prgSize"] < 32 * 1024 or fileInfo["chrSize"] < 8 * 1024:
        error("the file doesn't look like Super Mario Bros.")

    # create image of background pattern table (16*16 tiles, 128*128 px)
    sourceHnd.seek(fileInfo["chrStart"] + 0x1000)
    tileImage = pt_to_image(sourceHnd)

    # read PRG ROM
    sourceHnd.seek(fileInfo["prgStart"])
    prgData = sourceHnd.read(fileInfo["prgSize"])

    # create image of metatiles (16*16 metatiles, 256*256 px)
    mtileImage = create_mtile_image(sourceHnd, fileInfo["prgStart"], tileImage)

    # check maximum area number for area type
    areaCount = get_area_count(
        areaType, prgData[AREA_DATA_OFFSETS:AREA_DATA_OFFSETS+4]
    )
    if area >= areaCount:
        error(f"AREA must be 0-{areaCount-1} for this AREATYPE")

    print(f"area type: {areaType} ({AREA_TYPES[areaType]})")
    print(f"area # within area type: {area}")

    areaDataOffset = prgData[AREA_DATA_OFFSETS+areaType] + area
    print(f"area data offset: {areaDataOffset}")

    areaDataAddr = (
        prgData[AREA_DATA_ADDRESSES_LO+areaDataOffset]
        + prgData[AREA_DATA_ADDRESSES_HI+areaDataOffset] * 0x100
    ) & 0x7fff
    print(f"area data PRG address: ${areaDataAddr:04x}")

    parse_area_header(prgData[areaDataAddr:areaDataAddr+2])

    areaWidth = get_area_width(prgData[areaDataAddr+2:areaDataAddr+0x102])
    print("area width in screens:", areaWidth)

    # create indexed image
    areaImage = Image.new("P", (areaWidth * 16 * 16, 12 * 16))
    areaImage.putpalette((0,0,0, 85,85,85, 170,170,170, 255,255,255))

    print("area data:")
    screen = 0
    for i in range(areaDataAddr + 2, areaDataAddr + 0x100 + 2, 2):
        block = prgData[i:i+2]
        if block[0] == 0xfd:  # terminator
            break
        (screen, areaImage) \
        = parse_area_block(block, screen, areaImage, mtileImage)

    return areaImage

def main():
    if len(sys.argv) != 5:
        sys.exit(
            "Extract map data from NES Super Mario Bros. Args: INPUTFILE "
            "OUTPUTFILE AREATYPE AREA. INPUTFILE: iNES format, US version. "
            "OUTPUTFILE: PNG file, will be overwritten! AREATYPE: 0=water, "
            "1=ground, 2=underground, 3=castle. AREA: 0 or greater; max. "
            "value depends on AREATYPE. E.g. 1 5 = level 1-1."
        )
    (inputFile, outputFile, areaType, area) = sys.argv[1:]

    # validate args (max. area value is checked later)
    if not os.path.isfile(inputFile):
        error("input file not found")
    try:
        areaType = int(areaType, 10)
        area = int(area, 10)
    except ValueError:
        error("AREATYPE and AREA must be integers.")
    if not 0 <= areaType <= 3:
        error("AREATYPE must be 0-3.")
    if area < 0:
        error("AREA must be 0 or greater.")

    # read input file
    try:
        with open(inputFile, "rb") as handle:
            areaImage = extract_map(handle, areaType, area)
    except OSError:
        error("file read error")

    # write output file
    with open(outputFile, "wb") as handle:
        handle.seek(0)
        areaImage.save(handle, "png")

main()
