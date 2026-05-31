# ==============================================================================
# 6.1 More on Modules
# ==============================================================================
# https://docs.python.org/3/tutorial/modules.html#more-on-modules

# --- What is a module? ---
# A module is a file containing Python definitions and statements.
# The file name is the module name with the suffix .py appended.
# Within a module, the module's name (as a string) is available as the value
# of the global variable __name__.

# --- Using the fibo module ---
# The fibo.py file in this directory defines two functions: fib() and fib2().
# We can import it and use its functions.

import fibo

# Access module name
print(fibo.__name__)  # fibo

# Call functions from the module
fibo.fib(1000)
# Output: 0 1 1 2 3 5 8 13 21 34 55 89 144 233 377 610 987

result = fibo.fib2(100)
print(result)  # [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]

# --- A module can contain executable statements as well as function definitions ---
# These statements are intended to initialize the module.
# They are executed only the first time the module name is encountered in an
# import statement. (They are also run if the file is executed as a script.)

# --- Each module has its own private namespace ---
# The module's namespace is used as the global namespace for all functions
# defined in the module. Thus, the author of a module can use global variables
# in the module without worrying about accidental clashes with a user's
# global variables.

# --- Importing names with 'from' ---
from fibo import fib, fib2

fib(500)
# Output: 0 1 1 2 3 5 8 13 21 34 55 89 144 233 377

# Note: This does not introduce the module name 'fibo' in the local namespace.
# Uncomment to see the error:
# fibo.fib(500)  # NameError: name 'fibo' is not defined

# --- Importing all names with 'from module import * ---
from fibo import *

fib(500)
# Output: 0 1 1 2 3 5 8 13 21 34 55 89 144 233 377

# This imports all names except those beginning with an underscore (_).
# In general, importing * from a module or package is discouraged,
# as it often produces poorly readable code.

# --- Importing a module under a different name ---
import fibo as fib_module

fib_module.fib(200)
# Output: 0 1 1 2 3 5 8 13 21 34 55 89 144

from fibo import fib as fibonacci
fibonacci(200)
# Output: 0 1 1 2 3 5 8 13 21 34 55 89 144

# This is effectively the same as:
#   import fibo as fib_module
#   fib_module = fibo
# It just makes the binding more targeted.

# --- Modules can import other modules ---
# It is customary but not required to place all import statements at the
# beginning of a module (or script, for that matter).

# --- Module search path ---
# When a module named spam is imported, the interpreter first searches for
# a built-in module with that name. If not found, it then searches for a
# file named spam.py in a list of directories given by the variable sys.path.
# sys.path is initialized from:
#   1. The directory containing the input script (or current directory)
#   2. PYTHONPATH (a list of directory names, with the same syntax as PATH)
#   3. The installation-dependent default (by convention, site-packages)

import sys
print(sys.path)  # List of directories where Python looks for modules

# --- Compiled modules ---
# To speed up loading modules, Python caches the compiled version of each
# module in the __pycache__ directory under the name module.version.pyc.
# The version encodes the format of the compiled file; it generally contains
# the Python version number.
# Python checks the modification date of the source file against the compiled
# version to see if it's out of date and needs to be recompiled.
# You can also pass the -O flag to the interpreter to generate optimized
# .pyo files.

# ==============================================================================
# 6.1.1 Executing modules as scripts
# ==============================================================================
# https://docs.python.org/3/tutorial/modules.html#executing-modules-as-scripts

# --- Using __name__ to run module as script ---
# When you run a Python module with:
#   python fibo.py <arguments>
# the code in the module will be executed just as if you imported it,
# but with the __name__ set to "__main__".

# In fibo.py, we have:
#   if __name__ == "__main__":
#       import sys
#       fib(int(sys.argv[1]))

# This means that the code inside the if block only runs when the module
# is executed as a script, not when it is imported.

# When imported, __name__ is set to the module name:
print(__name__)  # __main__

# When fibo.py is imported, its __name__ is 'fibo':
print(fibo.__name__)  # fibo

# --- Why use this pattern? ---
# This pattern allows a module to provide a convenient command-line interface
# while also being importable without side effects.
# It is a common idiom in Python to have:
#   if __name__ == "__main__":
#       # run some code only when executed as a script
