# ==============================================================================
# 8.6 User-defined Exceptions
# ==============================================================================
# https://docs.python.org/3/tutorial/errors.html#user-defined-exceptions

# --- Creating custom exception classes ---
# Programs may name their own exceptions by creating a new exception class.
# Exceptions should typically be derived from the Exception class,
# either directly or indirectly.

# --- Simple custom exception ---
class MyError(Exception):
    pass

try:
    raise MyError('something went wrong')
except MyError as e:
    print(f'Caught: {e}')  # Caught: something went wrong

# --- Custom exception with additional behavior ---
class MyError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

try:
    raise MyError(2 * 2)
except MyError as e:
    print(f'My exception occurred, value: {e.value}')
# Output: My exception occurred, value: 4

# --- Example: custom exception hierarchy ---
# When creating a module that can raise several distinct errors,
# a common practice is to create a base class for exceptions defined
# by that module, and subclass that to create specific exception classes:

class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class InputError(Error):
    """Exception raised for errors in the input.

    Attributes:
        expression -- input expression in which the error occurred
        message   -- explanation of the error
    """

    def __init__(self, expression, message):
        self.expression = expression
        self.message = message


class TransitionError(Error):
    """Raised when an operation attempts a state transition that's not allowed.

    Attributes:
        previous -- state at beginning of transition
        next     -- new state being attempted
        message  -- explanation of why the specific transition is not allowed
    """

    def __init__(self, previous, next_state, message):
        self.previous = previous
        self.next = next_state
        self.message = message


# Using the custom exceptions:
try:
    raise InputError('42 / 0', 'Division by zero is not allowed')
except InputError as e:
    print(f'Error in expression "{e.expression}": {e.message}')
# Output: Error in expression "42 / 0": Division by zero is not allowed

try:
    raise TransitionError('idle', 'running', 'Cannot start without initialization')
except TransitionError as e:
    print(f'Cannot transition from {e.previous} to {e.next}: {e.message}')
# Output: Cannot transition from idle to running: Cannot start without initialization

# --- Catching base class catches all subclasses ---
# Since InputError and TransitionError derive from Error,
# catching Error will catch both:
try:
    raise InputError('bad input', 'invalid format')
except Error as e:
    print(f'Caught an Error: {type(e).__name__}: {e.message}')
# Output: Caught an Error: InputError: invalid format

# --- Most custom exceptions are simple ---
# Many custom exception classes are simple, just giving a descriptive name:
class NetworkError(Exception):
    """Base class for network-related errors."""
    pass


class ConnectionError(NetworkError):
    """Failed to connect to the server."""
    pass


class TimeoutError(NetworkError):
    """Operation timed out."""
    pass


# This allows callers to catch errors at different levels of specificity:
try:
    raise ConnectionError('Server refused connection')
except ConnectionError as e:
    print(f'Specific: {e}')       # Catches ConnectionError specifically
except NetworkError as e:
    print(f'General: {e}')        # Catches any NetworkError subclass

try:
    raise TimeoutError('Request took too long')
except ConnectionError as e:
    print(f'Specific: {e}')
except NetworkError as e:
    print(f'General: {e}')        # Catches TimeoutError as a NetworkError
# Output: General: Request took too long
