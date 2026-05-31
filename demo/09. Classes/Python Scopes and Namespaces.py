# ==============================================================================
# 9.2 Python Scopes and Namespaces
# ==============================================================================
# https://docs.python.org/3/tutorial/classes.html#python-scopes-and-namespaces

# --- Namespace ---
# A namespace is a mapping from names to objects.
# Examples: built-in names, global names in a module, local names in a function.
# There is absolutely no relation between names in different namespaces.

# --- Attribute ---
# Any name following a dot is an attribute.
# e.g., z.real -- 'real' is an attribute of object z.
# modname.funcname -- 'funcname' is an attribute of module 'modname'.

# --- Writable attributes can be deleted ---
import math
math.my_attr = 42  # add a new attribute
print(math.my_attr)  # 42
del math.my_attr  # remove the attribute
# print(math.my_attr)  # AttributeError

# --- Scopes ---
# At any time during execution, there are 3 or 4 nested scopes:
# 1. Innermost scope: local names
# 2. Scopes of enclosing functions: non-local, non-global names
# 3. Next-to-last scope: current module's global names
# 4. Outermost scope: built-in names

# --- Assignments go into the innermost scope ---
# If no global or nonlocal statement is in effect, assignments to names
# always go into the innermost scope. Assignments do not copy data --
# they just bind names to objects.

# --- The global statement ---
# Indicates that particular variables live in the global scope.

# --- The nonlocal statement ---
# Indicates that particular variables live in an enclosing scope.

# ==============================================================================
# 9.2.1 Scopes and Namespaces Example
# ==============================================================================
# https://docs.python.org/3/tutorial/classes.html#scopes-and-namespaces-example

# --- Demonstrating global and nonlocal ---
# This example demonstrates how to reference the different scopes and namespaces,
# and how global and nonlocal affect variable binding.


def scope_test():
    def do_local():
        spam = "local spam"

    def do_nonlocal():
        nonlocal spam
        spam = "nonlocal spam"

    def do_global():
        global spam
        spam = "global spam"

    spam = "test spam"
    do_local()
    print("After local assignment:", spam)
    do_nonlocal()
    print("After nonlocal assignment:", spam)
    do_global()
    print("After global assignment:", spam)


scope_test()
print("In global scope:", spam)

# Output:
# After local assignment: test spam
# After nonlocal assignment: nonlocal spam
# After global assignment: nonlocal spam
# In global scope: global spam

# Note:
# - The local assignment (default) didn't change scope_test's binding of spam.
# - The nonlocal assignment changed scope_test's binding of spam.
# - The global assignment changed the module-level binding.
