# ==============================================================================
# 5.1 More on Lists
# ==============================================================================
# https://docs.python.org/3/tutorial/datastructures.html#more-on-lists

# --- List methods ---
# The list data type has several more methods.

# --- list.append(x): Add an item to the end of the list ---
# Equivalent to a[len(a):] = [x]
fruits = ['orange', 'apple', 'pear', 'banana', 'kiwi', 'apple', 'banana']
fruits.append('grape')
print(fruits)  # ['orange', 'apple', 'pear', 'banana', 'kiwi', 'apple', 'banana', 'grape']

# --- list.extend(iterable): Extend the list by appending all items from the iterable ---
# Equivalent to a[len(a):] = iterable
more_fruits = ['mango', 'pineapple']
fruits.extend(more_fruits)
print(fruits)  # [..., 'grape', 'mango', 'pineapple']

# --- list.insert(i, x): Insert an item at a given position ---
# a.insert(0, x) inserts at the front; a.insert(len(a), x) is equivalent to a.append(x)
fruits.insert(0, 'strawberry')
print(fruits)  # ['strawberry', 'orange', ...]

# --- list.remove(x): Remove the first occurrence of x ---
# Raises ValueError if x is not present
fruits.remove('apple')
print(fruits)  # first 'apple' is removed; second 'apple' remains

# --- list.pop([i]): Remove the item at the given position and return it ---
# If no index is specified, pop() removes and returns the last item
last = fruits.pop()
print(last)     # pineapple
print(fruits)   # pineapple is gone

# --- list.clear(): Remove all items from the list ---
# Equivalent to del a[:]
test_list = [1, 2, 3]
test_list.clear()
print(test_list)  # []

# --- list.index(x[, start[, end]]): Return zero-based index of the first occurrence ---
fruits2 = ['orange', 'apple', 'pear', 'banana', 'kiwi', 'apple', 'banana']
print(fruits2.index('apple'))       # 1 (first occurrence)
print(fruits2.index('apple', 2))    # 5 (search starts at index 2)
print(fruits2.index('banana', 2, 6))  # 3 (search in slice [2:6])

# --- list.count(x): Return the number of times x appears in the list ---
print(fruits2.count('apple'))   # 2
print(fruits2.count('banana'))  # 2
print(fruits2.count('cherry'))  # 0

# --- list.sort(*, key=None, reverse=False): Sort the items in place ---
numbers = [3, 1, 4, 1, 5, 9, 2, 6]
numbers.sort()
print(numbers)  # [1, 1, 2, 3, 4, 5, 6, 9]

numbers.sort(reverse=True)
print(numbers)  # [9, 6, 5, 4, 3, 2, 1, 1]

# --- list.reverse(): Reverse the elements in place ---
letters = ['a', 'b', 'c', 'd']
letters.reverse()
print(letters)  # ['d', 'c', 'b', 'a']

# --- list.copy(): Return a shallow copy of the list ---
# Equivalent to a[:] or list(a)
original = [1, 2, 3]
copy = original.copy()
copy.append(4)
print(original)  # [1, 2, 3]  (original is unchanged)
print(copy)      # [1, 2, 3, 4]

# --- Summary of list methods that modify the list in place ---
# append(), extend(), insert(), remove(), pop(), clear(), sort(), reverse()
# These return None (except pop which returns the removed item).

# --- An example that uses most list methods ---
a = [66.25, 333, 333, 1, 1234.5]
print(a.count(333), a.count(66.25), a.count('x'))  # 2 1 0

a.insert(2, -1)
a.append(333)
print(a)  # [66.25, 333, -1, 333, 1, 1234.5, 333]

print(a.index(333))  # 1

a.remove(333)
print(a)  # [66.25, -1, 333, 1, 1234.5, 333]

a.reverse()
print(a)  # [333, 1234.5, 1, 333, -1, 66.25]

a.sort()
print(a)  # [-1, 1, 66.25, 333, 333, 1234.5]

print(a.pop())  # 1234.5
print(a)  # [-1, 1, 66.25, 333, 333]

# ==============================================================================
# 5.1.1 Using Lists as Stacks
# ==============================================================================
# https://docs.python.org/3/tutorial/datastructures.html#using-lists-as-stacks

# --- The list methods make it very easy to use a list as a stack ---
# Last-in, first-out (LIFO). Use append() to push, pop() to pop.

stack = [3, 4, 5]
stack.append(6)
stack.append(7)
print(stack)  # [3, 4, 5, 6, 7]

print(stack.pop())  # 7
print(stack)        # [3, 4, 5, 6]

print(stack.pop())  # 6
print(stack.pop())  # 5
print(stack)        # [3, 4]

# ==============================================================================
# 5.1.2 Using Lists as Queues
# ==============================================================================
# https://docs.python.org/3/tutorial/datastructures.html#using-lists-as-queues

# --- Lists are not efficient for queues ---
# While append() and pop(0) work, pop(0) is O(n) because all elements must shift.

# --- Use collections.deque for efficient queue operations ---
from collections import deque

queue = deque(["Eric", "John", "Michael"])
queue.append("Terry")           # Terry arrives
queue.append("Graham")          # Graham arrives
print(queue)                    # deque(['Eric', 'John', 'Michael', 'Terry', 'Graham'])

print(queue.popleft())          # Eric  (first to arrive, first out)
print(queue)                    # deque(['John', 'Michael', 'Terry', 'Graham'])

print(queue.popleft())          # John
print(queue)                    # deque(['Michael', 'Terry', 'Graham'])

# ==============================================================================
# 5.1.3 List Comprehensions
# ==============================================================================
# https://docs.python.org/3/tutorial/datastructures.html#list-comprehensions

# --- List comprehensions provide a concise way to create lists ---
# Common use: making new lists where each element is the result of some operation
# applied to each member of another sequence or iterable,
# or to create a subsequence of those elements that satisfy a certain condition.

# --- Without list comprehension ---
squares = []
for x in range(10):
    squares.append(x**2)
print(squares)  # [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]

# --- With list comprehension ---
squares = [x**2 for x in range(10)]
print(squares)  # [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]

# --- Also equivalent using map() ---
squares = list(map(lambda x: x**2, range(10)))
print(squares)  # [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]

# --- List comprehension with a condition ---
# A list comprehension consists of brackets containing an expression followed
# by a for clause, then zero or more for or if clauses.

# [(x, y) for x in [1,2,3] for y in [3,1,4] if x != y]
# is equivalent to:
combs = []
for x in [1, 2, 3]:
    for y in [3, 1, 4]:
        if x != y:
            combs.append((x, y))
print(combs)  # [(1, 3), (1, 4), (2, 3), (2, 1), (2, 4), (3, 1), (3, 4)]

# The list comprehension version is more concise:
combs = [(x, y) for x in [1, 2, 3] for y in [3, 1, 4] if x != y]
print(combs)  # [(1, 3), (1, 4), (2, 3), (2, 1), (2, 4), (3, 1), (3, 4)]

# --- More examples ---

# Create a new list with values doubled
vec = [-4, -2, 0, 2, 4]
doubled = [x * 2 for x in vec]
print(doubled)  # [-8, -4, 0, 4, 8]

# Filter the list to exclude negative numbers
positive = [x for x in vec if x >= 0]
print(positive)  # [0, 2, 4]

# Apply a function to all elements
abs_values = [abs(x) for x in vec]
print(abs_values)  # [4, 2, 0, 2, 4]

# Call a method on each element
freshfruit = ['  banana', '  loganberry ', 'passion fruit  ']
stripped = [weapon.strip() for weapon in freshfruit]
print(stripped)  # ['banana', 'loganberry', 'passion fruit']

# Create a list of 2-tuples like (number, square)
pairs = [(x, x**2) for x in range(6)]
print(pairs)  # [(0, 0), (1, 1), (2, 4), (3, 9), (4, 16), (5, 25)]

# The tuple must be parenthesized, otherwise a SyntaxError is raised
# [x, x**2 for x in range(6)]  # SyntaxError: invalid syntax

# Flatten a list using a list comprehension with two 'for'
vec = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
flat = [num for elem in vec for num in elem]
print(flat)  # [1, 2, 3, 4, 5, 6, 7, 8, 9]

# ==============================================================================
# 5.1.4 Nested List Comprehensions
# ==============================================================================
# https://docs.python.org/3/tutorial/datastructures.html#nested-list-comprehensions

# --- The initial expression in a list comprehension can be any expression ---
# Including another list comprehension.

# --- Example: transpose a 3x4 matrix ---
matrix = [
    [1, 2, 3, 4],
    [5, 6, 7, 8],
    [9, 10, 11, 12],
]

# Using nested list comprehension:
transposed = [[row[i] for row in matrix] for i in range(4)]
print(transposed)  # [[1, 5, 9], [2, 6, 10], [3, 7, 11], [4, 8, 12]]

# This is equivalent to:
transposed = []
for i in range(4):
    transposed.append([row[i] for row in matrix])
print(transposed)  # [[1, 5, 9], [2, 6, 10], [3, 7, 11], [4, 8, 12]]

# Which is also equivalent to:
transposed = []
for i in range(4):
    # the following 3 lines implement the nested listcomp
    transposed_row = []
    for row in matrix:
        transposed_row.append(row[i])
    transposed.append(transposed_row)
print(transposed)  # [[1, 5, 9], [2, 6, 10], [3, 7, 11], [4, 8, 12]]

# --- In the real world, you should prefer built-in functions over complex flow statements ---
# The zip() function would do a great job for this use case:
print(list(zip(*matrix)))  # [(1, 5, 9), (2, 6, 10), (3, 7, 11), (4, 8, 12)]
