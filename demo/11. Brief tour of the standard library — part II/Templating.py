# ==============================================================================
# 11.2 Templating
# ==============================================================================
# https://docs.python.org/3/tutorial/stdlib2.html#templating

# --- Basic Template usage with $ placeholders ---
from string import Template

# Placeholders are formed by $ with valid Python identifiers.
# Surrounding with braces allows it to be followed by more letters.
# Writing $$ creates a single escaped $:
t = Template('${village}folk send $$10 to $cause.')
print(t.substitute(village='Nottingham', cause='the ditch fund'))
# Nottinghamfolk send $10 to the ditch fund.

# --- substitute() vs safe_substitute() ---
# substitute() raises KeyError when a placeholder is missing:
t = Template('Return the $item to $owner.')
d = dict(item='unladen swallow')

# t.substitute(d)  # raises KeyError: 'owner'

# safe_substitute() leaves placeholders unchanged if data is missing:
print(t.safe_substitute(d))
# Return the unladen swallow to $owner.

# --- Custom delimiter with Template subclasses ---
import time
import os.path

photofiles = ['img_1074.jpg', 'img_1076.jpg', 'img_1077.jpg']


class BatchRename(Template):
    delimiter = '%'  # use % instead of $ as the placeholder delimiter


# Example: a batch renaming utility for photos
# fmt = input('Enter rename style (%d-date %n-seqnum %f-format):  ')
fmt = 'Ashley_%n%f'

t = BatchRename(fmt)
date = time.strftime('%d%b%y')
for i, filename in enumerate(photofiles):
    base, ext = os.path.splitext(filename)
    newname = t.substitute(d=date, n=i, f=ext)
    print('{0} --> {1}'.format(filename, newname))
# img_1074.jpg --> Ashley_0.jpg
# img_1076.jpg --> Ashley_1.jpg
# img_1077.jpg --> Ashley_2.jpg

# Another application for templating is separating program logic from the
# details of multiple output formats. This makes it possible to substitute
# custom templates for XML files, plain text reports, and HTML web reports.
