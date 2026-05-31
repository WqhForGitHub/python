# ==============================================================================
# 11.3 Working with Binary Data Record Layouts
# ==============================================================================
# https://docs.python.org/3/tutorial/stdlib2.html#working-with-binary-data-record-layouts

# --- The struct module: pack() and unpack() for binary records ---
import struct

# The struct module provides pack() and unpack() functions for working
# with variable length binary record formats.
#
# Pack codes "H" and "I" represent two and four byte unsigned numbers
# respectively. The "<" indicates that they are standard size and in
# little-endian byte order.
#
# The following example shows how to loop through header information
# in a ZIP file without using the zipfile module:

# with open('myfile.zip', 'rb') as f:
#     data = f.read()
#
# start = 0
# for i in range(3):                      # show the first 3 file headers
#     start += 14
#     fields = struct.unpack('<IIIHH', data[start:start+16])
#     crc32, comp_size, uncomp_size, filenamesize, extra_size = fields
#
#     start += 16
#     filename = data[start:start+filenamesize]
#     start += filenamesize
#     extra = data[start:start+extra_size]
#     print(filename, hex(crc32), comp_size, uncomp_size)
#
#     start += extra_size + comp_size      # skip to the next header

# --- A simpler example: pack and unpack ---
# Pack two unsigned shorts (H) and one unsigned int (I) into bytes:
packed = struct.pack('<HHI', 1, 2, 300)
print(packed)        # b'\x01\x00\x02\x00,\x01\x00\x00'
print(len(packed))   # 8 bytes (2 + 2 + 4)

# Unpack bytes back into values:
unpacked = struct.unpack('<HHI', packed)
print(unpacked)      # (1, 2, 300)
