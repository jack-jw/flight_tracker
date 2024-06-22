# openskies.py

"""
Import json files from the openskies api for testing
"""

# https://opensky-network.org/api/states/all
# Doesn't use requests because of usage limits
# really messy

import json
from os import cpu_count
from concurrent.futures import ThreadPoolExecutor, as_completed
import lookup

def _progress(iteration, total, message=''):
    percent = f"{100 * (iteration / float(total)):.1f}"
    filled_length = int(50 * iteration // total)
    progress_bar = "█" * filled_length + " " * (50 - filled_length)
    progress_line = f"\r{progress_bar} {percent}% {message}"
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

    if all(result[key] for key in ["lat", "lng", "hdg", "alt", "speed", "callsign"]):
        result["alt"] = int(result["alt"] * 3.281) # to ft
        result["speed"] = int(result["speed"] * 1.944) # to kts
        result["callsign"] = (result["callsign"][:3] + result["callsign"][3:].lstrip("0")).strip()
        result["icon"] = lookup.aircraft_icon(result["icao24"])
        return result
    return None


def load(filename, num_only=False):
    """
    Load the json file from the openskies api for testing
    """

    print(f"Importing {filename}...")
    _progress(0, 1)

    with open(filename, encoding="utf-8") as f:
        state = json.load(f)
        state = state["states"]

    state_len = len(state)
    result = {}
    iterator = 0
    loaded = 0

    with ThreadPoolExecutor(max_workers=cpu_count()) as executor:
        formatted_aircraft = {executor.submit(_format, aircraft): aircraft for aircraft in state}

        for future in as_completed(formatted_aircraft):
            iterator += 1
            fm_aircraft = future.result()
            if fm_aircraft:
                if num_only and not fm_aircraft["callsign"][3:].isdigit():
                    continue
                loaded += 1
                result[fm_aircraft["icao24"]] = fm_aircraft
                _progress(iterator, state_len, message=fm_aircraft["callsign"])

    print(f"\n{loaded} aircraft loaded out of {iterator} in set")
    return result
