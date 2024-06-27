# main.py

"""
For now just starts the HTTP server

Functions:
    start()
"""

from os import urandom, getlogin
from os.path import exists
from base64 import b64decode
from threading import Thread
from random import shuffle
from flask import Flask, render_template, send_from_directory, request
from flask_socketio import SocketIO, emit

from paths import INSTANCE_IMAGES, LOCAL_IMAGES
import lookup
import jetphotos
import openskies
import my_flights

nato = {
    "0": "ZERO",
    "1": "ONE",
    "2": "TWO",
    "3": "THREE",
    "4": "FOUR",
    "5": "FIVE",
    "6": "SIX",
    "7": "SEVEN",
    "8": "EIGHT",
    "9": "NINER",
    "A": "ALPHA",
    "B": "BRAVO",
    "C": "CHARLIE",
    "D": "DELTA",
    "E": "ECHO",
    "F": "FOXTROT",
    "G": "GOLF",
    "H": "HOTEL",
    "I": "INDIA",
    "J": "JULIET",
    "K": "KILO",
    "L": "LIMA",
    "M": "MIKE",
    "N": "NOVEMBER",
    "O": "OSCAR",
    "P": "PAPA",
    "Q": "QUEBEC",
    "R": "ROMEO",
    "S": "SIERRA",
    "T": "TANGO",
    "U": "UNIFORM",
    "V": "VICTOR",
    "W": "WHISKEY",
    "X": "X-RAY",
    "Y": "YANKEE",
    "Z": "ZULU"
}

def start():
    """
    Start the HTTP server
    """

    # will be replaced by the actual decoder later
    aircraft = openskies.load("../os.json", num_only=True)

    app = Flask("flight_tracker")
    app.config["SECRET_KEY"] = urandom(24)
    socketio = SocketIO(app)

    @app.route("/")
    def serve_map():
        return render_template("map.html", initial=getlogin()[:1].upper(), colour="#3478F6")

    @app.route("/my")
    def serve_my_flights():
        return render_template("my_flights.html", name=getlogin(), initial=getlogin()[:1].upper(), colour="#3478F6")

    @app.route("/image/aircraft/<tail>")
    def serve_aircraft_image(tail):
        placeholder = b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAA"
                                "AAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=")
        if tail in ("Unknown Reg", "placeholder"):
            return placeholder, 200, {"Content-Type": "image/png"}

        if exists(f"{INSTANCE_IMAGES}/aircraft-{tail}.jpeg"):
            return send_from_directory(INSTANCE_IMAGES, f"aircraft-{tail}.jpeg")

        image = jetphotos.thumb(tail)
        if image:
            return send_from_directory(LOCAL_IMAGES, image)
        return placeholder, 200, {"Content-Type": "image/png"}

    @app.route("/image/icon/<icontype>")
    def serve_icon(icontype):
        return send_from_directory("static/aircraft", icontype + ".svg")

    @app.route("/image/icon/untyped/<type>")
    def serve_untyped_icon(type):
        return send_from_directory("static/aircraft", lookup.aircraft_icon(type)["icon"] + ".svg")

    @socketio.on("decoder.get")
    def handle_decoder_get():
        aircraft_list = list(aircraft.items())
        shuffle(aircraft_list)
        shuffled_aircraft = dict(aircraft_list[:750])
        emit("decoder.get", shuffled_aircraft)

    @socketio.on("lookup.airport")
    def handle_lookup_airport(code, routing=None):
        airport = lookup.airport(code)
        airport["routing"] = routing
        emit("lookup.airport", airport)

    @socketio.on("lookup.add_origin")
    def handle_lookup_add_origin(callsign, origin):
        lookup.add_origin(callsign, origin)

    @socketio.on("lookup.add_destination")
    def handle_lookup_add_destination(callsign, destination):
        lookup.add_destination(callsign, destination)

    @socketio.on("lookup.all")
    def handle_lookup_all(icao24, callsign):
        info = {}
        info["airline"] = lookup.airline(callsign)
        info["aircraft"] = lookup.aircraft(icao24)
        info["callsign"] = callsign

        if "radio" in info["airline"]:
            info["radio"] = info["airline"]["radio"]
            for char in callsign[3:]:
                info["radio"] += " " + nato[char]
        else:
            info["radio"] = ""

        if "name" not in info["airline"]:
            if "operator" in info["aircraft"]:
                info["airline"]["name"] = info["aircraft"]["operator"]
            elif "owner" in info["aircraft"]:
                info["airline"]["name"] = info["aircraft"]["owner"]
            else:
                info["airline"]["name"] = "Unknown Airline"

        if "type" not in info["aircraft"]:
            info["aircraft"]["type"] = "Unknown Type"
        if "reg" not in info["aircraft"]:
            info["aircraft"]["reg"] = "Unknown Reg"

        route = lookup.route(callsign)
        if route:
            info["origin"] = (lookup.airport(route["origin"])
                              if "origin" in route else None)
            info["destination"] = (lookup.airport(route["destination"])
                                   if "destination" in route else None)
        else:
            info["origin"] = info["destination"] = None

        emit("lookup.all", info)

    @socketio.on("my_flights.get")
    def handle_my_flights_get():
        emit("my_flights.get", my_flights.get())

    socket_thread = Thread(target=socketio.run, args=(app, "0.0.0.0", 5003))
    socket_thread.start()

if __name__ == "__main__":
    print("""

 ⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⣿⣶⡀
 ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣿⣿⣿⣦
 ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⣿⣿⣿⣷⡄
 ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢿⣿⣿⣿⣿⣦⡀
 ⢀⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⣿⣿⣿⣿⣿⣷⣆
 ⣿⣿⣆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣿⣿⣿⣿⣿⣿⣷⡀
 ⣿⣿⣿⣆⠀⠀⠀⠀⠀⠀⠀⠀⢀⣻⣿⣿⣿⣿⣿⣿⣿⣦⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀
 ⣿⣿⣿⣿⣶⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣦⡄
 ⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
 ⣿⣿⣿⣿⠿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠟⠃
 ⣿⣿⣿⠏⠀⠀⠀⠀⠀⠀⠀⠀⠈⣽⣿⣿⣿⣿⣿⣿⣿⠟⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉
 ⣿⣿⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣿⣿⣿⣿⣿⣿⡿⠁
 ⠈⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣿⣿⣿⣿⣿⡿⠏
 ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣼⣿⣿⣿⣿⠟⠁
 ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⣿⣿⣿⡿⠋
 ⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣿⣿⣿⠟
 ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⣿⡿⠁

    """)
    lookup.check()
    start()
