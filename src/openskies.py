# openskies.py

"""
Import json files from the openskies api for testing
"""

# https://opensky-network.org/api/states/all
# Doesn't use requests because of usage limits
# really messy

import json
import lookup

def progress(iteration, total):
    percent = f"{100 * (iteration / float(total)):.1f}"
    filled_length = int(50 * iteration // total)
    bar = "█" * filled_length + "-" * (50 - filled_length)
    print(f"\r|{bar}| {percent}%", end="\r")

def load(filename, gb_only=False, num_only=False):
    """
    Load the json file from the openskies api for testing
    """

    print(f"Importing {filename}...")
    progress(0, 1)

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

    result = {}
    state_length = len(state)
    progress(0, state_length)

    for i in range(state_length):
        aircraft = state[i]

        # make right format and convert values
        dictionary = dict(zip(headers, aircraft))

        if dictionary["alt"]:
            dictionary["alt"] = int(dictionary["alt"] * 3.281)

        if dictionary["speed"]:
            dictionary["speed"] = int(dictionary["speed"] * 1.944)

        if num_only:
            try:
                flight_number = int(dictionary["callsign"][3:])
                numerical_callsign = True
                dictionary["callsign"] = dictionary["callsign"][:3] + str(flight_number)
            except ValueError:
                numerical_callsign = False
        else:
            numerical_callsign = True

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
            dictionary["callsign"] = dictionary["callsign"].strip()
            dictionary["icon"] = lookup.aircraft_icon(dictionary["icao24"])
            if gb_only:
                if 50 < dictionary["lat"] < 58 and -6 < dictionary["lng"] < 2:
                    result[dictionary["icao24"]] = dictionary
            else:
                result[dictionary["icao24"]] = dictionary

        progress(i, state_length)

    print()
    return result
