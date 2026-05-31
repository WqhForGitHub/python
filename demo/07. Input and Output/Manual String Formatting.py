# ==============================================================================
# 7.1.3 Manual String Formatting
# ==============================================================================
# https://docs.python.org/3/tutorial/inputoutput.html#manual-string-formatting

# --- Using str.rjust(), str.ljust(), str.center() ---
# These methods pad a string to a given width but do NOT truncate

# Same table of squares and cubes, formatted manually:
for x in range(1, 11):
    print(repr(x).rjust(2), repr(x*x).rjust(3), end=' ')
    # Note use of 'end' on previous line
    print(repr(x*x*x).rjust(4))
# Output:
#  1   1    1
#  2   4    8
#  3   9   27
#  4  16   64
#  5  25  125
#  6  36  216
#  7  49  343
#  8  64  512
#  9  81  729
# 10 100 1000

# Note: the one space between each column was added by the way print() works:
# it always adds spaces between its arguments.

# --- str.rjust(): right-justify by padding with spaces on the left ---
print('hello'.rjust(10))   #      hello
print('hello'.rjust(3))    # hello  (too long, returned unchanged)

# --- str.ljust(): left-justify by padding with spaces on the right ---
print('hello'.ljust(10))   # hello

# --- str.center(): center-align by padding on both sides ---
print('hello'.center(11))  #    hello

# --- If the input string is too long, it is returned unchanged ---
# These methods don't truncate. If you really want truncation, add a slice:
s = 'hello world'
print(s.ljust(5)[:5])  # hello  (truncated with slice)

# --- str.zfill(): pad a numeric string on the left with zeros ---
# It understands about plus and minus signs
print('12'.zfill(5))            # 00012
print('-3.14'.zfill(7))         # -003.14
print('3.14159265359'.zfill(5)) # 3.14159265359  (too long, not truncated)
