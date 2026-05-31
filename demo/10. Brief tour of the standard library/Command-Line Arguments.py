# ==============================================================================
# 10.3 Command-Line Arguments
# ==============================================================================
# https://docs.python.org/3/tutorial/stdlib.html#command-line-arguments

# --- sys.argv: command-line arguments as a list ---
import sys

# The first element is the script name, the rest are the arguments
print(sys.argv)

# Example: running 'python demo.py one two three' would produce:
# ['demo.py', 'one', 'two', 'three']

# --- The argparse module: sophisticated command-line argument processing ---
import argparse

parser = argparse.ArgumentParser(
    prog='top',
    description='Show top lines from each file')

# Positional argument: one or more filenames
parser.add_argument('filenames', nargs='+')

# Optional argument: number of lines with a default
parser.add_argument('-l', '--lines', type=int, default=10)

# Parse arguments (in a real script, this reads from sys.argv)
# args = parser.parse_args()
# print(args)

# When run with: python top.py --lines=5 alpha.txt beta.txt
# args.lines => 5
# args.filenames => ['alpha.txt', 'beta.txt']

# --- More argparse features ---
parser2 = argparse.ArgumentParser(description='Example with more features')

# Optional flag (boolean)
parser2.add_argument('-v', '--verbose', action='store_true', help='enable verbose output')

# Optional argument with choices
parser2.add_argument('--mode', choices=['fast', 'slow'], default='fast')

# Required optional argument
parser2.add_argument('--output', '-o', required=True, help='output file path')

# Print help text
# parser2.print_help()
