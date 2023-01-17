# extract map data from NES Super Mario Bros. by Nintendo
# under construction

# tile = 8*8 pixels with 2 bitplanes
# metatile = 2*2 tiles with 1 of 4 palettes
# screen = 16*13 metatiles (area objects can't be placed on bottom row)
# area = 1-32 screens horizontally (ground area 9 is 1 screen, ground area 16
#        is 24 screens)
# level = 1 or more areas, connected by pipes/vines/falling/other?

# for area/enemy data, see
# https://www.youtube.com/watch?v=1ysdUajrhL8
# (5:50-18:20 for area data, 18:20-22:00 for enemy data)

import os, struct, sys
from PIL import Image  # Pillow, https://python-pillow.org

HELP_TEXT = """\
Extract map data from NES Super Mario Bros. by Nintendo.
Argument syntax:
    Short summary of all areas:
        INPUTFILE
    All data and image of one area:
        INPUTFILE OUTPUTFILE AREATYPE AREA
Arguments:
    INPUTFILE: iNES format, US version.
    OUTPUTFILE: PNG, will be overwritten!
    AREATYPE: 0=water, 1=ground, 2=underground, 3=castle.
    AREA: 0 or greater; max. value depends on AREATYPE.
E.g. AREATYPE 1, AREA 5 = level 1-1.\
"""

AREA_TYPES = ("water", "ground", "underground", "castle")

# PRG ROM addresses (not CPU addresses)
METATILE_DATA          = 0x0b08
FLOOR_PATTERNS         = 0x13dc
AREA_DATA_OFFSETS      = 0x1d28
AREA_DATA_ADDRESSES_LO = 0x1d2c
AREA_DATA_ADDRESSES_HI = 0x1d4e

# enumerate types of area data blocks
(
    AB_Y_NO_SIZE,      # object with Y but no size (e.g. "?" with power-up)
    AB_Y_SIZE,         # object with both Y and size (e.g. brick row)
    AB_SIZE_NO_Y,      # object with size but no Y (e.g. castle)
    AB_NO_Y_NO_SIZE,   # object without Y or size (e.g. axe)
    AB_SCREEN,         # skip to screen
    AB_BACKGROUND,     # switch background
    AB_SCENERY_FLOOR,  # switch scenery & floor pattern
) = range(7)

# --- used by both extract_map() and print_summary() --------------------------

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

def get_area_count(areaType, handle, prgStart):
    # get number of areas for area type;

    # get area data offsets
    handle.seek(prgStart + AREA_DATA_OFFSETS)
    offsets = handle.read(4)

    if areaType < 3:
        return offsets[areaType+1] - offsets[areaType]
    return AREA_DATA_ADDRESSES_HI \
    - (AREA_DATA_ADDRESSES_LO + offsets[areaType])

def parse_area_header(header):
    # parse area data header (2 bytes, bits TTMMMBBB PPSSFFFF)

    return {
        "timeLimit":       header[0] >> 6,
        "startHeight":     (header[0] >> 3) & 0b111,
        "background":      header[0] & 0b111,         # initial
        "specialPlatform": header[1] >> 6,
        "scenery":         (header[1] >> 4) & 0b11,   # initial
        "floorPattern":    header[1] & 0b1111,        # initial
    }

def generate_area_blocks(handle, prgStart, areaDataAddr):
    # generate blocks (2 bytes each) from area data (excluding header and
    # terminator)

    handle.seek(prgStart + areaDataAddr + 2)
    areaData = handle.read(0x100)
    for i in range(0, len(areaData), 2):
        block = areaData[i:i+2]
        if block[0] == 0xfd:  # terminator
            break
        yield block

def get_area_block_type(block):
    # block: 2 bytes; return an AB_... constant (see definitions)

    y = block[0] & 0b1111

    if y < 12:
        return AB_Y_SIZE if block[1] & 0b1110000 else AB_Y_NO_SIZE
    if y == 12 or y == 15:
        return AB_SIZE_NO_Y
    if y == 13:
        return AB_NO_Y_NO_SIZE if block[1] & 0b1000000 else AB_SCREEN
    # Y = 14
    return AB_BACKGROUND if block[1] & 0b1000000 else AB_SCENERY_FLOOR

def get_area_width(handle, prgStart, areaDataAddr):
    # get area width in screens (1-32)

    screen = maxScreen = 0
    for block in generate_area_blocks(handle, prgStart, areaDataAddr):
        maxScreen = max(screen, maxScreen)
        if get_area_block_type(block) == AB_SCREEN:
            screen = block[1] & 0b11111
        elif block[1] >> 7:
            screen += 1
    return maxScreen + 1

def get_metatile_from_image(i, mtileImage):
    (y, x) = divmod(i, 16)
    return mtileImage.crop((x * 16, y * 16, (x + 1) * 16, (y + 1) * 16))

def get_area_data_addr(areaType, area, handle, prgStart):
    # get PRG ROM address of area data

    handle.seek(prgStart + AREA_DATA_OFFSETS + areaType)
    offset = handle.read(1)[0] + area

    handle.seek(prgStart + AREA_DATA_ADDRESSES_LO + offset)
    lowByte = handle.read(1)[0]
    handle.seek(prgStart + AREA_DATA_ADDRESSES_HI + offset)
    highByte = handle.read(1)[0]

    return (lowByte + highByte * 0x100) & 0x7fff

# --- used by extract_map(), not print_summary() ------------------------------

AREA_BLK_TYPES_Y_SIZE = {
    1: "special platform",
    2: "brick row",
    3: "3D block row",
    4: "coin row",
    5: "brick column",
    6: "3D block column",
    7: "vertical pipe",
}
METATILES_TYPE_Y_SIZE = {
    1: 0x16,  # special platform
    2: 0x47,  # brick
    5: 0x47,  # brick
    3: 0x61,  # 3D block
    6: 0x61,  # 3D block
    4: 0xc2,  # coin
    # vertical pipe is special
}

AREA_BLK_TYPES_Y_NO_SIZE = {
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
METATILES_TYPE_Y_NO_SIZE = {
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

AREA_BLK_TYPES_SIZE_NO_Y = {
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
METATILES_TYPE_SIZE_NO_Y = {
    0:  0x00,  # solid black
    5:  0x86,  # water
    6:  0xc0,  # question block
    7:  0xc0,  # question block
    9:  0x25,  # vertical pulley rope
    10: 0x45,  # castle
    11: 0x61,  # 3D block
}

AREA_BLK_TYPES_NO_Y_NO_SIZE = {
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
METATILES_TYPE_NO_Y_NO_SIZE = {
    1: 0x24,  # flagpole
}

REPL_MTILE = 0x88  # replacement metatile (smiling cloud)

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

def parse_area_block(block, screen, areaImage, mtileImage):
    # parse area data block (object) except terminator
    # (2 bytes, bits XXXXYYYY NTTTSSSS)
    # screen: current screen
    # areaImage: image to draw to
    # mtileImage: 16*16 metatiles
    # return: (current screen, areaImage)

    blockType = get_area_block_type(block)

    x = block[0] >> 4
    y = block[0] & 0b1111  # only meaningful for AB_Y_SIZE, AB_Y_NO_SIZE
    nextScreen = block[1] >> 7

    # get type of object, if any
    if blockType == AB_Y_NO_SIZE:
        objType = block[1] & 0b1111
    elif blockType == AB_Y_SIZE:
        objType = (block[1] >> 4) & 0b111
    elif blockType == AB_SIZE_NO_Y:
        objType = ((block[1] >> 4) & 0b111) + (8 if y == 15 else 0)
    elif blockType == AB_NO_Y_NO_SIZE:
        objType = block[1] & 0b111111

    # get other properties of object, if any
    if blockType == AB_Y_SIZE and objType == 7:  # vertical pipe
        enterable = (block[1] >> 3) & 0b1
        size = block[1] & 0b111
    elif blockType in (AB_Y_SIZE, AB_SIZE_NO_Y):
        size = block[1] & 0b1111

    if nextScreen:
        screen += 1

    print(f"screen={screen:2}, x={x:2}: ", end="")
    imageX = (screen * 16 + x) * 16

    if blockType == AB_Y_NO_SIZE:
        print(f"{AREA_BLK_TYPES_Y_NO_SIZE[objType]}, {y=}")
        mtile = get_metatile_from_image(
            METATILES_TYPE_Y_NO_SIZE.get(objType, REPL_MTILE), mtileImage
        )
        areaImage.paste(mtile, (imageX, y * 16))

    elif blockType == AB_Y_SIZE:
        if objType == 7:
            # vertical pipe
            print(
                f"{AREA_BLK_TYPES_Y_SIZE[objType]}, {y=}, {enterable=}, "
                f"{size=}"
            )
            for i in range(2):
                for j in range(size + 1):
                    mti = 0x10 + i + (0 if j == 0 else 4)
                    mtile = get_metatile_from_image(mti, mtileImage)
                    areaImage.paste(mtile, (imageX + i * 16, (y + j) * 16))
        else:
            print(f"{AREA_BLK_TYPES_Y_SIZE[objType]}, {y=}, {size=}")
            mtile = get_metatile_from_image(
                METATILES_TYPE_Y_SIZE[objType], mtileImage
            )
            if objType <= 4:
                # row
                for i in range(size + 1):
                    areaImage.paste(mtile, (imageX + i * 16, y * 16))
            else:
                # column
                for i in range(size + 1):
                    areaImage.paste(mtile, (imageX, (y + i) * 16))

    elif blockType == AB_SIZE_NO_Y:
        print(f"{AREA_BLK_TYPES_SIZE_NO_Y[objType]}, {size=}")
        mtile = get_metatile_from_image(
            METATILES_TYPE_SIZE_NO_Y.get(objType, REPL_MTILE), mtileImage
        )
        if objType in (6, 7):
            # question block row at Y=3/7
            j = 3 + (objType - 6) * 4
            for i in range(size + 1):
                areaImage.paste(mtile, (imageX + i * 16, j * 16))
        else:
            for i in range(size + 1):
                for j in range(13):
                    areaImage.paste(mtile, (imageX + i * 16, j * 16))

    elif blockType == AB_NO_Y_NO_SIZE:
        print(f"{AREA_BLK_TYPES_NO_Y_NO_SIZE[objType]}")
        mtile = get_metatile_from_image(
            METATILES_TYPE_NO_Y_NO_SIZE.get(objType, REPL_MTILE), mtileImage
        )
        for i in range(13):
            areaImage.paste(mtile, (imageX, i * 16))

    elif blockType == AB_SCREEN:
        screen = block[1] & 0b11111
        print(f"skip to screen {screen}")

    elif blockType == AB_BACKGROUND:
        bg = block[1] & 0b111
        print(f"use background {bg}")

    elif blockType == AB_SCENERY_FLOOR:
        scenery = (block[1] >> 4) & 0b11
        floor = block[1] & 0b1111
        print(f"use scenery {scenery} & floor pattern {floor}")

    else:
        error("this should never happen")

    return (screen, areaImage)

def get_floor_patterns(handle, prgStart):
    # return floor patterns as 16 tuples of 13 ints (0=blank, 1=brick; top to
    # bottom)

    handle.seek(prgStart + FLOOR_PATTERNS)
    patterns = handle.read(16 * 2)
    patternsList = []
    for i in range(0, 16 * 2, 2):
        # interpret 2 bytes as unsigned little endian
        pattern = patterns[i] + patterns[i+1] * 0x100
        # convert bottom 13 bits into a tuple, low bit first
        patternList = []
        for j in range(13):
            patternList.append(pattern & 1)
            pattern >>= 1
        patternsList.append(tuple(patternList))
    return patternsList

def draw_floor_patterns(areaImage, areaDataAddr, mtileImage, handle, prgStart):
    # draw floor patterns on area image

    areaWidth = get_area_width(handle, prgStart, areaDataAddr)
    floorPatterns = get_floor_patterns(handle, prgStart)
    mtile = get_metatile_from_image(0x54, mtileImage)

    # find out where floor pattern changes
    patternChanges = {}  # key = screen * 16 + X, value = pattern
    screen = 0
    for block in generate_area_blocks(handle, prgStart, areaDataAddr):
        if block[1] >> 7:
            screen += 1
        if get_area_block_type(block) == AB_SCENERY_FLOOR:
            x = block[0] >> 4
            pattern = block[1] & 0b1111
            patternChanges[screen*16+x] = pattern

    # get initial floor pattern
    handle.seek(prgStart + areaDataAddr)
    pattern = parse_area_header(handle.read(2))["floorPattern"]

    # draw columns
    for x in range(areaWidth * 16):
        for (y, isFilled) in enumerate(floorPatterns[pattern]):
            if isFilled:
                areaImage.paste(mtile, (x * 16, y * 16))
        pattern = patternChanges.get(x, pattern)
    return areaImage

def extract_map(handle, areaType, area):
    # return area image, print info

    # parse iNES header
    fileInfo = decode_ines_header(handle)

    # create image of background pattern table (16*16 tiles, 128*128 px)
    handle.seek(fileInfo["chrStart"] + 0x1000)
    tileImage = pt_to_image(handle)

    # read PRG ROM
    handle.seek(fileInfo["prgStart"])
    prgData = handle.read(fileInfo["prgSize"])

    # create image of metatiles (16*16 metatiles, 256*256 px)
    mtileImage = create_mtile_image(handle, fileInfo["prgStart"], tileImage)

    # check maximum area number for area type
    areaCount = get_area_count(areaType, handle, fileInfo["prgStart"])
    if area >= areaCount:
        error(f"AREA must be 0-{areaCount-1} for this AREATYPE")

    print(f"area type: {areaType} ({AREA_TYPES[areaType]})")
    print(f"area # within area type: {area}")

    areaDataAddr = get_area_data_addr(
        areaType, area, handle, fileInfo["prgStart"]
    )
    print(f"area data PRG address: ${areaDataAddr:04x}")

    hdrInfo = parse_area_header(prgData[areaDataAddr:areaDataAddr+2])
    print(
        "header - area-wide values: "
        "time limit", hdrInfo["timeLimit"],
        ", start height", hdrInfo["startHeight"],
        ", special platform", hdrInfo["specialPlatform"],
    )
    print(
        "header - initial values: "
        "background", hdrInfo["background"],
        ", scenery", hdrInfo["scenery"],
        ", floor pattern", hdrInfo["floorPattern"],
    )

    areaWidth = get_area_width(handle, fileInfo["prgStart"], areaDataAddr)
    print("area width in screens:", areaWidth)

    # create indexed image
    areaImage = Image.new("P", (areaWidth * 16 * 16, 13 * 16))
    areaImage.putpalette((0,0,0, 85,85,85, 170,170,170, 255,255,255))

    # draw floor patterns
    areaImage = draw_floor_patterns(
        areaImage, areaDataAddr, mtileImage, handle, fileInfo["prgStart"]
    )

    print("area data:")
    screen = 0
    for block in generate_area_blocks(
        handle, fileInfo["prgStart"], areaDataAddr
    ):
        (screen, areaImage) \
        = parse_area_block(block, screen, areaImage, mtileImage)

    return areaImage

# -----------------------------------------------------------------------------

def print_summary(handle):
    # print a summary of all areas

    # read PRG ROM
    fileInfo = decode_ines_header(handle)
    handle.seek(fileInfo["prgStart"])
    prgData = handle.read(fileInfo["prgSize"])

    for areaType in range(4):
        print(f"area type {areaType} ({AREA_TYPES[areaType]}):")
        areaCount = get_area_count(areaType, handle, fileInfo["prgStart"])
        for area in range(areaCount):
            dataAddr = get_area_data_addr(
                areaType, area, handle, fileInfo["prgStart"]
            )
            width = get_area_width(handle, fileInfo["prgStart"], dataAddr)
            handle.seek(dataAddr)
            hdrInfo = parse_area_header(handle.read(2))
            print(
                f"area {area:2}: "
                f"address ${dataAddr:04x}, "
                f"{width:2} screens, "
                f"special platform type {hdrInfo['specialPlatform']}"
            )

# -----------------------------------------------------------------------------

def main():
    if len(sys.argv) not in (2, 5):
        sys.exit(HELP_TEXT)

    inputFile = sys.argv[1]

    if len(sys.argv) == 5:
        summary = False
        (outputFile, areaType, area) = sys.argv[2:5]
        try:
            areaType = int(areaType, 10)
            area = int(area, 10)
        except ValueError:
            error("AREATYPE and AREA must be integers.")
        if not 0 <= areaType <= 3:
            error("AREATYPE must be 0-3.")
        if area < 0:
            error("AREA must be 0 or greater.")
    else:
        summary = True

    if not os.path.isfile(inputFile):
        error("input file not found")

    # read input file
    try:
        with open(inputFile, "rb") as handle:
            fileInfo = decode_ines_header(handle)
            if fileInfo is None:
                error("not a valid iNES ROM file")
            if fileInfo["prgSize"] < 32 * 1024 \
            or fileInfo["chrSize"] < 8 * 1024:
                error("the file doesn't look like Super Mario Bros.")

            if summary:
                print_summary(handle)
            else:
                areaImage = extract_map(handle, areaType, area)
    except OSError:
        error("file read error")

    # write output file
    if not summary:
        with open(outputFile, "wb") as handle:
            handle.seek(0)
            areaImage.save(handle, "png")

main()
