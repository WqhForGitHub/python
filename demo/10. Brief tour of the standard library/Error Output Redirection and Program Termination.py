# ==============================================================================
# 10.4 Error Output Redirection and Program Termination
# ==============================================================================
# https://docs.python.org/3/tutorial/stdlib.html#error-output-redirection-and-program-termination

# --- sys.stdin, sys.stdout, sys.stderr ---
import sys

# stderr is useful for emitting warnings and error messages
# to make them visible even when stdout has been redirected
sys.stderr.write('Warning, log file not found starting a new one\n')

# --- Redirecting stdout ---
# You can redirect stdout to a file
original_stdout = sys.stdout

import io
sys.stdout = io.StringIO()
print("This goes to the redirected stdout")
captured = sys.stdout.getvalue()
sys.stdout = original_stdout  # Restore original stdout

print(f"Captured: {captured.strip()}")
# Output: Captured: This goes to the redirected stdout

# --- sys.exit(): terminating a script ---
# The most direct way to terminate a script is to use sys.exit()
# sys.exit()              # Exit with status 0 (success)
# sys.exit(1)             # Exit with status 1 (error)
# sys.exit('Error msg')   # Exit and print an error message

# --- sys.exit() can be caught with try/except SystemExit ---
try:
    sys.exit(42)
except SystemExit as e:
    print(f"Caught SystemExit with code: {e.code}")
# Output: Caught SystemExit with code: 42
