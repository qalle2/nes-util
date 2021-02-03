"""Find the PRG ROM addresses affected by an NES Game Genie code."""

import os
import sys
import qneslib  # qalle's NES library, https://github.com/qalle2/nes-util

def main():
    """The main function."""

    # read args
    if len(sys.argv) != 3:
        sys.exit(
            "Find the PRG ROM addresses affected by an NES Game Genie code in an iNES ROM file "
            "(.nes). Args: file code"
        )
    (file, code) = (sys.argv[1], sys.argv[2])  # pylint complains about [1:]

    if not os.path.isfile(file):
        sys.exit("File not found.")

    # decode the code
    values = qneslib.game_genie_decode(code)
    if values is None:
        sys.exit("Invalid NES Game Genie code.")
    (cpuAddr, compareValue) = (values[0], values[2])

    try:
        with open(file, "rb") as handle:
            if qneslib.ines_header_decode(handle) is None:
                sys.exit("Invalid iNES ROM file.")

            # get PRG addresses
            print(", ".join(
                f"0x{PRGAddr:04x}" for PRGAddr
                in qneslib.cpu_address_to_prg_addresses(handle, cpuAddr, compareValue)
            ))
    except OSError:
        sys.exit("Error reading the file.")

if __name__ == "__main__":
    main()
