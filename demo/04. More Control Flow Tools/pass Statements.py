# ==============================================================================
# 4.5 pass Statements
# ==============================================================================
# https://docs.python.org/3/tutorial/controlflow.html#pass-statements

# --- The pass statement does nothing ---
# It can be used when a statement is required syntactically but the
# program requires no action.

# --- Common use: empty class ---
class MyEmptyClass:
    pass

# --- Common use: placeholder for future code ---
# This is commonly used for creating minimal classes:
class Person:
    pass  # TODO: implement this class later

p = Person()
p.name = 'John'  # attributes can be added dynamically
print(p.name)  # John

# --- Common use: empty function stub ---
def initlog(*args):
    pass  # TODO: implement this later
# Remember to implement this!

# --- Common use: empty if/while/for block ---
# while False:
#     pass  # Busy-wait for keyboard interrupt (Ctrl+C)

# --- pass vs ... (Ellipsis) ---
# In Python 3, ... (Ellipsis) can sometimes be used similarly to pass
# as a placeholder, but pass is the standard convention.

def placeholder():
    pass

# --- pass in except blocks ---
# When you want to silently ignore an exception:
try:
    x = 1 / 0
except ZeroDivisionError:
    pass  # silently ignore the error
print('Continuing after error')  # Continuing after error

# --- pass in abstract methods ---
import abc

class AbstractBase(abc.ABC):
    @abc.abstractmethod
    def method(self):
        pass  # Subclasses must override this
