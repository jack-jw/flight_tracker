# my_flights.py

import lookup

def get():
    # flights_table = lookup.get_my_flights_table()
    flights = []
    airports = {}

    flights_table = (
        {"origin": "EGLL", "destination": "WSSS"},
        {"origin": "WSSS", "destination": "YSSY"},
        {"origin": "YSSY", "destination": "VHHH"},
        {"origin": "EGLL", "destination": "VHHH"},
        {"origin": "EGLL", "destination": "KSFO"},
        {"origin": "EGLL", "destination": "KIAD"},
        {"origin": "YSSY", "destination": "NFFN"},
        {"origin": "EGLL", "destination": "EDDB"},
        {"origin": "EGLL", "destination": "RJTT"},
        {"origin": "RJAA", "destination": "YSSY"},
        {"origin": "YSSY", "destination": "YPPH"}
    )
    for flight in flights_table:
        flights.append({"origin": flight["origin"], "destination": flight["destination"]})

        for airport in (flight["origin"], flight["destination"]):
            info = lookup.airport(airport)
            if info["icao"] in airports:
                airports[info["icao"]]["visits"] += 1
            else:
                airports[info["icao"]] = info
                airports[info["icao"]]["visits"] = 1
    return {"airports": airports, "flights": flights, "count": len(flights)}

print(get())
