# my_flights.py

import lookup

def get():
    # flights_table = lookup.get_my_flights_table()
    flights = []
    airports = {}
    airport_visit_min = airport_visit_max = 0

    flights_table = (
        {"origin": "EGLL", "destination": "WSSS"},
        {"origin": "WSSS", "destination": "YSSY"},
        {"origin": "YSSY", "destination": "WSSS"},
        {"origin": "YSSY", "destination": "VHHH"},
        {"origin": "EGLL", "destination": "VHHH"},
        {"origin": "EGLL", "destination": "KSFO"},
        {"origin": "EGLL", "destination": "KIAD"},
        {"origin": "YSSY", "destination": "NFFN"},
        {"origin": "EGLL", "destination": "EDDB"},
        {"origin": "EGLL", "destination": "RJTT"},
        {"origin": "RJAA", "destination": "YSSY"},
        {"origin": "YSSY", "destination": "YPPH"},
        {"origin": "NFFN", "destination": "YSSY"},
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

            if airport_visit_max < airports[info["icao"]]["visits"]:
                airport_visit_max = airports[info["icao"]]["visits"]

            if airport_visit_min == 0 or airport_visit_min > airports[info["icao"]]["visits"]:
                airport_visit_min = airports[info["icao"]]["visits"]

    visit_range = airport_visit_max - airport_visit_min
    distributor = (10, 16)

    if visit_range != 0:
        for airport in airports:
            airports[airport]["size"] = distributor[0] + ((airports[airport]["visits"] - airport_visit_min) / visit_range) * (distributor[1] - distributor[0])
    else:
        for airport in airports:
            airports[airport]["size"] = (distributor[0] + distributor[1]) / 2

    print(airport_visit_min, airport_visit_max)

    return {"airports": airports, "flights": flights, "count": len(flights)}

print(get())
