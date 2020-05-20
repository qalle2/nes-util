"""Convert an NES Game Genie code from one version of a game to another using both iNES ROM files
(.nes)."""

import argparse
import os
import sys
import ineslib
import nesgenielib

# --- Argument parsing -----------------------------------------------------------------------------

def parse_arguments():
    """Parse command line arguments using argparse."""

    parser = argparse.ArgumentParser(
        description="Read two versions (e.g. Japanese and US) of the same NES game in iNES format "
        "(.nes) and a Game Genie code for one of the versions. Output the equivalent code for the "
        "other version of the game. Technical explanation: decode the code; find out PRG ROM "
        "addresses affected in file1; see what's in and around them; look for similar bytestrings "
        "in file2's PRG ROM; convert the addresses back into CPU addresses; encode them into codes."
    )

    parser.add_argument(
        "-b", "--slice-length-before", type=int, default=4,
        help="Length of PRG ROM slice to compare before the relevant byte. (Fewer bytes will be "
        "compared if the relevant byte is too close to the start of the PRG ROM.) 0 to 20, "
        "default=4. Decrease to get more results."
    )
    parser.add_argument(
        "-a", "--slice-length-after", type=int, default=4,
        help="Length of PRG ROM slice to compare after the relevant byte. (Fewer bytes will be "
        "compared if the relevant byte is too close to the end of the PRG ROM.) 0 to 20, "
        "default=4. Decrease to get more results."
    )
    parser.add_argument(
        "-d", "--max-different-bytes", type=int, default=1,
        help="Maximum number of non-matching bytes allowed in each pair of PRG ROM slices to "
        "compare. (The relevant byte must always match.) Minimum=0, default=1, maximum=sum of "
        "--slice-length-before and --slice-length-after, minus one. Increase to get more results."
    )
    parser.add_argument(
        "code",
        help="An NES Game Genie code that is known to work with file1. Six-letter codes are not "
        "allowed if file1 uses PRG ROM bankswitching."
    )
    parser.add_argument(
        "file1", help="An iNES ROM file (.nes) to read. The game your code is known to work with."
    )
    parser.add_argument(
        "file2",
        help="Another iNES ROM file (.nes) to read. The equivalent code for this game will be "
        "searched for."
    )

    args = parser.parse_args()

    if not 0 <= args.slice_length_before <= 20:
        sys.exit("Invalid value for --slice_length_before.")
    if not 0 <= args.slice_length_after <= 20:
        sys.exit("Invalid value for --slice_length_after.")
    if not 0 <= args.max_different_bytes < args.slice_length_before + args.slice_length_after:
        sys.exit("Invalid value for --max-different-bytes.")
    if nesgenielib.decode_code(args.code) is None:
        sys.exit("Invalid Game Genie code.")
    if not os.path.isfile(args.file1):
        sys.exit("file1 not found.")
    if not os.path.isfile(args.file2):
        sys.exit("file2 not found.")

    return args

# --- used with both input files -------------------------------------------------------------------

def validate_iNES_header(handle, filename):
    """Validate an iNES header."""

    try:
        ineslib.parse_iNES_header(handle)
    except ineslib.iNESError as error:
        sys.exit(f"Error in {filename:s}: {error!s}")

def read_PRG_data(handle, PRGAddress=0, length=None):
    """Read bytes from PRG ROM. (Default length: maximum.)"""

    fileInfo = ineslib.parse_iNES_header(handle)
    handle.seek(16 + fileInfo["trainerSize"] + PRGAddress)
    return handle.read(fileInfo["PRGSize"] - PRGAddress if length is None else length)

def is_PRG_bankswitched(handle):
    """Is the PRG ROM of the game bankswitched? (May give false positives.)"""

    fileInfo = ineslib.parse_iNES_header(handle)
    return fileInfo["PRGSize"] > ineslib.get_smallest_PRG_bank_size(fileInfo["mapper"])

def get_PRG_bank_size(handle):
    """Get the PRG ROM bank size of the game. (The result may be too small.)"""

    fileInfo = ineslib.parse_iNES_header(handle)
    return min(ineslib.get_smallest_PRG_bank_size(fileInfo["mapper"]), fileInfo["PRGSize"])

# --- used with file1 and user's code --------------------------------------------------------------

def get_compare_value(code):
    """Get compare value from user's code."""

    decoded = nesgenielib.decode_code(code)
    return decoded[2] if len(decoded) == 3 else None

def print_decoded_code(code):
    """Print user's code in decoded form."""

    decoded = nesgenielib.decode_code(code)
    (addr, replaceValue) = (decoded[0], decoded[1])
    compareValue = get_compare_value(code)
    print("Your code decoded: address=0x{:04x}, replace=0x{:02x}, compare={:s}".format(
        addr, replaceValue, "none" if compareValue is None else f"0x{compareValue:02x}"
    ))

def get_banked_PRG_addresses(handle, CPUAddress, compareValue):
    """Generate PRG ROM addresses that match the CPU address and the compare value in the file.
    (The file may use PRG ROM bankswitching.)"""

    fileInfo = ineslib.parse_iNES_header(handle)
    PRGBankSize = get_PRG_bank_size(handle)
    print("PRG ROM bank size of file1: {:d} KiB".format(PRGBankSize // 1024))
    offset = CPUAddress & (PRGBankSize - 1)  # offset within each PRG bank

    # for each bank, if that offset matches the compare value, yield the PRG ROM address
    for PRGAddr in range(offset, fileInfo["PRGSize"], PRGBankSize):
        if read_PRG_data(handle, PRGAddr, 1)[0] == compareValue:
            yield PRGAddr

def get_PRG_addresses(handle, args):
    """Get PRG ROM addresses from file1."""

    decoded = nesgenielib.decode_code(args.code)
    codeAddr = decoded[0]
    codeCompareValue = decoded[2] if len(decoded) == 3 else None

    # get PRG addresses
    if codeCompareValue is None:
        # using a six-letter code
        if is_PRG_bankswitched(handle):
            sys.exit(
                "file1 seems to use PRG ROM bankswitching; this program does not support using "
                "six-letter codes with such files."
            )
        fileInfo = ineslib.parse_iNES_header(handle)
        return [codeAddr & (fileInfo["PRGSize"] - 1)]
    # using an eight-letter code
    return list(get_banked_PRG_addresses(handle, codeAddr, codeCompareValue))

def get_PRG_slices(handle, PRGAddresses, args):
    """Generate the slice surrounding each relevant PRG ROM address: (bytes_before, bytes_after)."""

    fileInfo = ineslib.parse_iNES_header(handle)

    for PRGAddr in PRGAddresses:
        # get actual length of slice before/after relevant byte
        lenBefore = min(args.slice_length_before, PRGAddr)
        lenAfter = min(args.slice_length_after, fileInfo["PRGSize"] - PRGAddr - 1)
        slice_ = read_PRG_data(handle, PRGAddr - lenBefore, lenBefore + 1 + lenAfter)
        yield (slice_[:lenBefore], slice_[lenBefore+1:])

def get_fake_compare_value(handle, code):
    """Get a fake compare value from file1 for user's six-letter code."""

    codeAddr = nesgenielib.decode_code(code)[0]
    fileInfo = ineslib.parse_iNES_header(handle)
    PRGAddr = codeAddr & (fileInfo["PRGSize"] - 1)
    return read_PRG_data(handle, PRGAddr, 1)[0]

def print_slices(slices, compareValue):
    """Print the slices we found from file1."""

    print("Unique bytestrings around those addresses in file1 (relevant byte in <brackets>):")
    for (before, after) in sorted(slices):
        print("    {:s} <0x{:02x}> {:s}".format(
            " ".join(f"0x{byte:02x}" for byte in before),
            compareValue,
            " ".join(f"0x{byte:02x}" for byte in after)
        ))

# --- used with file2 and codes to output ----------------------------------------------------------

def find_slices_in_PRG(handle, slices, compareValue, args):
    """Generate PRG addresses of each slice."""

    PRGData = read_PRG_data(handle)

    for (sliceBefore, sliceAfter) in slices:
        slice_ = sliceBefore + bytes((compareValue,)) + sliceAfter
        # PRG addresses of possible relevant bytes
        for PRGAddr in range(len(sliceBefore), len(PRGData) - len(sliceAfter)):
            # the relevant byte must always match
            if PRGData[PRGAddr] == compareValue:
                # if not too many different bytes around, yield PRG address of relevant byte
                PRGSlice = PRGData[PRGAddr-len(sliceBefore):PRGAddr+len(sliceAfter)+1]
                differentByteCnt = sum(
                    1 for (byte1, byte2) in zip(slice_, PRGSlice) if byte1 != byte2
                )
                if differentByteCnt <= args.max_different_bytes:
                    yield PRGAddr

def PRG_addresses_to_CPU_addresses(handle, PRGAddresses):
    """Generate CPU addresses (0x8000-0xffff) from PRG addresses."""

    PRGBankSize = get_PRG_bank_size(handle)
    print("PRG ROM bank size of file2: {:d} KiB".format(PRGBankSize // 1024))

    offsetMask = PRGBankSize - 1
    origins = range(0x8000, 0x10000, PRGBankSize)

    for PRGAddr in PRGAddresses:
        offset = PRGAddr & offsetMask
        for origin in origins:
            yield origin | offset

def print_results(CPUAddresses, originalCode, compareValue):
    """Print the codes we found."""

    if compareValue is None:
        print("Outputting six-letter codes because file2 doesn't bankswitch PRG ROM.")
    else:
        print("Outputting eight-letter codes because file2 bankswitches PRG ROM.")

    # get address and replace value from original code
    decoded = nesgenielib.decode_code(originalCode)
    (originalAddr, replaceValue) = (decoded[0], decoded[1])

    # sort addresses by difference from original address
    CPUAddresses.sort(key=lambda addr: abs(addr - originalAddr))

    # print codes with new addresses
    codes = (
        nesgenielib.encode_code(addr, replaceValue, compareValue) for addr in CPUAddresses
    )
    print("Possible Game Genie codes for file2 (try the first one first):", ", ".join(codes))

# --------------------------------------------------------------------------------------------------

def main():
    """The main function."""

    args = parse_arguments()
    compareValue = get_compare_value(args.code)  # needed throughout the program
    print_decoded_code(args.code)

    # read file1
    try:
        with open(args.file1, "rb") as handle:
            validate_iNES_header(handle, "file1")

            PRGAddresses = get_PRG_addresses(handle, args)
            if not PRGAddresses:
                sys.exit("Your code seems to affect file1 in no way.")
            print(
                "PRG ROM addresses affected in file1:",
                ", ".join(f"0x{addr:04x}" for addr in sorted(PRGAddresses))
            )

            slices = set(get_PRG_slices(handle, PRGAddresses, args))

            if compareValue is None:
                compareValue = get_fake_compare_value(handle, args.code)
    except OSError:
        sys.exit("Error reading file1.")

    print_slices(slices, compareValue)

    # read file2
    try:
        with open(args.file2, "rb") as handle:
            validate_iNES_header(handle, "file2")

            PRGAddresses = set(find_slices_in_PRG(handle, slices, compareValue, args))
            if not PRGAddresses:
                sys.exit("file2 contains nothing similar to what your code affects in file1.")
            print(
                "PRG ROM addresses in file2 matching some of the bytestrings above:",
                ", ".join(f"0x{addr:04x}" for addr in sorted(PRGAddresses))
            )

            CPUAddresses = sorted(PRG_addresses_to_CPU_addresses(handle, PRGAddresses))
            print(
                "Equivalent CPU addresses in file2:",
                ", ".join(f"0x{addr:04x}" for addr in CPUAddresses)
            )

            # if file2 not bankswitched, discard compare value to output six-letter codes
            compareValue = compareValue if is_PRG_bankswitched(handle) else None
    except OSError:
        sys.exit("Error reading file2.")

    print_results(CPUAddresses, args.code, compareValue)

if __name__ == "__main__":
    main()
