# ==============================================================================
# 9.5 Inheritance
# ==============================================================================
# https://docs.python.org/3/tutorial/classes.html#inheritance

# --- Basic inheritance syntax ---
# class DerivedClassName(BaseClassName):
#     <statement-1>
#     .
#     .
#     .
#     <statement-N>


class Animal:
    def speak(self):
        return 'Some sound'

    def info(self):
        return 'I am an animal'


class Dog(Animal):
    def speak(self):
        return 'Woof!'


d = Dog()
print(d.speak())  # Woof!  (overridden method)
print(d.info())   # I am an animal  (inherited method)

# --- Base class from another module ---
# class DerivedClassName(modname.BaseClassName):

# --- Method resolution: search proceeds to look in the base class ---


class Base:
    def greet(self):
        return 'Hello from Base'


class Derived(Base):
    pass


obj = Derived()
print(obj.greet())  # Hello from Base  (found in Base class)

# --- Derived classes may override methods of their base classes ---
# A method of a base class that calls another method may end up calling
# a method of a derived class that overrides it.


class Base2:
    def method_a(self):
        return 'Base.method_a'

    def method_b(self):
        return self.method_a()  # may call overridden version


class Derived2(Base2):
    def method_a(self):
        return 'Derived.method_a'


obj2 = Derived2()
print(obj2.method_b())  # Derived.method_a  (calls overridden method)

# --- Calling the base class method directly ---


class Base3:
    def greet(self):
        return 'Hello from Base'


class Derived3(Base3):
    def greet(self):
        return Base3.greet(self) + ' and Derived'


print(Derived3().greet())  # Hello from Base and Derived

# --- isinstance() and issubclass() ---
print(isinstance(d, Dog))     # True
print(isinstance(d, Animal))  # True
print(isinstance(d, int))     # False

print(issubclass(Dog, Animal))  # True
print(issubclass(bool, int))    # True
print(issubclass(float, int))   # False

# ==============================================================================
# 9.5.1 Multiple Inheritance
# ==============================================================================
# https://docs.python.org/3/tutorial/classes.html#multiple-inheritance

# --- Multiple inheritance syntax ---
# class DerivedClassName(Base1, Base2, Base3):
#     <statement-1>
#     .
#     .
#     .
#     <statement-N>

# Attribute search is depth-first, left-to-right, not searching twice
# in the same class where there is an overlap in the hierarchy.


class Base1:
    def method(self):
        return 'Base1.method'


class Base2:
    def method(self):
        return 'Base2.method'

    def extra(self):
        return 'Base2.extra'


class Multi(Base1, Base2):
    pass


m = Multi()
print(m.method())  # Base1.method  (Base1 is searched first)
print(m.extra())   # Base2.extra   (not found in Base1, so searches Base2)

# --- Using super() for cooperative method calls ---
# The method resolution order changes dynamically to support cooperative calls
# to super().


class A:
    def greet(self):
        return 'A'


class B(A):
    def greet(self):
        return 'B -> ' + super().greet()


class C(A):
    def greet(self):
        return 'C -> ' + super().greet()


class D(B, C):
    def greet(self):
        return 'D -> ' + super().greet()


print(D().greet())  # D -> B -> C -> A
print(D.__mro__)    # (<class '__main__.D'>, <class '__main__.B'>, <class '__main__.C'>, <class '__main__.A'>, <class 'object'>)
