# ==============================================================================
# 3.1.2 Strings
# ==============================================================================
# https://docs.python.org/3/tutorial/introduction.html#strings

# --- String literals ---
# Strings can be enclosed in single quotes or double quotes
print('spam eggs')     # spam eggs
print("spam eggs")     # spam eggs
print('doesn\'t')      # doesn't  (escape single quote with backslash)
print("doesn't")       # doesn't  (or use double quotes to avoid escaping)
print('"Yes," they said.')   # "Yes," they said.
print("\"Yes,\" they said.") # "Yes," they said.
print('"Isn\'t," they said.') # "Isn't," they said.

# --- Escape sequences ---
print('First line.\nSecond line.')  # \n is a newline
print(r'C:\some\name')  # Raw strings: backslashes are treated as literal characters

# --- Multi-line strings ---
# Using triple quotes: strings can span multiple lines
print("""
Usage: thingy [OPTIONS]
     -h                        Display this usage message
     -H hostname               Hostname to connect to
""")

# Single-line output (note the backslash to suppress the initial newline):
print("""\
Usage: thingy [OPTIONS]
     -h                        Display this usage message
     -H hostname               Hostname to connect to
""")

# --- String concatenation ---
print(3 * 'un' + 'ium')  # unununium  (repeated 3 times, then concatenated)

# Adjacent string literals are automatically concatenated
print('Py' 'thon')  # Python

# This is useful for long strings:
text = ('Put several strings within parentheses '
        'to have them joined together.')
print(text)

# This only works with literals, NOT with variables or expressions:
prefix = 'Py'
# print(prefix 'thon')  # SyntaxError! Must use + operator
print(prefix + 'thon')  # Python

# --- String indexing ---
word = 'Python'
print(word[0])   # P  (first character, position 0)
print(word[5])   # n  (sixth character, position 5)

# Negative indices count from the right
print(word[-1])  # n  (last character)
print(word[-2])  # o  (second-last character)
print(word[-6])  # P  (same as word[0])

# --- String slicing ---
# Slicing gives you a substring: word[start:end]
# start is inclusive, end is exclusive
print(word[0:2])   # Py  (characters from position 0 (included) to 2 (excluded))
print(word[2:5])   # tho (characters from position 2 (included) to 5 (excluded))

# Omitting start or end defaults to the beginning or end
print(word[:2])    # Py   (from beginning to position 2, excluded)
print(word[4:])    # on   (from position 4 to end)
print(word[-2:])   # on   (from second-last to end)

# --- Out-of-range slicing is handled gracefully ---
print(word[4:42])  # on
print(word[42:])   # '' (empty string)

# --- Strings are immutable ---
# word[0] = 'J'  # TypeError: 'str' object does not support item assignment
# To create a different string, construct a new one:
print('J' + word[1:])  # Jython
print(word[:2] + 'py') # Pypy

# --- Built-in string functions ---
print(len(word))  # 6  (length of the string)

# --- String methods ---
s = 'Hello, World!'
print(s.lower())        # hello, world!
print(s.upper())        # HELLO, WORLD!
print(s.replace('World', 'Python'))  # Hello, Python!
print(s.strip())        # Hello, World!  (removes leading/trailing whitespace)
print(s.split(', '))    # ['Hello', 'World!']
print(s.find('World'))  # 7  (index of first occurrence)
print(s.count('l'))     # 3  (count occurrences)

# --- f-Strings (formatted string literals) ---
name = 'Python'
version = 3
print(f'{name} version {version}')        # Python version 3
print(f'The value of pi is approximately {3.14159:.2f}')  # The value of pi is approximately 3.14
