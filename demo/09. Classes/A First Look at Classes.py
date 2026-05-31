# ==============================================================================
# 9.3 A First Look at Classes
# ==============================================================================
# https://docs.python.org/3/tutorial/classes.html#a-first-look-at-classes

# ==============================================================================
# 9.3.1 Class Definition Syntax
# ==============================================================================
# https://docs.python.org/3/tutorial/classes.html#class-definition-syntax

# --- The simplest form of class definition ---
# class ClassName:
#     <statement-1>
#     .
#     .
#     .
#     <statement-N>

# Class definitions must be executed before they have any effect.
# The statements inside a class definition will usually be function definitions.
# When a class definition is entered, a new namespace is created and used as
# the local scope. When the class definition is left normally, a class object
# is created.

# ==============================================================================
# 9.3.2 Class Objects
# ==============================================================================
# https://docs.python.org/3/tutorial/classes.html#class-objects

# --- Class objects support two kinds of operations: attribute references and instantiation ---


class MyClass:
    """A simple example class"""
    i = 12345

    def f(self):
        return 'hello world'


# --- Attribute references ---
print(MyClass.i)   # 12345
print(MyClass.f)   # <function MyClass.f at ...>
print(MyClass.__doc__)  # A simple example class

# Class attributes can also be assigned to
MyClass.i = 99999
print(MyClass.i)   # 99999
MyClass.i = 12345  # restore

# --- Class instantiation ---
x = MyClass()  # creates a new instance of the class
print(type(x))  # <class '__main__.MyClass'>

# --- The __init__() method ---
# The instantiation operation creates an empty object by default.
# To create objects with instances customized to a specific initial state,
# define a __init__() method.


class Complex:
    def __init__(self, realpart, imagpart):
        self.r = realpart
        self.i = imagpart


x = Complex(3.0, -4.5)
print(x.r, x.i)  # 3.0 -4.5

# ==============================================================================
# 9.3.3 Instance Objects
# ==============================================================================
# https://docs.python.org/3/tutorial/classes.html#instance-objects

# --- Data attributes ---
# Data attributes need not be declared; they spring into existence when
# they are first assigned to.


class MyClass2:
    """A simple example class"""
    i = 12345

    def f(self):
        return 'hello world'


x = MyClass2()

# Data attributes can be added on the fly
x.counter = 1
while x.counter < 10:
    x.counter = x.counter * 2
print(x.counter)  # 16
del x.counter

# ==============================================================================
# 9.3.4 Method Objects
# ==============================================================================
# https://docs.python.org/3/tutorial/classes.html#method-objects

# --- Calling a method ---


class MyClass3:
    """A simple example class"""
    i = 12345

    def f(self):
        return 'hello world'


x = MyClass3()
print(x.f())  # hello world

# --- Method objects can be stored and called later ---
xf = x.f
print(xf())  # hello world

# --- The instance object is passed as the first argument ---
# x.f() is exactly equivalent to MyClass3.f(x)
print(MyClass3.f(x))  # hello world

# ==============================================================================
# 9.3.5 Class and Instance Variables
# ==============================================================================
# https://docs.python.org/3/tutorial/classes.html#class-and-instance-variables

# --- Instance variables are unique to each instance ---
# --- Class variables are shared by all instances ---


class Dog:
    kind = 'canine'         # class variable shared by all instances

    def __init__(self, name):
        self.name = name    # instance variable unique to each instance


d = Dog('Fido')
e = Dog('Buddy')
print(d.kind)   # canine  (shared by all dogs)
print(e.kind)   # canine  (shared by all dogs)
print(d.name)   # Fido    (unique to d)
print(e.name)   # Buddy   (unique to e)

# --- Mistaken use of a class variable with mutable objects ---


class DogBad:
    tricks = []             # mistaken use of a class variable

    def __init__(self, name):
        self.name = name

    def add_trick(self, trick):
        self.tricks.append(trick)


d = DogBad('Fido')
e = DogBad('Buddy')
d.add_trick('roll over')
e.add_trick('play dead')
print(d.tricks)  # ['roll over', 'play dead']  -- unexpectedly shared by all dogs!

# --- Correct design: use an instance variable instead ---


class DogGood:
    def __init__(self, name):
        self.name = name
        self.tricks = []    # creates a new empty list for each dog

    def add_trick(self, trick):
        self.tricks.append(trick)


d = DogGood('Fido')
e = DogGood('Buddy')
d.add_trick('roll over')
e.add_trick('play dead')
print(d.tricks)  # ['roll over']
print(e.tricks)  # ['play dead']
