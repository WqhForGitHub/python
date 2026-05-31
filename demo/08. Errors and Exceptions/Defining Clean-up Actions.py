# ==============================================================================
# 8.7 Defining Clean-up Actions
# ==============================================================================
# https://docs.python.org/3/tutorial/errors.html#defining-clean-up-actions

# --- The finally clause ---
# The try statement has another optional clause called 'finally',
# which is intended to define clean-up actions that must be executed
# under all circumstances.

# raise KeyboardInterrupt
# finally:
#     print('Goodbye, world!')
# Output: Goodbye, world!
# Then the KeyboardInterrupt is re-raised.

# A safer example that demonstrates the same concept:
try:
    try:
        raise ValueError('simulated interrupt')
    finally:
        print('Goodbye, world!')
except ValueError:
    print('Caught the re-raised exception')
# Output: Goodbye, world!
# Caught the re-raised exception

# --- finally always executes ---
# The finally clause executes whether or not an exception occurs:
# Case 1: No exception
try:
    print('Trying...')
except:
    print('An error occurred.')
finally:
    print('Finally clause executed.')
# Output:
# Trying...
# Finally clause executed.

# Case 2: Exception that is caught
try:
    print('Trying...')
    1 / 0
except ZeroDivisionError:
    print('Caught division error.')
finally:
    print('Finally clause executed.')
# Output:
# Trying...
# Caught division error.
# Finally clause executed.

# Case 3: Exception that is NOT caught by the except clause
try:
    try:
        print('Trying...')
        1 / 0
    except ValueError:
        print('This will not catch ZeroDivisionError.')
    finally:
        print('Finally clause executed anyway.')
except ZeroDivisionError:
    print('Caught by outer try')
# Output:
# Trying...
# Finally clause executed anyway.
# Caught by outer try

# --- finally and return ---
# If the try clause reaches a break, continue, or return statement,
# the finally clause executes just BEFORE the break/continue/return:
def divide(x, y):
    try:
        result = x / y
    except ZeroDivisionError:
        print('division by zero!')
        return None
    else:
        print(f'result is {result}')
        return result
    finally:
        print('executing finally clause')

print(divide(2, 1))
# Output:
# result is 2.0
# executing finally clause
# 2.0

print(divide(2, 0))
# Output:
# division by zero!
# executing finally clause
# None

try:
    print(divide('2', '1'))
except TypeError:
    print('TypeError caught: strings cannot be divided')
# Output:
# executing finally clause
# TypeError caught: strings cannot be divided

# --- A finally clause is always executed before leaving the try statement ---
# whether an exception was caught or not.
# When an exception has occurred and has NOT been handled by the except clause
# (or if it occurred in an except or else clause), it is re-raised after
# the finally clause has been executed.

# --- Practical example: ensuring a resource is released ---
def read_file_lines(filename):
    f = None
    try:
        f = open(filename)
        return f.readlines()
    except FileNotFoundError:
        print(f'File {filename} not found')
        return []
    finally:
        if f is not None:
            f.close()
            print('File closed.')

lines = read_file_lines('nonexistent.txt')
# Output: File nonexistent.txt not found
# (Note: f is None because open() failed, so f.close() is not called)

# Now test with a real file to see the finally clause close it:
import tempfile
import os

tmpdir = tempfile.gettempdir()
testfile = os.path.join(tmpdir, 'cleanup_test.txt')
with open(testfile, 'w', encoding='utf-8') as f:
    f.write('line1\nline2\n')

lines = read_file_lines(testfile)
print(f'Read {len(lines)} lines')
# Output:
# File closed.
# Read 2 lines

os.remove(testfile)

# --- More complex real-world example ---
def process_data(data):
    """Simulates processing with clean-up."""
    print('Starting processing...')
    try:
        if data is None:
            raise ValueError('Data cannot be None')
        result = len(data)
        print(f'Data length: {result}')
        return result
    except ValueError as e:
        print(f'Error: {e}')
        return -1
    finally:
        print('Cleaning up resources...')

print(process_data([1, 2, 3]))
# Output:
# Starting processing...
# Data length: 3
# Cleaning up resources...
# 3

print(process_data(None))
# Output:
# Starting processing...
# Error: Data cannot be None
# Cleaning up resources...
# -1
