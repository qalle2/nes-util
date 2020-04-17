# nes-util
Various utilities related to the [Nintendo Entertainment System](http://en.wikipedia.org/wiki/Nintendo_Entertainment_System).

Note: you need ineslib.py and nesgenielib.py to run most of the other programs.

## ineslib.py
```
NAME
    ineslib

DESCRIPTION
    A library for parsing/encoding iNES ROM files (.nes).
    See http://wiki.nesdev.com/w/index.php/INES

CLASSES
    builtins.Exception(builtins.BaseException)
        iNESError

FUNCTIONS
    create_iNES_header(PRGSize, CHRSize, mapper=0, mirroring='h', saveRAM=False)
        Return a 16-byte iNES header as bytes. On error, raise an exception with an error message.
        PRGSize: PRG ROM size (16 * 1024 to 4096 * 1024 and a multiple of 16 * 1024)
        CHRSize: CHR ROM size (0 to 2040 * 1024 and a multiple of 8 * 1024)
        mapper: mapper number (0-255)
        mirroring: name table mirroring ('h'=horizontal, 'v'=vertical, 'f'=four-screen)
        saveRAM: does the game have save RAM

    get_smallest_PRG_bank_size(mapper)
        Get the smallest PRG ROM bank size the mapper supports (8 KiB for unknown mappers).
        mapper: iNES mapper number (0-255)
        return: bank size in bytes (8/16/32 KiB)

    parse_iNES_header(handle)
        Parse an iNES header. Return a dict. On error, raise an exception with an error message.
```

## nesgenielib.py
```
NAME
    nesgenielib

DESCRIPTION
    A library for decoding and encoding NES Game Genie codes.
    See http://nesdev.com/nesgg.txt

FUNCTIONS
    decode_code(code)
        Decode a Game Genie code.
        code: 6 or 8 letters from GENIE_LETTERS, case insensitive
        Return:
            if code is 6 letters: a tuple of ints: (address, replacement_value)
            if code is 8 letters: a tuple of ints: (address, replacement_value, compare_value)
            if code is invalid: None

    encode_code(address, replacement, compare=None)
        Encode a Game Genie code.
        address: NES CPU address (0x8000-0xffff or equivalently 0x0000-0x7fff)
        replacement: replacement value (0x00-0xff)
        compare: compare value (int, 0x00-0xff) or None
        return:
            if compare is None: a 6-letter code (str)
            if compare is not None: an 8-letter code (str)
            if the arguments are invalid: None

    is_valid_code(code)
        Validate a Game Genie code case-insensitively. Return True if valid, False if invalid.

    parse_values(input_)
        Parse a hexadecimal representation of the numbers regarding a Game Genie code.
        input_: must match 'aaaa:rr' or 'aaaa?cc:rr', where:
            aaaa = NES CPU address in hexadecimal
            rr = replacement value in hexadecimal
            cc = compare value in hexadecimal
        Return:
            if input_ matches 'aaaa:rr': (address, replacement_value)
            if input_ matches 'aaaa?cc:rr': (address, replacement_value, compare_value)
            if input_ matches neither: None

    random_code()
        Create a random 6-letter Game Genie code.

    stringify_values(address, replacement, compare=None)
        Convert the numbers regarding a Game Genie code into a hexadecimal representation.
        address: NES CPU address (0x8000-0xffff)
        replacement: replacement value (0x00-0xff)
        compare: compare value (0x00-0xff) or None
        Return:
            if compare is None: 'aaaa:rr'
            if compare is not None: 'aaaa?cc:rr'

DATA
    GENIE_LETTERS = 'APZLGITYEOXUKSVN'
```

The structure of NES Game Genie codes:
* The codes consist of the following 16 letters: `A P Z L G I T Y E O X U K S V N`
* The codes are six or eight letters long (e.g. `SXIOPO`, `YEUZUGAA`).
* In canonical codes, the third letter reflects the length of the code:
  * In six-letter codes, the letter is one of `A P Z L G I T Y`
  * In eight-letter codes, the letter is one of `E O X U K S V N`
* The Game Genie and my programs accept non-canonical codes too.
* All codes encode a 15-bit address (NES CPU ROM `0x8000-0xffff`) and a "replacement value" (`0x00-0xff`).
* Eight-letter codes also contain a "compare value" (`0x00-0xff`).

## ines_combine.py
```
usage: ines_combine.py [-h] -p PRG_ROM [-c CHR_ROM] [-m MAPPER] [-n {h,v,f}] [-s] outputFile

Create an iNES ROM file (.nes) from PRG ROM and CHR ROM data files.

positional arguments:
  outputFile            The iNES ROM file (.nes) to write.

optional arguments:
  -h, --help            show this help message and exit
  -p PRG_ROM, --prg-rom PRG_ROM
                        PRG ROM data file; required; the size must be 16-4096 KiB and a multiple of 16 KiB. (default:
                        None)
  -c CHR_ROM, --chr-rom CHR_ROM
                        CHR ROM data file; the size must be 0-2040 KiB and a multiple of 8 KiB. If the file is empty
                        or the argument is omitted, the game uses CHR RAM. (default: None)
  -m MAPPER, --mapper MAPPER
                        Mapper number (0-255). (default: 0)
  -n {h,v,f}, --mirroring {h,v,f}
                        Type of name table mirroring: h=horizontal, v=vertical, f=four-screen. (default: h)
  -s, --save-ram        The game contains battery-backed PRG RAM at $6000-$7fff. (default: False)
```

## ines_info.py
Print information of an iNES ROM file (.nes) in CSV format. Argument: file. Output fields: file, size, PRG ROM size, CHR ROM size, mapper, name table mirroring, does the game have save RAM, trainer size, file MD5 hash, PRG ROM MD5 hash, CHR ROM MD5 hash.

## ines_split.py
```
usage: ines_split.py [-h] [-p PRG] [-c CHR] input_file

Extract PRG ROM and/or CHR ROM data from an iNES ROM file (.nes).

positional arguments:
  input_file         The iNES ROM file (.nes) to read.

optional arguments:
  -h, --help         show this help message and exit
  -p PRG, --prg PRG  The file to extract PRG ROM data to (16-4096 KiB).
  -c CHR, --chr CHR  The file to extract CHR ROM data to (8-2040 KiB).

Specify at least one output file.
```

## nes_chr_decode.py
Requires the [Pillow](https://python-pillow.org) module.
```
usage: nes_chr_decode.py [-h] [-p PALETTE PALETTE PALETTE PALETTE] input_file output_file

Convert NES CHR (graphics) data into a PNG file.

positional arguments:
  input_file            The file to read. Either a raw NES CHR data file (the size must be a multiple of 256 bytes) or
                        an iNES ROM file (.nes) to read CHR ROM data from.
  output_file           The PNG image file to write. Its width will be 128 pixels, height a multiple of 8 pixels. It
                        will have 1-4 unique colors.

optional arguments:
  -h, --help            show this help message and exit
  -p PALETTE PALETTE PALETTE PALETTE, --palette PALETTE PALETTE PALETTE PALETTE
                        Output palette (which colors correspond to CHR colors 0-3). Four 6-digit hexadecimal RRGGBB
                        color codes ("000000"-"ffffff") separated by spaces. (default: ('000000', '555555', 'aaaaaa',
                        'ffffff'))
```

## nes_chr_encode.py
Requires the [Pillow](https://python-pillow.org) module.
```
usage: nes_chr_encode.py [-h] [-p PALETTE PALETTE PALETTE PALETTE] input_file output_file

Convert a PNG image into an NES CHR (graphics) data file.

positional arguments:
  input_file            The image file to read (e.g. PNG). The width must be 128 pixels. The height must be a multiple
                        of 8 pixels. There must be four unique colors or less. --palette must contain all the colors
                        in the image, but the image need not contain all the colors in --palette.
  output_file           The NES CHR data file to write. The size will be a multiple of 256 bytes.

optional arguments:
  -h, --help            show this help message and exit
  -p PALETTE PALETTE PALETTE PALETTE, --palette PALETTE PALETTE PALETTE PALETTE
                        PNG palette (which colors correspond to CHR colors 0-3). Four 6-digit hexadecimal RRGGBB color
                        codes ("000000"-"ffffff") separated by spaces. Must be all distinct. (default: ('000000',
                        '555555', 'aaaaaa', 'ffffff'))
```

## nes_color_swap.py
```
usage: nes_color_swap.py [-h] [-l {0,1,2,3} {0,1,2,3} {0,1,2,3} {0,1,2,3}] [-f FIRST_TILE] [-c TILE_COUNT]
                         input_file output_file

Swap colors in the graphics data (CHR ROM) of an iNES ROM file (.nes).

positional arguments:
  input_file            The iNES ROM file (.nes) to read.
  output_file           The iNES ROM file (.nes) to write.

optional arguments:
  -h, --help            show this help message and exit
  -l {0,1,2,3} {0,1,2,3} {0,1,2,3} {0,1,2,3}, --colors {0,1,2,3} {0,1,2,3} {0,1,2,3} {0,1,2,3}
                        Change original colors 0-3 to these colors. (default: (0, 2, 3, 1))
  -f FIRST_TILE, --first-tile FIRST_TILE
                        The first tile to change (0 or greater). (default: 0)
  -c TILE_COUNT, --tile-count TILE_COUNT
                        The number of tiles to change (0 = all starting from --first-tile). (default: 0)
```

## nesgenie.py
Encode and decode NES Game Genie codes. Argument: six-letter code, eight-letter code, aaaa:rr or aaaa?cc:rr (aaaa = address in hexadecimal, rr = replacement value in hexadecimal, cc = compare value in hexadecimal).

## nesgenie_6to8.py
Convert a 6-letter NES Game Genie code into 8 letters using the iNES ROM file (.nes). Args: file code

## nesgenie_prgaddr.py
Find the PRG ROM addresses affected by an NES Game Genie code in an iNES ROM file (.nes). Args: file code

## nesgenie_verconv.py
```
usage: nesgenie_verconv.py [-h] [-s SLICE_LENGTH] [-d MAX_DIFFERENT_BYTES] [-v] code file1 file2

Read two versions (e.g. Japanese and US) of the same NES game in iNES format (.nes) and a Game Genie code for one of
the versions. Output the equivalent code for the other version of the game.

positional arguments:
  code                  An eight-letter NES Game Genie code that is known to work with file1.
  file1                 An iNES ROM file (.nes) to read. The game your code is known to work with.
  file2                 Another iNES ROM file (.nes) to read. The equivalent code for this game will be searched for.

optional arguments:
  -h, --help            show this help message and exit
  -s SLICE_LENGTH, --slice-length SLICE_LENGTH
                        Length of PRG ROM slices to compare. (Each slice will be equally distributed before and after
                        its relevant byte if possible.) Minimum=1, default=9. Decrease to get more results.
  -d MAX_DIFFERENT_BYTES, --max-different-bytes MAX_DIFFERENT_BYTES
                        Maximum number of non-matching bytes allowed in each pair of PRG ROM slices to compare. (The
                        relevant byte, usually in the middle of the slice, must always match.) Minimum=0, default=1.
                        Increase to get more results.
  -v, --verbose         Print technical information.
```
