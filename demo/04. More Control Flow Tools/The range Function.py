# ==============================================================================
# 4.3 The range() Function
# ==============================================================================
# https://docs.python.org/3/tutorial/controlflow.html#the-range-function

# --- Basic range(n): generates 0 to n-1 ---
for i in range(5):
    print(i, end=' ')
print()  # 0 1 2 3 4

# --- range(start, stop): from start to stop-1 ---
for i in range(5, 10):
    print(i, end=' ')
print()  # 5 6 7 8 9

# --- range(start, stop, step): with step ---
for i in range(0, 10, 3):
    print(i, end=' ')
print()  # 0 3 6 9

for i in range(-10, -100, -30):
    print(i, end=' ')
print()  # -10 -40 -70

# --- range() returns an iterable, not a list ---
print(range(10))  # range(0, 10)

# In many ways, the object returned by range() behaves as if it is a list,
# but in fact it isn't. It is an object which returns the successive items
# of the desired sequence when you iterate over it, but it doesn't really
# make the list, thus saving space.

# --- Converting range to a list ---
print(list(range(5)))  # [0, 1, 2, 3, 4]

# --- Using range with len() to iterate over indices ---
a = ['Mary', 'had', 'a', 'little', 'lamb']
for i in range(len(a)):
    print(i, a[i])
# Output:
# 0 Mary
# 1 had
# 2 a
# 3 little
# 4 lamb

# --- However, enumerate() is usually preferred over range(len()) ---
a = ['Mary', 'had', 'a', 'little', 'lamb']
for i, v in enumerate(a):
    print(i, v)
# Output:
# 0 Mary
# 1 had
# 2 a
# 3 little
# 4 lamb

# --- range() supports containment testing ---
print(5 in range(10))    # True
print(10 in range(10))   # False
print(5 not in range(10))  # False

# --- range() supports indexing and slicing ---
r = range(10)
print(r[0])    # 0
print(r[-1])   # 9
print(r[2:5])  # range(2, 5)

# --- range() with a single negative step ---
# A negative step counts down
for i in range(10, 0, -2):
    print(i, end=' ')
print()  # 10 8 6 4 2
