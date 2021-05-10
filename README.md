# nes-util
Various utilities related to the [Nintendo Entertainment System](http://en.wikipedia.org/wiki/Nintendo_Entertainment_System).

**Note**: many programs in this repo require the [Pillow](https://python-pillow.org) module and qneslib.py (immediately below).

## qneslib.py
Does not do anything by itself but is needed by many other programs in this repo. Just copy this file to the same directory. Formerly known as neslib.py, ineslib.py and nesgenielib.py.
```
NAME
    qneslib - qalle's NES library (Nintendo Entertainment System stuff).

CLASSES
    builtins.Exception(builtins.BaseException)
        QneslibError

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
            otherwise:       (CPU_address, replacement_value, compare_value):
                CPU_address:       0x8000-0xffff
                replacement_value: 0x00-0xff
                compare_value:     None if 6-letter code, 0x00-0xff if 8-letter code

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
        handle: iNES ROM file
        return: None on error, otherwise a dict with the following keys:
            trainerStart: trainer address
            trainerSize:  trainer size
            prgStart:     PRG ROM address
            prgSize:      PRG ROM size
            chrStart:     CHR ROM address
            chrSize:      CHR ROM size
            mapper:       iNES mapper number (0x00-0xff)
            mirroring:    name table mirroring ('h'=horizontal, 'v'=vertical, 'f'=four-screen)
            extraRam:     does the game have extra RAM? (bool)

    ines_header_encode(prgSize, chrSize, mapper=0, mirroring='h', extraRam=False)
        Create an iNES file header.
        prgSize:   PRG ROM size
        chrSize:   CHR ROM size
        mapper:    iNES mapper number (0x00-0xff)
        mirroring: name table mirroring (h=horizontal, v=vertical, f=four-screen)
        extraRam:  does the game have extra RAM (bool)
        return:    16 bytes
        raise:     QneslibError on error

    is_mapper_known(mapper)
        Is the mapper known by this program? (If not, mapper functions are more likely to return
        incorrect info.)
        mapper: iNES mapper number (0x00-0xff)
        return: bool

    is_prg_bankswitched(prgSize, mapper)
        Does the game use PRG ROM bankswitching? (May give false positives, especially if the
        mapper is unknown. Should not give false negatives.)
        prgSize: PRG ROM size
        mapper:  iNES mapper number (0x00-0xff)
        return:  bool

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

![NES Game Genie code format](nesgenieformat.png)

## ines_combine.py
```
usage: ines_combine.py [-h] -p PRG_ROM [-c CHR_ROM] [-m MAPPER] [-n {h,v,f}] [-x] outputFile

Create an iNES ROM file (.nes) from PRG ROM and CHR ROM data files.

positional arguments:
  outputFile            The iNES ROM file (.nes) to write.

optional arguments:
  -h, --help            show this help message and exit
  -p PRG_ROM, --prg-rom PRG_ROM
                        PRG ROM data file. Required. Size: 16...4096 KiB and a multiple of 16 KiB.
  -c CHR_ROM, --chr-rom CHR_ROM
                        CHR ROM data file. Size: 0...2040 KiB and a multiple of 8 KiB.
  -m MAPPER, --mapper MAPPER
                        Mapper number (0...255). Default=0 (NROM).
  -n {h,v,f}, --mirroring {h,v,f}
                        Type of name table mirroring: h=horizontal (default), v=vertical, f=four-
                        screen.
  -x, --extra-ram       The game contains extra RAM at $6000...$7fff.
```

## ines_info.py
Print information of an iNES ROM file (.nes) in CSV format. Argument: file. Output fields: "file","size","prgSize","chrSize","mapper","mirroring","extraRam","trainerSize","checksum","prgChecksum","chrChecksum". prg=PRG ROM, chr=CHR ROM, mirroring=name table mirroring (h=horizontal, v=vertical, f=four-screen), checksum=CRC32 (zlib).

Example:
```
"smb1.nes",40976,32768,8192,0,"v","no",0,"3337ec46","5cf548d3","867b51ad"
```

## ines_split.py
```
usage: ines_split.py [-h] [-p PRG] [-c CHR] input_file

Extract PRG ROM and/or CHR ROM data from an iNES ROM file (.nes).

positional arguments:
  input_file         iNES ROM file (.nes) to read.

optional arguments:
  -h, --help         show this help message and exit
  -p PRG, --prg PRG  File to write PRG ROM data to.
  -c CHR, --chr CHR  File to write CHR ROM data to. Not written if there is no data.
```

## nes_blaster_mapext.py
```
usage: nes_blaster_mapext.py [-h] [-j] [-n MAP_NUMBER] [-u ULTRA_SUBBLOCK_IMAGE]
                             [-s SUBBLOCK_IMAGE] [-b BLOCK_IMAGE] [-m MAP_IMAGE] [-v]
                             input_file

Extract world maps from NES Blaster Master to PNG files.

positional arguments:
  input_file            Blaster Master ROM file in iNES format (.nes, US/US prototype/EUR/JP; see
                        also --japan).

optional arguments:
  -h, --help            show this help message and exit
  -j, --japan           Input file is Japanese version (Chou-Wakusei Senki - MetaFight).
  -n MAP_NUMBER, --map-number MAP_NUMBER
                        Map to extract: 0...7 = side view of area 1...8, 8...15 = overhead view of
                        area 1...8. Default=0.
  -u ULTRA_SUBBLOCK_IMAGE, --ultra-subblock-image ULTRA_SUBBLOCK_IMAGE
                        Save ultra-subblocks as PNG file (256*256 px).
  -s SUBBLOCK_IMAGE, --subblock-image SUBBLOCK_IMAGE
                        Save subblocks as PNG file (512*512 px).
  -b BLOCK_IMAGE, --block-image BLOCK_IMAGE
                        Save blocks as PNG file (1024*1024 px).
  -m MAP_IMAGE, --map-image MAP_IMAGE
                        Save map as PNG file (up to 2048*2048 px).
  -v, --verbose         Print more information. Note: all addresses are hexadecimal.
```

## nes_chr_decode.py
```
usage: nes_chr_decode.py [-h] [-p PALETTE PALETTE PALETTE PALETTE] input_file output_file

Convert NES CHR (graphics) data into a PNG file.

positional arguments:
  input_file            File to read. An iNES ROM file (.nes) or raw CHR data (the size must be a
                        multiple of 256 bytes).
  output_file           PNG file to write. Always 128 pixels (16 tiles) wide.

optional arguments:
  -h, --help            show this help message and exit
  -p PALETTE PALETTE PALETTE PALETTE, --palette PALETTE PALETTE PALETTE PALETTE
                        Output palette (which image colors correspond to CHR colors 0...3). Four
                        hexadecimal RRGGBB color codes separated by spaces. Default: 000000 555555
                        aaaaaa ffffff
```

## nes_chr_encode.py
```
usage: nes_chr_encode.py [-h] [-p PALETTE PALETTE PALETTE PALETTE] [-v] input_file output_file

Convert an image file into an NES CHR (graphics) data file.

positional arguments:
  input_file            Image file to read. Width must be 128 pixels (16 tiles). Height must be a
                        multiple of 8 pixels (1 tile). There must be four unique colors or less.
                        See also --palette.
  output_file           NES CHR data file to write. The size will be a multiple of 256 bytes (16
                        tiles).

optional arguments:
  -h, --help            show this help message and exit
  -p PALETTE PALETTE PALETTE PALETTE, --palette PALETTE PALETTE PALETTE PALETTE
                        Input palette (which image colors correspond to CHR colors 0...3). Four
                        hexadecimal RRGGBB color codes separated by spaces. Must be all distinct
                        and include every unique color in the input file. May contain colors not
                        present in the input file. Default: 000000 555555 aaaaaa ffffff
  -v, --verbose         Print more info.
```

## nes_color_swap.py
```
usage: nes_color_swap.py [-h] [-c {0,1,2,3} {0,1,2,3} {0,1,2,3} {0,1,2,3}] [-f FIRST_TILE]
                         [-n TILE_COUNT]
                         input_file output_file

Swap colors in the graphics data (CHR ROM) of an iNES ROM file (.nes).

positional arguments:
  input_file            iNES ROM file (.nes) to read.
  output_file           iNES ROM file (.nes) to write.

optional arguments:
  -h, --help            show this help message and exit
  -c {0,1,2,3} {0,1,2,3} {0,1,2,3} {0,1,2,3}, --colors {0,1,2,3} {0,1,2,3} {0,1,2,3} {0,1,2,3}
                        Change original colors 0...3 to these colors. Four colors (each 0...3)
                        separated by spaces. Default: 0 2 3 1
  -f FIRST_TILE, --first-tile FIRST_TILE
                        First tile to change (0 or greater, default=0).
  -n TILE_COUNT, --tile-count TILE_COUNT
                        Number of tiles to change. 0 (default) = all starting from --first-tile.
```

## nes_cpuaddr.py
Convert an NES PRG ROM address into possible CPU addresses using the iNES ROM file (.nes). Args: file address_in_hexadecimal

## nes_prgbyte.py
Get byte value at specified PRG ROM address in an iNES ROM file (.nes). Args: file address_in_hexadecimal

## nesgenie.py
Encode and decode NES Game Genie codes. Argument: six-letter code, eight-letter code, AAAA RR or AAAA RR CC (AAAA = address in hexadecimal, RR = replacement value in hexadecimal, CC = compare value in hexadecimal).

Example:
```
SXIOPO: CPU address = 0x91d9, replace value = 0xad, compare value = none
```

## nesgenie_6to8.py
Convert a 6-letter NES Game Genie code into 8 letters using the iNES ROM file (.nes). Args: file code

## nesgenie_prgaddr.py
Find the PRG ROM addresses affected by an NES Game Genie code in an iNES ROM file (.nes). Args: file code

## nesgenie_verconv.py
```
usage: nesgenie_verconv.py [-h] [-s SLICE_LENGTH] [-d MAX_DIFFERENT_BYTES] [-v] code file1 file2

Convert an NES Game Genie code from one version of a game to another using both iNES ROM files
(.nes). Technical explanation: decode the code; find out PRG ROM addresses affected in file1; see
what's in and around them; look for similar bytestrings in file2's PRG ROM; convert the addresses
back into CPU addresses; encode them into codes.

positional arguments:
  code                  An NES Game Genie code that is known to work with file1. Six-letter codes
                        are not allowed if file1 uses PRG ROM bankswitching.
  file1                 An iNES ROM file (.nes) to read. The game your code is known to work with.
  file2                 Another iNES ROM file (.nes) to read. The equivalent code for this game
                        will be searched for.

optional arguments:
  -h, --help            show this help message and exit
  -s SLICE_LENGTH, --slice-length SLICE_LENGTH
                        How many PRG ROM bytes to compare both before and after the relevant byte
                        (that is, total number of bytes compared is twice this value, plus one).
                        Fewer bytes will be compared if the relevant byte is too close to start or
                        end of PRG ROM. 1 to 20, default=4. Decrease to get more results.
  -d MAX_DIFFERENT_BYTES, --max-different-bytes MAX_DIFFERENT_BYTES
                        Maximum number of non-matching bytes allowed in each pair of PRG ROM
                        slices to compare. (The relevant byte must always match.) Minimum=0,
                        default=1, maximum=twice --slice-length, minus one. Increase to get more
                        results.
  -v, --verbose         Print more information. Note: all printed numbers are hexadecimal.
```

## nes.asm
NES assembly routines for [asm6f](https://github.com/freem/asm6f). Used by many of my projects.
