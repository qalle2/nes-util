"""Print information of an iNES ROM file (.nes)."""

import hashlib
import os
import sys
import ineslib

def to_ASCII(text):
    """Replace non-ASCII characters with backslash codes."""

    return text.encode("ascii", errors="backslashreplace").decode("ascii")

def hash_file_slice(handle, bytesLeft):
    """Compute the MD5 hash of a slice of the file, starting from current position."""

    hash_ = hashlib.md5()
    while bytesLeft:
        chunkSize = min(bytesLeft, 2 ** 20)
        hash_.update(handle.read(chunkSize))
        bytesLeft -= chunkSize
    return hash_.hexdigest()

def get_iNES_info(handle):
    """Process an iNES file."""

    fileSize = handle.seek(0, 2)
    try:
        fileInfo = ineslib.parse_iNES_header(handle)
    except Exception as e:
        sys.exit(to_ASCII(os.path.basename(handle.name)) + ": error: " + str(e))

    handle.seek(0)
    fileHash = hash_file_slice(handle, fileSize)
    handle.seek(16 + fileInfo["trainerSize"])
    PRGHash = hash_file_slice(handle, fileInfo["PRGSize"])
    CHRHash = hash_file_slice(handle, fileInfo["CHRSize"]) if fileInfo["CHRSize"] else ""

    fileInfo.update({
        "file": os.path.basename(handle.name),
        "size": fileSize,
        "fileHash": fileHash,
        "PRGHash": PRGHash,
        "CHRHash": CHRHash,
    })
    return fileInfo

def format_CSV_output_value(value):
    """Format a value for CSV output."""

    if isinstance(value, bool):
        value = "yes" if value else "no"
    return str(value) if isinstance(value, int) else '"{:s}"'.format(to_ASCII(value))

def print_file_info(fileInfo):
    """Print file info."""

    # field names in fileInfo (note: make sure the help text is up to date)
    fields = (
        "file", "size", "PRGSize", "CHRSize", "mapper", "mirroring", "saveRAM", "trainerSize",
        "fileHash", "PRGHash", "CHRHash"
    )
    assert len(fields) == len(set(fields)) == len(fileInfo)  # no duplicates/missing fields
    print(",".join(format_CSV_output_value(fileInfo[field]) for field in fields))

def main():
    """The main function."""

    if len(sys.argv) != 2:
        sys.exit(
            "Print information of an iNES ROM file (.nes) in CSV format. Argument: file. Output "
            "fields: file, size, PRG ROM size, CHR ROM size, mapper, name table mirroring, does "
            "the game have save RAM, trainer size, file MD5 hash, PRG ROM MD5 hash, CHR ROM MD5 "
            "hash."
        )
    inputFile = sys.argv[1]
    if not os.path.isfile(inputFile):
        sys.exit("File not found.")

    try:
        with open(inputFile, "rb") as handle:
            fileInfo = get_iNES_info(handle)
    except OSError:
        sys.exit("Error reading the file.")

    print_file_info(fileInfo)

if __name__ == "__main__":
    main()
