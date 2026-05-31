# ==============================================================================
# 10.10 Performance Measurement
# ==============================================================================
# https://docs.python.org/3/tutorial/stdlib.html#performance-measurement

# --- The timeit module: measuring execution time ---
from timeit import Timer

# Compare tuple swapping vs traditional swap
# Traditional swap: t=a; a=b; b=t
t1 = Timer('t=a; a=b; b=t', 'a=1; b=2')
print(f"Traditional swap: {t1.timeit():.6f} seconds")

# Pythonic swap: a, b = b, a
t2 = Timer('a,b = b,a', 'a=1; b=2')
print(f"Pythonic swap:    {t2.timeit():.6f} seconds")

# --- Using timeit from the command line ---
# python -m timeit 'a,b = b,a' --setup='a=1; b=2'

# --- timeit.timeit: simpler interface ---
import timeit

# Measure a simple expression
result = timeit.timeit('"-".join(str(n) for n in range(100))', number=10000)
print(f"join with generator: {result:.4f}s")

result = timeit.timeit('"-".join([str(n) for n in range(100)])', number=10000)
print(f"join with list comp: {result:.4f}s")

result = timeit.timeit('"-".join(map(str, range(100)))', number=10000)
print(f"join with map:       {result:.4f}s")

# --- The profile and pstats modules ---
# For identifying time-critical sections in larger blocks of code,
# use profile and pstats instead of timeit's fine-grained measurements.

# Example: profiling a function
# import profile
# def my_function():
#     total = sum(range(10000))
#     return total
# profile.run('my_function()')
