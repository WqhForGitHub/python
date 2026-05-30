# ==============================================================================
# 3.1 Using Python as a Calculator  Numbers
# ==============================================================================
# https://docs.python.org/3/tutorial/introduction.html#numbers

# --- Basic arithmetic ---
# Addition
print(2 + 2)        # 4

# Subtraction
print(50 - 5 * 6)   # 20

# Multiplication and division have higher precedence
print(8 / 5)         # 1.6  (division always returns a float)

# --- Floor division and modulo ---
print(17 / 3)        # 5.666666666666667  (classic division returns float)
print(17 // 3)       # 5   (floor division discards the fractional part)
print(17 % 3)        # 2   (the modulo operator returns the remainder)
print(5 ** 2)        # 25  (5 squared)
print(2 ** 7)        # 128 (2 to the 7th power)

# --- Mixed-type arithmetic ---
# When mixing int and float, the result is always float
print(4 * 3.75 - 1)  # 14.0

# --- Variable assignment ---
width = 20
height = 5 * 9
print(width * height)  # 900

# --- If a variable is not "defined" (assigned a value), using it is an error ---
# Uncomment the following line to see the NameError:
# n  # NameError: name 'n' is not defined

# --- Floats ---
# Floating point arithmetic can have rounding issues
print(0.1 + 0.2)     # 0.30000000000000004
print(0.1 + 0.2 == 0.3)  # False

# Python provides useful tools for exact decimal arithmetic via the decimal module
from decimal import Decimal
print(Decimal('0.1') + Decimal('0.2'))  # 0.3

# --- Last printed expression: _ ---
# In interactive mode, the last printed expression is assigned to the variable _
tax = 12.5 / 100
price = 100.50
print(price * tax)    # 12.5625
# In interactive mode: price + _ would give 113.0625
# Note: _ only works in the interactive interpreter, not in scripts.

# --- Complex numbers ---
# Complex numbers are also supported; the imaginary part is written with a "j" suffix
print(3 + 4j)         # (3+4j)
print((3 + 4j).real)  # 3.0
print((3 + 4j).imag)  # 4.0
print(abs(3 + 4j))    # 5.0  (magnitude: sqrt(3^2 + 4^2))
