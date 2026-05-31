# ==============================================================================
# 6.3 The dir() Function
# ==============================================================================
# https://docs.python.org/3/tutorial/modules.html#the-dir-function

# --- dir() with a module argument ---
# The built-in function dir() is used to find out which names a module defines.
# It returns a sorted list of strings.

import fibo

names = dir(fibo)
print(names)
# Output: ['__builtins__', '__cached__', '__doc__', '__file__', '__loader__',
#          '__name__', '__package__', '__spec__', 'fib', 'fib2']

# --- dir() without arguments ---
# Without arguments, dir() lists the names you have defined currently.
# It lists all types of names: variables, modules, functions, etc.

a = [1, 2, 3, 4, 5]
import fibo
fib = fibo.fib

# dir() does not list the names of built-in functions and variables
current_names = dir()
print(current_names)
# Includes 'a', 'fibo', 'fib', and other names defined in this scope

# --- Listing built-in names ---
# If you want a list of built-in functions and variables, use dir(builtins)
import builtins

builtin_names = dir(builtins)
print(builtin_names)
# Output: ['ArithmeticError', 'AssertionError', 'AttributeError',
#          'BaseException', 'BlockingIOError', 'BrokenPipeError',
#          'BufferError', 'BytesWarning', 'Callable', ...,
#          'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'breakpoint',
#          'bytearray', 'bytes', 'callable', 'chr', 'classmethod', 'compile',
#          'complex', 'copyright', 'credits', 'delattr', 'dict', 'dir',
#          'divmod', 'enumerate', 'eval', 'exec', 'exit', 'filter', 'float',
#          'format', 'frozenset', 'getattr', 'globals', 'hasattr', 'hash',
#          'help', 'hex', 'id', 'input', 'int', 'isinstance', 'issubclass',
#          'iter', 'len', 'license', 'list', 'locals', 'map', 'max',
#          'memoryview', 'min', 'next', 'object', 'oct', 'open', 'ord',
#          'pow', 'print', 'property', 'quit', 'range', 'repr', 'reversed',
#          'round', 'set', 'setattr', 'slice', 'sorted', 'staticmethod',
#          'str', 'sum', 'super', 'tuple', 'type', 'vars', 'zip']

# --- dir() on different objects ---
# dir() works on any object, not just modules.
# For a string object:
print(dir('hello'))
# Returns all string methods: ['__add__', '__class__', ..., 'capitalize',
#  'casefold', 'center', 'count', 'encode', 'endswith', 'expandtabs',
#  'find', 'format', 'format_map', 'index', 'isalnum', 'isalpha', ...]

# For a list object:
print(dir([1, 2, 3]))
# Returns all list methods: ['__add__', '__class__', ..., 'append', 'clear',
#  'copy', 'count', 'extend', 'index', 'insert', 'pop', 'remove', 'reverse',
#  'sort']
