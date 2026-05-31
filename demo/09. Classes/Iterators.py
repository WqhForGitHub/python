# ==============================================================================
# 9.8 Iterators
# ==============================================================================
# https://docs.python.org/3/tutorial/classes.html#iterators

# --- Most container objects can be looped over using a for statement ---
for element in [1, 2, 3]:
    print(element, end=' ')
print()  # 1 2 3

for key in {'one': 1, 'two': 2}:
    print(key, end=' ')
print()  # one two

for char in "123":
    print(char, end=' ')
print()  # 1 2 3

# --- Behind the scenes: the iterator protocol ---
# The for statement calls iter() on the container object.
# iter() returns an iterator object that defines __next__() which accesses
# elements one at a time. When there are no more elements, __next__()
# raises a StopIteration exception.

s = 'abc'
it = iter(s)
print(next(it))  # a
print(next(it))  # b
print(next(it))  # c
# next(it)  # raises StopIteration

# --- Adding iterator behavior to your classes ---
# Define an __iter__() method which returns an object with a __next__() method.
# If the class defines __next__(), then __iter__() can just return self.


class Reverse:
    """Iterator for looping over a sequence backwards."""

    def __init__(self, data):
        self.data = data
        self.index = len(data)

    def __iter__(self):
        return self

    def __next__(self):
        if self.index == 0:
            raise StopIteration
        self.index = self.index - 1
        return self.data[self.index]


rev = Reverse('spam')
for char in rev:
    print(char, end=' ')
print()  # m a p s

# --- Using the iterator directly ---
rev2 = Reverse('hello')
print(iter(rev2) is rev2)  # True  (__iter__ returns self)
print(next(rev2))  # o
print(next(rev2))  # l
print(next(rev2))  # l
print(next(rev2))  # e
print(next(rev2))  # h
# next(rev2)  # StopIteration
