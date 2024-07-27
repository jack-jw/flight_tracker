# instance.py

"""
Layer between the rest of the code and individual setups (platforms, user settings, etc.)

  - Paths to files
    Path.localdb - string path to the local database
    Path.instancedb - string path to the instance database
    Path.settings - string path to the settings file

  - Setting managment
    Settings.defaults - default settings as a dictionary
    Settings.get() - get an individual setting or "all"
    Settings.set() - set an individual setting
"""

# fix mess

from getpass import getuser
from os import name, makedirs
from os.path import dirname, exists, expanduser
from sys import version_info
from platform import system

if name != "posix":
    raise OSError("flight_tracker only runs on UNIX-like systems.")
    # for now (no windows PC to test on)

if version_info < (3, 10): # requires Python 3.10+
    raise RuntimeError("flight_tracker requires Python 3.10 or above.")

class Path:
    """
    Get paths

    Constants:
        Path.localdb - string path to the local database
        Path.instancedb - string path to the instance database
        Path.settings - string path to the settings file
    """

    localdb = instancedb = settings = expanduser("~")
    if system() == "Darwin":
        localdb += "/Library/Caches/flight_tracker.db"
        instancedb += "/Library/Application Support/flight_tracker.db"
        settings += "/Library/Preferences/flight_tracker.plist"
    else:
        # not the best implementation
        # might be better to put scripts and these together for Linux/non-Mac UNIX?
        localdb += "/.flight_tracker/local.db"
        instancedb += "/.flight_tracker/instance.db"
        settings += "/.flight_tracker/settings.json"

    for file in (localdb, instancedb, settings):
        makedirs(dirname(file), exist_ok=True)

class Settings:
    """
    Manage settings
    Works during run-time
    * The file is not re-read during run-time - restart after updating it

    Functions:
        Settings.get() - get an individual setting or "all"
        Settings.set() - set an individual setting

    Constants:
        Settings.defaults - default settings as a dictionary
    """

    defaults = {
        "name": getuser(),
        "colour": "#3478F6",
        "port": 5003,
        "usewikimedia": False,
        "fontdisambiguation": False
    }

    # Check system
    if system() == "Darwin":
        from plistlib import load, dump
        mode = "b"
    else:
        from json import load, dump
        mode = ""

    # Make settings file if it doesn't exist
    if not exists(Path.settings):
        with open(Path.settings, "w" + mode) as sf:
            dump({}, sf)

    # Load the settings from the file
    with open(Path.settings, "r" + mode) as sf:
        preferences = load(sf)

    @staticmethod
    def get(setting=False):
        """
        Get a setting (or all settings when passed nothing)
        Takes the setting's name as a string
        Returns the setting in its associated type
        """

        if not setting:
            return {**Settings.defaults, **Settings.preferences}
        return {**Settings.defaults, **Settings.preferences}.get(setting)

    @staticmethod
    def set(setting, value):
        """
        Set a setting
        Takes the setting's name as a string and the setting's value
        The setting's value should be its associated type (will not check for you)
        """

        Settings.preferences[setting] = value
        with open(Path.settings, "w" + Settings.mode) as sf:
            Settings.dump(Settings.preferences, sf)
