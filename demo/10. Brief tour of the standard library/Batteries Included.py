# ==============================================================================
# 10.12 Batteries Included
# ==============================================================================
# https://docs.python.org/3/tutorial/stdlib.html#batteries-included

# Python has a "batteries included" philosophy. This is best seen through the
# sophisticated and robust capabilities of its larger packages.

# --- xmlrpc.client and xmlrpc.server: remote procedure calls ---
# These modules make implementing remote procedure calls almost trivial.
# No direct knowledge or handling of XML is needed.

# import xmlrpc.client
# import xmlrpc.server

# proxy = xmlrpc.client.ServerProxy('http://localhost:8000/')
# print(proxy.add(2, 3))  # Calls a remote function

# --- The email package: managing email messages ---
# A library for managing email messages, including MIME and other
# RFC 5322-based message documents. Unlike smtplib and poplib which
# actually send and receive messages, the email package has a complete
# toolset for building or decoding complex message structures.

from email.mime.text import MIMEText

msg = MIMEText('Hello, this is the body of the email.')
msg['Subject'] = 'Test Email'
msg['From'] = 'sender@example.com'
msg['To'] = 'recipient@example.com'
print(msg.as_string())

# --- The json package: parsing JSON data ---
import json

# Encode Python objects to JSON
data = {'name': 'Alice', 'age': 30, 'skills': ['Python', 'SQL']}
json_str = json.dumps(data, indent=2)
print(json_str)

# Decode JSON to Python objects
parsed = json.loads(json_str)
print(parsed['name'])  # 'Alice'
print(parsed['skills'])  # ['Python', 'SQL']

# --- The csv module: reading and writing CSV files ---
import csv
import io

# Write CSV
output = io.StringIO()
writer = csv.writer(output)
writer.writerow(['Name', 'Age'])
writer.writerow(['Alice', 30])
writer.writerow(['Bob', 25])
csv_content = output.getvalue()
print(csv_content)

# Read CSV
reader = csv.reader(io.StringIO(csv_content))
for row in reader:
    print(row)

# --- The sqlite3 module: lightweight SQL database ---
# A wrapper for the SQLite database library, providing a persistent
# database that can be updated and accessed using slightly nonstandard SQL.

import sqlite3
import tempfile
import os

with tempfile.TemporaryDirectory() as tmpdir:
    db_path = os.path.join(tmpdir, 'example.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create a table
    cursor.execute('CREATE TABLE stocks (date text, trans text, symbol text, qty real, price real)')

    # Insert a row
    cursor.execute("INSERT INTO stocks VALUES ('2025-01-05', 'BUY', 'RHAT', 100, 35.14)")

    # Query
    cursor.execute('SELECT * FROM stocks')
    print(cursor.fetchall())  # [('2025-01-05', 'BUY', 'RHAT', 100.0, 35.14)]

    conn.close()

# --- Internationalization modules ---
# gettext, locale, and the codecs package support internationalization.

import locale
print(locale.getpreferredencoding())  # e.g., 'cp1252' or 'UTF-8'

import codecs
# codecs supports many text encodings
encoded = codecs.encode('Hello', 'rot_13')
print(encoded)  # 'Uryyb'
