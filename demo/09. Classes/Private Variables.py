# ==============================================================================
# 9.6 Private Variables
# ==============================================================================
# https://docs.python.org/3/tutorial/classes.html#private-variables

# --- Convention: underscore prefix means non-public ---
# A name prefixed with an underscore (e.g. _spam) should be treated as
# a non-public part of the API.

# --- Name mangling ---
# Any identifier of the form __spam (at least two leading underscores,
# at most one trailing underscore) is textually replaced with
# _classname__spam, where classname is the current class name with
# leading underscore(s) stripped.


class MyClass:
    def __init__(self):
        self.public = 'public'
        self._internal = 'internal'       # convention: non-public
        self.__private = 'private'        # name mangling applied

    def __private_method(self):
        return 'private method'

    def get_private(self):
        return self.__private


obj = MyClass()
print(obj.public)     # public
print(obj._internal)  # internal  (accessible but convention says don't)
# print(obj.__private)  # AttributeError! Name has been mangled.
print(obj._MyClass__private)       # private  (access via mangled name)
print(obj.get_private())           # private  (access via public method)
print(obj._MyClass__private_method())  # private method

# --- Name mangling helps avoid name clashes with subclasses ---


class Mapping:
    def __init__(self, iterable):
        self.items_list = []
        self.__update(iterable)

    def update(self, iterable):
        for item in iterable:
            self.items_list.append(item)

    __update = update   # private copy of original update() method


class MappingSubclass(Mapping):
    def update(self, keys, values):
        # provides new signature for update()
        # but does not break __init__()
        for item in zip(keys, values):
            self.items_list.append(item)


m = Mapping(['a', 'b'])
print(m.items_list)  # ['a', 'b']

ms = MappingSubclass([])
ms.update(['x', 'y'], [1, 2])
print(ms.items_list)  # [('x', 1), ('y', 2)]

# The above example works even if MappingSubclass were to introduce a
# __update identifier since it is replaced with _Mapping__update in the
# Mapping class and _MappingSubclass__update in the MappingSubclass class.

# --- Name mangling details ---
# Note: the mangling rules are designed mostly to avoid accidents;
# it still is possible to access or modify a variable that is considered private.


class Demo:
    __secret = 'mangled'


print(Demo._Demo__secret)  # mangled  (accessible via mangled name)
