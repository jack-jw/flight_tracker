# opensky.py

"""
Import json files from the OpenSky API for testing
"""

# https://opensky-network.org/api/states/all
# Doesn't use requests because of usage limits
# really messy

import json
from random import shuffle
import lookup

def _progress(iteration, total, message=""):
    percent = f"{100 * (iteration / float(total)):.1f}"
    filled_length = int(50 * iteration // total)
    progress_bar = "█" * filled_length + " " * (50 - filled_length)
    progress_line = f"\r{progress_bar} {percent}% {message[:7].ljust(7)}"
    print(progress_line, end="\r")

def _format(individual):
    headers = [
        "icao24",
        "callsign",
        "origin_country",
        "time_position",
        "last_contact",
        "lng",
        "lat",
        "alt",
        "on_ground",
        "speed",
        "hdg",
        "vspeed",
        "sensors",
        "baro_alt",
        "squawk",
        "spi",
        "position_source",
        "category"
    ]

    result = dict(zip(headers, individual))

    # delete unnecessary keys to save bandwidth
    for delete in ("origin_country",
                   "time_position",
                   "last_contact",
                   "on_ground",
                   "sensors",
                   "baro_alt",
                   "squawk",
                   "spi",
                   "position_source",
                   "category"):
        try:
            del result[delete]
        except KeyError:
            pass

    if all(result[key] for key in ["lat", "lng", "hdg", "speed", "callsign"]):

        # these ones aren't completely necessary for it to be functional
        if "alt" in result and result["alt"]:
            result["alt"] *= 3.28084 # to ft
        else:
            result["alt"] = 0 # to not cause problems

        if "vspeed" in result and result["vspeed"]:
            result["vspeed"] *= 3.2808399 # to ft/s
        else:
            result["vspeed"] = 0 # to not cause problems

        result["speed"] *= 1.943844 # to kts
        result["callsign"] = (result["callsign"][:3] + result["callsign"][3:].lstrip("0")).strip()
        result.update(lookup.basic(result["icao24"]))
        return result
    return None

def load(filename, num_only=False):
    """
    Load the json file from the OpenSky API for testing
    """

    _progress(0, 1)

    with open(filename, encoding="utf-8") as f:
        state = json.load(f)
        state = state["states"]

    state_len = len(state)
    result = {}
    iterator = 0
    loaded = 0

    for aircraft in state:
        iterator += 1
        formatted_aircraft = _format(aircraft)
        if not formatted_aircraft or (num_only and not formatted_aircraft["callsign"][3:].isdigit()):
            continue

        loaded += 1
        result[formatted_aircraft["icao24"]] = formatted_aircraft
        _progress(iterator, state_len, message=formatted_aircraft["callsign"])

    _progress(1, 1)
    print(f"\n{loaded} aircraft loaded out of {iterator} in set")
    return result

def preemit(aircraft_set):
    aircraft_list = list(aircraft_set.items())
    shuffle(aircraft_list)
    shuffled_aircraft = dict(aircraft_list[:750])
    return shuffled_aircraft
