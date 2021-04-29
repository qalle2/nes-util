import argparse, os, sys
import qneslib  # qalle's NES library, https://github.com/qalle2/nes-util

def parse_arguments():
    # parse command line arguments using argparse

    parser = argparse.ArgumentParser(
        description="Convert an NES Game Genie code from one version of a game to another using "
        "both iNES ROM files (.nes). Technical explanation: decode the code; find out PRG ROM "
        "addresses affected in file1; see what's in and around them; look for similar bytestrings "
        "in file2's PRG ROM; convert the addresses back into CPU addresses; encode them into "
        "codes."
    )

    parser.add_argument(
        "-s", "--slice-length", type=int, default=4,
        help="How many PRG ROM bytes to compare both before and after the relevant byte (that is, "
        "total number of bytes compared is twice this value, plus one). Fewer bytes will be "
        "compared if the relevant byte is too close to start or end of PRG ROM. 1 to 20, "
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
        sys.exit("Invalid --slice-length.")
    if not 0 <= args.max_different_bytes < 2 * args.slice_length:
        sys.exit("Invalid --max-different-bytes.")
    if qneslib.game_genie_decode(args.code) is None:
        sys.exit("Invalid code.")

    if not os.path.isfile(args.file1):
        sys.exit("file1 not found.")
    if not os.path.isfile(args.file2):
        sys.exit("file2 not found.")

    return args

def print_decoded_code(args):
    (addr, repl, comp) = qneslib.game_genie_decode(args.code)
    comp = "none" if comp is None else f"{comp:02x}"
    print(f"Code: CPU address={addr:04x}, replace value={repl:02x}, compare value={comp}")

def get_prg_addresses(fileInfo, args, handle):
    # get PRG ROM addresses affected by code in file1

    (cpuAddr, repl, comp) = qneslib.game_genie_decode(args.code)

    if comp is None and qneslib.is_prg_bankswitched(fileInfo["prgSize"], fileInfo["mapper"]):
        sys.exit("Six-letter codes not supported because file1 uses PRG ROM bankswitching.")

    prgBankSize = qneslib.min_prg_bank_size(fileInfo["prgSize"], fileInfo["mapper"])
    prgAddrGen = qneslib.address_cpu_to_prg(cpuAddr, prgBankSize, fileInfo["prgSize"])
    if comp is None:
        return set(prgAddrGen)
    prgAddresses = set()
    for prgAddr in prgAddrGen:
        handle.seek(fileInfo["prgStart"] + prgAddr)
        if handle.read(1)[0] == comp:
            prgAddresses.add(prgAddr)
    return prgAddresses

def get_prg_slices(prgAddresses, fileInfo, args, handle):
    # generate slices surrounding each PRG ROM address in file1: (bytes_before, bytes_after)

    for prgAddr in prgAddresses:
        # get actual length of slice before/after relevant byte
        lenBefore = min(args.slice_length, prgAddr)
        lenAfter = min(args.slice_length, fileInfo["prgSize"] - prgAddr - 1)

        handle.seek(fileInfo["prgStart"] + prgAddr - lenBefore)
        slice_ = handle.read(lenBefore + 1 + lenAfter)

        # don't use [-lenAfter:] as lenAfter may be zero
        yield (slice_[:lenBefore], slice_[lenBefore+1:])

def get_fake_compare_value(handle, args):
    # get a fake compare value from file1 for user's six-letter code
    cpuAddr = qneslib.game_genie_decode(args.code)[0]
    fileInfo = qneslib.ines_header_decode(handle)
    prgAddr = cpuAddr & (fileInfo["prgSize"] - 1)
    handle.seek(fileInfo["prgStart"] + prgAddr)
    return handle.read(1)[0]

def print_slices(slices, compareValue):
    # print slices found in file1
    print(
        "Bytestrings around those addresses in file1 (relevant byte in <brackets>):",
        ", ".join(f"{s[0].hex()}<{compareValue:02x}>{s[1].hex()}" for s in sorted(slices))
    )

def find_slices_in_prg(handle, slices, comp, args):
    # generate PRG addresses of each slice (used with file2; comp = compare value)

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

def print_results(cpuAddresses, compareValue, args):
    # print codes with new addresses (sort by difference from original address)
    (origCpuAddr, replaceValue) = qneslib.game_genie_decode(args.code)[:2]
    cpuAddresses = sorted(cpuAddresses)
    cpuAddresses.sort(key=lambda addr: abs(addr - origCpuAddr))
    print("Game Genie codes for file2 (try the first one first):", ", ".join(
        qneslib.game_genie_encode(a, replaceValue, compareValue) for a in cpuAddresses
    ))

args = parse_arguments()

if args.verbose:
    print_decoded_code(args)

compareValue = qneslib.game_genie_decode(args.code)[2]

# get PRG addresses, PRG slices and optionally a fake compare value from file1
try:
    with open(args.file1, "rb") as handle:
        fileInfo = qneslib.ines_header_decode(handle)
        if fileInfo is None:
            sys.exit("file1 is not a valid iNES ROM file.")

        prgAddresses = get_prg_addresses(fileInfo, args, handle)
        if not prgAddresses:
            sys.exit("Your code seems to affect file1 in no way.")
        slices = set(get_prg_slices(prgAddresses, fileInfo, args, handle))

        if compareValue is None:
            compareValue = get_fake_compare_value(handle, args)
            if args.verbose:
                print(f"Using fake compare value: {compareValue:02x}")
except OSError:
    sys.exit("Error reading file1.")

if args.verbose:
    print("PRG addresses in file1:", ", ".join(f"{addr:04x}" for addr in sorted(prgAddresses)))
    print_slices(slices, compareValue)

# find PRG addresses in file2
try:
    with open(args.file2, "rb") as handle:
        fileInfo = qneslib.ines_header_decode(handle)
        if fileInfo is None:
            sys.exit("file2 is not a valid iNES ROM file.")
        prgAddresses = set(find_slices_in_prg(handle, slices, compareValue, args))
except OSError:
    sys.exit("Error reading file2.")
if not prgAddresses:
    sys.exit("file2 contains nothing similar to what your code affects in file1.")
if args.verbose:
    print("PRG address matches in file2:", ", ".join(f"{a:04x}" for a in sorted(prgAddresses)))

# convert PRG addresses into CPU addresses
cpuAddresses = set()
prgBankSize = qneslib.min_prg_bank_size(fileInfo["prgSize"], fileInfo["mapper"])
for prgAddr in prgAddresses:
    cpuAddresses.update(qneslib.address_prg_to_cpu(prgAddr, prgBankSize))
if args.verbose:
    print("CPU address matches in file2:", ", ".join(f"{a:04x}" for a in sorted(cpuAddresses)))

# if file2 not bankswitched, discard compare value to output six-letter codes
if not qneslib.is_prg_bankswitched(fileInfo["prgSize"], fileInfo["mapper"]):
    compareValue = None

print_results(cpuAddresses, compareValue, args)
