# ==============================================================================
# 6.2 Standard Modules
# ==============================================================================
# https://docs.python.org/3/tutorial/modules.html#standard-modules

# --- The sys module ---
# Python comes with a library of standard modules, described in the
# Python Library Reference. Some modules are built into the interpreter;
# these provide access to operations that are not part of the core of the
# language but are nevertheless built in.

import sys

# sys.ps1 and sys.ps2 define the strings used as primary and secondary prompts:
# (Only available in interactive mode)
# >>> sys.ps1
# '>>> '
# >>> sys.ps2
# '... '
# These can be modified:
# >>> sys.ps1 = 'C> '
# C> print('Hello!')
# Hello!

# --- sys.path ---
# The list of directories where Python searches for modules.
print(len(sys.path))  # Number of search paths (varies by system)

# You can modify sys.path to add new directories:
# sys.path.append('/ufs/guido/lib/python')

# --- Built-in modules ---
# Some modules are built into the interpreter. They are not files on disk
# but are part of the interpreter itself.
# Example: the 'sys' module is always available.

# You can check if a module is built-in:
print('sys' in sys.builtin_module_names)  # True

# --- Other commonly used standard modules ---
import os
print(os.getcwd())  # Current working directory

import math
print(math.pi)  # 3.141592653589793

import random
print(random.choice(['apple', 'pear', 'banana']))  # Random fruit

# --- The module search path includes the standard library ---
# The standard library modules are automatically found by the interpreter
# because their directory is included in sys.path.
