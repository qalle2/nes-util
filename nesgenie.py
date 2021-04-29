import sys
import qneslib  # qalle's NES library, https://github.com/qalle2/nes-util

if len(sys.argv) == 2:
    # decode Game Genie code
    values = qneslib.game_genie_decode(sys.argv[1])
    if values is None:
        sys.exit("Invalid Game Genie code.")
    # reencode to get canonical form
    code = qneslib.game_genie_encode(*values)
elif 3 <= len(sys.argv) <= 4:
    # encode Game Genie code
    try:
        values = [int(n, 16) for n in sys.argv[1:]]
    except ValueError:
        sys.exit("Invalid hexadecimal integers.")
    code = qneslib.game_genie_encode(*values)
    if code is None:
        sys.exit("Hexadecimal integers out of range.")
    # redecode to get canonical form
    values = qneslib.game_genie_decode(code)
else:
    sys.exit(
        "Encode and decode NES Game Genie codes. Argument: six-letter code, eight-letter "
        "code, AAAA RR or AAAA RR CC (AAAA = address in hexadecimal, RR = replacement value "
        "in hexadecimal, CC = compare value in hexadecimal)."
    )

comp = "none" if values[2] is None else f"0x{values[2]:02x}"
print(
    f"{code}: CPU address = 0x{values[0]:04x}, replace value = 0x{values[1]:02x}, "
    f"compare value = {comp}"
)
