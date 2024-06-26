# nes-util
Utilities for
[Nintendo Entertainment System](https://en.wikipedia.org/wiki/Nintendo_Entertainment_System)
game hacking.

Warning: the test scripts under `test/` delete files. They also need input
files listed in `test-in-files.md5`.

Table of contents:
* [Non-game-specific](#non-game-specific)
  * [ines_combine.py](#ines_combinepy)
  * [ines_info.py](#ines_infopy)
  * [ines_split.py](#ines_splitpy)
  * [nes_chr_decode.py](#nes_chr_decodepy)
  * [nes_chr_encode.py](#nes_chr_encodepy)
  * [nes_color_swap.py](#nes_color_swappy)
  * [nes_cpuaddr.py](#nes_cpuaddrpy)
  * [nes_prgbyte.py](#nes_prgbytepy)
  * [nesgenie_dec.py](#nesgenie_decpy)
  * [nesgenie_enc.py](#nesgenie_encpy)
  * [nesgenie_6to8.py](#nesgenie_6to8py)
  * [nesgenie_prgaddr.py](#nesgenie_prgaddrpy)
  * [nesgenie_verconv.py](#nesgenie_verconvpy)
  * [qneslib.py](#qneslibpy)
* [Game-specific](#game-specific)
  * [nes_blaster_mapext.py](#nes_blaster_mapextpy)
  * [nes_irriship_mapext.py](#nes_irriship_mapextpy)
  * [nes_irriship_tasgen.py](#nes_irriship_tasgenpy)
  * [nes_smb_mapext.py](#nes_smb_mapextpy)

## Non-game-specific

### ines_combine.py
```
usage: ines_combine.py [-h] -p PRG_ROM [-c CHR_ROM] [-m MAPPER] [-n {h,v,f}]
                       [-x]
                       outputFile

Create an iNES ROM file (.nes).

positional arguments:
  outputFile            iNES ROM file (.nes) to write.

options:
  -h, --help            show this help message and exit
  -p PRG_ROM, --prg-rom PRG_ROM
                        PRG ROM data file to read. Required. Size: 16-4096 KiB
                        and a multiple of 16 KiB.
  -c CHR_ROM, --chr-rom CHR_ROM
                        CHR ROM data file to read. Size: 0-2040 KiB and a
                        multiple of 8 KiB.
  -m MAPPER, --mapper MAPPER
                        iNES mapper number (0-255). Default=0 (NROM).
  -n {h,v,f}, --mirroring {h,v,f}
                        Type of name table mirroring: h=horizontal (default),
                        v=vertical, f=four-screen.
  -x, --extra-ram       The game contains extra RAM at $6000-$7fff.
```

### ines_info.py
Print information of an iNES ROM file (.nes).

Example:
```
trainer size: 0
PRG ROM size: 32768
CHR ROM size: 8192
iNES mapper number: 0
name table mirroring: vertical
has extra RAM at $6000-$7fff: no
```

### ines_split.py
```
usage: ines_split.py [-h] [-p PRG] [-c CHR] input_file

Extract PRG ROM and/or CHR ROM data from an iNES ROM file (.nes).

positional arguments:
  input_file         iNES ROM file (.nes) to read.

options:
  -h, --help         show this help message and exit
  -p PRG, --prg PRG  File to write PRG ROM data to.
  -c CHR, --chr CHR  File to write CHR ROM data to. Not written if there is no
                     data.
```

### nes_chr_decode.py
Requires [Pillow](https://python-pillow.org).
```
Convert NES CHR (graphics) data into a PNG file.
Arguments: inputFile outputFile palette
    inputFile: File to read. An iNES ROM (.nes) or raw CHR data. Size of raw
        CHR data must be a multiple of 256 bytes.
    outputFile: PNG file to write. 16 tiles wide.
    palette: Optional. Output palette or which colors will correspond to CHR
        colors 0-3. Four hexadecimal RRGGBB codes (000000-ffffff) separated by
        commas. Default: 000000,555555,aaaaaa,ffffff
```

### nes_chr_encode.py
Requires [Pillow](https://python-pillow.org).
```
Convert an image file into an NES CHR (graphics) data file.
Arguments: inputFile outputFile palette
    inputFile: Image file to read (e.g. PNG). Width must be
        128 pixels (16 tiles). Height must
        be a multiple of 8 pixels (1 tile). No more than 4 unique
        colors.
    outputFile: NES CHR data file to write. The size will be a multiple of
        256 bytes (16 tiles).
    palette: Optional. Input palette (which image colors correspond to CHR
        colors 0-3). Four hexadecimal RRGGBB color codes (000000-ffffff)
        separated by commas. All colors must be distinct. Palette must include
        every unique color in input file. Palette may contain colors not
        present in input file.
        Default: 000000,555555,aaaaaa,ffffff
```

### nes_color_swap.py
```
usage: nes_color_swap.py [-h] [-c {0,1,2,3} {0,1,2,3} {0,1,2,3} {0,1,2,3}]
                         [-f FIRST_TILE] [-n TILE_COUNT]
                         input_file output_file

Swap colors in the graphics data (CHR ROM) of an iNES ROM file (.nes).

positional arguments:
  input_file            iNES ROM file (.nes) to read.
  output_file           iNES ROM file (.nes) to write.

options:
  -h, --help            show this help message and exit
  -c {0,1,2,3} {0,1,2,3} {0,1,2,3} {0,1,2,3},
  --colors {0,1,2,3} {0,1,2,3} {0,1,2,3} {0,1,2,3}
                        Change original colors 0...3 to these colors. Four
                        colors (each 0...3) separated by spaces. Default: 0 2
                        3 1
  -f FIRST_TILE, --first-tile FIRST_TILE
                        First tile to change (0 or greater, default=0).
  -n TILE_COUNT, --tile-count TILE_COUNT
                        Number of tiles to change. 0 (default) = all starting
                        from --first-tile.
```

An example from *Super Mario Bros.* by Nintendo:

![screenshot](nes_color_swap.png)

### nes_cpuaddr.py
Requires qneslib.py (see below).

Convert an NES PRG ROM address into possible CPU addresses using the iNES ROM
file (.nes). Args: file address_in_hexadecimal

### nes_prgbyte.py
Get byte value at specified PRG ROM address in an iNES ROM file (.nes).
Arguments: file address-in-hexadecimal

### nesgenie_dec.py
Decode an NES Game Genie code. Argument: code (6 or 8 letters from
AEGIKLNOPSTUVXYZ).

Example:
```
$ python3 nesgenie_dec.py yeuzugaa
CPU address = 0xacb3, replace value = 0x07, compare value = 0x00
```

### nesgenie_enc.py
Encode an NES Game Genie code. Arguments: AAAA RR or AAAA RR CC (AAAA =
CPU address, RR = replacement value, CC = compare value; all in hexadecimal).

Example:
```
$ python3 nesgenie_enc.py acb3 07 00
YEUZUGAA
```

### nesgenie_6to8.py
Requires qneslib.py (see below).

Convert a 6-letter NES Game Genie code into 8 letters using the iNES ROM file
(.nes). Can be useful if the 6-letter code has unintended side effects. Args:
file code

### nesgenie_prgaddr.py
Requires qneslib.py (see below).

Find the PRG ROM addresses affected by an NES Game Genie code in an iNES ROM
file (.nes). Args: file code

### nesgenie_verconv.py
Requires qneslib.py (see below).
```
usage: nesgenie_verconv.py [-h] [-s SLICE_LENGTH] [-d MAX_DIFFERENT_BYTES]
                           [-v]
                           code file1 file2

Convert an NES Game Genie code from one version of a game to another using
both iNES ROM files (.nes). Technical explanation: decode the code; find out
PRG ROM addresses affected in file1; see what's in and around them; look for
similar bytestrings in file2's PRG ROM; convert the addresses back into CPU
addresses; encode them into codes.

positional arguments:
  code                  An NES Game Genie code that is known to work with
                        file1. Six-letter codes are not allowed if file1 uses
                        PRG ROM bankswitching.
  file1                 An iNES ROM file (.nes) to read. The game your code is
                        known to work with.
  file2                 Another iNES ROM file (.nes) to read. The equivalent
                        code for this game will be searched for.

options:
  -h, --help            show this help message and exit
  -s SLICE_LENGTH, --slice-length SLICE_LENGTH
                        How many PRG ROM bytes to compare both before and
                        after the relevant byte (that is, total number of
                        bytes compared is twice this value, plus one). Fewer
                        bytes will be compared if the relevant byte is too
                        close to start or end of PRG ROM. 1 to 20, default=4.
                        Decrease to get more results.
  -d MAX_DIFFERENT_BYTES, --max-different-bytes MAX_DIFFERENT_BYTES
                        Maximum number of non-matching bytes allowed in each
                        pair of PRG ROM slices to compare. (The relevant byte
                        must always match.) Minimum=0, default=1,
                        maximum=twice --slice-length, minus one. Increase to
                        get more results.
  -v, --verbose         Print more information. Note: all printed numbers are
                        hexadecimal.
```

### qneslib.py
Does not do anything by itself but is needed by some other programs in this
repo. Just copy this file to the same directory. Formerly known as neslib.py,
ineslib.py and nesgenielib.py.
```
NAME
    qneslib - qalle's NES library (Nintendo Entertainment System stuff).

FUNCTIONS
    address_cpu_to_prg(cpuAddr, prgBankSize, prgSize)
        Convert a CPU ROM address into possible PRG ROM addresses.
        cpuAddr:     CPU ROM address (0x8000-0xffff)
        prgBankSize: PRG ROM bank size (8_192/16_384/32_768)
        prgSize:     PRG ROM size
        generate:    PRG ROM addresses

    address_prg_to_cpu(prgAddr, prgBankSize)
        Convert a PRG ROM address into possible CPU ROM addresses.
        prgAddr:     PRG ROM address
        prgBankSize: PRG ROM bank size (8_192/16_384/32_768)
        generate:    CPU ROM addresses (0x8000-0xffff)

    game_genie_decode(code)
        Decode a Game Genie code.
        code: 6 or 8 letters from GAME_GENIE_LETTERS
        return:
            if invalid code: None
            otherwise:       (cpu_address, replacement_value, compare_value):
                cpu_address:       0x8000-0xffff
                replacement_value: 0x00-0xff
                compare_value:     None if 6-letter code, 0x00-0xff if 8-letter
                                   code

    game_genie_encode(addr, repl, comp=None)
        Encode a Game Genie code.
        addr: CPU address (0x0000-0xffff; MSB ignored)
        repl: replacement value (0x00-0xff)
        comp: compare value (0x00-0xff/None)
        return:
            if invalid arguments: None
            if comp is None     : 6-letter code
            if comp is not None : 8-letter code

    ines_header_decode(handle)
        Parse the header of an iNES ROM file.
        Note: does not support VS System or PlayChoice-10 flags or NES 2.0 header.
        handle: iNES ROM file
        return: None on error, otherwise a dict with the following keys:
            trainerStart: trainer address
            trainerSize:  trainer size
            prgStart:     PRG ROM address
            prgSize:      PRG ROM size
            chrStart:     CHR ROM address
            chrSize:      CHR ROM size
            mapper:       iNES mapper number (0x00-0xff)
            mirroring:    name table mirroring ('h'=horizontal, 'v'=vertical,
                          'f'=four-screen)
            extraRam:     does the game have extra RAM? (bool)

    ines_header_encode(prgSize, chrSize, mapper=0, mirroring='h', extraRam=False)
        Create an iNES file header.
        Note: does not support VS System or PlayChoice-10 flags or NES 2.0 header.
        prgSize:   PRG ROM size
        chrSize:   CHR ROM size
        mapper:    iNES mapper number (0x00-0xff)
        mirroring: name table mirroring ('h'=horizontal, 'v'=vertical,
                   'f'=four-screen)
        extraRam:  does the game have extra RAM? (bool)
        return:    16 bytes or None on error

    is_mapper_known(mapper)
        Is the mapper known by this program? (If not, mapper functions are more
        likely to return incorrect info.)
        mapper: iNES mapper number (0x00-0xff)
        return: bool

    is_prg_bankswitched(prgSize, mapper)
        Does the game use PRG ROM bankswitching? (May give false positives,
        especially if the mapper is unknown. Should not give false negatives.)
        prgSize: PRG ROM size
        mapper:  iNES mapper number (0x00-0xff)
        return:  bool

    mapper_name(mapper)
        Get the name of the mapper.
        mapper: iNES mapper number (0x00-0xff)
        return: string ("(unknown)" if unknown mapper)

    min_prg_bank_size(prgSize, mapper)
        Get the smallest PRG ROM bank size a game may use.
        prgSize: PRG ROM size
        mapper:  iNES mapper number (0x00-0xff)
        return:  8_192/16_384/32_768 (8_192 if unknown mapper)

    min_prg_bank_size_for_mapper(mapper)
        Get the smallest PRG ROM bank size supported by the mapper.
        mapper: iNES mapper number (0x00-0xff)
        return: 8_192/16_384/32_768 (8_192 if unknown mapper)

    tile_slice_decode(loByte, hiByte)
        Decode 8*1 pixels of one tile of CHR data.
        loByte: low bitplane (0x00-0xff)
        hiByte: high bitplane (0x00-0xff)
        return: eight 2-bit ints

    tile_slice_encode(pixels)
        Encode 8*1 pixels of one tile of CHR data.
        pixels: eight 2-bit ints
        return: (low_bitplane, high_bitplane); both 0x00-0xff

DATA
    GAME_GENIE_LETTERS = 'APZLGITYEOXUKSVN'
    PALETTE = {0: (116, 116, 116), 1: (36, 24, 140), 2: (0, 0, 168), 3: (6...
```

NES Game Genie code format:

![NES Game Genie code format](nesgenieformat.png)

## Game-specific

### nes_blaster_mapext.py
Requires [Pillow](https://python-pillow.org).
```
usage: nes_blaster_mapext.py [-h] [-j] [-n MAP_NUMBER] [-u USB_IMAGE]
                             [-s SB_IMAGE] [-b BLOCK_IMAGE] [-m MAP_IMAGE]
                             [-v]
                             input_file

Extract world maps from NES Blaster Master to PNG files.

positional arguments:
  input_file            Blaster Master ROM file in iNES format (.nes, US/US
                        prototype/EUR/JP; see also --japan).

options:
  -h, --help            show this help message and exit
  -j, --japan           Input file is Japanese version (Chou-Wakusei Senki -
                        MetaFight).
  -n MAP_NUMBER, --map-number MAP_NUMBER
                        Map to extract: 0-7 = side view of area 1-8, 8-15 =
                        overhead view of area 1-8. Default=0.
  -u USB_IMAGE, --usb-image USB_IMAGE
                        Save ultra-subblocks (16*16 px each) as PNG file (up
                        to 256*256 px).
  -s SB_IMAGE, --sb-image SB_IMAGE
                        Save subblocks (32*32 px each) as PNG file (up to
                        512*512 px).
  -b BLOCK_IMAGE, --block-image BLOCK_IMAGE
                        Save blocks (64*64 px each) as PNG file (up to
                        1024*1024 px).
  -m MAP_IMAGE, --map-image MAP_IMAGE
                        Save map as PNG file (up to 32*32 blocks or 2048*2048
                        px).
  -v, --verbose         Print more information.
```

### nes_irriship_mapext.py
Requires [Pillow](https://python-pillow.org).

Extract map data from NES Irritating Ship. Arguments: inputFile outputFile
(inputFile = iNES ROM, outputFile = PNG (will be overwritten)).

### nes_irriship_tasgen.py
Generate an FCEUX movie that plays Irritating Ship. Under construction.

### nes_smb_mapext.py
**Note:** This program is at an early stage.
[VGMaps](https://vgmaps.com/Atlas/NES/index.htm#SuperMarioBros) has much better
maps of *Super Mario Bros.*

Requires [Pillow](https://python-pillow.org).

```
Extract map data (excluding enemies) from NES Super Mario Bros. by Nintendo.
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
E.g. AREATYPE 1, AREA 5 = above-ground part of level 1-1.
Note: looping castle areas look totally wrong; all other areas look more or
less wrong too.
```
