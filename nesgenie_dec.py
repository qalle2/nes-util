import sys

def decode_code(code):
    # decode an NES Game Genie code
    # see https://www.nesdev.org/nesgg.txt

    if len(code) not in (6, 8):
        return None
    # convert letters into integers (0x0-0xf)
    try:
        code = ["APZLGITYEOXUKSVN".index(l) for l in code.upper()]
    except ValueError:
        return None
    # 24/32 bits (16 for address, 8 for replacement, 0 or 8 for compare)
    bigint = 0
    for loPos in (3, 5, 2, 4, 1, 0, 7, 6)[:len(code)]:
        hiPos = (loPos - 1) % len(code)
        bigint = (bigint << 4) | (code[hiPos] & 8) | (code[loPos] & 7)
    # split integer and set MSB of address
    (bigint, comp) \
    = (bigint, None) if len(code) == 6 else (bigint >> 8, bigint & 0xff)
    (addr, repl) = (bigint >> 8, bigint & 0xff)
    return (addr | 0x8000, repl, comp)

def main():
    if len(sys.argv) != 2:
        sys.exit(
            "Decode an NES Game Genie code. Argument: code (6 or 8 letters "
            "from AEGIKLNOPSTUVXYZ)."
        )

    code = sys.argv[1]
    values = decode_code(code)
    if values is None:
        sys.exit("Invalid Game Genie code.")

    comp = "none" if values[2] is None else f"0x{values[2]:02x}"
    print(
        f"CPU address = 0x{values[0]:04x}, "
        f"replace value = 0x{values[1]:02x}, "
        f"compare value = {comp}"
    )

main()
