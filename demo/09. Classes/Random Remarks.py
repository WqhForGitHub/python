# ==============================================================================
# 9.4 Random Remarks
# ==============================================================================
# https://docs.python.org/3/tutorial/classes.html#random-remarks

# --- Attribute lookup prioritizes the instance over the class ---


class Warehouse:
    purpose = 'storage'
    region = 'west'


w1 = Warehouse()
print(w1.purpose, w1.region)  # storage west

w2 = Warehouse()
w2.region = 'east'
print(w2.purpose, w2.region)  # storage east

# --- Function objects can be assigned to class attributes ---


# Function defined outside the class
def f1(self, x, y):
    return min(x, x + y)


class C:
    f = f1

    def g(self):
        return 'hello world'

    h = g


# f, g and h are all attributes of class C that refer to function objects,
# and consequently they are all methods of instances of C.
obj = C()
print(obj.f(3, -1))  # -1  (min(3, 2))
print(obj.g())       # hello world
print(obj.h())       # hello world  (h is equivalent to g)

# --- Methods may call other methods by using method attributes of self ---


class Bag:
    def __init__(self):
        self.data = []

    def add(self, x):
        self.data.append(x)

    def addtwice(self, x):
        self.add(x)
        self.add(x)


b = Bag()
b.addtwice(5)
print(b.data)  # [5, 5]

# --- Each value is an object, and therefore has a class (also called its type) ---
print(b.__class__)  # <class '__main__.Bag'>
