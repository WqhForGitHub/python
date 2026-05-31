# ==============================================================================
# 6.4 Packages
# ==============================================================================
# https://docs.python.org/3/tutorial/modules.html#packages

# --- What are packages? ---
# Packages are a way of structuring Python's module namespace by using
# "dotted module names". For example, the module name A.B designates a
# submodule named B in a package named A.

# --- Package directory structure ---
# The sound/ directory in this folder is an example package:
#
# sound/                          Top-level package
#   __init__.py                   Initialize the sound package
#   formats/                      Subpackage for file format conversions
#       __init__.py
#       wavread.py
#       wavwrite.py
#       aiffread.py
#       aiffwrite.py
#       auread.py
#       auwrite.py
#   effects/                      Subpackage for sound effects
#       __init__.py
#       echo.py
#       surround.py
#       reverse.py
#   filters/                      Subpackage for filters
#       __init__.py
#       equalizer.py
#       vocoder.py
#       karaoke.py

# --- The __init__.py file ---
# The __init__.py files are required to make Python treat directories
# as packages. In the simplest case, __init__.py can just be an empty file,
# but it can also execute initialization code for the package or set the
# __all__ variable.

# --- Importing submodules from a package ---
# Users of the package can import individual modules from the package:

import sound.effects.echo

# This loads the submodule sound.effects.echo, and must be referenced
# with its full name:
sound.effects.echo.echo_filter("mysound", delay=0.3)
# Output: Applying echo effect: delay=0.3s, decay=0.7

# --- Alternative import: from package import module ---
from sound.effects import surround

# This loads the submodule surround, and makes it available without
# its package prefix:
surround.surround_filter("mysound")
# Output: Applying surround effect: level=1.0

# --- Alternative import: from module import name ---
from sound.filters.equalizer import equalizer_filter

equalizer_filter("mysound", frequency=1000, gain=3)
# Output: Applying equalizer: freq=1000Hz, gain=3dB

# ==============================================================================
# 6.4.1 Importing * From a Package
# ==============================================================================
# https://docs.python.org/3/tutorial/modules.html#importing-from-a-package

# --- What happens with 'from package import *'? ---
# Ideally, one would hope that this somehow goes out to the filesystem,
# finds which submodules are present in the package, and imports them all.
# This can take a long time and may have unwanted side effects.

# --- The __all__ list ---
# The __all__ variable in __init__.py defines the list of module names
# that should be imported when 'from package import *' is encountered.

# In sound/effects/__init__.py, we have:
#   __all__ = ["echo", "surround", "reverse"]

# This means:
#   from sound.effects import *
# will import the three named submodules of the sound package.

# --- Without __all__, import * imports only the package ---
# If __all__ is not defined, 'from sound.effects import *' does NOT
# import all submodules into the local namespace; it only ensures that
# the package sound.effects has been imported (possibly running any
# initialization code in __init__.py) and then imports whatever names
# are defined in the package.

# --- Best practice ---
# Using 'from package import *' is generally discouraged.
# Prefer explicit imports like:
#   from sound.effects import echo

# ==============================================================================
# 6.4.2 Intra-package References
# ==============================================================================
# https://docs.python.org/3/tutorial/modules.html#intra-package-references

# --- Absolute imports ---
# When packages are structured into subpackages, you can use absolute
# imports to refer to sibling subpackages.

# For example, if the module sound.filters.equalizer needs to use the
# echo module in the sound.effects package, it can use:
#   from sound.effects import echo

# --- Relative imports ---
# Relative imports use leading dots to indicate the current and parent
# packages involved in the relative import.
#   from . import echo          # same package (sound.effects)
#   from .. import formats      # parent package (sound)
#   from ..filters import equalizer  # sibling package (sound.filters)

# A single dot (.) means the current package.
# Two dots (..) means the parent package.
# Three dots (...) means the grandparent package, etc.

# --- Example of relative import in sound/effects/surround.py ---
# If surround.py needs to use the echo module:
#   from . import echo          # import echo from the same package

# If surround.py needs to use the formats subpackage:
#   from .. import formats      # import formats from the parent package

# If surround.py needs to use equalizer from filters:
#   from ..filters import equalizer  # import from sibling package

# --- Relative imports are based on the module's name ---
# Since the name of the main module is always "__main__", modules
# that are intended to be used as the main module of a Python
# application must always use absolute imports.

# ==============================================================================
# 6.4.3 Packages in Multiple Directories
# ==============================================================================
# https://docs.python.org/3/tutorial/modules.html#packages-in-multiple-directories

# --- The __path__ attribute ---
# Packages support one more special attribute, __path__.
# This is initialized to be a list containing the name of the directory
# holding the package's __init__.py before the code in that file is executed.

# This variable can be modified; doing so affects future searches for
# modules contained in the package.

# While this feature is not commonly needed, it can be used to extend
# the set of modules found in a package.

print(sound.__path__)
# Output: a _NamespacePath or list containing the package directory path
