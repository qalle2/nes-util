# nes-gg

Encodes and decodes codes for the [Nintendo Entertainment System](http://en.wikipedia.org/wiki/Nintendo_Entertainment_System) (NES) cheat cartridge [Game Genie](http://en.wikipedia.org/wiki/Game_Genie).

Developed with Python 3 under 64-bit Windows.

## Resources used

* [*NES Game Genie Code Format DOC v0.71 by Benzene of Digital Emutations*](http://nesdev.com/nesgg.txt)

## Structure of codes

The codes consist of the following 16 letters (in alphabetical order):

`A E G I K L N O P S T U V X Y Z`

The codes are either six or eight letters long. Both of them encode a 15-bit address in NES CPU memory space (`0x8000`-`0xffff`) and an eight-bit "replace value" (`0x00`-`0xff`) to feed to the CPU when it attempts to read that address. In addition, eight-letter codes encode an eight-bit "compare value" (`0x00`-`0xff`); a value will only be "replaced" if its original value equals the compare value. (Due to bankswitching, multiple game cartridge ROM addresses may be mapped to the same NES CPU memory address at different times.)

In six-letter codes, the third letter should be one of `A G I L P T Y Z`. In eight-letter codes, it should be one of `E K N O S U V X`.

## Examples

### Decoding a six-letter code

#### Input
`python nes-gg.py SXIOPO`

#### Output
`SXIOPO = 91D9:AD`

### Decoding an eight-letter code

#### Input
`python nes-gg.py YEUZUGAA`

#### Output
`YEUZUGAA = ACB3?00:07`

### Encoding a six-letter code

#### Input
`python nes-gg.py 91D9:AD`

#### Output
`91D9:AD = SXIOPO`

### Encoding an eight-letter code

#### Input
`python nes-gg.py ACB3?00:07`

#### Output
`ACB3?00:07 = YEUZUGAA`
