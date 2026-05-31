# ==============================================================================
# 5.2 The del Statement
# ==============================================================================
# https://docs.python.org/3/tutorial/datastructures.html#the-del-statement

# --- del: remove an item from a list given its index (not its value) ---
# Unlike pop(), del does not return a value.

a = [-1, 1, 66.25, 333, 333, 1234.5]
print(a)  # [-1, 1, 66.25, 333, 333, 1234.5]

# --- Delete an item by index ---
del a[0]
print(a)  # [1, 66.25, 333, 333, 1234.5]

# --- Delete a slice ---
del a[2:4]
print(a)  # [1, 66.25, 1234.5]

# --- Delete the entire list ---
del a[:]
print(a)  # []

# --- del can also be used to delete entire variables ---
a = [1, 2, 3]
del a
# print(a)  # NameError: name 'a' is not defined

# --- Referencing a after del raises NameError ---
# After del a, the name 'a' no longer exists at all.
