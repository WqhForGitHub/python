# ==============================================================================
# 8.8 Predefined Clean-up Actions
# ==============================================================================
# https://docs.python.org/3/tutorial/errors.html#predefined-clean-up-actions

# --- The problem with manual cleanup ---
# Some objects define standard clean-up actions to be undertaken when the
# object is no longer needed, regardless of whether or not the operation
# using the object succeeded or failed.

# Consider the following example which tries to open and write to a file:
# with open('myfile.txt') as f:
#     for line in f:
#         print(line, end='')

# --- The with statement ---
# The with statement allows objects like files to be used in a way that
# ensures they are always cleaned up promptly and correctly.
import tempfile
import os

tmpdir = tempfile.gettempdir()
workfile = os.path.join(tmpdir, 'predefined_cleanup_demo.txt')

# --- Without with: risk of resource leak ---
# If an exception occurs during writing, the file may not be closed properly:
# f = open(workfile, 'w', encoding='utf-8')
# try:
#     f.write('Some data')
#     # If an exception happens here, f.close() won't be called
# finally:
#     f.close()

# --- With with: guaranteed cleanup ---
# After the statement is executed, the file f is always closed, even if a
# problem was encountered while processing the lines.
with open(workfile, 'w', encoding='utf-8') as f:
    f.write('Hello, world!\n')
    f.write('Second line\n')
# f is automatically closed here
print(f.closed)  # True

# --- with handles exceptions gracefully ---
# Even if an error occurs inside the with block, the resource is cleaned up:
try:
    with open(workfile, 'r', encoding='utf-8') as f:
        content = f.read()
        print(f'File content: {content!r}')
        # Even if an error occurs after this line, f will be closed
except FileNotFoundError:
    print('File not found')
# Output: File content: 'Hello, world!\nSecond line\n'

# --- The context manager protocol ---
# Objects that work with 'with' implement the context manager protocol:
#   __enter__() - called when entering the with block, returns the object
#   __exit__(exc_type, exc_val, exc_tb) - called when leaving the with block

# --- Creating your own context manager ---
# You can create context managers using a class:

class ManagedResource:
    """A simple context manager for demonstration."""

    def __init__(self, name):
        self.name = name

    def __enter__(self):
        print(f'Acquiring resource: {self.name}')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print(f'Releasing resource: {self.name}')
        if exc_type is not None:
            print(f'  Exception occurred: {exc_type.__name__}: {exc_val}')
        # Return False to propagate the exception, True to suppress it
        return False

    def do_work(self):
        print(f'Working with {self.name}')

# Normal usage:
with ManagedResource('database_connection') as resource:
    resource.do_work()
# Output:
# Acquiring resource: database_connection
# Working with database_connection
# Releasing resource: database_connection

# With an exception:
try:
    with ManagedResource('file_handle') as resource:
        resource.do_work()
        raise ValueError('Something went wrong')
except ValueError:
    print('Exception was handled')
# Output:
# Acquiring resource: file_handle
# Working with file_handle
# Releasing resource: file_handle
#   Exception occurred: ValueError: Something went wrong
# Exception was handled

# --- Using contextlib.contextmanager ---
# A simpler way to create context managers using a generator:
from contextlib import contextmanager

@contextmanager
def managed_resource(name):
    """A context manager created from a generator."""
    print(f'Acquiring resource: {name}')
    try:
        yield name
    finally:
        print(f'Releasing resource: {name}')

with managed_resource('network_socket') as r:
    print(f'Using: {r}')
# Output:
# Acquiring resource: network_socket
# Using: network_socket
# Releasing resource: network_socket

# --- Multiple context managers ---
# You can use multiple context managers in a single with statement:
second_file = os.path.join(tmpdir, 'predefined_cleanup_demo2.txt')

with open(workfile, 'r', encoding='utf-8') as src, \
     open(second_file, 'w', encoding='utf-8') as dst:
    dst.write(src.read())
# Both files are automatically closed when the block ends

# Verify the copy
with open(second_file, 'r', encoding='utf-8') as f:
    print(f.read())
# Output:
# Hello, world!
# Second line

# --- Suppressing exceptions with contextlib.suppress ---
# If you only need to suppress specific exceptions, use contextlib.suppress:
from contextlib import suppress

with suppress(FileNotFoundError):
    os.remove('/nonexistent/file.txt')
# No exception is raised, even though the file doesn't exist

# This is equivalent to:
# try:
#     os.remove('/nonexistent/file.txt')
# except FileNotFoundError:
#     pass

print('Done - no exception raised for missing file')
# Output: Done - no exception raised for missing file

# --- Practical example: temporary file that auto-cleans ---
# Using with to ensure temporary resources are cleaned up:
from contextlib import contextmanager
import tempfile
import shutil

@contextmanager
def temporary_directory():
    """Create a temporary directory that is cleaned up after use."""
    dirpath = tempfile.mkdtemp()
    print(f'Created temp dir: {dirpath}')
    try:
        yield dirpath
    finally:
        shutil.rmtree(dirpath)
        print(f'Cleaned up temp dir: {dirpath}')

with temporary_directory() as tmp:
    # Create a file in the temporary directory
    filepath = os.path.join(tmp, 'test.txt')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('Temporary data')
    print(f'Created file in temp dir: {os.listdir(tmp)}')
# Output:
# Created temp dir: /tmp/...
# Created file in temp dir: ['test.txt']
# Cleaned up temp dir: /tmp/...

# Clean up demo files
os.remove(workfile)
os.remove(second_file)
