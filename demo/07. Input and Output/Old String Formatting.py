# ==============================================================================
# 7.1.4 Old String Formatting
# ==============================================================================
# https://docs.python.org/3/tutorial/inputoutput.html#old-string-formatting

# The % operator (modulo) can also be used for string formatting.
# Given format % values, the % conversion specifications in format are
# replaced with zero or more elements of values.
# This operation is commonly known as string interpolation.

import math

# --- Basic % formatting ---
print('The value of pi is approximately %5.3f.' % math.pi)
# The value of pi is approximately 3.142.

# --- Multiple values with % formatting ---
print('Hello, %s! You have %d messages.' % ('Alice', 5))
# Hello, Alice! You have 5 messages.

# --- Using a tuple for multiple values ---
print('%s %s' % ('Hello', 'World'))  # Hello World

# --- Using a dictionary with %(key)s format ---
print('%(name)s is %(age)d years old.' % {'name': 'Bob', 'age': 30})
# Bob is 30 years old.

# --- Common format specifiers ---
# %s - string
# %d - integer
# %f - floating point
# %x - hexadecimal
# %o - octal
# %e - exponential notation
# %r - repr()

print('%10s' % 'test')    #       test  (right-justified, width 10)
print('%-10s' % 'test')   # test        (left-justified, width 10)
print('%05d' % 42)        # 00042  (zero-padded, width 5)
print('%.2f' % 3.14159)   # 3.14  (2 decimal places)
print('%+d' % 42)         # +42  (always show sign)
