# nes-util
Various utilities related to the [Nintendo Entertainment System](http://en.wikipedia.org/wiki/Nintendo_Entertainment_System).

## ineslib.py
```
NAME
    ineslib - A library for parsing iNES ROM files (.nes).

FUNCTIONS
    parse_iNES_header(handle)
        Parse an iNES header. See http://wiki.nesdev.com/w/index.php/INES
        Return a dict. On error, raise an exception with an error message.
```

## nesgenielib.py
```
NAME
    nesgenielib - A library for decoding and encoding NES Game Genie codes.

FUNCTIONS
    decode_code(code)
        Decode a Game Genie code.
        If an eight-letter code, return (address, replacement_value, compare_value).
        If a six-letter code, return (address, replacement_value).
        If an invalid code, return None.

    encode_code(address, replacement, compare=None)
        Encode a Game Genie code.
        address: 16-bit int, replacement/compare: replacement value and compare value (8-bit ints)

    parse_values(input_)
        Parse 'aaaa:rr' or 'aaaa?cc:rr' where aaaa = address in hexadecimal, rr = replacement value
        in hexadecimal, cc = compare value in hexadecimal. Return the values as a tuple of integers,
        with the replacement value before the compare value, or None if the input matches neither.

    stringify_values(address, replacement, compare=None)
        Convert the address, replacement value and compare value into a hexadecimal representation
        ('aaaa:rr' or 'aaaa?cc:rr').
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

## ines_info.py
Print information of an iNES ROM file (.nes) in CSV format. Argument: file. Output fields: file, size, PRG ROM size, CHR ROM size, mapper, name table mirroring, does the game have save RAM, trainer size, file MD5 hash, PRG ROM MD5 hash, CHR ROM MD5 hash.

## nesgenie.py
Encode and decode NES Game Genie codes. Argument: six-letter code, eight-letter code, aaaa:rr or aaaa?cc:rr (aaaa = address in hexadecimal, rr = replacement value in hexadecimal, cc = compare value in hexadecimal).

## ines-split
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

## nesgenie_6to8.py
Convert a 6-letter NES Game Genie code into 8 letters using the iNES ROM file (.nes). Args: file code
