# opensky.py

"""
Download and convert JSON files from the OpenSky API for testing
"""

from json import loads, dumps
from sys import stderr
from requests import get, Response
from get import check_dbs, info

__all__: list[str] = [
    "extract",
    "convert",
    "ENDPOINT"
]

ENDPOINT: str = "https://opensky-network.org/api/states/all"


def extract(os_json: str) -> list[list[str | int | float]]:
    """
    Extract the aircraft list from an OpenSky API state
    """
    return loads(os_json)["states"]


def convert(state: list[list[str | int | float]]) -> dict[str, dict[str, str | int | float]]:
    """
    Convert an OpenSky API aircraft list to flight_tracker format
    """
    headers: tuple[str, ...] = (
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

    conv_headers: tuple[tuple[str, float], ...] = (
        ("hdg", 1),  # ensure it's there
        ("alt", 3.28084),  # to ft
        ("climb", 196.8503937008),  # to ft/min
        ("speed", 1.943844)  # to kt
    )

    result: dict[str, dict[str, str | int | float]] = {}

    for osac in state:
        ftac: dict[str, str | int | float] = dict(zip(headers, osac))

        if all(key in ftac and ftac[key] for key in ("icao", "lat", "lng", "csign")):
            # delete unnecessary keys to save bandwidth
            ftac = dict(filter(lambda item: item[1] and not item[0].startswith("del_"),
                               ftac.items()))

            # convert to flight tracker values (or add default 0)
            for convertee, multiplier in conv_headers:
                if convertee in ftac and ftac[convertee]:
                    ftac[convertee] = float(ftac[convertee]) * multiplier
                else:
                    ftac[convertee] = 0

            ftac["csign"] = str(ftac["csign"]).strip()
            ftac.update(info(str(ftac["icao"]), "basic"))
            if not (any(char.isdigit() for char in str(ftac["csign"])[:3]) or (
                    ("reg" in ftac and str(ftac["reg"]).replace("-", "") == ftac["csign"]))):
                ftac["csign"] = str(ftac["csign"])[:3] + str(ftac["csign"])[3:].lstrip("0")
            result[str(ftac["icao"])] = ftac

    return result


if __name__ == "__main__":
    check_dbs(lambda log: print(log, file=stderr))
    response: Response = get(ENDPOINT, timeout=120)
    aircraft: dict[str, dict[str, str | int | float]] = convert(extract(response.text))
    print(dumps(aircraft))
