# ==============================================================================
# 4.2 for Statements
# ==============================================================================
# https://docs.python.org/3/tutorial/controlflow.html#for-statements

# --- Basic for loop over a list ---
words = ['cat', 'window', 'defenestrate']
for w in words:
    print(w, len(w))
# Output:
# cat 3
# window 6
# defenestrate 12

# --- for loop over a string ---
for ch in 'Python':
    print(ch, end=' ')
print()  # P y t h o n

# --- for loop over a dictionary ---
knights = {'gallahad': 'the pure', 'robin': 'the brave'}
for k, v in knights.items():
    print(k, v)
# Output:
# gallahad the pure
# robin the brave

# --- Iterating over a copy of a list ---
# If you need to modify the sequence you are iterating over while inside the loop,
# it is recommended that you first make a copy.
words = ['cat', 'window', 'defenestrate']
for w in words[:]:  # Loop over a slice copy of the entire list
    if len(w) > 6:
        words.insert(0, w)
print(words)  # ['defenestrate', 'cat', 'window', 'defenestrate']

# --- Dangers of modifying a list while iterating ---
# Without the copy, the loop can behave unexpectedly:
# (This is a common pitfall - avoid doing this!)
# words = ['cat', 'window', 'defenestrate']
# for w in words:
#     if len(w) > 6:
#         words.insert(0, w)
# This would create an infinite loop because items keep getting added!

# --- The enumerate() function ---
# When you need both the index and value while iterating:
words = ['cat', 'window', 'defenestrate']
for i, w in enumerate(words):
    print(f'{i}: {w}')
# Output:
# 0: cat
# 1: window
# 2: defenestrate

# --- The zip() function ---
# Loop over two or more sequences at the same time:
questions = ['name', 'quest', 'favorite color']
answers = ['lancelot', 'the holy grail', 'blue']
for q, a in zip(questions, answers):
    print(f'What is your {q}?  It is {a}.')
# Output:
# What is your name?  It is lancelot.
# What is your quest?  It is the holy grail.
# What is your favorite color?  It is blue.

# --- The reversed() function ---
# Loop over a sequence in reverse:
for i in reversed(range(1, 10, 2)):
    print(i, end=' ')
print()  # 9 7 5 3 1

# --- The sorted() function ---
# Loop over a sequence in sorted order:
basket = ['apple', 'orange', 'apple', 'pear', 'orange', 'banana']
for f in sorted(set(basket)):
    print(f, end=' ')
print()  # apple banana orange pear
