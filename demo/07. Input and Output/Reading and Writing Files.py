# ==============================================================================
# 7.2 Reading and Writing Files
# ==============================================================================
# https://docs.python.org/3/tutorial/inputoutput.html#reading-and-writing-files

# open() returns a file object, and is most commonly used with two positional
# arguments and one keyword argument: open(filename, mode, encoding=None)

# --- Opening a file ---
# f = open('workfile', 'w', encoding="utf-8")

# --- File modes ---
# 'r'  - open for reading (default)
# 'w'  - open for writing (truncates existing file)
# 'a'  - open for appending (data written is added to the end)
# 'r+' - open for both reading and writing
# 'b'  - binary mode (appended to mode, e.g. 'rb', 'wb')
# 't'  - text mode (default)

# --- Text mode vs binary mode ---
# In text mode (default), you read and write strings encoded in a specific encoding.
# If encoding is not specified, the default is platform dependent.
# encoding="utf-8" is recommended unless you know you need a different encoding.
# In binary mode, data is read and written as bytes objects.
# You cannot specify encoding when opening a file in binary mode.

# In text mode, platform-specific line endings are converted to \n when reading,
# and \n is converted back to platform-specific line endings when writing.
# This is fine for text files but will corrupt binary data (JPEG, EXE, etc.).

# --- Using the with statement (recommended) ---
# The file is properly closed after the suite finishes, even if an exception
# is raised. Using with is also much shorter than equivalent try-finally blocks.
import tempfile
import os

# Create a temporary file for demonstration
tmpdir = tempfile.gettempdir()
workfile = os.path.join(tmpdir, 'workfile_demo.txt')

with open(workfile, 'w', encoding="utf-8") as f:
    f.write('Hello, file!\n')

# We can check that the file has been automatically closed
print(f.closed)  # True

# --- Without with, you must call f.close() manually ---
f = open(workfile, 'w', encoding="utf-8")
f.write('Manual close example\n')
f.close()

# Warning: calling f.write() without using with or calling f.close() might
# result in the arguments of f.write() not being completely written to disk,
# even if the program exits successfully.

# --- After a file is closed, attempts to use it will fail ---
f = open(workfile, 'r', encoding="utf-8")
content = f.read()
f.close()
# f.read()  # ValueError: I/O operation on closed file

print(content)  # Manual close example

# Clean up the temporary file
os.remove(workfile)
