# ==============================================================================
# 5.8 Comparing Sequences and Other Types
# ==============================================================================
# https://docs.python.org/3/tutorial/datastructures.html#comparing-sequences-and-other-types

# --- Sequence objects may be compared to other objects with the same sequence type ---
# The comparison uses lexicographical ordering:
# first compare the first two items, if they differ this determines the outcome;
# if they are equal, compare the next two items, and so on.

# --- List comparison (lexicographical) ---
print([1, 2, 3] < [1, 2, 4])    # True  (3 < 4)
print([1, 2, 3] == [1, 2, 3])   # True
print([1, 2, 3] < [1, 2, 3])    # False

# --- Tuple comparison (lexicographical) ---
print((1, 2, 3) < (1, 2, 4))    # True
print((1, 2, 3) == (1, 2, 3))   # True

# --- String comparison (lexicographical) ---
print('ABC' < 'ABD')            # True  ('C' < 'D')
print('ABC' == 'ABC')           # True
print('ABC' < 'ABCD')           # True  (shorter sequence is smaller when prefix matches)

# --- If all items of two sequences compare equal, the shorter sequence is smaller ---
print([1, 2] < [1, 2, 0])      # True  ([1,2] is a prefix of [1,2,0])
print((1, 2) < (1, 2, 0))      # True
print('ab' < 'abc')             # True

# --- If all items compare equal and sequences are the same length, they are equal ---
print([1, 2] == [1, 2])         # True

# --- Mixed types comparison ---
# Comparing items of different types is allowed if the items themselves
# are comparable. Otherwise, TypeError is raised.

# Numeric types can be compared across types:
print(1 < 2.0)    # True (int vs float)

# Strings compare lexicographically using Unicode code point numbers:
print('0' < 'A')  # True  (ord('0')=48, ord('A')=65)

# --- When items are incomparable, TypeError is raised ---
# For example, comparing a number and a string:
# print(1 < 'a')  # TypeError: '<' not supported between instances of 'int' and 'str'

# --- Chained comparisons with sequences ---
print([1, 2, 3] < [1, 2, 4] < [1, 3, 0])  # True

# --- Practical example: sorting a list of tuples ---
# Tuples are compared lexicographically, so this sorts by first element,
# then by second element, etc.
pairs = [(2, 'two'), (1, 'one'), (3, 'three'), (1, 'alpha')]
pairs.sort()
print(pairs)  # [(1, 'alpha'), (1, 'one'), (2, 'two'), (3, 'three')]

# --- Sorting with a key function ---
# To sort by a specific element instead of lexicographic order:
pairs = [(2, 'two'), (1, 'one'), (3, 'three'), (1, 'alpha')]
pairs.sort(key=lambda pair: pair[1])  # sort by second element
print(pairs)  # [(1, 'alpha'), (3, 'three'), (1, 'one'), (2, 'two')]
