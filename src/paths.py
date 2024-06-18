# paths.py

"""
Definitions for paths to keep them consistent
Dot paths should be relative to the working directory
"""

from platform import system
from os import mkdir
from os.path import abspath, expanduser, exists, join

if system() == "Darwin":
    _LIBRARY = expanduser("~/Library")
    INSTANCE = join(_LIBRARY, "Application Support/flight_tracker")
    LOCAL = join(_LIBRARY, "Caches/flight_tracker")
else:
    INSTANCE = abspath("../instance")
    LOCAL = join(INSTANCE, "local")

INSTANCE_IMAGES = join(INSTANCE, "images")
LOCAL_IMAGES = join(LOCAL, "images")

_PATHS = (INSTANCE, INSTANCE_IMAGES, LOCAL, LOCAL_IMAGES)

for folder in _PATHS:
    if not exists(folder):
        mkdir(folder)
