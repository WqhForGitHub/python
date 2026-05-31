# ==============================================================================
# 5.4 Sets
# ==============================================================================
# https://docs.python.org/3/tutorial/datastructures.html#sets

# --- A set is an unordered collection with no duplicate elements ---
# Basic uses include membership testing and eliminating duplicate entries.
# Set objects also support mathematical operations like union, intersection,
# difference, and symmetric difference.

# --- Creating sets ---
# Curly braces or the set() function can be used to create sets.
# Note: to create an empty set you have to use set(), not {};
# the latter creates an empty dictionary.

basket = {'apple', 'orange', 'apple', 'pear', 'orange', 'banana'}
print(basket)  # {'orange', 'banana', 'pear', 'apple'}  (duplicates removed, order not guaranteed)

# --- Empty set vs empty dict ---
empty_set = set()
empty_dict = {}
print(type(empty_set))  # <class 'set'>
print(type(empty_dict))  # <class 'dict'>

# --- Membership testing ---
print('orange' in basket)   # True
print('crabgrass' in basket)  # False

# --- Set from a list (eliminate duplicates) ---
a = set('abracadabra')
b = set('alacazam')
print(a)  # {'a', 'd', 'b', 'c', 'r'}  (unique letters in 'abracadabra')
print(b)  # {'a', 'm', 'c', 'l', 'z'}  (unique letters in 'alacazam')

# --- Set operations ---
# Letters in a but not in b (difference)
print(a - b)  # {'d', 'b', 'r'}

# Letters in a or b or both (union)
print(a | b)  # {'a', 'd', 'b', 'c', 'r', 'm', 'l', 'z'}

# Letters in both a and b (intersection)
print(a & b)  # {'a', 'c'}

# Letters in a or b but not both (symmetric difference)
print(a ^ b)  # {'d', 'b', 'r', 'm', 'l', 'z'}

# --- Set comprehensions ---
a_comprehension = {x for x in 'abracadabra' if x not in 'abc'}
print(a_comprehension)  # {'d', 'r'}

# --- Set methods ---
s = {1, 2, 3}
s.add(4)
print(s)  # {1, 2, 3, 4}

s.discard(4)  # Remove 4 if present; no error if not
print(s)  # {1, 2, 3}

s.remove(3)  # Remove 3; raises KeyError if not present
print(s)  # {1, 2}

# s.remove(99)  # KeyError: 99
s.discard(99)  # No error

# --- frozenset: immutable set ---
# A frozenset is a set that cannot be changed after creation.
fs = frozenset([1, 2, 3])
print(fs)  # frozenset({1, 2, 3})
# fs.add(4)  # AttributeError: 'frozenset' object has no attribute 'add'
