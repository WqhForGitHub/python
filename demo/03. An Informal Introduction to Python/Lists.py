# ==============================================================================
# 3.1.3 Lists
# ==============================================================================
# https://docs.python.org/3/tutorial/introduction.html#lists

# --- Creating lists ---
# Lists are written as comma-separated values between square brackets
squares = [1, 4, 9, 16, 25]
print(squares)  # [1, 4, 9, 16, 25]

# --- List indexing (same as strings) ---
print(squares[0])   # 1   (first element)
print(squares[-1])  # 25  (last element)

# --- List slicing ---
print(squares[1:3])  # [4, 9]  (elements from index 1 to 2)
print(squares[:3])   # [1, 4, 9]  (from beginning to index 2)
print(squares[2:])   # [9, 16, 25]  (from index 2 to end)
print(squares[-3:])  # [9, 16, 25]  (last three elements)

# --- Slicing returns a new list (shallow copy) ---
print(squares[:])    # [1, 4, 9, 16, 25]  (a copy of the entire list)

# --- Lists are mutable (unlike strings) ---
cubes = [1, 8, 27, 65, 125]  # Oops, 4^3 = 64, not 65
cubes[3] = 64               # Replace the wrong value
print(cubes)  # [1, 8, 27, 64, 125]

# --- Adding elements to the end of a list: append() ---
cubes.append(216)  # 6^3
cubes.append(7 ** 3)  # 7^3
print(cubes)  # [1, 8, 27, 64, 125, 216, 343]

# --- Assignment to slices ---
letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g']
print(letters)  # ['a', 'b', 'c', 'd', 'e', 'f', 'g']

# Replace some values
letters[2:5] = ['C', 'D', 'E']
print(letters)  # ['a', 'b', 'C', 'D', 'E', 'f', 'g']

# Remove some values (assign an empty list to a slice)
letters[2:5] = []
print(letters)  # ['a', 'b', 'f', 'g']

# Clear the entire list
letters[:] = []
print(letters)  # []

# --- Built-in len() function ---
letters = ['a', 'b', 'c', 'd']
print(len(letters))  # 4

# --- Nested lists ---
# Lists can contain other lists (or any type)
a = ['a', 'b', 'c']
n = [1, 2, 3]
x = [a, n]
print(x)        # [['a', 'b', 'c'], [1, 2, 3]]
print(x[0])     # ['a', 'b', 'c']
print(x[0][1])  # 'b'

# --- List concatenation ---
print([1, 2, 3] + [4, 5, 6])  # [1, 2, 3, 4, 5, 6]

# --- List repetition ---
print([1, 2, 3] * 3)  # [1, 2, 3, 1, 2, 3, 1, 2, 3]

# --- Other useful list operations ---
fruits = ['banana', 'apple', 'cherry']
fruits.insert(1, 'orange')      # Insert at index 1
print(fruits)  # ['banana', 'orange', 'apple', 'cherry']

removed = fruits.pop()           # Remove and return last element
print(removed)  # cherry
print(fruits)   # ['banana', 'orange', 'apple']

fruits.sort()
print(fruits)   # ['apple', 'banana', 'orange']

fruits.reverse()
print(fruits)   # ['orange', 'banana', 'apple']

print('banana' in fruits)  # True  (membership test)
