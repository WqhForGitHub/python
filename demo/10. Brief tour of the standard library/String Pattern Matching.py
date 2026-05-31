# ==============================================================================
# 10.5 String Pattern Matching
# ==============================================================================
# https://docs.python.org/3/tutorial/stdlib.html#string-pattern-matching

# --- The re module: regular expression tools for advanced string processing ---
import re

# re.findall: find all matches of a pattern
print(re.findall(r'\bf[a-z]*', 'which foot or hand fell fastest'))
# Output: ['foot', 'fell', 'fastest']

# re.sub: substitute pattern matches
print(re.sub(r'(\b[a-z]+) \1', r'\1', 'cat in the the hat'))
# Output: 'cat in the hat'

# --- When only simple capabilities are needed, string methods are preferred ---
# They are easier to read and debug
print('tea for too'.replace('too', 'two'))
# Output: 'tea for two'

# --- More re examples ---

# re.search: find the first match
match = re.search(r'world', 'hello world')
print(match.group())  # 'world'

# re.match: match at the beginning of the string
match = re.match(r'hello', 'hello world')
print(match.group())  # 'hello'

# re.split: split a string by pattern
print(re.split(r'\W+', 'Words, words, words.'))
# Output: ['Words', 'words', 'words', '']

# --- Using compiled patterns for repeated use ---
pattern = re.compile(r'\d+')
print(pattern.findall('12 drummers, 11 pipers, 10 lords'))
# Output: ['12', '11', '10']

# --- Groups in patterns ---
m = re.match(r'(\w+) (\w+)', 'Isaac Newton')
print(m.group(0))  # 'Isaac Newton' (entire match)
print(m.group(1))  # 'Isaac' (first group)
print(m.group(2))  # 'Newton' (second group)

# --- Named groups ---
m = re.match(r'(?P<first>\w+) (?P<last>\w+)', 'Isaac Newton')
print(m.group('first'))  # 'Isaac'
print(m.group('last'))   # 'Newton'
