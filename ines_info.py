"""Print information of an iNES ROM file (.nes)."""

import os
import sys
import zlib
import qneslib  # qalle's NES library, https://github.com/qalle2/nes-util

def file_slice_checksum(handle, bytesLeft):
    """Compute the CRC32 checksum of a slice of the file, starting from current position."""

    checksum = 0
    while bytesLeft:
        chunkSize = min(bytesLeft, 2 ** 20)
        checksum = zlib.crc32(handle.read(chunkSize), checksum)
        bytesLeft -= chunkSize
    return format(checksum, "08x")

def get_ines_info(handle):
    """Process an iNES file."""

    fileInfo = qneslib.ines_header_decode(handle)
    if fileInfo is None:
        sys.exit(os.path.basename(handle.name) + ": invalid iNES ROM file")

    fileSize = handle.seek(0, 2)

    handle.seek(0)
    fileChecksum = file_slice_checksum(handle, fileSize)
    handle.seek(fileInfo["prgStart"])
    prgChecksum = file_slice_checksum(handle, fileInfo["prgSize"])
    handle.seek(fileInfo["chrStart"])
    chrChecksum = file_slice_checksum(handle, fileInfo["chrSize"])

    fileInfo.update({
        "file": os.path.basename(handle.name),
        "size": fileSize,
        "fileChecksum": fileChecksum,
        "prgChecksum": prgChecksum,
        "chrChecksum": chrChecksum,
    })
    return fileInfo

def format_output_value(value):
    if isinstance(value, bool):
        value = ["no", "yes"][value]
    return f'{value}' if isinstance(value, int) else f'"{value}"'

def print_file_info(fileInfo):
    """Print file info."""

    # field names in fileInfo (note: make sure the help text is up to date)
    fields = (
        "file", "size", "prgSize", "chrSize", "mapper", "mirroring", "saveRam", "trainerSize",
        "fileChecksum", "prgChecksum", "chrChecksum"
    )
    print(",".join(format_output_value(fileInfo[field]) for field in fields))

def main():
    """The main function."""

    if len(sys.argv) != 2:
        fields = (
            "file", "size", "PRG ROM size", "CHR ROM size", "mapper", "name table mirroring",
            "has save RAM?", "trainer size", "file CRC32", "PRG ROM CRC32", "CHR ROM CRC32"
        )
        sys.exit(
            "Print information of an iNES ROM file (.nes) in CSV format. Argument: file. Output "
            "fields: " + ",".join(f'"{f}"' for f in fields)
        )

    inputFile = sys.argv[1]
    if not os.path.isfile(inputFile):
        sys.exit("File not found.")

    try:
        with open(inputFile, "rb") as handle:
            fileInfo = get_ines_info(handle)
    except OSError:
        sys.exit("Error reading the file.")

    print_file_info(fileInfo)

if __name__ == "__main__":
    main()
