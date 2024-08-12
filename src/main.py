# main.py

"""
Start the HTTP server
"""

# pylint: disable=wrong-import-position,wrong-import-order
from gevent.monkey import patch_all
patch_all()

from os import urandom
from sys import stdin
from random import shuffle
from json import loads
from xml.etree.ElementTree import parse, tostring, Element
from flask import Flask, jsonify, render_template, Response
from flask_socketio import SocketIO, emit
import get

get.check_dbs()
flags: Element = parse("flags.xml").getroot()
with open("aircraft.svg", "r", encoding="utf-8") as svg:
    aircraft_icons: str = svg.read()

# will be replaced by the actual decoder later
aircraft: dict[str, dict[str, str | int | float]] = loads(stdin.read())

flask: Flask = Flask("flight_tracker")
flask.config["SECRET_KEY"] = urandom(24)
socketio: SocketIO = SocketIO(flask)

@flask.route("/")
def serve_map() -> str:
    """
    Render and return the map HTML
    """
    return render_template("map.jinja",
                           strings=get.STRINGS,
                           initial=str(get.settings["name"])[0],
                           colour=get.settings["colour"],
                           fontdisambiguation=get.settings["fontdisambiguation"],
                           aircraft_icons=aircraft_icons)

@flask.route("/aircraft.json")
def serve_aircraft_json() -> Response:
    """
    Get the current state of aircraft as a JSON file
    """
    return jsonify(aircraft)

@flask.route("/image/flag/<country>")
def serve_flag(country: str) -> tuple[str, int, dict[str, str]]:
    """
    Get the flag of a country (from flags.xml) by its ISO 2-letter code
    """
    common: str = ("<svg xmlns=\"http://www.w3.org/2000/svg\" "
                   "viewBox=\"0 0 512 512\" height=\"512\" width=\"512\"")
    flag_elem: Element | None = flags.find(f".//*[@id='{country.lower()}']")
    flag: str = ""
    if flag_elem is None:
        flag_elem = flags.find(".//*[@id='xx']")
    if isinstance(flag_elem, Element):
        flag = tostring(flag_elem, encoding="unicode").replace("<svg", common)
    return flag, 200, {"Content-Type": "image/svg+xml"}

@flask.route("/my")
def serve_my_flights() -> str:
    """
    Render and return the my_flights HTML
    """
    return render_template("my_flights.jinja",
                           strings=get.STRINGS,
                           name=get.settings["name"],
                           initial=str(get.settings["name"])[0],
                           colour=get.settings["colour"],
                           fontdisambiguation=get.settings["fontdisambiguation"],
                           my_flights=get.my_flights(),
                           aircraft_icons=aircraft_icons)

@flask.route("/my/add")
def serve_my_flights_add() -> str:
    """
    Render and return the my_flights_add HTML
    """
    return render_template("my_flights_add.jinja",
                           strings=get.STRINGS,
                           colour=get.settings["colour"],
                           fontdisambiguation=get.settings["fontdisambiguation"])

@flask.route("/info/<kind>/<query>.json")
def serve_get_info_json(query: str, kind: str) -> Response:
    """
    Use the get info function and return a RESTful API response
    """
    return jsonify(get.info(query, kind))

@socketio.on("connect")
def send_aircraft() -> None:
    """
    Emit the current aircraft state dict (750 randomly picked for performance, temporary)
    Adds the aircraft to the map on the front end
    """
    aircraft_l: list[tuple[str, dict[str, str | int | float]]] = list(aircraft.items())
    shuffle(aircraft_l)
    shuffled: dict[str, dict[str, str | int | float]] = dict(aircraft_l[:750])
    emit("aircraft", shuffled)

@socketio.on("route")
def handle_add_route(csign: str, orig: str, dest: str) -> None:
    """
    SocketIO handler for get.add_route

    Add the origin and/or destination of a route
    Can add both the origin and the destination or just one
    Only takes 4-letter ICAO codes for airports
    """
    get.add_route(csign, orig=orig, dest=dest)

@socketio.on("select")
def handle_select(icao: str, csign: str) -> None:
    """
    Emit necessary info about an aircraft and its airline/route using get.info(),
    and its image using get.image() to show on the front end
    Takes an aircraft's 24-bit ICAO address and callsign
    Emits a dict with keys aircraft, airline, dest, image, orig, route
    Key "route" contains the callsign ("csign") and its radio equivalent
    Selects the aircraft on the front end
    """
    info: dict[str, dict[str, str]] = {
        "aircraft": get.info(icao, "aircraft"),
        "route": {
            "csign": csign
        }
    }

    if not (any(char.isdigit() for char in csign[:3]) or (
            ("reg" in info["aircraft"] and
             info["aircraft"]["reg"].replace("-", "") == csign))):
        info["airline"] = get.info(csign, "airline")
    else:
        info["airline"] = {}

    if "radio" in info["airline"]:
        info["route"]["radio"] = " ".join([info["airline"]["radio"], get.radio(csign[3:])]).strip()
    else:
        info["route"]["radio"] = get.radio(csign)

    if "name" not in info["airline"]:
        if "operatoricao" in info["aircraft"]:
            airline: dict[str, str] = get.info(info["aircraft"]["operatoricao"], "airline")
            if "name" in airline:
                info["airline"]["name"] = airline["name"]

        if "name" not in info["airline"]:
            if "operator" in info["aircraft"]:
                info["airline"]["name"] = info["aircraft"]["operator"]
            elif "owner" in info["aircraft"]:
                info["airline"]["name"] = info["aircraft"]["owner"]

    route: dict[str, str] = get.info(csign, "route")
    if route:
        info["orig"] = (get.info(route["orig"], "airport")
                        if "orig" in route else {})
        info["dest"] = (get.info(route["dest"], "airport")
                        if "dest" in route else {})
    else:
        info["orig"] = info["dest"] = {}

    if "reg" in info["aircraft"]:
        info["image"] = get.image(info["aircraft"]["reg"],
                                  "reg",
                                  bool(get.settings["usewikimedia"]))
    elif not get.settings["usewikimedia"]:
        info["image"] = get.image(icao, "hex")
    else:
        info["image"] = {"src": "", "attr": "", "link": ""}

    emit("select", info)

if __name__ == "__main__":
    port: str | int | None = get.settings["port"]
    if isinstance(port, int):
        print(get.STRINGS["logs"]["running"].format("http://localhost:" + str(port)))
        try:
            socketio.run(flask, host="0.0.0.0", port=port)
        except KeyboardInterrupt:
            pass
    else:
        raise TypeError(get.STRINGS["logs"]["badport"])
