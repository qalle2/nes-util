# nes-gg

Encodes and decodes codes for the [Nintendo Entertainment System](http://en.wikipedia.org/wiki/Nintendo_Entertainment_System) (NES) cheat cartridge [Game Genie](http://en.wikipedia.org/wiki/Game_Genie).

Developed with Python 3 under 64-bit Windows.

## Resources used

* [*NES Game Genie Code Format DOC v0.71 by Benzene of Digital Emutations*](http://nesdev.com/nesgg.txt)

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
