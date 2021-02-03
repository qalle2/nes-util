"""Convert an NES Game Genie code from one version of a game to another using both iNES ROM files
(.nes)."""

import argparse
import os
import sys
import qneslib  # qalle's NES library, https://github.com/qalle2/nes-util

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
    if qneslib.game_genie_decode(args.code) is None:
        sys.exit("Invalid Game Genie code.")
    if not os.path.isfile(args.file1):
        sys.exit("file1 not found.")
    if not os.path.isfile(args.file2):
        sys.exit("file2 not found.")

    return args

# --- used with file1 and user's code --------------------------------------------------------------

def print_decoded_code(code):
    """Print user's code in decoded form."""

    (addr, replaceValue, compareValue) = qneslib.game_genie_decode(code)
    print(
        "Your code decoded: CPU address = 0x{:04x}, replace value = 0x{:02x}, compare value = {:s}"
        .format(addr, replaceValue, "none" if compareValue is None else f"0x{compareValue:02x}")
    )

def get_prg_addresses(handle, args):
    """Get PRG ROM addresses from file1."""

    decoded = qneslib.game_genie_decode(args.code)
    (codeAddr, codeCompareValue) = (decoded[0], decoded[2])

    if codeCompareValue is None and qneslib.is_prg_bankswitched(qneslib.ines_header_decode(handle)):
        sys.exit("Six-letter codes cannot be used because file1 uses PRG bankswitching.")

    return list(qneslib.cpu_address_to_prg_addresses(handle, codeAddr, codeCompareValue))

def get_prg_slices(handle, prgAddresses, args):
    """Generate the slice surrounding each relevant PRG ROM address: (bytes_before, bytes_after)."""

    fileInfo = qneslib.ines_header_decode(handle)

    for prgAddr in prgAddresses:
        # get actual length of slice before/after relevant byte
        lenBefore = min(args.slice_length_before, prgAddr)
        lenAfter = min(args.slice_length_after, fileInfo["prgSize"] - prgAddr - 1)

        handle.seek(fileInfo["prgStart"] + prgAddr - lenBefore)
        slice_ = handle.read(lenBefore + 1 + lenAfter)

        yield (slice_[:lenBefore], slice_[lenBefore+1:])

def get_fake_compare_value(handle, code):
    """Get a fake compare value from file1 for user's six-letter code."""

    codeAddr = qneslib.game_genie_decode(code)[0]
    fileInfo = qneslib.ines_header_decode(handle)
    prgAddr = codeAddr & (fileInfo["prgSize"] - 1)
    handle.seek(fileInfo["prgStart"] + prgAddr)
    return handle.read(1)[0]

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

def find_slices_in_prg(handle, slices, compareValue, args):
    """Generate PRG addresses of each slice."""

    # read all PRG data
    fileInfo = qneslib.ines_header_decode(handle)
    handle.seek(fileInfo["prgStart"])
    prgData = handle.read(fileInfo["prgSize"])

    for (sliceBefore, sliceAfter) in slices:
        slice_ = sliceBefore + bytes((compareValue,)) + sliceAfter
        # PRG addresses of possible relevant bytes
        for prgAddr in range(len(sliceBefore), len(prgData) - len(sliceAfter)):
            # the relevant byte must always match
            if prgData[prgAddr] == compareValue:
                # if not too many different bytes around, yield PRG address of relevant byte
                prgSlice = prgData[prgAddr-len(sliceBefore):prgAddr+len(sliceAfter)+1]
                differentByteCnt = sum(
                    1 for (byte1, byte2) in zip(slice_, prgSlice) if byte1 != byte2
                )
                if differentByteCnt <= args.max_different_bytes:
                    yield prgAddr

def print_results(cpuAddresses, originalCode, compareValue):
    """Print the codes we found."""

    # get address and replace value from original code
    decoded = qneslib.game_genie_decode(originalCode)
    (originalAddr, replaceValue) = (decoded[0], decoded[1])

    # sort addresses by difference from original address
    cpuAddresses = sorted(cpuAddresses)
    cpuAddresses.sort(key=lambda addr: abs(addr - originalAddr))

    # print codes with new addresses
    codes = (
        qneslib.game_genie_encode(addr, replaceValue, compareValue) for addr in cpuAddresses
    )
    print("Possible Game Genie codes for file2 (try the first one first):", ", ".join(codes))

# --------------------------------------------------------------------------------------------------

def main():
    """The main function."""

    args = parse_arguments()
    compareValue = qneslib.game_genie_decode(args.code)[2]  # needed throughout the program
    print_decoded_code(args.code)

    # read file1
    try:
        with open(args.file1, "rb") as handle:
            if qneslib.ines_header_decode(handle) is None:
                sys.exit("file1 is not a valid iNES ROM file.")

            prgAddresses = get_prg_addresses(handle, args)
            if not prgAddresses:
                sys.exit("Your code seems to affect file1 in no way.")
            print(
                "PRG ROM addresses affected in file1:",
                ", ".join(f"0x{addr:04x}" for addr in sorted(prgAddresses))
            )

            slices = set(get_prg_slices(handle, prgAddresses, args))

            if compareValue is None:
                compareValue = get_fake_compare_value(handle, args.code)
    except OSError:
        sys.exit("Error reading file1.")

    print_slices(slices, compareValue)

    # read file2
    try:
        with open(args.file2, "rb") as handle:
            fileInfo = qneslib.ines_header_decode(handle)
            if fileInfo is None:
                sys.exit("file2 is not a valid iNES ROM file.")

            prgAddresses = set(find_slices_in_prg(handle, slices, compareValue, args))
            if not prgAddresses:
                sys.exit("file2 contains nothing similar to what your code affects in file1.")
            print(
                "PRG ROM addresses in file2 matching some of the bytestrings above:",
                ", ".join(f"0x{addr:04x}" for addr in sorted(prgAddresses))
            )

            cpuAddresses = set()
            for prgAddr in prgAddresses:
                cpuAddresses.update(qneslib.prg_address_to_cpu_addresses(fileInfo, prgAddr))

            print(
                "Equivalent CPU addresses in file2:",
                ", ".join(f"0x{addr:04x}" for addr in sorted(cpuAddresses))
            )

            # if file2 not bankswitched, discard compare value to output six-letter codes
            if not qneslib.is_prg_bankswitched(qneslib.ines_header_decode(handle)):
                compareValue = None
    except OSError:
        sys.exit("Error reading file2.")

    print_results(cpuAddresses, args.code, compareValue)

if __name__ == "__main__":
    main()
