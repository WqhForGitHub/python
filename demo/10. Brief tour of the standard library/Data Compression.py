# ==============================================================================
# 10.9 Data Compression
# ==============================================================================
# https://docs.python.org/3/tutorial/stdlib.html#data-compression

# --- Common data archiving and compression formats ---
# Supported modules: zlib, gzip, bz2, lzma, zipfile, tarfile

# --- zlib: compression and decompression ---
import zlib

s = b'witch which has which witches wrist watch'
print(len(s))  # 41

t = zlib.compress(s)
print(len(t))  # Compressed size (e.g., 37)

decompressed = zlib.decompress(t)
print(decompressed)
# Output: b'witch which has which witches wrist watch'

# CRC32 checksum
print(zlib.crc32(s))  # 226805979

# --- gzip: working with gzip files ---
import gzip
import io

# Compress data to a gzip byte stream
compressed = gzip.compress(b'Hello, World! ' * 100)
print(f"Original: {len(b'Hello, World! ' * 100)}, Compressed: {len(compressed)}")

# Decompress
decompressed = gzip.decompress(compressed)
print(decompressed[:20])  # b'Hello, World! Hello'

# --- bz2: another compression format ---
import bz2

compressed_bz2 = bz2.compress(b'repeated data ' * 100)
print(f"bz2 compressed size: {len(compressed_bz2)}")
print(bz2.decompress(compressed_bz2)[:20])

# --- lzma: LZMA/XZ compression ---
import lzma

compressed_lzma = lzma.compress(b'repeated data ' * 100)
print(f"lzma compressed size: {len(compressed_lzma)}")
print(lzma.decompress(compressed_lzma)[:20])

# --- zipfile: working with ZIP archives ---
import zipfile
import tempfile
import os

with tempfile.TemporaryDirectory() as tmpdir:
    zip_path = os.path.join(tmpdir, 'example.zip')

    # Create a ZIP file
    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.writestr('hello.txt', 'Hello, World!')
        zf.writestr('data.txt', 'Some data here')

    # Read a ZIP file
    with zipfile.ZipFile(zip_path, 'r') as zf:
        print(zf.namelist())  # ['hello.txt', 'data.txt']
        print(zf.read('hello.txt'))  # b'Hello, World!'

# --- tarfile: working with tar archives ---
import tarfile

with tempfile.TemporaryDirectory() as tmpdir:
    tar_path = os.path.join(tmpdir, 'example.tar.gz')

    # Create a tar archive
    file_path = os.path.join(tmpdir, 'test.txt')
    with open(file_path, 'w') as f:
        f.write('tar file content')

    with tarfile.open(tar_path, 'w:gz') as tf:
        tf.add(file_path, arcname='test.txt')

    # Read a tar archive
    with tarfile.open(tar_path, 'r:gz') as tf:
        print(tf.getnames())  # ['test.txt']
