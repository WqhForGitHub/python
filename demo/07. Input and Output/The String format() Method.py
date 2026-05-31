# ==============================================================================
# 7.1.2 The String format() Method
# ==============================================================================
# https://docs.python.org/3/tutorial/inputoutput.html#the-string-format-method

# --- Basic usage ---
# The brackets and characters within them (format fields) are replaced with
# the objects passed into str.format()
print('We are the {} who say "{}!"'.format('knights', 'Ni'))
# We are the knights who say "Ni!"

# --- Positional arguments ---
# A number in the brackets refers to the position of the object
print('{0} and {1}'.format('spam', 'eggs'))  # spam and eggs
print('{1} and {0}'.format('spam', 'eggs'))  # eggs and spam

# --- Keyword arguments ---
print('This {food} is {adjective}.'.format(
    food='spam', adjective='absolutely horrible'))
# This spam is absolutely horrible.

# --- Combining positional and keyword arguments ---
print('The story of {0}, {1}, and {other}.'.format('Bill', 'Manfred',
                                                     other='Georg'))
# The story of Bill, Manfred, and Georg.

# --- Referencing dict keys with square brackets ---
table = {'Sjoerd': 4127, 'Jack': 4098, 'Dcab': 8637678}
print('Jack: {0[Jack]:d}; Sjoerd: {0[Sjoerd]:d}; '
      'Dcab: {0[Dcab]:d}'.format(table))
# Jack: 4098; Sjoerd: 4127; Dcab: 8637678

# --- Using ** to unpack a dictionary as keyword arguments ---
table = {'Sjoerd': 4127, 'Jack': 4098, 'Dcab': 8637678}
print('Jack: {Jack:d}; Sjoerd: {Sjoerd:d}; Dcab: {Dcab:d}'.format(**table))
# Jack: 4098; Sjoerd: 4127; Dcab: 8637678

# This is particularly useful in combination with vars(), which returns a
# dictionary containing all local variables.

# --- Aligned columns with format() ---
for x in range(1, 11):
    print('{0:2d} {1:3d} {2:4d}'.format(x, x*x, x*x*x))
# Output:
#  1   1    1
#  2   4    8
#  3   9   27
#  4  16   64
#  5  25  125
#  6  36  216
#  7  49  343
#  8  64  512
#  9  81  729
# 10 100 1000
