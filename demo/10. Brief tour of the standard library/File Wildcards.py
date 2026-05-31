# ==============================================================================
# 10.2 File Wildcards
# ==============================================================================
# https://docs.python.org/3/tutorial/stdlib.html#file-wildcards

# --- The glob module: making file lists from directory wildcard searches ---
import glob

# Find all Python files in the current directory
py_files = glob.glob('*.py')
print(py_files)

# --- glob supports Unix-style wildcards ---
# * matches everything
# ? matches any single character
# [seq] matches any character in seq
# [!seq] matches any character not in seq

# Match files with a single character before .py
single_char = glob.glob('?.py')
print(single_char)

# Match files starting with a specific prefix
# prefixed = glob.glob('test_*.py')

# --- Recursive glob with ** ---
# Search recursively in all subdirectories
# all_py = glob.glob('**/*.py', recursive=True)

# --- glob.iglob: returns an iterator instead of a list ---
for f in glob.iglob('*.py'):
    print(f)
