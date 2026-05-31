# ==============================================================================
# 9.7 Odds and Ends
# ==============================================================================
# https://docs.python.org/3/tutorial/classes.html#odds-and-ends

# --- Using dataclasses for record-like data types ---
# The idiomatic approach is to use dataclasses for bundling together
# a few named data items (similar to Pascal "record" or C "struct").

from dataclasses import dataclass


@dataclass
class Employee:
    name: str
    dept: str
    salary: int


john = Employee('john', 'computer lab', 1000)
print(john.dept)    # computer lab
print(john.salary)  # 1000
print(john)         # Employee(name='john', dept='computer lab', salary=1000)

# --- Emulating abstract data types ---
# A piece of Python code that expects a particular abstract data type can often
# be passed a class that emulates the methods of that data type instead.


class UpperCaseStringBuffer:
    """Emulates a file object but reads from a string buffer."""

    def __init__(self, text):
        self.text = text
        self.pos = 0

    def read(self):
        result = self.text[self.pos:].upper()
        self.pos = len(self.text)
        return result


buf = UpperCaseStringBuffer('hello world')
print(buf.read())  # HELLO WORLD

# --- Instance method objects have attributes ---
# m.__self__ is the instance object with the method m()
# m.__func__ is the function object corresponding to the method.


class Example:
    def method(self):
        return 'hello'


e = Example()
m = e.method
print(m.__self__)  # <__main__.Example object at ...>
print(m.__func__)  # <function Example.method at ...>
print(m())         # hello
