# ==============================================================================
# 7.2.2 Saving Structured Data with json
# ==============================================================================
# https://docs.python.org/3/tutorial/inputoutput.html#saving-structured-data-with-json

# Strings can easily be written to and read from a file. Numbers take a bit
# more effort, since the read() method only returns strings. When you want to
# save more complex data types like nested lists and dictionaries, parsing and
# serializing by hand becomes complicated.

# Python allows you to use JSON (JavaScript Object Notation), a popular data
# interchange format. The json module can take Python data hierarchies and
# convert them to string representations (serializing), and reconstruct the
# data from string representations (deserializing).

import json
import tempfile
import os

# --- json.dumps(): serialize to a JSON string ---
x = [1, 'simple', 'list']
print(json.dumps(x))  # [1, "simple", "list"]

# --- json.dump(): serialize to a file ---
tmpdir = tempfile.gettempdir()
jsonfile = os.path.join(tmpdir, 'json_demo.json')

with open(jsonfile, 'w', encoding="utf-8") as f:
    json.dump(x, f)

# --- json.load(): deserialize from a file ---
with open(jsonfile, 'r', encoding="utf-8") as f:
    x_loaded = json.load(f)
    print(x_loaded)  # [1, 'simple', 'list']
    print(type(x_loaded))  # <class 'list'>

# --- Serializing more complex data ---
data = {
    'name': 'Alice',
    'age': 30,
    'hobbies': ['reading', 'coding'],
    'address': {
        'city': 'Wonderland',
        'zip': '12345'
    }
}

# Pretty-printed JSON with indentation
print(json.dumps(data, indent=2))
# Output:
# {
#   "name": "Alice",
#   "age": 30,
#   "hobbies": [
#     "reading",
#     "coding"
#   ],
#   "address": {
#     "city": "Wonderland",
#     "zip": "12345"
#   }
# }

# --- json.dumps() with sort_keys ---
print(json.dumps(data, sort_keys=True))
# {"address": {"city": "Wonderland", "zip": "12345"}, "age": 30, "hobbies": ["reading", "coding"], "name": "Alice"}

# --- json.loads(): deserialize from a string ---
json_string = '{"name": "Bob", "age": 25}'
parsed = json.loads(json_string)
print(parsed)  # {'name': 'Bob', 'age': 25}
print(type(parsed))  # <class 'dict'>

# --- Note: JSON files must be encoded in UTF-8 ---
# Use encoding="utf-8" when opening JSON files for both reading and writing.

# --- Serializing custom objects requires extra effort ---
# This simple technique handles lists and dictionaries, but serializing
# arbitrary class instances requires a custom default function or a JSONEncoder.

# --- pickle vs json ---
# pickle is a Python-specific protocol for serializing arbitrary Python objects.
# It cannot be used to communicate with applications in other languages.
# It is also insecure by default: deserializing pickle data from an untrusted
# source can execute arbitrary code. Use json for interoperability and safety.

# Clean up
os.remove(jsonfile)
