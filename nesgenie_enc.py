import sys

def encode_code(addr, repl, comp=None):
    # encode an NES Game Genie code
    # see https://www.nesdev.org/nesgg.txt

    # create 24/32-bit int; clear/set MSB of address to get correct 3rd letter
    # later (one of APZLGITY for 6-letter codes, one of EOXUKSVN for 8-letter
    # codes)
    if comp is None:
        codeLen = 6
        addr &= 0x7fff
        bigint = (addr << 8) | repl
    else:
        codeLen = 8
        addr |= 0x8000
        bigint = (addr << 16) | (repl << 8) | comp
    # convert into 4-bit ints
    encoded = codeLen * [0]
    for loPos in (3, 5, 2, 4, 1, 0, 7, 6)[codeLen-1::-1]:
        hiPos = (loPos - 1) % codeLen
        encoded[loPos] |= bigint & 0b111
        encoded[hiPos] |= bigint & 0b1000
        bigint >>= 4
    # convert into letters
    return "".join("APZLGITYEOXUKSVN"[i] for i in encoded)

def main():
    if not 3 <= len(sys.argv) <= 4:
        sys.exit(
            "Encode an NES Game Genie code. Arguments: AAAA RR or AAAA RR CC "
            "(AAAA = address, RR = replacement value, CC = compare value; "
            "all in hexadecimal)."
        )

    try:
        values = [int(n, 16) for n in sys.argv[1:]]
    except ValueError:
        sys.exit("Arguments must be hexadecimal integers.")
    if not 0 <= values[0] <= 0xffff \
    or not 0 <= values[1] <= 0xff \
    or len(values) == 3 and not 0 <= values[2] <= 0xff:
        sys.exit("Arguments out of range.")

    print(encode_code(*values))

main()
