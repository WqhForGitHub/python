# ==============================================================================
# 7.2.1 Methods of File Objects
# ==============================================================================
# https://docs.python.org/3/tutorial/inputoutput.html#methods-of-file-objects

import tempfile
import os

# Create a temporary file for demonstration
tmpdir = tempfile.gettempdir()
workfile = os.path.join(tmpdir, 'workfile_methods_demo.txt')

# --- f.read(size): read file contents ---
# When size is omitted or negative, the entire contents of the file are read
with open(workfile, 'w', encoding="utf-8") as f:
    f.write('This is the entire file.\n')

with open(workfile, 'r', encoding="utf-8") as f:
    print(f.read())  # This is the entire file.

with open(workfile, 'r', encoding="utf-8") as f:
    print(f.read())  # This is the entire file.
    print(repr(f.read()))  # ''  (end of file reached, returns empty string)

# --- f.readline(): read a single line ---
with open(workfile, 'w', encoding="utf-8") as f:
    f.write('This is the first line of the file.\n')
    f.write('Second line of the file\n')

with open(workfile, 'r', encoding="utf-8") as f:
    print(repr(f.readline()))  # 'This is the first line of the file.\n'
    print(repr(f.readline()))  # 'Second line of the file\n'
    print(repr(f.readline()))  # ''  (end of file, returns empty string)

# Note: a blank line is represented by '\n', not '' (empty string).
# This makes the return value unambiguous.

# --- Iterating over a file object (memory efficient, fast, simple) ---
with open(workfile, 'r', encoding="utf-8") as f:
    for line in f:
        print(line, end='')
# Output:
# This is the first line of the file.
# Second line of the file

# --- Reading all lines into a list ---
with open(workfile, 'r', encoding="utf-8") as f:
    lines = list(f)
    print(lines)  # ['This is the first line of the file.\n', 'Second line of the file\n']

with open(workfile, 'r', encoding="utf-8") as f:
    lines = f.readlines()
    print(lines)  # ['This is the first line of the file.\n', 'Second line of the file\n']

# --- f.write(string): write to a file ---
# Returns the number of characters written
with open(workfile, 'w', encoding="utf-8") as f:
    n = f.write('This is a test\n')
    print(n)  # 15

# Other types need to be converted to string first:
with open(workfile, 'w', encoding="utf-8") as f:
    value = ('the answer', 42)
    s = str(value)  # convert the tuple to string
    n = f.write(s)
    print(n)  # 18

# --- f.tell(): get current file position ---
# Returns an integer giving the current position in the file
with open(workfile, 'r', encoding="utf-8") as f:
    f.read(5)
    print(f.tell())  # 5

# --- f.seek(offset, whence): change file position ---
# whence=0: beginning of file (default)
# whence=1: current file position
# whence=2: end of file
with open(workfile, 'wb+') as f:
    f.write(b'0123456789abcdef')
    f.seek(5)         # Go to the 6th byte in the file
    print(f.read(1))  # b'5'
    f.seek(-3, 2)     # Go to the 3rd byte before the end
    print(f.read(1))  # b'd'

# Note: In text files (opened without 'b'), only seeks relative to the
# beginning of the file are allowed (except seek(0, 2) for the very end),
# and the only valid offset values are those from f.tell() or zero.

# Clean up
os.remove(workfile)
