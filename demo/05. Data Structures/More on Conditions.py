# ==============================================================================
# 5.7 More on Conditions
# ==============================================================================
# https://docs.python.org/3/tutorial/datastructures.html#more-on-conditions

# --- The conditions used in while and if statements can contain any operators ---
# not just comparisons.

# --- Comparison operators ---
# in, not in: check whether a value occurs (does not occur) in a sequence
# is, is not: check whether two objects are really the same object

# --- All comparison operators have the same priority ---
# which is lower than that of all numerical operators.

# --- Comparisons can be chained ---
# For example, a < b == c tests whether a is less than b and moreover b equals c.

x = 2
print(1 < x < 3)    # True  (equivalent to: 1 < x and x < 3)
print(1 < x > 0)    # True  (equivalent to: 1 < x and x > 0)
print(0 < x < 1)    # False

# --- Comparisons may be combined with Boolean operators: and, or, not ---
# not has the highest priority, and or the lowest.
# A and not B or C is equivalent to (A and (not B)) or C.

# --- 'and' and 'or' are short-circuit operators ---
# Their operands are evaluated from left to right, and evaluation stops
# as soon as the outcome is determined.

# Examples of short-circuiting:
print(True and False)   # False  (doesn't evaluate beyond 'False')
print(False or True)    # True
print(not True)         # False

# --- Short-circuiting with side effects ---
# It is possible to assign the result of a comparison or other Boolean expression
# to a variable.

string1, string2, string3 = '', 'Trondheim', 'Hammer Dance'
non_null = string1 or string2 or string3
print(non_null)  # Trondheim
# string1 is empty (falsy), so string2 is evaluated; non-null, so it's returned.

# --- Comparing different types ---
# Comparisons can be made between different types:
print(1 < 2)       # True
print(2 == 2.0)    # True (int and float can be compared numerically)
print('a' < 'b')   # True (strings compared lexicographically)

# --- The in and not in operators ---
print('a' in 'abc')       # True
print('d' not in 'abc')   # True
print(1 in [1, 2, 3])     # True

# --- The is and is not operators ---
# Test for object identity (same object in memory)
a = [1, 2, 3]
b = [1, 2, 3]
c = a
print(a == b)    # True  (same value)
print(a is b)    # False (different objects)
print(a is c)    # True  (same object)

# --- Common pitfall: is vs == ---
# Use 'is' for None comparisons, '==' for value comparisons
x = None
print(x is None)  # True  (recommended way to check for None)
