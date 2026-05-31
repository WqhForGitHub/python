# ==============================================================================
# 5.3 Tuples and Sequences
# ==============================================================================
# https://docs.python.org/3/tutorial/datastructures.html#tuples-and-sequences

# --- A tuple consists of a number of values separated by commas ---
t = 12345, 54321, 'hello!'
print(t[0])  # 12345
print(t)     # (12345, 54321, 'hello!')

# --- Tuples may be nested ---
u = t, (1, 2, 3, 4, 5)
print(u)  # ((12345, 54321, 'hello!'), (1, 2, 3, 4, 5))

# --- Tuples are immutable: you can't assign to individual items ---
# t[0] = 88888  # TypeError: 'tuple' object does not support item assignment

# --- But tuples can contain mutable objects ---
v = ([1, 2, 3], [3, 2, 1])
print(v)  # ([1, 2, 3], [3, 2, 1])
v[0][0] = 99  # This works because we're modifying the list, not the tuple
print(v)  # ([99, 2, 3], [3, 2, 1])

# --- Tuples vs Lists ---
# Tuples are immutable, and usually contain a heterogeneous sequence of elements
# that are accessed via unpacking or indexing.
# Lists are mutable, and their elements are usually homogeneous and are
# accessed by iterating over the list.

# --- Empty and singleton tuples ---
empty = ()
print(len(empty))  # 0

singleton = 'hello',    # <-- note trailing comma
print(len(singleton))  # 1
print(singleton)        # ('hello',)

# The trailing comma is required for a singleton tuple:
# 'hello' (without comma) is just a string in parentheses, not a tuple
not_a_tuple = ('hello')
print(type(not_a_tuple))  # <class 'str'>

is_a_tuple = ('hello',)
print(type(is_a_tuple))   # <class 'tuple'>

# --- Tuple packing ---
t = 12345, 54321, 'hello!'  # This is called "tuple packing"

# --- Sequence unpacking (the reverse of tuple packing) ---
x, y, z = t
print(x)  # 12345
print(y)  # 54321
print(z)  # hello!

# Sequence unpacking requires that there are as many variables on the left
# side of the equals sign as there are elements in the sequence.
# x, y = t  # ValueError: too many values to unpack

# --- Multiple assignment using tuple unpacking ---
a, b = 1, 2
print(a, b)  # 1 2

# Swap variables without a temporary variable
a, b = b, a
print(a, b)  # 2 1

# --- Extended unpacking with * ---
first, *rest = range(5)
print(first)  # 0
print(rest)   # [1, 2, 3, 4]

*beginning, last = range(5)
print(beginning)  # [0, 1, 2, 3]
print(last)       # 4

first, *middle, last = range(5)
print(first)   # 0
print(middle)  # [1, 2, 3]
print(last)    # 4
