# ==============================================================================
# 10.11 Quality Control
# ==============================================================================
# https://docs.python.org/3/tutorial/stdlib.html#quality-control

# --- The doctest module: validating tests embedded in docstrings ---

def average(values):
    """Computes the arithmetic mean of a list of numbers.

    >>> print(average([20, 30, 70]))
    40.0
    >>> print(average([1, 5, 7]))
    4.333333333333333
    """
    return sum(values) / len(values)


import doctest

# Automatically validate the embedded tests
doctest.testmod(verbose=True)
# Output:
# Trying:
#     print(average([20, 30, 70]))
# Expecting:
#     40.0
# ok
# ...

# --- The unittest module: more comprehensive testing framework ---
import unittest


class TestStatisticalFunctions(unittest.TestCase):

    def test_average(self):
        self.assertEqual(average([20, 30, 70]), 40.0)
        self.assertEqual(round(average([1, 5, 7]), 1), 4.3)
        with self.assertRaises(ZeroDivisionError):
            average([])
        with self.assertRaises(TypeError):
            average(20, 30, 70)

    def test_average_positive(self):
        self.assertGreater(average([1, 2, 3]), 0)


# Run the tests (without calling sys.exit, which would stop the script)
# In a real project, you would run: python -m unittest this_file.py
suite = unittest.TestLoader().loadTestsFromTestCase(TestStatisticalFunctions)
runner = unittest.TextTestRunner(verbosity=2)
runner.run(suite)

# --- Common unittest assertion methods ---
# assertEqual(a, b)       : a == b
# assertNotEqual(a, b)    : a != b
# assertTrue(x)           : bool(x) is True
# assertFalse(x)          : bool(x) is False
# assertIs(a, b)          : a is b
# assertIsNone(x)         : x is None
# assertIn(a, b)          : a in b
# assertIsInstance(a, b)  : isinstance(a, b)
# assertRaises(exc, func) : func() raises exc
