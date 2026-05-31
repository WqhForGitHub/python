# ==============================================================================
# 7.1.1 Formatted String Literals
# ==============================================================================
# https://docs.python.org/3/tutorial/inputoutput.html#formatted-string-literals

# Formatted string literals (f-strings) let you include the value of Python
# expressions inside a string by prefixing the string with f or F and writing
# expressions as {expression}.

# --- Basic f-string usage ---
year = 2016
event = 'Referendum'
print(f'Results of the {year} {event}')  # Results of the 2016 Referendum

# --- Format specifiers ---
# An optional format specifier can follow the expression after a colon ':'
import math
print(f'The value of pi is approximately {math.pi:.3f}.')
# The value of pi is approximately 3.142.

# --- Minimum field width ---
# Passing an integer after the ':' sets the minimum number of characters wide
# This is useful for making columns line up
table = {'Sjoerd': 4127, 'Jack': 4098, 'Dcab': 7678}
for name, phone in table.items():
    print(f'{name:10} ==> {phone:10d}')
# Output:
# Sjoerd     ==>       4127
# Jack       ==>       4098
# Dcab       ==>       7678

# --- Conversion modifiers ---
# '!a' applies ascii(), '!s' applies str(), '!r' applies repr()
animals = 'eels'
print(f'My hovercraft is full of {animals}.')   # My hovercraft is full of eels.
print(f'My hovercraft is full of {animals!r}.')  # My hovercraft is full of 'eels'.

# --- Self-documenting expressions with '=' ---
# The '=' specifier expands to the expression text, an equal sign, and the repr
bugs = 'roaches'
count = 13
area = 'living room'
print(f'Debugging {bugs=} {count=} {area=}')
# Debugging bugs='roaches' count=13 area='living room'
