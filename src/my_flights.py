# my_flights.py

import lookup
from bisect import bisect_left

def _eval_ranking(addition, ranking):
    if ranking:
        ranking_keys = [d["flights"] for d in ranking]
        rank = bisect_left(ranking_keys, addition["flights"])
    else:
        rank = 0
    ranking.insert(rank, addition)
    return ranking

def get():
    # flights_table = lookup.get_my_flights_table()
    airlines = {}
    aircraft = {}
    airports = {}
    flights = []

    # random flights for demo for now
    flights_table = (
        {"origin": "EGLL", "destination": "WSSS", "aircraft": "B789", "callsign": "BAW15"},
        {"origin": "WSSS", "destination": "YSSY", "aircraft": "B789", "callsign": "BAW15"},
        {"origin": "YSSY", "destination": "WSSS", "aircraft": "B789", "callsign": "BAW16"},
        {"origin": "YSSY", "destination": "VHHH", "aircraft": "A35K", "callsign": "CPA100"},
        {"origin": "VHHH", "destination": "EGLL", "aircraft": "B772", "callsign": "CPA238"},
        {"origin": "EGLL", "destination": "KSFO", "aircraft": "B772", "callsign": "BAW285"},
        {"origin": "EGLL", "destination": "KIAD", "aircraft": "B772", "callsign": "BAW293"},
        {"origin": "NFFN", "destination": "YSSY", "aircraft": "B738", "callsign": "VOZ184"},
        {"origin": "EDDB", "destination": "EGLL", "aircraft": "A320", "callsign": "BAW995"},
        {"origin": "RJTT", "destination": "EGLL", "aircraft": "B789", "callsign": "JAL41"},
        {"origin": "YSSY", "destination": "RJTT", "aircraft": "B789", "callsign": "JAL51"},
        {"origin": "YSSY", "destination": "YPPH", "aircraft": "A333", "callsign": "QFA641"},
        {"origin": "NFFN", "destination": "YSSY", "aircraft": "B738", "callsign": "VOZ184"},
        {"origin": "EGLC", "destination": "EDDB", "aircraft": "E195", "callsign": "CFE7029"}
    )

    for flight in flights_table:
        flights.append({"origin": flight["origin"], "destination": flight["destination"]})

        for airport in (flight["origin"], flight["destination"]):
            info = lookup.airport(airport)
            if info["icao"] in airports:
                airports[info["icao"]]["flights"] += 1
            else:
                airports[info["icao"]] = info
                airports[info["icao"]]["flights"] = 1

        info = lookup.airline(flight["callsign"][:3])
        if info["icao"] in airlines:
            airlines[info["icao"]]["flights"] += 1
        else:
            airlines[info["icao"]] = info
            airlines[info["icao"]]["flights"] = 1

        if flight["aircraft"] in aircraft:
            aircraft[flight["aircraft"]]["flights"] += 1
        else:
            aircraft[flight["aircraft"]] = {"flights": 1, "icao": flight["aircraft"]}

    response = {
        "airlines": airlines,
        "aircraft": aircraft,
        "airports": airports,
        "flights": flights,
        "rankings": {
            "airlines": [],
            "aircraft": [],
            "airports": []
        }
    }

    for category in response["rankings"]:
        for key in response[category]:
            individual = response[category][key]
            ranking_entry = {"icao": individual["icao"], "flights": individual["flights"]}
            response["rankings"][category] = _eval_ranking(ranking_entry, response["rankings"][category])
        response["rankings"][category].reverse()
        response["rankings"][category] = response["rankings"][category][:5]

    return response
