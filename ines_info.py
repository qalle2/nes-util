import os, sys, zlib
import qneslib  # qalle's NES library, https://github.com/qalle2/nes-util

OUTPUT_FIELDS = (
    "file", "size", "prgSize", "chrSize", "mapper", "mirroring", "extraRam", "trainerSize",
    "checksum", "prgChecksum", "chrChecksum"
)

def file_slice_checksum(handle, bytesLeft):
    # compute CRC32 checksum starting from current file position
    checksum = 0
    while bytesLeft:
        chunkSize = min(bytesLeft, 2 ** 20)
        checksum = zlib.crc32(handle.read(chunkSize), checksum)
        bytesLeft -= chunkSize
    return format(checksum, "08x")

def get_ines_info(handle):
    # get information of an iNES ROM file

    fileInfo = qneslib.ines_header_decode(handle)
    if fileInfo is None:
        sys.exit(f"{handle.name}: invalid iNES ROM file")

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

def format_output_value(value):
    # format a value (bool/int/str) for output
    if isinstance(value, bool):
        value = ["no", "yes"][value]
    return f'{value}' if isinstance(value, int) else f'"{value}"'

if len(sys.argv) != 2:
    sys.exit(
        "Print information of an iNES ROM file (.nes) in CSV format. Argument: file. Output "
        "fields: " + ",".join(f'"{f}"' for f in OUTPUT_FIELDS) + ". prg=PRG ROM, chr=CHR ROM, "
        "mirroring=name table mirroring (h=horizontal, v=vertical, f=four-screen), "
        "checksum=CRC32 (zlib)."
    )

inputFile = sys.argv[1]
if not os.path.isfile(inputFile):
    sys.exit("File not found.")

try:
    with open(inputFile, "rb") as handle:
        fileInfo = get_ines_info(handle)
except OSError:
    sys.exit("Error reading the file.")

print(",".join(format_output_value(fileInfo[f]) for f in OUTPUT_FIELDS))
