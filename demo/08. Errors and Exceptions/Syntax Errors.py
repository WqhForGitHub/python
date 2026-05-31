# ==============================================================================
# 8.1 Syntax Errors
# ==============================================================================
# https://docs.python.org/3/tutorial/errors.html#syntax-errors

# --- What is a Syntax Error? ---
# Syntax errors, also known as parsing errors, are the most common kind of
# complaint you get while you are still learning Python.

# --- Example: missing colon after 'while' ---
# while True print('Hello world')
#   ^
# SyntaxError: invalid syntax

# The parser repeats the offending line and displays a little 'arrow' pointing
# at the earliest point in the line where the error was detected.

# --- The error is caused by the token PRECEDING the arrow ---
# In the example above, the error is detected at the function print(),
# because a colon (':') is missing before it.

# Correct version:
while True:
    print('Hello world')
    break  # added break to prevent infinite loop
# Output: Hello world

# --- Example: incomplete expression ---
# 1 +
#    ^
# SyntaxError: invalid syntax

# The arrow points to the end of the line, indicating that something
# was expected after the '+' operator.

# --- Example: mismatched parentheses ---
# print('hello'
#              ^
# SyntaxError: unexpected EOF while parsing

# Correct version:
print('hello')  # hello

# --- Example: invalid assignment ---
# if x = 0:
#      ^
# SyntaxError: invalid syntax
# Use '==' for comparison, not '='

# Correct version:
x = 5
if x == 5:
    print('x is 5')  # x is 5

# --- File name and line number ---
# When a syntax error occurs, Python shows the file name and line number,
# so you can locate the error easily:
#   File "example.py", line 1
#     while True print('Hello world')
#                   ^
# SyntaxError: invalid syntax
