# openskies.py

"""
Import json files from the openskies api for testing
"""

# https://opensky-network.org/api/states/all
# Doesn't use requests because of usage limits
# really messy

import json
from random import shuffle

def load(filename, gb_only=False, num_only=False):
    """
    Load the json file from the openskies api for testing
    """

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

    with open(filename, encoding="utf-8") as f:
        state = json.load(f)
        state = state["states"]
        shuffle(state)

    result = {}
    iterator = 0

    for aircraft in state:
        # make right format and convert values
        dictionary = dict(zip(headers, aircraft))
        dictionary["icon"] = "plane"

        if dictionary["alt"]:
            dictionary["alt"] = int(dictionary["alt"] * 3.281)

        if dictionary["speed"]:
            dictionary["speed"] = int(dictionary["speed"] * 1.944)

        if num_only:
            try:
                int(dictionary["callsign"][3:])
                numerical_callsign = True
            except ValueError:
                numerical_callsign = False
        else:
            numerical_callsign = True # not the best implementation

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
                del dictionary[delete]
            except KeyError:
                pass

        # add to the result
        if all(dictionary[key] for key in ["lat", "lng", "hdg", "alt", "callsign"]) and numerical_callsign:
            if iterator == 500:
                break
            else:
                if gb_only:
                    if 50 < dictionary["lat"] < 58 and -6 < dictionary["lng"] < 2:
                        result[dictionary["icao24"]] = dictionary
                        iterator += 1
                else:
                    result[dictionary["icao24"]] = dictionary
                    iterator += 1

    return result
