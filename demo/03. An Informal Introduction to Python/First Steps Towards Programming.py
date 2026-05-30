# ==============================================================================
# 3.2 First Steps Towards Programming
# ==============================================================================
# https://docs.python.org/3/tutorial/introduction.html#first-steps-towards-programming

# --- Fibonacci series: the sum of two elements defines the next ---
a, b = 0, 1
while a < 10:
    print(a, end=' ')
    a, b = b, a + b
# Output: 0 1 1 2 3 5 8
print()  # newline after the loop

# --- Key concepts demonstrated above ---

# 1. Multiple assignment: a, b = 0, 1
#    The variables a and b simultaneously get the new values 0 and 1.

# 2. The while loop executes as long as the condition (a < 10) is true.
#    In Python, any non-zero integer value is true; zero is false.

# 3. The body of the loop is indented.
#    Python uses indentation to group statements (no braces needed).

# 4. print() function with keyword argument 'end'
#    By default, print() adds a newline. 'end' changes what is printed at the end.

# --- The print() function ---
i = 256 * 256
print('The value of i is', i)  # The value of i is 65536

# --- Keyword argument 'end' to avoid newline ---
a, b = 0, 1
while a < 1000:
    print(a, end=',')
    a, b = b, a + b
# Output: 0,1,1,2,3,5,8,13,21,34,55,89,144,233,377,610,987,
print()

# --- Keyword argument 'sep' to change separator ---
print('Hello', 'World', sep=', ')  # Hello, World

# --- if/elif/else statements ---
x = int(input("Please enter an integer: "))
if x < 0:
    print('Negative')
elif x == 0:
    print('Zero')
elif x == 1:
    print('Single')
else:
    print('More')

# --- for statements ---
# Iterate over any sequence (list, string, etc.)
words = ['cat', 'window', 'defenestrate']
for w in words:
    print(w, len(w))

# --- The range() function ---
# range(n) generates numbers from 0 to n-1
for i in range(5):
    print(i, end=' ')  # 0 1 2 3 4
print()

# range(start, stop) — from start to stop-1
for i in range(5, 10):
    print(i, end=' ')  # 5 6 7 8 9
print()

# range(start, stop, step) — with step
for i in range(0, 10, 3):
    print(i, end=' ')  # 0 3 6 9
print()

for i in range(-10, -100, -30):
    print(i, end=' ')  # -10 -40 -70
print()

# range() returns an iterable object, not a list
print(range(10))           # range(0, 10)
print(list(range(5)))      # [0, 1, 2, 3, 4]  (convert to list)

# --- break and continue ---
# break exits the nearest enclosing for or while loop
for n in range(2, 10):
    for x in range(2, n):
        if n % x == 0:
            print(f'{n} equals {x} * {n // x}')
            break
    else:
        # The else clause runs when the loop completes without hitting break
        print(f'{n} is a prime number')

# continue skips to the next iteration
for num in range(2, 10):
    if num % 2 == 0:
        print(f'Found an even number: {num}')
        continue
    print(f'Found an odd number: {num}')
