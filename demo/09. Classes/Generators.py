# ==============================================================================
# 9.9 Generators
# ==============================================================================
# https://docs.python.org/3/tutorial/classes.html#generators

# --- Generators are a simple and powerful tool for creating iterators ---
# They are written like regular functions but use the yield statement
# whenever they want to return data. Each time next() is called on it,
# the generator resumes where it left off.


def reverse(data):
    for index in range(len(data) - 1, -1, -1):
        yield data[index]


for char in reverse('golf'):
    print(char, end=' ')
print()  # f l o g

# --- Generators automatically create __iter__() and __next__() methods ---
# They also automatically save local variables and execution state between calls.


def fibonacci(n):
    """Generate Fibonacci numbers up to n."""
    a, b = 0, 1
    while a < n:
        yield a
        a, b = b, a + b


for num in fibonacci(100):
    print(num, end=' ')
print()  # 0 1 1 2 3 5 8 13 21 34 55 89

# --- Generator termination automatically raises StopIteration ---
# When generators terminate (function returns or falls off the end),
# they automatically raise StopIteration.


def count_up_to(max_value):
    count = 1
    while count <= max_value:
        yield count
        count += 1


gen = count_up_to(3)
print(next(gen))  # 1
print(next(gen))  # 2
print(next(gen))  # 3
# next(gen)  # StopIteration

# --- Using generators with list() ---
print(list(reverse('python')))  # ['n', 'o', 'h', 't', 'y', 'p']
