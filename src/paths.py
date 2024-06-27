# paths.py

"""
Calculates paths for different OSes, to be used elsewhere
"""

from platform import system
from os import name, makedirs
from os.path import expanduser, join

if name == "posix":
    _USER = expanduser("~")
    if system() == "Darwin":
        INSTANCE = join(_USER, "Library/Application Support/flight_tracker")
        LOCAL = join(_USER, "Library/Caches/flight_tracker")
    else:
        INSTANCE = join(_USER, ".local/share/flight_tracker")
        LOCAL = join(_USER, ".cache/flight_tracker")
else:
    raise OSError("flight_tracker only runs on UNIX-like systems.")
    # for now (no windows PC to test on)

INSTANCE_IMAGES = join(INSTANCE, "images")
LOCAL_IMAGES = join(LOCAL, "images")

_PATHS = (INSTANCE, INSTANCE_IMAGES, LOCAL, LOCAL_IMAGES)

for folder in _PATHS:
    makedirs(folder, exist_ok=True)
