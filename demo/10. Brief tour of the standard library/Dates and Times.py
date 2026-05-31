# ==============================================================================
# 10.8 Dates and Times
# ==============================================================================
# https://docs.python.org/3/tutorial/stdlib.html#dates-and-times

# --- The datetime module: manipulating dates and times ---
import datetime as dt

# dates are easily constructed and formatted
now = dt.date.today()
print(now)
# Output: e.g., datetime.date(2025, 5, 31)

# strftime: format a date as a string
print(now.strftime("%m-%d-%y. %d %b %Y is a %A on the %d day of %B."))
# Output: e.g., '05-31-25. 31 May 2025 is a Saturday on the 31 day of May.'

# --- Dates support calendar arithmetic ---
birthday = dt.date(1964, 7, 31)
age = now - birthday
print(age.days)  # Number of days between the two dates

# --- datetime objects include both date and time ---
now_datetime = dt.datetime.now()
print(now_datetime)

# Format datetime
print(now_datetime.strftime("%Y-%m-%d %H:%M:%S"))

# --- Timedelta: representing durations ---
delta = dt.timedelta(days=100)
future = now + delta
print(f"100 days from now: {future}")

# --- Parsing strings into dates ---
# strptime: parse a string into a date/datetime
date_str = '2025-01-15'
parsed_date = dt.datetime.strptime(date_str, '%Y-%m-%d')
print(parsed_date)
# Output: datetime.datetime(2025, 1, 15, 0, 0)

# --- time module: lower-level time functions ---
import time

# Current time in seconds since the epoch
print(time.time())

# Formatted time string
print(time.strftime('%Y-%m-%d %H:%M:%S'))

# Sleep for a short time (demonstration)
start = time.time()
time.sleep(0.01)  # Sleep for 10 milliseconds
elapsed = time.time() - start
print(f"Slept for approximately {elapsed:.3f} seconds")
