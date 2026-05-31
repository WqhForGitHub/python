# ==============================================================================
# 10.1 Operating System Interface
# ==============================================================================
# https://docs.python.org/3/tutorial/stdlib.html#operating-system-interface

# --- The os module: interacting with the operating system ---
import os

# Return the current working directory
print(os.getcwd())

# Change current working directory
# os.chdir('/server/accesslogs')

# Run a command in the system shell
# os.system('mkdir today')

# --- Important: use 'import os' instead of 'from os import *' ---
# This will keep os.open() from shadowing the built-in open() function
# which operates much differently.

# --- Using dir() and help() as interactive aids ---
# dir(os) returns a list of all module functions
print(dir(os)[:10])  # showing first 10 for brevity

# help(os) returns an extensive manual page created from the module's docstrings
# help(os)

# --- The shutil module: higher level file and directory management ---
import shutil

# Copy a file
# shutil.copyfile('data.db', 'archive.db')

# Move a file or directory
# shutil.move('/build/executables', 'installdir')

# --- shutil also provides copy2 (preserves metadata), copytree, rmtree ---
import tempfile

# Create a temporary directory for demonstration
with tempfile.TemporaryDirectory() as tmpdir:
    # Create a source file
    src = os.path.join(tmpdir, 'data.db')
    with open(src, 'w') as f:
        f.write('hello')

    # copyfile: copy contents only
    dst = os.path.join(tmpdir, 'archive.db')
    shutil.copyfile(src, dst)
    print(shutil.copyfile(src, dst))  # archive.db

    # copy2: copy contents + metadata (timestamps, etc.)
    dst2 = os.path.join(tmpdir, 'archive2.db')
    shutil.copy2(src, dst2)

    # Create a subdirectory tree and copy it
    subdir = os.path.join(tmpdir, 'subdir')
    os.mkdir(subdir)
    with open(os.path.join(subdir, 'file.txt'), 'w') as f:
        f.write('content')

    copied_tree = os.path.join(tmpdir, 'copied_tree')
    shutil.copytree(subdir, copied_tree)
    print(os.listdir(copied_tree))  # ['file.txt']

    # Remove a directory tree
    shutil.rmtree(copied_tree)
    print(os.path.exists(copied_tree))  # False
