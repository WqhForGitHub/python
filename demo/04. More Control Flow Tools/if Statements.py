# ==============================================================================
# 4.1 if Statements
# ==============================================================================
# https://docs.python.org/3/tutorial/controlflow.html#if-statements

# --- Basic if statement ---
x = int(42)
if x < 0:
    print('Negative changed to zero')
elif x == 0:
    print('Zero')
elif x == 1:
    print('Single')
else:
    print('More')
# Output: More

# --- The if...elif...else chain ---
# There can be zero or more elif parts, and the else part is optional.
# An if...elif...elif... sequence is a substitute for switch/case in other languages.

# --- Only one branch is executed ---
# At most one branch is executed; it is the first one with a true condition.
x = 5
if x < 0:
    print('negative')
elif x == 0:
    print('zero')
elif x <= 5:
    print('five or less')
else:
    print('more than five')
# Output: five or less

# --- Comparison operators ---
# ==  equal
# !=  not equal
# <   less than
# >   greater than
# <=  less than or equal
# >=  greater than or equal
# is  object identity
# is not  negated object identity

# --- Boolean operators ---
# and, or, not
x = 3
if x > 0 and x < 10:
    print('x is a positive single-digit number')
# Output: x is a positive single-digit number

# --- Chained comparisons ---
# Comparisons can be chained: a < b == c tests whether a is less than b
# and moreover b equals c.
x = 5
if 0 < x < 10:
    print('x is between 0 and 10')
# Output: x is between 0 and 10

# --- Truth value testing ---
# The following values are considered false:
#   None, False, zero of any numeric type (0, 0.0, 0j),
#   empty sequences ('', (), []), empty mappings ({})
# Everything else is considered true.

# --- Simple one-liner if ---
if True:
    print('This always prints')
# Output: This always prints

# --- No switch/case statement in Python ---
# Use if...elif...elif... as a substitute, or match (Python 3.10+)
