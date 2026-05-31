# ==============================================================================
# 7.1 Fancier Output Formatting
# ==============================================================================
# https://docs.python.org/3/tutorial/inputoutput.html#fancier-output-formatting

# There are several ways to present the output of a program:
# - Expression statements (in interactive mode)
# - The print() function
# - The write() method of file objects (sys.stdout)
# Often you'll want more control over the formatting of your output than simply
# printing space-separated values.

# --- Overview of formatting methods ---

# 1. Formatted string literals (f-strings): prefix with f or F, use {expression}
year = 2016
event = 'Referendum'
print(f'Results of the {year} {event}')  # Results of the 2016 Referendum

# 2. The str.format() method: use {} as placeholders, provide values as arguments
yes_votes = 42_572_654
total_votes = 85_705_149
percentage = yes_votes / total_votes
print('{:-9} YES votes  {:2.2%}'.format(yes_votes, percentage))
#  42572654 YES votes  49.67%

# 3. Manual string formatting: use string slicing and concatenation
# The string type has methods for padding strings to a given column width.

# --- str() vs repr() ---
# str() returns representations of values which are fairly human-readable
# repr() generates representations which can be read by the interpreter
# For many values (numbers, lists, dicts), both return the same thing
# Strings have two distinct representations

s = 'Hello, world.'
print(str(s))   # Hello, world.
print(repr(s))  # 'Hello, world.'

print(str(1/7))  # 0.14285714285714285

x = 10 * 3.25
y = 200 * 200
s = 'The value of x is ' + repr(x) + ', and y is ' + repr(y) + '...'
print(s)  # The value of x is 32.5, and y is 40000...

# The repr() of a string adds string quotes and backslashes:
hello = 'hello, world\n'
hellos = repr(hello)
print(hellos)  # 'hello, world\n'

# The argument to repr() may be any Python object:
print(repr((x, y, ('spam', 'eggs'))))  # (32.5, 40000, ('spam', 'eggs'))

# --- string.Template ---
# The string module also contains a simple templating approach
from string import Template
t = Template('$name was born in $country')
print(t.substitute(name='Guido', country='the Netherlands'))
# Guido was born in the Netherlands
