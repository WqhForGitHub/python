# ==============================================================================
# 11.7 Tools for Working with Lists
# ==============================================================================
# https://docs.python.org/3/tutorial/stdlib2.html#tools-for-working-with-lists

# Many data structure needs can be met with the built-in list type. However,
# sometimes there is a need for alternative implementations with different
# performance trade-offs.

# --- array: compact arrays of homogeneous data ---
from array import array

# The array module provides an array object that is like a list that stores
# only homogeneous data and stores it more compactly. The following example
# shows an array of numbers stored as two byte unsigned binary numbers
# (typecode "H") rather than the usual 16 bytes per entry for regular
# lists of Python int objects:
a = array('H', [4000, 10, 700, 22222])
print(sum(a))       # 26932
print(a[1:3])       # array('H', [10, 700])

# Type codes:
# 'b' signed char, 'B' unsigned char, 'h' signed short, 'H' unsigned short,
# 'i' signed int, 'I' unsigned int, 'f' float, 'd' double, etc.

# --- collections.deque: fast appends and pops from both ends ---
from collections import deque

# A deque is like a list with faster appends and pops from the left side
# but slower lookups in the middle. Well suited for queues and breadth-first
# tree searches:
d = deque(["task1", "task2", "task3"])
d.append("task4")
print("Handling", d.popleft())
# Handling task1

# Example: breadth-first search pattern
# unsearched = deque([starting_node])
#
# def breadth_first_search(unsearched):
#     node = unsearched.popleft()
#     for m in gen_moves(node):
#         if is_goal(m):
#             return m
#         unsearched.append(m)

# --- bisect: functions for manipulating sorted lists ---
import bisect

# bisect.insort() inserts an item into a sorted list while maintaining order:
scores = [(100, 'perl'), (200, 'tcl'), (400, 'lua'), (500, 'python')]
bisect.insort(scores, (300, 'ruby'))
print(scores)
# [(100, 'perl'), (200, 'tcl'), (300, 'ruby'), (400, 'lua'), (500, 'python')]

# bisect.bisect() finds the insertion point in a sorted list:
data = [10, 20, 30, 40, 50]
print(bisect.bisect(data, 25))  # 2 (would insert at index 2)

# --- heapq: heap-based priority queue ---
from heapq import heapify, heappop, heappush

# The heapq module provides functions for implementing heaps based on
# regular lists. The lowest valued entry is always kept at position zero.
# Useful for applications which repeatedly access the smallest element
# but do not want to run a full list sort:
data = [1, 3, 5, 7, 9, 2, 4, 6, 8, 0]
heapify(data)                     # rearrange the list into heap order
heappush(data, -5)                # add a new entry
print([heappop(data) for i in range(3)])  # fetch the three smallest entries
# [-5, 0, 1]
