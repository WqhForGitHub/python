# ==============================================================================
# 8.5 Exception Chaining
# ==============================================================================
# https://docs.python.org/3/tutorial/errors.html#exception-chaining

# --- The raise ... from statement ---
# The 'raise ... from' statement is used to chain exceptions,
# making it clear that one exception was the direct cause of another.

# --- Implicit chaining ---
# When an exception is raised while another exception is being handled,
# Python automatically chains them:
def divide(a, b):
    try:
        return a / b
    except ZeroDivisionError:
        raise ValueError('Invalid operands')  # implicit chaining

try:
    divide(1, 0)
except ValueError as e:
    print(f'Caught: {e}')
    print(f'Cause: {e.__cause__}')
    print(f'Context: {e.__context__}')
# Output:
# Caught: Invalid operands
# Cause: None
# Context: division by zero

# --- Explicit chaining with 'raise ... from' ---
# Use 'from' to explicitly indicate that one exception caused another.
# This sets the __cause__ attribute:
def convert(s):
    try:
        return int(s)
    except ValueError as e:
        raise ValueError(f'Cannot convert {s!r} to int') from e

try:
    convert('abc')
except ValueError as e:
    print(f'Caught: {e}')
    print(f'Cause: {e.__cause__}')
# Output:
# Caught: Cannot convert 'abc' to int
# Cause: invalid literal for int() with base 10: 'abc'

# --- The traceback shows the chain ---
# When an exception is chained, the traceback shows both exceptions:
#   The above exception was the direct cause of the following exception:
#   Traceback (most recent call last):
#     ...
#   ValueError: Cannot convert 'abc' to int

# --- Suppressing chaining with 'raise ... from None' ---
# If you want to suppress the chain (hide the original exception),
# use 'raise ... from None':
def parse_data(data):
    try:
        return int(data)
    except ValueError:
        raise ValueError('Invalid data format') from None

try:
    parse_data('xyz')
except ValueError as e:
    print(f'Caught: {e}')
    print(f'Cause: {e.__cause__}')
    print(f'Suppressed context: {e.__suppress_context__}')
# Output:
# Caught: Invalid data format
# Cause: None
# Suppressed context: True

# --- When to use exception chaining ---
# - Use 'raise X from Y' when Y is the direct cause of X
# - Use 'raise X from None' when you want to replace an exception
#   without exposing the original
# - Implicit chaining happens automatically when an exception is raised
#   inside an except block

# --- Practical example: wrapping I/O errors ---
import os

def read_config(path):
    try:
        with open(path) as f:
            return f.read()
    except OSError as e:
        raise RuntimeError(f'Failed to read config from {path}') from e

try:
    read_config('/nonexistent/config.ini')
except RuntimeError as e:
    print(f'Caught: {e}')
    print(f'Cause: {type(e.__cause__).__name__}: {e.__cause__}')
# Output:
# Caught: Failed to read config from /nonexistent/config.ini
# Cause: FileNotFoundError: [Errno 2] No such file or directory: '/nonexistent/config.ini'
