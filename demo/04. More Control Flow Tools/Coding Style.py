# ==============================================================================
# 4.9 Intermezzo: Coding Style
# ==============================================================================
# https://docs.python.org/3/tutorial/controlflow.html#intermezzo-coding-style

# --- PEP 8: Style Guide for Python Code ---
# Python code readability matters. Most projects follow PEP 8.

# --- Key PEP 8 rules ---

# 1. Use 4-space indentation, and no tabs.
# Good:
if True:
    print('4 spaces')  # 4 spaces of indentation

# Bad (don't use tabs):
# if True:
# 	print('tab')  # Tab character

# 2. Wrap lines so they don't exceed 79 characters.
# For docstrings/comments: 72 characters.

# 3. Use blank lines to separate functions and classes,
#    and larger blocks of code inside functions.

def function_one():
    """First function."""
    pass


def function_two():
    """Second function, separated by two blank lines for top-level definitions."""
    pass


class MyClass:
    """A class definition."""

    def method_one(self):
        """Methods inside a class are separated by one blank line."""
        pass

    def method_two(self):
        """Another method."""
        pass

# 4. Put imports on separate lines.
# Good:
import os
import sys

# Bad:
# import os, sys

# But this is OK:
from subprocess import Popen, PIPE

# 5. Use consistent quotes (single or double, pick one and be consistent).
name = 'Python'   # single quotes
name = "Python"   # double quotes - both are fine, just be consistent

# 6. Use spaces around operators and after commas.
# Good:
x = 1
y = x + 2
my_list = [1, 2, 3]

# Bad:
# x=1
# y=x+2
# my_list = [1,2,3]

# 7. Use CamelCase for class names and lowercase_with_underscores for
#    functions and methods.

class MyClassName:  # CamelCase for classes
    pass

def my_function_name():  # lowercase_with_underscores for functions
    pass

# 8. Use UTF-8 encoding for Python source code.
# 9. Don't use non-ASCII characters in identifiers.

# --- Use auto-formatters ---
# Tools like 'black' automatically format your code to follow PEP 8:
# pip install black
# black your_script.py

# 'autopep8' is another option:
# pip install autopep8
# autopep8 --in-place your_script.py

# --- Use linters ---
# 'flake8' checks your code for PEP 8 violations:
# pip install flake8
# flake8 your_script.py
