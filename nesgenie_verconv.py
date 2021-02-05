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
        "in file2's PRG ROM; convert the addresses back into CPU addresses; encode them into "
        "codes."
    )

    parser.add_argument(
        "-s", "--slice-length", type=int, default=4,
        help="How many PRG ROM bytes to compare both before and after the relevant byte (that is, "
        "total number of bytes compared is twice this value, plus one). Fewer bytes will be "
        "compared if the relevant byte is too close to start or end of PRG ROM.) 1 to 20, "
        "default=4. Decrease to get more results."
    )
    parser.add_argument(
        "-d", "--max-different-bytes", type=int, default=1,
        help="Maximum number of non-matching bytes allowed in each pair of PRG ROM slices to "
        "compare. (The relevant byte must always match.) Minimum=0, default=1, maximum=twice "
        "--slice-length, minus one. Increase to get more results."
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Print more information. Note: all printed numbers are hexadecimal."
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

    if not 1 <= args.slice_length <= 20:
        sys.exit("Invalid value for --slice-length.")
    if not 0 <= args.max_different_bytes < 2 * args.slice_length:
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
    (addr, repl, comp) = qneslib.game_genie_decode(code)
    comp = "none" if comp is None else f"{comp:02x}"
    print(f"Code: CPU address={addr:04x}, replace value={repl:02x}, compare value={comp}")

def get_prg_addresses(handle, code):
    """Get PRG ROM addresses affected by code in file1."""

    (cpuAddr, repl, comp) = qneslib.game_genie_decode(code)
    fileInfo = qneslib.ines_header_decode(handle)

    if comp is None and qneslib.is_prg_bankswitched(fileInfo["prgSize"], fileInfo["mapper"]):
        sys.exit("Six-letter codes not supported because file1 uses PRG ROM bankswitching.")

    return set(qneslib.cpu_address_to_prg_addresses(handle, cpuAddr, comp))

def get_prg_slices(handle, prgAddresses, sliceLen):
    """Generate slices surrounding each PRG ROM address: (bytes_before, bytes_after)."""

    fileInfo = qneslib.ines_header_decode(handle)

    for prgAddr in prgAddresses:
        # get actual length of slice before/after relevant byte
        lenBefore = min(sliceLen, prgAddr)
        lenAfter  = min(sliceLen, fileInfo["prgSize"] - prgAddr - 1)

        handle.seek(fileInfo["prgStart"] + prgAddr - lenBefore)
        slice_ = handle.read(lenBefore + 1 + lenAfter)

        # don't use [-lenAfter:] as lenAfter may be zero
        yield (slice_[:lenBefore], slice_[lenBefore+1:])

def get_fake_compare_value(handle, code):
    """Get a fake compare value from file1 for user's six-letter code."""

    cpuAddr  = qneslib.game_genie_decode(code)[0]
    fileInfo = qneslib.ines_header_decode(handle)
    prgAddr  = cpuAddr & (fileInfo["prgSize"] - 1)
    handle.seek(fileInfo["prgStart"] + prgAddr)
    return handle.read(1)[0]

def print_slices(slices, compareValue):
    """Print slices found in file1."""

    print("Bytestrings around those addresses in file1 (relevant byte in <brackets>):")
    for (before, after) in sorted(slices):
        before = " ".join(f"{byte:02x}" for byte in before)
        after  = " ".join(f"{byte:02x}" for byte in after)
        print(f"    {before} <{compareValue:02x}> {after}")

# --- used with file2 and codes to output ----------------------------------------------------------

def find_slices_in_prg(handle, slices, comp, args):
    """Generate PRG addresses of each slice. comp = compare value"""

    # read all PRG data
    fileInfo = qneslib.ines_header_decode(handle)
    handle.seek(fileInfo["prgStart"])
    prgData = handle.read(fileInfo["prgSize"])

    for (sliceBefore, sliceAfter) in slices:
        slice_ = sliceBefore + bytes((comp,)) + sliceAfter
        # PRG addresses of possible relevant bytes
        for prgAddr in range(len(sliceBefore), len(prgData) - len(sliceAfter)):
            # the relevant byte must always match
            if prgData[prgAddr] == comp:
                # if not too many different bytes around, yield PRG address of relevant byte
                prgSlice = prgData[prgAddr-len(sliceBefore):prgAddr+len(sliceAfter)+1]
                differentByteCnt = sum(
                    1 for (byte1, byte2) in zip(slice_, prgSlice) if byte1 != byte2
                )
                if differentByteCnt <= args.max_different_bytes:
                    yield prgAddr

def print_results(cpuAddresses, code, comp):
    """Print the codes we found.
    code: original code, comp: compare value (may be the fake one we created)"""

    # get address and replace value from original code
    (origCpuAddr, repl) = qneslib.game_genie_decode(code)[0:2]

    # sort addresses by difference from original address
    cpuAddresses = sorted(cpuAddresses)
    cpuAddresses.sort(key=lambda addr: abs(addr - origCpuAddr))

    # print codes with new addresses
    print("Game Genie codes for file2 (try the first one first):", ", ".join(
        qneslib.game_genie_encode(addr, repl, comp) for addr in cpuAddresses
    ))

# --------------------------------------------------------------------------------------------------

def main():
    args = parse_arguments()

    if args.verbose:
        print_decoded_code(args.code)

    # needed throughout the program; if None, replaced with a fake value later
    compareValue = qneslib.game_genie_decode(args.code)[2]

    # read file1
    try:
        with open(args.file1, "rb") as handle:
            fileInfo = qneslib.ines_header_decode(handle)
            if fileInfo is None:
                sys.exit("file1 is not a valid iNES ROM file.")

            prgAddresses = get_prg_addresses(handle, args.code)
            if not prgAddresses:
                sys.exit("Your code seems to affect file1 in no way.")
            if args.verbose:
                print(
                    "PRG addresses affected in file1:",
                    ", ".join(f"{addr:04x}" for addr in sorted(prgAddresses))
                )

            slices = set(get_prg_slices(handle, prgAddresses, args.slice_length))

            if compareValue is None:
                compareValue = get_fake_compare_value(handle, args.code)
    except OSError:
        sys.exit("Error reading file1.")

    if args.verbose:
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

            cpuAddresses = set()
            prgBankSize = qneslib.min_prg_bank_size(fileInfo["prgSize"], fileInfo["mapper"])
            for prgAddr in prgAddresses:
                cpuAddresses.update(qneslib.prg_address_to_cpu_addresses(prgAddr, prgBankSize))

            if args.verbose:
                print("Matching addresses in file2:")
                print("    PRG:", ", ".join(f"{addr:04x}" for addr in sorted(prgAddresses)))
                print("    CPU:", ", ".join(f"{addr:04x}" for addr in sorted(cpuAddresses)))

            # if file2 not bankswitched, discard compare value to output six-letter codes
            if not qneslib.is_prg_bankswitched(fileInfo["prgSize"], fileInfo["mapper"]):
                compareValue = None
    except OSError:
        sys.exit("Error reading file2.")

    print_results(cpuAddresses, args.code, compareValue)

if __name__ == "__main__":
    main()
