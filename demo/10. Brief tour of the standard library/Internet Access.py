# ==============================================================================
# 10.7 Internet Access
# ==============================================================================
# https://docs.python.org/3/tutorial/stdlib.html#internet-access

# --- urllib.request: retrieving data from URLs ---
from urllib.request import urlopen

# Fetch a web page
with urlopen('https://docs.python.org/3/') as response:
    for line in response:
        line = line.decode()  # Convert bytes to a str
        if 'updated' in line.lower():
            print(line.rstrip())  # Remove trailing newline
            break  # Just show the first match

# --- smtplib: sending mail ---
# Note: this example needs a mailserver running on localhost
import smtplib

# server = smtplib.SMTP('localhost')
# server.sendmail('soothsayer@example.org', 'jcaesar@example.org',
# """To: jcaesar@example.org
# From: soothsayer@example.org
#
# Beware the Ides of March.
# """)
# server.quit()

# --- More urllib examples ---
# Reading the full content of a URL
# content = urlopen('https://example.com').read().decode()

# Handling errors
from urllib.error import URLError, HTTPError

try:
    with urlopen('https://docs.python.org/3/nonexistent-page') as response:
        pass
except HTTPError as e:
    print(f'HTTP Error: {e.code}')  # e.g., 404
except URLError as e:
    print(f'URL Error: {e.reason}')

# --- Parsing URLs ---
from urllib.parse import urlparse, urlunparse, urlencode

# Parse a URL
parsed = urlparse('https://docs.python.org/3/tutorial/stdlib.html?q=test')
print(parsed.scheme)   # 'https'
print(parsed.netloc)   # 'docs.python.org'
print(parsed.path)     # '/3/tutorial/stdlib.html'
print(parsed.query)    # 'q=test'

# Build query strings
params = urlencode({'q': 'python', 'page': 1})
print(params)  # 'q=python&page=1'
