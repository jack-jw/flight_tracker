# paths.py

"""
Definitions for paths to keep them consistent
Dot paths should be relative to the working directory
"""

from platform import system
from os import mkdir
from os.path import expanduser, exists, join

_USER = expanduser("~")

if system() == "Darwin":
    INSTANCE = join(_USER, "Library/Application Support/flight_tracker")
    LOCAL = join(_USER, "Library/Caches/flight_tracker")

elif system() == "Linux":
    # need to test this
    for folder in (join(_USER, ".local"), join(_USER, ".local/share"), join(_USER, ".cache")):
        if not exists(folder):
            mkdir(folder)

    INSTANCE = join(_USER, ".local/share/flight_tracker")
    LOCAL = join(_USER, ".cache/flight_tracker")

else:
    raise OSError("flight_tracker only runs on macOS and Linux.") # for now

INSTANCE_IMAGES = join(INSTANCE, "images")
LOCAL_IMAGES = join(LOCAL, "images")

_PATHS = (INSTANCE, INSTANCE_IMAGES, LOCAL, LOCAL_IMAGES)

for folder in _PATHS:
    if not exists(folder):
        mkdir(folder)
