# ==============================================================================
# 9.10 Generator Expressions
# ==============================================================================
# https://docs.python.org/3/tutorial/classes.html#generator-expressions

# --- Generator expressions use a syntax similar to list comprehensions ---
# but with parentheses instead of square brackets.
# They are more compact but less versatile than full generator definitions
# and tend to be more memory friendly than equivalent list comprehensions.

# --- Sum of squares ---
print(sum(i * i for i in range(10)))  # 285

# --- Dot product ---
xvec = [10, 20, 30]
yvec = [7, 5, 3]
print(sum(x * y for x, y in zip(xvec, yvec)))  # 260

# --- Unique words from a page (illustrative) ---
# unique_words = set(word for line in page for word in line.split())

# --- Max GPA student (illustrative) ---
# valedictorian = max((student.gpa, student.name) for student in graduates)

# --- Reverse a string using a generator expression ---
data = 'golf'
print(list(data[i] for i in range(len(data) - 1, -1, -1)))  # ['f', 'l', 'o', 'g']

# --- Generator expression vs list comprehension ---
# Generator expression: lazy evaluation, memory efficient
gen_expr = (x ** 2 for x in range(5))
print(gen_expr)  # <generator object <genexpr> at ...>
print(list(gen_expr))  # [0, 1, 4, 9, 16]

# List comprehension: eager evaluation, creates entire list in memory
list_comp = [x ** 2 for x in range(5)]
print(list_comp)  # [0, 1, 4, 9, 16]
