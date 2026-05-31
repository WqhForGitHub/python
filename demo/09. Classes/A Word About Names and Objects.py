# ==============================================================================
# 9.1 A Word About Names and Objects
# ==============================================================================
# https://docs.python.org/3/tutorial/classes.html#a-word-about-names-and-objects

# --- Aliasing: multiple names can be bound to the same object ---
# Objects have individuality, and multiple names (in multiple scopes)
# can be bound to the same object. This is known as aliasing in other languages.

a = [1, 2, 3]
b = a  # b and a refer to the same list object
b.append(4)
print(a)  # [1, 2, 3, 4]  -- a is also modified because a and b are the same object

# --- Aliasing with immutable types is safe ---
# With immutable basic types (numbers, strings, tuples), aliasing can be safely ignored.

x = 42
y = x  # y and x both refer to the integer 42
y = 100  # y now refers to a different object; x is unchanged
print(x)  # 42
print(y)  # 100

# --- Aliasing with mutable objects has surprising effects ---
# Passing an object is cheap since only a pointer is passed by the implementation;
# and if a function modifies an object passed as an argument, the caller will
# see the change.

def modify_list(lst):
    lst.append(99)

my_list = [1, 2, 3]
modify_list(my_list)
print(my_list)  # [1, 2, 3, 99]  -- the original list is modified
