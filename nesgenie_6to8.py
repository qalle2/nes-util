"""Converts a 6-letter NES Game Genie code into 8 letters using the iNES ROM file (.nes)."""

import sys
import ineslib
import nesgenielib

def get_compare_values(handle, PRGSize, PRGBankSize, address):
    """Get possible compare values from the PRG ROM. Yield one value per call."""

    # get offset within each bank by ignoring the most significant bits of the address
    offset = address & (PRGBankSize - 1)
    # for each bank, read the byte at that offset
    for PRGPos in range(offset, PRGSize, PRGBankSize):
        handle.seek(16 + PRGPos)
        yield handle.read(1)[0]

def main():
    """The main function."""

    # read args
    if len(sys.argv) != 3:
        sys.exit(
            "Convert a 6-letter NES Game Genie code into 8 letters using the iNES ROM file (.nes). "
            "Args: file code"
        )
    (file, code) = (sys.argv[1], sys.argv[2])  # pylint complains about [1:]

    # validate and decode the code
    decoded = nesgenielib.decode_code(code)
    if decoded is None or len(decoded) == 3:
        sys.exit("Invalid six-letter Game Genie code.")
    (address, replacement) = decoded

    try:
        with open(file, "rb") as handle:
            try:
                fileInfo = ineslib.parse_iNES_header(handle)
            except ineslib.iNESError as e:
                sys.exit("Error: " + str(e))
            PRGBankSize = ineslib.get_smallest_PRG_bank_size(fileInfo["mapper"])
            if PRGBankSize >= fileInfo["PRGSize"]:
                sys.exit("There is no reason to use eight-letter codes with this game.")

            compareValues = set(get_compare_values(
                handle, fileInfo["PRGSize"], PRGBankSize, address
            ))
    except OSError:
        sys.exit("Error reading the file.")

    # ignore a compare value that equals the replacement value
    compareValues.discard(replacement)

    if compareValues:
        print("Try each of these eight-letter codes instead of your six-letter code:")
        codes = (nesgenielib.encode_code(address, replacement, comp) for comp in compareValues)
        for code in sorted(codes):
            print(code)
    else:
        print("No eight-letter codes found.")

if __name__ == "__main__":
    main()
