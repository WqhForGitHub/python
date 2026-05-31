# ==============================================================================
# 5.6 Looping Techniques
# ==============================================================================
# https://docs.python.org/3/tutorial/datastructures.html#looping-techniques

# --- Looping over dictionaries with items() ---
knights = {'gallahad': 'the pure', 'robin': 'the brave'}
for k, v in knights.items():
    print(k, v)
# Output:
# gallahad the pure
# robin the brave

# --- Looping over a sequence with enumerate() ---
# When you need both the index and the value while iterating
for i, v in enumerate(['tic', 'tac', 'toe']):
    print(i, v)
# Output:
# 0 tic
# 1 tac
# 2 toe

# --- Looping over two or more sequences with zip() ---
questions = ['name', 'quest', 'favorite color']
answers = ['lancelot', 'the holy grail', 'blue']
for q, a in zip(questions, answers):
    print('What is your {0}?  It is {1}.'.format(q, a))
# Output:
# What is your name?  It is lancelot.
# What is your quest?  It is the holy grail.
# What is your favorite color?  It is blue.

# --- Note: zip() stops at the shortest sequence ---
a = [1, 2, 3, 4, 5]
b = ['a', 'b', 'c']
print(list(zip(a, b)))  # [(1, 'a'), (2, 'b'), (3, 'c')]  (stops at the shorter)

# --- Looping over a sequence in reverse with reversed() ---
for i in reversed(range(1, 10, 2)):
    print(i, end=' ')
print()  # 9 7 5 3 1

# --- Looping over a sequence in sorted order with sorted() ---
# sorted() returns a new sorted list while leaving the source unaltered
basket = ['apple', 'orange', 'apple', 'pear', 'orange', 'banana']
for f in sorted(set(basket)):
    print(f, end=' ')
print()  # apple banana orange pear

# --- Using sorted() with key function ---
fruits = ['orange', 'apple', 'pear', 'banana', 'kiwi']
for f in sorted(fruits, key=len):
    print(f, end=' ')
print()  # pear kiwi apple banana orange  (sorted by length)

# --- Using set() to eliminate duplicates while sorting ---
# The set() function can be combined with sorted() to iterate over
# unique elements in sorted order (see example above)

# --- It is sometimes tempting to change a list while you are iterating over it ---
# However, it is often simpler and safer to create a new list instead.

import math

# Instead of modifying a list in place during iteration:
raw_data = [56.2, float('nan'), 51.7, 55.3, 52.5, float('nan'), 47.8]

# Filter out NaN values by creating a new list:
filtered_data = []
for value in raw_data:
    if not math.isnan(value):
        filtered_data.append(value)

print(filtered_data)  # [56.2, 51.7, 55.3, 52.5, 47.8]

# The same using a list comprehension (more elegant):
filtered_data = [value for value in raw_data if not math.isnan(value)]
print(filtered_data)  # [56.2, 51.7, 55.3, 52.5, 47.8]
