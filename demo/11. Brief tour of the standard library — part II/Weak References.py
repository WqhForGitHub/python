# ==============================================================================
# 11.6 Weak References
# ==============================================================================
# https://docs.python.org/3/tutorial/stdlib2.html#weak-references

# --- The weakref module: tracking objects without creating a reference ---
import weakref
import gc

# Python does automatic memory management (reference counting for most
# objects and garbage collection to eliminate cycles). The memory is freed
# shortly after the last reference to it has been eliminated.
#
# However, sometimes there is a need to track objects only as long as they
# are being used by something else. Unfortunately, just tracking them
# creates a reference that makes them permanent. The weakref module provides
# tools for tracking objects without creating a reference.


class A:
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return str(self.value)


a = A(10)                          # create a reference
d = weakref.WeakValueDictionary()
d['primary'] = a                   # does not create a reference
print(d['primary'])                # fetch the object if it is still alive
# 10

del a                              # remove the one reference
gc.collect()                       # run garbage collection right away

# The entry was automatically removed from the WeakValueDictionary
# when the object was garbage collected:
# d['primary']  # raises KeyError: 'primary'

# --- Typical applications: caching objects that are expensive to create ---
# WeakValueDictionary: values are weak references; entries are removed
# when the referenced object is no longer used elsewhere.
#
# WeakKeyDictionary: keys are weak references; entries are removed
# when the key object is no longer used elsewhere.
#
# WeakSet: a set that holds weak references to its elements.
#
# ref(): creates a weak reference to an object.
# When the object is still alive, calling the reference returns the object;
# when the object has been collected, calling the reference returns None.

obj = A(42)
r = weakref.ref(obj)
print(r())       # 42 (object still alive)
del obj
gc.collect()
print(r())       # None (object has been collected)
