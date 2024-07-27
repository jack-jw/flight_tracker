# opensky.py

"""
Download and convert json files from the OpenSky API for testing
"""

from json import loads, dumps
from sys import stderr
from requests import get
from get import basic, check_dbs

def _format(i):
    headers = (
        "icao",
        "csign",
        "del_origin",
        "del_time",
        "del_contact",
        "lng",
        "lat",
        "alt",
        "del_ground",
        "speed",
        "hdg",
        "climb",
        "del_sensors",
        "del_geo_alt",
        "del_squawk",
        "del_special",
        "del_source",
        "cat"
    )

    conv_headers = {
        "hdg": 1,
        "alt": 3.28084,
        "climb": 196.8503937008,
        "speed": 1.943844
    }

    result = dict(zip(headers, i))

    # delete unnecessary keys to save bandwidth
    for header, value in result.copy().items():
        if header.startswith("del_") or not value:
            del result[header]

    for header, conversion in conv_headers.items():
        if header in result and result[header]:
            result[header] *= conversion
        else:
            result[header] = 0

    if all(key in result for key in ("icao", "lat", "lng", "csign")):
        result["csign"] = result["csign"].strip()
        result.update(basic(result["icao"]))
        if (not any(char.isdigit() for char in result["csign"][:3]) and (
           ("reg" in result and result["reg"].replace("-", "") == result["csign"]))):
            result["csign"] = result["csign"][:3] + result["csign"][3:].lstrip("0")
        return result
    return None

def convert(state):
    """
    Convert an OpenSky API state to flight_tracker format for testing
    """

    state = loads(state)
    state = state["states"]

    result = {}

    for aircraft in state:
        formatted_aircraft = _format(aircraft)
        if not formatted_aircraft:
            continue
        result[formatted_aircraft["icao"]] = formatted_aircraft

    return result

if __name__ == "__main__":
    check_dbs(lambda l: print(l, file=stderr))
    response = get("https://opensky-network.org/api/states/all", timeout=120)
    aircraft_list = convert(response.text)
    print(dumps(aircraft_list))
