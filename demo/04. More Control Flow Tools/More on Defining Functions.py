# ==============================================================================
# 4.8 More on Defining Functions
# ==============================================================================
# https://docs.python.org/3/tutorial/controlflow.html#more-on-defining-functions

# --- 4.8.1 Default Argument Values ---
# The most useful form is to specify a default value for one or more arguments.

def ask_ok(prompt, retries=4, reminder='Please try again!'):
    while True:
        ok = input(prompt)
        if ok in ('y', 'ye', 'yes'):
            return True
        if ok in ('n', 'no', 'nop', 'nope'):
            return False
        retries -= 1
        if retries < 0:
            raise ValueError('invalid user response')
        print(reminder)

# This function can be called in several ways:
# ask_ok('Do you really want to quit?')                  # 1 required argument
# ask_ok('OK to overwrite the file?', 2)                 # 2 arguments
# ask_ok('OK to overwrite the file?', 2, 'Come on!')     # all 3 arguments

# --- Default values are evaluated at function definition time ---
# IMPORTANT: The default value is evaluated only once.
# This makes a difference when the default is a mutable object.

def f(a, L=[]):
    L.append(a)
    return L

print(f(1))  # [1]
print(f(2))  # [1, 2]
print(f(3))  # [1, 2, 3]
# The list accumulates across calls because it's the same object!

# --- Avoiding the mutable default gotcha ---
# If you don't want the default to be shared between calls:
def f(a, L=None):
    if L is None:
        L = []
    L.append(a)
    return L

print(f(1))  # [1]
print(f(2))  # [2]
print(f(3))  # [3]

# --- Default value can be any expression ---
i = 5
def f(arg=i):
    print(arg)

i = 6
f()  # 5  (default was set when the function was defined, not when it's called)

# --- Keyword arguments ---
# Functions can also be called using keyword arguments of the form kwarg=value.

def parrot(voltage, state='a stiff', action='voom', type='Norwegian Blue'):
    print("-- This parrot wouldn't", action, end=' ')
    print("if you put", voltage, "volts through it.")
    print("-- Lovely plumage, the", type)
    print("-- It's", state, "!")

parrot(1000)                                          # 1 positional argument
parrot(voltage=1000)                                  # 1 keyword argument
parrot(voltage=1000000, action='VOOOOOM')             # 2 keyword arguments
parrot(action='VOOOOOM', voltage=1000000)             # 2 keyword arguments (order doesn't matter)
parrot('a million', 'bereft of life', 'jump')         # 3 positional arguments
parrot('a thousand', state='pushing up the daisies')  # 1 positional, 1 keyword

# --- Invalid calls ---
# parrot()                    # required argument missing
# parrot(voltage=5.0, 'dead') # non-keyword argument after a keyword argument
# parrot(110, voltage=220)    # duplicate value for the same argument
# parrot(actor='John Cleese') # unknown keyword argument

# --- 4.8.2 Keyword Arguments ---
# **name: collects all remaining keyword arguments into a dictionary

def cheeseshop(kind, *arguments, **keywords):
    print("-- Do you have any", kind, "?")
    print("-- I'm sorry, we're all out of", kind)
    for arg in arguments:
        print(arg)
    print("-" * 40)
    for kw in keywords:
        print(kw, ":", keywords[kw])

cheeseshop(
    "Limburger",
    "It's very runny, sir.",
    "It's really very, VERY runny, sir.",
    shopkeeper="Michael Palin",
    client="John Cleese",
    sketch="Cheese Shop Sketch"
)
# Output:
# -- Do you have any Limburger ?
# -- I'm sorry, we're all out of Limburger
# It's very runny, sir.
# It's really very, VERY runny, sir.
# ----------------------------------------
# shopkeeper : Michael Palin
# client : John Cleese
# sketch : Cheese Shop Sketch

# --- *name: collects positional arguments into a tuple ---
def concat(*args, sep="/"):
    return sep.join(args)

print(concat("earth", "mars", "venus"))        # earth/mars/venus
print(concat("earth", "mars", "venus", sep="."))  # earth.mars.venus

# --- 4.8.3 Special Parameters ---
# By default, arguments may be passed to a Python function either by position
# or explicitly by keyword. For readability and performance, it makes sense to
# restrict the way arguments can be passed.

# def f(pos1, pos2, /, pos_or_kwd, *, kwd1, kwd2):
#       -----------    ----------    ----------
#         |              |              |
#         |        Positional or keyword   |
#         |                                - Keyword only
#          -- Positional only

# --- Positional-only parameters (/) ---
# Parameters before / are positional-only.
def pos_only(arg1, arg2, /):
    print(arg1, arg2)

pos_only(1, 2)       # OK
# pos_only(arg1=1, arg2=2)  # TypeError: positional-only argument

# --- Keyword-only parameters (*) ---
# Parameters after * are keyword-only.
def kwd_only(*, arg1, arg2):
    print(arg1, arg2)

kwd_only(arg1=1, arg2=2)  # OK
# kwd_only(1, 2)           # TypeError: keyword-only argument

# --- Combined example ---
def standard_arg(arg):
    print(arg)

standard_arg(1)         # OK, positional
standard_arg(arg=2)     # OK, keyword

def pos_only_arg(arg, /):
    print(arg)

pos_only_arg(1)         # OK
# pos_only_arg(arg=1)   # TypeError

def kwd_only_arg(*, arg):
    print(arg)

kwd_only_arg(arg=3)     # OK
# kwd_only_arg(3)       # TypeError

def combined_example(pos_only, /, standard, *, kwd_only):
    print(pos_only, standard, kwd_only)

combined_example(1, 2, kwd_only=3)         # OK
combined_example(1, standard=2, kwd_only=3) # OK
# combined_example(pos_only=1, standard=2, kwd_only=3)  # TypeError

# --- 4.8.4 Arbitrary Argument Lists ---
# *args collects any number of positional arguments into a tuple.

def write_multiple_items(file, separator, *args):
    file.write(separator.join(args))

# *args must come after all formal parameters, and before keyword-only parameters.

# --- Variable arguments in practice ---
def concat(*args, sep="/"):
    return sep.join(args)

print(concat("a", "b", "c"))          # a/b/c
print(concat("a", "b", "c", sep=",")) # a,b,c

# --- Unpacking with * in function calls ---
# The reverse: unpacking arguments from a list or tuple.
print(list(range(3, 6)))    # [3, 4, 5]   normal call with separate arguments
args = [3, 6]
print(list(range(*args)))   # [3, 4, 5]   call with arguments unpacked from a list

# --- 4.8.5 Unpacking Argument Lists ---

# Unpacking a dictionary with **:
def parrot(voltage, state='a stiff', action='voom'):
    print("-- This parrot wouldn't", action, end=' ')
    print("if you put", voltage, "volts through it.")
    print("It's", state, "!")

d = {"voltage": "four million", "state": "bleedin' demised", "action": "VOOM"}
parrot(**d)
# Output:
# -- This parrot wouldn't VOOM if you put four million volts through it.
# It's bleedin' demised !

# Unpacking a tuple with *:
args = (3, 6)
print(list(range(*args)))  # [3, 4, 5]

# --- 4.8.6 Lambda Expressions ---
# Small anonymous functions created with the 'lambda' keyword.

# Lambda: a function with a single expression as its body.
def make_incrementor(n):
    return lambda x: x + n

f = make_incrementor(42)
print(f(0))   # 42
print(f(1))   # 43

# Lambda as a sort key:
pairs = [(1, 'one'), (2, 'two'), (3, 'three'), (4, 'four')]
pairs.sort(key=lambda pair: pair[1])
print(pairs)  # [(4, 'four'), (1, 'one'), (3, 'three'), (2, 'two')]

# Equivalent named function:
def sort_by_second(pair):
    return pair[1]
pairs2 = [(1, 'one'), (2, 'two'), (3, 'three'), (4, 'four')]
pairs2.sort(key=sort_by_second)
print(pairs2)  # [(4, 'four'), (1, 'one'), (3, 'three'), (2, 'two')]

# Lambda with map and filter:
squares = list(map(lambda x: x**2, range(10)))
print(squares)  # [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]

evens = list(filter(lambda x: x % 2 == 0, range(10)))
print(evens)   # [0, 2, 4, 6, 8]

# But list comprehensions are often more readable:
squares = [x**2 for x in range(10)]
print(squares)  # [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]

# --- 4.8.7 Documentation Strings ---
# The first line should always be a short, concise summary of the object's purpose.
# If there are more lines, the second line should be blank, followed by further
# explanation.

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

# Docstring conventions:
# - First line: short summary (capitalized, period at end)
# - Second line: blank (if more detail follows)
# - Following lines: detailed description

# --- 4.8.8 Function Annotations ---
# Annotations are stored in the __annotations__ attribute of the function
# as a dictionary and have no effect on any other part of the function.

def f(ham: str, eggs: str = 'eggs') -> str:
    print("Annotations:", f.__annotations__)
    print("Arguments:", ham, eggs)
    return ham + ' and ' + eggs

print(f('spam'))
# Output:
# Annotations: {'ham': <class 'str'>, 'eggs': <class 'str'>, 'return': <class 'str'>}
# Arguments: spam eggs
# spam and eggs

# Annotations can be any expression:
def f(x: int, y: float = 0.0) -> float:
    """Add an int and a float, returning a float."""
    return x + y

print(f(3, 4.5))  # 7.5
print(f.__annotations__)  # {'x': <class 'int'>, 'y': <class 'float'>, 'return': <class 'float'>}
