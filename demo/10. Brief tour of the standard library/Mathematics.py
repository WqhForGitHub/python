# ==============================================================================
# 10.6 Mathematics
# ==============================================================================
# https://docs.python.org/3/tutorial/stdlib.html#mathematics

# --- The math module: access to C library functions for floating-point math ---
import math

print(math.cos(math.pi / 4))
# Output: 0.7071067811865476

print(math.log(1024, 2))
# Output: 10.0

# Other useful math functions
print(math.ceil(3.2))    # 4 (ceiling)
print(math.floor(3.8))   # 3 (floor)
print(math.sqrt(16))     # 4.0 (square root)
print(math.gcd(12, 8))   # 4 (greatest common divisor)

# --- The random module: tools for making random selections ---
import random

# Choose a random element from a sequence
print(random.choice(['apple', 'pear', 'banana']))

# Sample without replacement
print(random.sample(range(100), 10))

# Random float from [0.0, 1.0)
print(random.random())

# Random integer chosen from range(6) => 0 to 5
print(random.randrange(6))

# Random integer in a range
print(random.randint(1, 10))  # inclusive of both endpoints

# Shuffle a list in place
cards = list(range(5))
random.shuffle(cards)
print(cards)

# --- The statistics module: basic statistical properties ---
import statistics

data = [2.75, 1.75, 1.25, 0.25, 0.5, 1.25, 3.5]

print(statistics.mean(data))      # 1.6071428571428572
print(statistics.median(data))    # 1.25
print(statistics.variance(data))  # 1.3720238095238095

# Other statistics functions
print(statistics.stdev(data))       # standard deviation
print(statistics.mode(data))        # most common value: 1.25
print(statistics.quantiles(data))   # cut points for equal-sized groups
