# ==============================================================================
# 4.6 match Statements
# ==============================================================================
# https://docs.python.org/3/tutorial/controlflow.html#match-statements
# Note: match statements were introduced in Python 3.10

# --- Basic match statement ---
# A match statement takes an expression and compares its value to successive
# patterns given as one or more case blocks.

def http_error(status):
    match status:
        case 400:
            return 'Bad request'
        case 404:
            return 'Not found'
        case 418:
            return "I'm a teapot"
        case 401 | 403 | 407:  # Multiple patterns combined with |
            return 'Not allowed'
        case _:  # _ is a wildcard that never fails to match
            return "Something's wrong with the internet"

print(http_error(400))  # Bad request
print(http_error(404))  # Not found
print(http_error(418))  # I'm a teapot
print(http_error(401))  # Not allowed
print(http_error(500))  # Something's wrong with the internet

# --- Variable binding in patterns ---
# Patterns can bind variables, using the variable name in the match.
# point is an (x, y) tuple
point = (1, 0)
match point:
    case (0, 0):
        print('Origin')
    case (0, y):
        print(f'Y-axis at y={y}')
    case (x, 0):
        print(f'X-axis at x={x}')
    case (x, y):
        print(f'Somewhere at x={x}, y={y}')
    case _:
        print('Not a point')
# Output: X-axis at x=1

# --- Class pattern matching ---
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

# Using keyword arguments in class patterns
point = Point(x=1, y=2)
match point:
    case Point(x=0, y=0):
        print('Origin')
    case Point(x=0, y=y):
        print(f'On Y-axis at y={y}')
    case Point(x=x, y=0):
        print(f'On X-axis at x={x}')
    case Point():
        print('Somewhere else')
    case _:
        print('Not a point')
# Output: Somewhere else

# --- Nested patterns ---
# Patterns can be arbitrarily nested
points = [Point(0, 0), Point(1, 1)]
match points:
    case []:
        print('No points')
    case [Point(0, 0)]:
        print('The origin')
    case [Point(x, y)]:
        print(f'Single point at x={x}, y={y}')
    case [Point(0, 0), Point(x, y)]:
        print(f'Origin and another point at x={x}, y={y}')
    case _:
        print('Something else')
# Output: Origin and another point at x=1, y=1

# --- Guards (if clause) in patterns ---
# A guard can be added to a pattern using 'if'
point = Point(x=-1, y=2)
match point:
    case Point(x=x, y=y) if x == y:
        print(f'On the diagonal at x=y={x}')
    case Point(x=x, y=y) if x == -y:
        print(f'On the anti-diagonal at x={x}, y={y}')
    case Point(x=x, y=y):
        print(f'Not on a diagonal at x={x}, y={y}')
# Output: Not on a diagonal at x=-1, y=2
