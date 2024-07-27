# main.py

"""
Starts the HTTP server
"""

# pylint: disable=wrong-import-position,wrong-import-order
from gevent.monkey import patch_all
patch_all()

from os import urandom
from sys import stdin
from random import shuffle
from json import loads
from xml.etree.ElementTree import parse, tostring
from flask import Flask, jsonify, render_template
from flask_socketio import SocketIO, emit
from instance import Settings as S
import get

get.check_dbs()
graphics = {}
graphics["flags"] = parse("flags.xml").getroot()
with open("aircraft.svg", "r", encoding="utf-8") as svg:
    graphics["aircraft"] = svg.read()

# will be replaced by the actual decoder later
aircraft = loads(stdin.read())

flask = Flask("flight_tracker")
flask.config["SECRET_KEY"] = urandom(24)
socketio = SocketIO(flask)

@flask.route("/")
def serve_map():
    """
    Render and return the map HTML
    """

    return render_template("map.jinja",
                            initial=S.get("name")[0],
                            colour=S.get("colour"),
                            aircraft_icons=graphics["aircraft"])

@flask.route("/aircraft.json")
def serve_aircraft_json():
    """
    Get the current state of aircraft as a JSON file
    """
    return jsonify(aircraft)

@flask.route("/image/flag/<country>")
def serve_flag(country):
    """
    Get the flag of a country (from flags.xml) by its ISO 2-letter code
    """
    common = ("<svg xmlns=\"http://www.w3.org/2000/svg\" "
              "viewBox=\"0 0 512 512\" height=\"512\" width=\"512\"")
    flag = graphics["flags"].find(f".//*[@id='{country.lower()}']")
    if flag is None:
        flag = graphics["flags"].find(".//*[@id='xx']")
    flag = tostring(flag, encoding="unicode").replace("<svg", common)
    return flag, 200, {"Content-Type": "image/svg+xml"}

@flask.route("/my")
def serve_my_flights():
    """
    Render and return the my_flights HTML
    """
    return render_template("my_flights.jinja",
                            name=S.get("name"),
                            initial=S.get("name")[0],
                            colour=S.get("colour"),
                            my_flights=get.my_flights(),
                            aircraft_icons=graphics["aircraft"])

@socketio.on("connect")
def handle_decoder_get():
    """
    Emit the current aircraft state dictionary
    Adds the aircraft to the map on the front end
    """
    aircraft_list = list(aircraft.items())
    shuffle(aircraft_list)
    shuffled_aircraft = dict(aircraft_list[:750])
    emit("aircraft", shuffled_aircraft)

@socketio.on("lookup.airport")
def handle_lookup_airport(code, routing=None):
    """
    Look up an airport using get.info(..., "airport")
    Takes an airport code (IATA or ICAO)
    Returns a dictionary with keys the same as get.info(..., "airport")
    Accepts routing
    """
    airport = get.info(code, "airport")
    airport["routing"] = routing
    emit("lookup.airport", airport)

@socketio.on("lookup.add_orig")
def handle_lookup_add_orig(csign, orig):
    """
    Add a route's origin using get.add_route()
    Takes a callsign and a route origin ICAO (4 character)
    """
    get.add_route(csign, orig=orig)

@socketio.on("lookup.add_dest")
def handle_lookup_add_dest(csign, dest):
    """
    Add a route's destination using get.add_route()
    Takes a callsign and a route destination ICAO (4 character)
    """
    get.add_route(csign, dest=dest)

@socketio.on("select")
def handle_lookup_all(icao, csign):
    """
    Get infromation about an aircraft and its airline and route using get.info(),
    and its image using get.image()
    Selects the aircraft on the front end
    Takes an aircraft's ICAO 24-bit address and its callsign
    Returns a dictionary with keys aircraft, airline, callsign, dest, radio, image, orig
    Keys are the same as get.info() functions
    """
    info = {
        "aircraft": get.info(icao, "aircraft"),
        "airline": get.info(csign, "airline"),
        "csign": csign,
    }

    if "radio" in info["airline"]:
        info["radio"] = (info["airline"]["radio"] + " " + get.radio(csign[3:])).strip()

    if "name" not in info["airline"]:
        if "operatoricao" in info["aircraft"]:
            airline = get.info(info["aircraft"]["operatoricao"], "airline")
            if "name" in airline:
                info["airline"]["name"] = airline["name"]

        if "name" not in info["airline"]:
            if "operator" in info["aircraft"]:
                info["airline"]["name"] = info["aircraft"]["operator"]
            elif "owner" in info["aircraft"]:
                info["airline"]["name"] = info["aircraft"]["owner"]

    route = get.info(csign, "route")
    if route:
        info["orig"] = (get.info(route["orig"], "airport")
                        if "orig" in route else None)
        info["dest"] = (get.info(route["dest"], "airport")
                        if "dest" in route else None)
    else:
        info["orig"] = info["dest"] = None

    if "reg" in info["aircraft"]:
        info["image"] = get.image(info["aircraft"]["reg"], "reg", S.get("usewikimedia"))
    elif not S.get("usewikimedia"):
        info["image"] = get.image(icao, "hex")
    else:
        info["image"] = {"src": None, "attr": None, "link": None}

    emit("select", info)

if __name__ == "__main__":
    print(f"Running on http://localhost:{S.get('port')}")
    socketio.run(flask, host="0.0.0.0", port=S.get("port"))
