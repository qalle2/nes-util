import argparse, collections, os, sys, zlib
import qneslib  # qalle's NES library, https://github.com/qalle2/nes-util

OUTPUT_FIELDS = collections.OrderedDict((
    ("file",        "file name"),
    ("size",        "file size"),
    ("trainerSize", "trainer size"),
    ("prgSize",     "PRG ROM size"),
    ("chrSize",     "CHR ROM size"),
    ("mapper",      "iNES mapper number"),
    ("mirroring",   "name table mirroring"),
    ("extraRam",    "extra RAM"),
    ("checksum",    "file checksum"),
    ("prgChecksum", "PRG ROM checksum"),
    ("chrChecksum", "CHR ROM checksum"),
))

def parse_arguments():
    # parse and validate command line arguments using argparse

    parser = argparse.ArgumentParser(
        description="Print information of an iNES ROM file (.nes). Note: all checksums are CRC32 "
        "(zlib) in decimal."
    )
    parser.add_argument("input_file", help="File to read.")
    parser.add_argument(
        "-c", "--csv", action="store_true",
        help="Output in CSV format. Fields: " + ",".join(f'"{f}"' for f in OUTPUT_FIELDS)
    )
    args = parser.parse_args()

    if not os.path.isfile(args.input_file):
        sys.exit("Input file not found.")

    return args

def file_slice_checksum(handle, bytesLeft):
    # compute CRC32 checksum starting from current file position
    checksum = 0
    while bytesLeft:
        chunkSize = min(bytesLeft, 2 ** 20)
        checksum = zlib.crc32(handle.read(chunkSize), checksum)
        bytesLeft -= chunkSize
    return checksum

def get_ines_info(handle):
    # get information of an iNES ROM file

    fileInfo = qneslib.ines_header_decode(handle)
    if fileInfo is None:
        sys.exit(f"{os.path.basename(handle.name)}: invalid iNES ROM file")

    fileSize = handle.seek(0, 2)

    # file checksum
    handle.seek(0)
    checksum = file_slice_checksum(handle, fileSize)
    # PRG ROM checksum
    handle.seek(fileInfo["prgStart"])
    prgChecksum = file_slice_checksum(handle, fileInfo["prgSize"])
    # CHR ROM checksum
    handle.seek(fileInfo["chrStart"])
    chrChecksum = file_slice_checksum(handle, fileInfo["chrSize"])

    fileInfo.update({
        "file": os.path.basename(handle.name),
        "size": fileSize,
        "checksum": checksum,
        "prgChecksum": prgChecksum,
        "chrChecksum": chrChecksum,
    })
    return fileInfo

def format_csv_output_value(value):
    # format a value (bool/int/str) for output
    if isinstance(value, bool):
        value = ["no", "yes"][value]
    return f'{value}' if isinstance(value, int) else f'"{value}"'

def main():
    args = parse_arguments()

    try:
        with open(args.input_file, "rb") as handle:
            fileInfo = get_ines_info(handle)
    except OSError:
        sys.exit("Error reading the file.")

    if args.csv:
        print(",".join(format_csv_output_value(fileInfo[f]) for f in OUTPUT_FIELDS))
    else:
        for field in OUTPUT_FIELDS:
            value = fileInfo[field]
            if isinstance(value, bool):
                value = ["no", "yes"][value]
            elif field == "mirroring":
                value = {"h": "horizontal", "v": "vertical", "f": "four-screen"}[value]
            print(f"{OUTPUT_FIELDS[field]}: {value}")

if __name__ == "__main__":
    main()
