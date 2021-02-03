"""Convert an NES PRG ROM address into possible CPU addresses."""

import os
import sys
import qneslib  # qalle's NES library, https://github.com/qalle2/nes-util

def main():
    """The main function."""

    # read args
    if len(sys.argv) != 3:
        sys.exit(
            "Convert an NES PRG ROM address into possible CPU addresses using the iNES ROM file "
            "(.nes). Args: file address_in_hexadecimal"
        )
    (file, prgAddr) = (sys.argv[1], sys.argv[2])  # pylint complains about [1:]

    if not os.path.isfile(file):
        sys.exit("File not found.")

    try:
        with open(file, "rb") as handle:
            fileInfo = qneslib.ines_header_decode(handle)
            if fileInfo is None:
                sys.exit("Invalid iNES ROM file.")
    except OSError:
        sys.exit("Error reading the file.")

    # parse & validate address
    try:
        prgAddr = int(prgAddr, 16)
        if not 0 <= prgAddr < fileInfo["prgSize"]:
            raise ValueError
    except ValueError:
        sys.exit("Invalid PRG address.")

    prgBankSize = qneslib.min_prg_bank_size(fileInfo["prgSize"], fileInfo["mapper"])
    cpuAddresses = qneslib.prg_address_to_cpu_addresses(prgAddr, prgBankSize)
    print("Possible CPU addresses:", ", ".join(f"0x{addr:04x}" for addr in sorted(cpuAddresses)))

if __name__ == "__main__":
    main()

