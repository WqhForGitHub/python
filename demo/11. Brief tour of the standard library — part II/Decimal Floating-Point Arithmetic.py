# ==============================================================================
# 11.8 Decimal Floating-Point Arithmetic
# ==============================================================================
# https://docs.python.org/3/tutorial/stdlib2.html#decimal-floating-point-arithmetic

# --- The decimal module: exact decimal representation ---
from decimal import *

# The decimal module offers a Decimal datatype for decimal floating-point
# arithmetic. Compared to the built-in float implementation of binary
# floating point, the class is especially helpful for:
#
# - financial applications and other uses which require exact decimal
#   representation,
# - control over precision,
# - control over rounding to meet legal or regulatory requirements,
# - tracking of significant decimal places, or
# - applications where the user expects the results to match calculations
#   done by hand.

# --- Decimal vs float: rounding differences ---
# Calculating a 5% tax on a 70 cent phone charge:
print(round(Decimal('0.70') * Decimal('1.05'), 2))   # Decimal('0.74')
print(round(.70 * 1.05, 2))                          # 0.73

# The Decimal result keeps a trailing zero, automatically inferring four
# place significance from multiplicands with two place significance.
# Decimal reproduces mathematics as done by hand and avoids issues that
# can arise when binary floating point cannot exactly represent decimal
# quantities.

# --- Exact representation: modulo and equality ---
print(Decimal('1.00') % Decimal('.10'))   # Decimal('0.00')
print(1.00 % 0.10)                        # 0.09999999999999995

print(sum([Decimal('0.1')] * 10) == Decimal('1.0'))   # True
print(0.1 + 0.1 + 0.1 + 0.1 + 0.1 +
      0.1 + 0.1 + 0.1 + 0.1 + 0.1 == 1.0)            # False

# --- Controlling precision ---
# The decimal module provides arithmetic with as much precision as needed:
getcontext().prec = 36
print(Decimal(1) / Decimal(7))
# Decimal('0.142857142857142857142857142857142857')
