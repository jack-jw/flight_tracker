# main.py

"""
For now just starts the HTTP server

Functions:
    start()
"""

from os import urandom
from os.path import exists
from base64 import b64decode
from threading import Thread
from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO, emit

from paths import INSTANCE, INSTANCE_IMAGES
import lookup
import jetphotos
import openskies

def start():
    """
    Start the HTTP server
    """

    app = Flask(__name__)
    app.config["SECRET_KEY"] = urandom(24)
    socketio = SocketIO(app)

    @app.route("/")
    def index():
        return render_template("map.html", initial="★", colour="#3478F6")

    @app.route("/image/aircraft/<tail>")
    def serve_image(tail):
        placeholder = b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAA"
                                "AAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=")
        if (tail == "Unknown Reg") or (tail == "placeholder"):
            return placeholder, 200, {"Content-Type": "image/png"}

        if exists(f"{INSTANCE_IMAGES}/aircraft-{tail}.jpeg"):
            with open(f"{INSTANCE_IMAGES}/aircraft-{tail}.jpeg", "rb") as f:
                image_content = f.read()
            return image_content, 200, {"Content-Type": "image/jpeg"}

        image = jetphotos.thumb(tail)
        if image:
            with open(image, "rb") as f:
                image_content = f.read()
            return image_content, 200, {"Content-Type": "image/jpeg"}
        return placeholder, 200, {"Content-Type": "image/png"}

    @app.route('/icon/<path:type>')
    def serve_icon(type):
        return send_from_directory('static/aircraft', type)

    @socketio.on("connect")
    def handle_connect():
        # will be replaced by the actual decoder later
        emit("decoder.get", openskies.load("../os.json", gb_only=False, num_only=True))

    @socketio.on("lookup.airport")
    def handle_airport_info_query(code, routing=None):
        airport = lookup.airport(code)
        airport["routing"] = routing
        emit("lookup.airport", airport)

    @socketio.on("lookup.add_origin")
    def handle_add_origin(callsign, origin):
        lookup.add_origin(callsign, origin)

    @socketio.on("lookup.add_destination")
    def handle_add_destination(callsign, destination):
        lookup.add_destination(callsign, destination)

    @socketio.on("lookup.all")
    def handle_all_info_query(aircraft_address, callsign):
        info = {}
        info["airline"] = lookup.airline(callsign)
        info["aircraft"] = lookup.aircraft(aircraft_address)

        info["callsign"] = callsign

        if "name" not in info["airline"]:
            if "operator" in info["aircraft"]:
                info["airline"]["name"] = info["aircraft"]["operator"]
            elif "owner" in info["aircraft"]:
                info["airline"]["name"] = info["aircraft"]["owner"]

        route = lookup.route(callsign)
        if route:
            info["origin"] = (lookup.airport(route["origin"])
                              if "origin" in route else None)
            info["destination"] = (lookup.airport(route["destination"])
                                   if "destination" in route else None)
        else:
            info["origin"] = info["destination"] = None

        emit("lookup.all", info)

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
