"""Convert an NES PRG ROM address into possible CPU addresses."""

import os
import sys
import ineslib
import neslib

def main():
    """The main function."""

    # read args
    if len(sys.argv) != 3:
        sys.exit(
            "Convert an NES PRG ROM address into possible CPU addresses using the iNES ROM file "
            "(.nes). Args: file address_in_hexadecimal"
        )
    (file, PRGAddr) = (sys.argv[1], sys.argv[2])  # pylint complains about [1:]

    if not os.path.isfile(file):
        sys.exit("File not found.")

    try:
        with open(file, "rb") as handle:
            # parse iNES header
            try:
                fileInfo = ineslib.parse_iNES_header(handle)
            except ineslib.iNESError as error:
                sys.exit("Error: " + str(error))
    except OSError:
        sys.exit("Error reading the file.")

    # parse & validate address
    try:
        PRGAddr = int(PRGAddr, 16)
        if not 0 <= PRGAddr < fileInfo["PRGSize"]:
            raise ValueError
    except ValueError:
        sys.exit("Invalid PRG address.")

    CPUAddresses = neslib.PRG_address_to_CPU_addresses(fileInfo, PRGAddr)
    print("Possible CPU addresses:", " ".join(f"0x{addr:04x}" for addr in sorted(CPUAddresses)))

if __name__ == "__main__":
    main()
