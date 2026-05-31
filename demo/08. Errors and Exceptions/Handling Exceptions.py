# ==============================================================================
# 8.3 Handling Exceptions
# ==============================================================================
# https://docs.python.org/3/tutorial/errors.html#handling-exceptions

# --- Basic try/except ---
# The try statement allows you to handle exceptions gracefully.
# Example: converting user input to an integer
#   x = int(input('Please enter a number: '))
# If the user types 'abc', a ValueError is raised.
# We can handle it with try/except:
try:
    x = int('abc')  # simulating invalid user input
except ValueError:
    print('Oops!  That was no valid number.  Try again...')
# Output: Oops!  That was no valid number.  Try again...

try:
    x = int('42')  # valid input
except ValueError:
    print('Oops!  That was no valid number.  Try again...')
else:
    print(f'Successfully parsed: {x}')
# Output: Successfully parsed: 42

# --- The try statement works as follows ---
# 1. The try clause (the code between try and except) is executed.
# 2. If no exception occurs, the except clause is skipped.
# 3. If an exception occurs, the rest of the try clause is skipped.
#    If the exception type matches what's after except, the except clause runs.
# 4. If an exception occurs but doesn't match, it's passed to outer try statements.

# --- Handling multiple exceptions ---
# You can have multiple except clauses to handle different exceptions:
import sys

try:
    f = open('myfile.txt')
    s = f.readline()
    i = int(s.strip())
except OSError as err:
    print(f'OS error: {err}')
except ValueError:
    print('Could not convert data to an integer.')
except Exception as e:
    print(f'Unexpected error: {e}')
# Since 'myfile.txt' doesn't exist, this will likely print:
# OS error: [Errno 2] No such file or directory: 'myfile.txt'

# --- Handling multiple exceptions in one except clause ---
# An except clause can name multiple exceptions as a parenthesized tuple:
try:
    result = 1 / 0
except (RuntimeError, TypeError, ZeroDivisionError) as e:
    print(f'Caught an error: {e}')
# Output: Caught an error: division by zero

# --- The exception instance ---
# The exception is bound to the variable after 'as' keyword.
# It has a .args attribute that stores the arguments:
try:
    raise Exception('spam', 'eggs')
except Exception as e:
    print(type(e))        # <class 'Exception'>
    print(e.args)         # ('spam', 'eggs')
    print(e)              # ('spam', 'eggs')
    a, b = e.args
    print(f'a = {a}')    # a = spam
    print(f'b = {b}')    # b = eggs

# --- Bare except (not recommended) ---
# A bare except catches all exceptions, including SystemExit and KeyboardInterrupt.
# This can mask bugs and make debugging very hard. Avoid it in production code.
# try:
#     something_risky()
# except:   # catches everything - dangerous!
#     print('Something went wrong')

# --- Using the base class catches derived classes too ---
# If we write except Exception, it catches Exception and all its subclasses:
try:
    1 / 0  # ZeroDivisionError is a subclass of Exception
except Exception as e:
    print(f'Caught: {type(e).__name__}: {e}')
# Output: Caught: ZeroDivisionError: division by zero

# --- else clause ---
# The try/except statement has an optional else clause, which runs only if
# no exception was raised in the try block:
for arg in sys.argv[1:]:
    try:
        f = open(arg, 'r')
    except OSError:
        print(f'cannot open {arg}')
    else:
        print(arg, 'has', len(f.readlines()), 'lines')
        f.close()

# A simpler example:
try:
    number = int('42')  # no exception
except ValueError:
    print('Not a number!')
else:
    print(f'Valid number: {number}')
# Output: Valid number: 42

# The else clause is better than adding extra code to the try clause
# because it avoids accidentally catching exceptions that weren't raised
# by the code being protected.

# --- Practical example: safe division ---
def safe_divide(a, b):
    try:
        result = a / b
    except ZeroDivisionError:
        print('Error: division by zero')
        return None
    except TypeError:
        print('Error: both arguments must be numbers')
        return None
    else:
        print(f'{a} / {b} = {result}')
        return result

print(safe_divide(10, 2))   # 10 / 2 = 5.0, returns 5.0
print(safe_divide(10, 0))   # Error: division by zero, returns None
print(safe_divide('10', 2))  # Error: both arguments must be numbers, returns None
