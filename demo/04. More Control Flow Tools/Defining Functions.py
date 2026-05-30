# ==============================================================================
# 4.7 Defining Functions
# ==============================================================================
# https://docs.python.org/3/tutorial/controlflow.html#defining-functions

# --- Basic function definition ---
# The keyword 'def' introduces a function definition.
# It must be followed by the function name and a parenthesized list of parameters.

def fib(n):
    """Print a Fibonacci series up to n."""
    a, b = 0, 1
    while a < n:
        print(a, end=' ')
        a, b = b, a + b
    print()

fib(2000)
# Output: 0 1 1 2 3 5 8 13 21 34 55 89 144 233 377 610 987 1597

# --- Function call ---
# Calling a function with arguments executes the function body.

# --- Returning a value ---
# Functions without a return statement return None.

def fib2(n):
    """Return a list of Fibonacci numbers up to n."""
    result = []
    a, b = 0, 1
    while a < n:
        result.append(a)    # see below
        a, b = b, a + b
    return result

f100 = fib2(100)
print(f100)  # [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]

# --- Functions return None by default ---
def no_return():
    pass

print(no_return())  # None

# --- Functions are objects ---
# Functions can be assigned to variables and passed as arguments.
f = fib
f(100)
# Output: 0 1 1 2 3 5 8 13 21 34 55 89

# --- Docstrings ---
# The first statement of a function body can be a string literal;
# this is the function's docstring.
def my_function():
    """Do nothing, but document it.

    No, really, it doesn't do anything.
    """
    pass

print(my_function.__doc__)
# Output:
# Do nothing, but document it.
#
# No, really, it doesn't do anything.

# --- List append() method ---
# result.append(a) calls a method of the list object result.
# A method is a function that 'belongs' to an object.
result = []
result.append(1)
result.append(2)
result.append(3)
print(result)  # [1, 2, 3]

# Equivalent but less efficient:
result = []
result = result + [4]
print(result)  # [4]
