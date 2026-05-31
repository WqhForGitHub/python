# ==============================================================================
# 5.5 Dictionaries
# ==============================================================================
# https://docs.python.org/3/tutorial/datastructures.html#dictionaries

# --- Dictionaries are indexed by keys, which must be immutable ---
# A dictionary is an unordered set of key: value pairs.
# Keys must be of an immutable type (string, number, tuple with immutable elements).
# Dictionaries are mutable.

# --- Creating a dictionary ---
tel = {'jack': 4098, 'sape': 4139}
print(tel)  # {'jack': 4098, 'sape': 4139}

# --- Accessing a value by key ---
print(tel['jack'])  # 4098

# --- Adding / modifying an entry ---
tel['guido'] = 4127
print(tel)  # {'jack': 4098, 'sape': 4139, 'guido': 4127}

tel['jack'] = 1111  # Overwrite existing key
print(tel['jack'])  # 1111

# --- Deleting an entry ---
del tel['sape']
print(tel)  # {'jack': 1111, 'guido': 4127}

# --- dict() constructor from key-value pairs ---
tel2 = dict([('sape', 4139), ('guido', 4127), ('jack', 4098)])
print(tel2)  # {'sape': 4139, 'guido': 4127, 'jack': 4098}

# --- dict() with keyword arguments ---
tel3 = dict(sape=4139, guido=4127, jack=4098)
print(tel3)  # {'sape': 4139, 'guido': 4127, 'jack': 4098}

# --- Checking if a key is in the dictionary ---
print('jack' in tel)    # True
print('irv' in tel)     # False

# --- dict.keys(), dict.values(), dict.items() ---
tel = {'jack': 4098, 'sape': 4139, 'guido': 4127}
print(list(tel.keys()))    # ['jack', 'sape', 'guido']
print(list(tel.values()))  # [4098, 4139, 4127]
print(list(tel.items()))   # [('jack', 4098), ('sape', 4139), ('guido', 4127)]

# --- Dictionary comprehensions ---
# Dict comprehensions can be used to create dictionaries from arbitrary
# key and value expressions:
squares = {x: x**2 for x in (2, 4, 6)}
print(squares)  # {2: 4, 4: 16, 6: 36}

# --- dict.get(key[, default]) ---
# Return the value for key if key is in the dictionary, else default.
tel = {'jack': 4098, 'sape': 4139}
print(tel.get('jack'))       # 4098
print(tel.get('irv'))        # None  (default when key not found)
print(tel.get('irv', 0))     # 0     (custom default)

# --- dict.setdefault(key[, default]) ---
# If key is in the dictionary, return its value.
# If not, insert key with a value of default and return default.
d = {}
d.setdefault('a', 1)  # Returns 1 and sets d['a'] = 1
print(d)  # {'a': 1}
d.setdefault('a', 99)  # Returns 1 (existing value, not changed)
print(d)  # {'a': 1}

# --- dict.update([other]) ---
# Update the dictionary with the key/value pairs from other.
d = {'a': 1, 'b': 2}
d.update({'b': 3, 'c': 4})
print(d)  # {'a': 1, 'b': 3, 'c': 4}

# --- dict.pop(key[, default]) ---
# If key is in the dictionary, remove it and return its value.
d = {'a': 1, 'b': 2, 'c': 3}
print(d.pop('b'))  # 2
print(d)  # {'a': 1, 'c': 3}

# --- dict.popitem() ---
# Remove and return a (key, value) pair from the dictionary.
# Pairs are returned in LIFO order (last-in, first-out).
d = {'a': 1, 'b': 2, 'c': 3}
print(d.popitem())  # ('c', 3)  (last inserted)
print(d)  # {'a': 1, 'b': 2}

# --- dict.clear() ---
# Remove all items from the dictionary.
d = {'a': 1, 'b': 2}
d.clear()
print(d)  # {}

# --- Looping over dictionaries ---
knights = {'gallahad': 'the pure', 'robin': 'the brave'}
for k, v in knights.items():
    print(k, v)
# Output:
# gallahad the pure
# robin the brave

# --- When looping through a sequence, the position index and value can be retrieved ---
# using the enumerate() function (already covered, but here's a dict example):
for i, (k, v) in enumerate(knights.items()):
    print(i, k, v)
# Output:
# 0 gallahad the pure
# 1 robin the brave
