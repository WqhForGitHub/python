# ==============================================================================
# 8.2 Exceptions
# ==============================================================================
# https://docs.python.org/3/tutorial/errors.html#exceptions

# --- What is an Exception? ---
# Even if a statement or expression is syntactically correct, it may cause an
# error when an attempt is made to execute it. Errors detected during execution
# are called exceptions and are not unconditionally fatal.

# --- Example: Division by zero ---
# 10 * (1/0)
# Traceback (most recent call last):
#   File "<stdin>", line 1, in <module>
# ZeroDivisionError: division by zero

# --- Example: Undefined variable ---
# 4 + spam*3
# Traceback (most recent call last):
#   File "<stdin>", line 1, in <module>
# NameError: name 'spam' is not defined

# --- Example: Type mismatch ---
# '2' + 2
# Traceback (most recent call last):
#   File "<stdin>", line 1, in <module>
# TypeError: can only concatenate str (not "int") to str

# --- Exception format ---
# The last line of the error message indicates what happened.
# It comes in the form: ExceptionType: detail about what happened
# The preceding part shows the context where the exception occurred
# (the traceback).

# --- Built-in exception types ---
# Here are some common built-in exceptions:
import builtins

common_exceptions = [
    ZeroDivisionError,   # division or modulo by zero
    NameError,           # name not found
    TypeError,           # operation on inappropriate type
    ValueError,          # right type but inappropriate value
    IndexError,          # sequence subscript out of range
    KeyError,            # dictionary key not found
    FileNotFoundError,   # file or directory not found
    AttributeError,      # attribute reference or assignment fails
    ImportError,         # import statement fails to find module
    RuntimeError,        # error that doesn't fall in any other category
    StopIteration,       # no more items from an iterator
]

for exc in common_exceptions:
    print(f'{exc.__name__}: {exc.__doc__}'.split('\n')[0])
# Output (partial):
# ZeroDivisionError: Second argument to a division or modulo operation was zero.
# NameError: Name not found globally.
# TypeError: Inappropriate argument type.
# ValueError: Inappropriate argument value (of correct type).
# ...

# --- Demonstrating a few common exceptions ---
# IndexError: accessing an out-of-range index
try:
    lst = [1, 2, 3]
    lst[10]
except IndexError as e:
    print(f'IndexError: {e}')  # IndexError: list index out of range

# KeyError: accessing a non-existent dictionary key
try:
    d = {'a': 1}
    d['b']
except KeyError as e:
    print(f'KeyError: {e}')  # KeyError: 'b'

# ValueError: wrong value for the type
try:
    int('abc')
except ValueError as e:
    print(f'ValueError: {e}')  # ValueError: invalid literal for int() with base 10: 'abc'

# FileNotFoundError: trying to open a non-existent file
try:
    open('nonexistent_file.txt')
except FileNotFoundError as e:
    print(f'FileNotFoundError: {e}')  # FileNotFoundError: [Errno 2] No such file or directory: ...

# --- All built-in exceptions form a hierarchy ---
# BaseException
#  +-- SystemExit
#  +-- KeyboardInterrupt
#  +-- GeneratorExit
#  +-- Exception
#       +-- StopIteration
#       +-- ArithmeticError
#       |    +-- FloatingPointError
#       |    +-- OverflowError
#       |    +-- ZeroDivisionError
#       +-- LookupError
#       |    +-- IndexError
#       |    +-- KeyError
#       +-- ...
print(ZeroDivisionError.__bases__)  # (<class 'ArithmeticError'>,)
print(ArithmeticError.__bases__)    # (<class 'Exception'>,)
