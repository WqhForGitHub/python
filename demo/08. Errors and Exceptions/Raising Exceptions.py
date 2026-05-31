# ==============================================================================
# 8.4 Raising Exceptions
# ==============================================================================
# https://docs.python.org/3/tutorial/errors.html#raising-exceptions

# --- The raise statement ---
# The raise statement allows the programmer to force a specified exception to occur.
# raise NameError('HiThere')
# Traceback (most recent call last):
#   File "<stdin>", line 1, in <module>
# NameError: HiThere

# --- The sole argument to raise is the exception to be raised ---
# This must be either an exception instance or an exception class
# (a class that derives from BaseException).

# Using an exception instance:
# exc = ValueError('invalid value')
# raise exc

# Using an exception class (shorthand - creates an instance automatically):
# raise ValueError  # equivalent to raise ValueError()

# --- Re-raising an exception ---
# If you need to determine whether an exception was raised but don't intend
# to handle it, a simpler form of the raise statement allows you to re-raise:
try:
    try:
        1 / 0
    except ZeroDivisionError:
        print('Caught a division error, re-raising...')
        raise
except ZeroDivisionError:
    print('Re-raised exception caught in outer handler')
# Output:
# Caught a division error, re-raising...
# Re-raised exception caught in outer handler

# --- Raising a different exception ---
# You can catch one exception and raise a different one:
try:
    try:
        value = int('not_a_number')
    except ValueError:
        raise TypeError('Expected a numeric type')
except TypeError as e:
    print(f'Caught: {e}')
# Output: Caught: Expected a numeric type

# --- Exception arguments ---
# Exceptions can take arguments to provide detail about the error:
try:
    raise ValueError('The value must be positive', 42)
except ValueError as e:
    print(f'Exception type: {type(e).__name__}')
    print(f'Exception args: {e.args}')
    print(f'String representation: {str(e)}')
# Output:
# Exception type: ValueError
# Exception args: ('The value must be positive', 42)
# String representation: ('The value must be positive', 42)

# --- Practical example: input validation ---
def set_age(age):
    if not isinstance(age, int):
        raise TypeError('Age must be an integer')
    if age < 0:
        raise ValueError('Age cannot be negative')
    if age > 150:
        raise ValueError('Age seems unrealistic')
    print(f'Age set to {age}')

try:
    set_age(-5)
except (TypeError, ValueError) as e:
    print(f'Invalid age: {e}')
# Output: Invalid age: Age cannot be negative

try:
    set_age('twenty')
except (TypeError, ValueError) as e:
    print(f'Invalid age: {e}')
# Output: Invalid age: Age must be an integer

set_age(25)  # Age set to 25
