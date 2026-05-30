# ==============================================================================
# 4.4 break and continue Statements, and else Clauses on Loops
# ==============================================================================
# https://docs.python.org/3/tutorial/controlflow.html#break-and-continue-statements-and-else-clauses-on-loops

# --- break statement ---
# break exits the nearest enclosing for or while loop.

# Example: finding prime numbers
for n in range(2, 10):
    for x in range(2, n):
        if n % x == 0:
            print(f'{n} equals {x} * {n // x}')
            break
    else:
        # The else clause belongs to the for loop, NOT the if statement.
        # It executes when the loop completes without encountering a break.
        print(f'{n} is a prime number')
# Output:
# 2 is a prime number
# 3 is a prime number
# 4 equals 2 * 2
# 5 is a prime number
# 6 equals 2 * 3
# 7 is a prime number
# 8 equals 2 * 4
# 9 equals 3 * 3

# --- The else clause on for loops ---
# A for loop's else clause runs when no break occurs.
# This is different from if-else; it's more like a "no-break" clause.

# Example: searching for an item
items = [1, 3, 5, 7, 9]
target = 6
for item in items:
    if item == target:
        print(f'Found {target}!')
        break
else:
    print(f'{target} not found in the list')
# Output: 6 not found in the list

# When the target IS found:
target = 5
for item in items:
    if item == target:
        print(f'Found {target}!')
        break
else:
    print(f'{target} not found in the list')
# Output: Found 5!

# --- The else clause on while loops ---
# Similarly, while loops can have an else clause that runs when
# the condition becomes false (i.e., the loop ends normally).
n = 5
while n > 0:
    print(n, end=' ')
    n -= 1
else:
    print('Blastoff!')
# Output: 5 4 3 2 1 Blastoff!

# --- continue statement ---
# continue skips the rest of the current iteration and moves to the next.

for num in range(2, 10):
    if num % 2 == 0:
        print(f'Found an even number: {num}')
        continue
    print(f'Found an odd number: {num}')
# Output:
# Found an even number: 2
# Found an odd number: 3
# Found an even number: 4
# Found an odd number: 5
# Found an even number: 6
# Found an odd number: 7
# Found an even number: 8
# Found an odd number: 9

# --- break vs continue ---
# break: completely exits the loop
# continue: skips to the next iteration of the loop

# Example showing the difference:
print('--- break example ---')
for i in range(5):
    if i == 3:
        break  # stops the loop entirely
    print(i, end=' ')
print()  # 0 1 2

print('--- continue example ---')
for i in range(5):
    if i == 3:
        continue  # skips only i=3
    print(i, end=' ')
print()  # 0 1 2 4
