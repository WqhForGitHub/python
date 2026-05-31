# ==============================================================================
# 11.1 Output Formatting
# ==============================================================================
# https://docs.python.org/3/tutorial/stdlib2.html#output-formatting

# --- reprlib: abbreviated display of large containers ---
import reprlib

# reprlib.repr() provides a limited version of repr() for large or deeply
# nested containers, showing only a representative sample:
print(reprlib.repr(set('supercalifragilisticexpialidocious')))
# {'a', 'c', 'd', 'e', 'f', 'g', ...}

# --- pprint: pretty-printer for data structures ---
import pprint

t = [[['black', 'cyan'], 'white', ['green', 'red']],
     [['magenta', 'yellow'], 'blue']]

# pprint.pprint() adds line breaks and indentation to reveal structure:
pprint.pprint(t, width=30)
# [[['black', 'cyan'],
#   'white',
#   ['green', 'red']],
#  [['magenta', 'yellow'],
#   'blue']]

# --- textwrap: format paragraphs to fit a given screen width ---
import textwrap

doc = """The wrap() method is just like fill() except that it returns
a list of strings instead of one big string with newlines to separate
the wrapped lines."""

print(textwrap.fill(doc, width=40))
# The wrap() method is just like fill()
# except that it returns a list of strings
# instead of one big string with newlines
# to separate the wrapped lines.

# --- locale: culture-specific data formatting ---
import locale

# Set locale for formatting (the locale name is platform-dependent)
# On Windows: 'English_United States.1252'
# On Unix/Linux: 'en_US.UTF-8'
# locale.setlocale(locale.LC_ALL, 'English_United States.1252')

conv = locale.localeconv()  # get a mapping of conventions
x = 1234567.8

# Format with grouping separators:
# locale.format_string("%d", x, grouping=True)  # '1,234,567'

# Format as currency:
# locale.format_string("%s%.*f", (conv['currency_symbol'],
#                          conv['frac_digits'], x), grouping=True)
# '$1,234,567.80'
