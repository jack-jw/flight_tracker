# my_flights.py

import lookup
from bisect import bisect_left

def get():
    flights_table = lookup.get_my_flights_table()
    airlines = {}
    airports = {}
    continents = []
    countries = []
    domestic = 0
    flights = []
    intercontinental = 0
    international = 0
    types = {}

    for flight in flights_table:
        flights.append({"origin": flight["origin"], "destination": flight["destination"]})

        for airport in (flight["origin"], flight["destination"]):
            if airport in airports:
                airports[airport]["flights"] += 1
            else:
                info = lookup.airport(airport)
                airports[info["icao"]] = info
                airports[info["icao"]]["flights"] = 1
                if info["country"] not in countries:
                    countries.append(info["country"])
                if info["continent"] not in continents:
                    continents.append(info["continent"])

        if airports[flight["origin"]]["country"] == airports[flight["destination"]]["country"]:
            domestic += 1
        else:
            international += 1

        if airports[flight["origin"]]["continent"] != airports[flight["destination"]]["continent"]:
            intercontinental += 1

        if flight["callsign"]:
            info = lookup.airline(flight["callsign"][:3])
            if info["icao"] in airlines:
                airlines[info["icao"]]["flights"] += 1
            else:
                airlines[info["icao"]] = info
                airlines[info["icao"]]["flights"] = 1

        if flight["type"]:
            if flight["type"] in types:
                types[flight["type"]]["flights"] += 1
            else:
                types[flight["type"]] = {"flights": 1, "icao": flight["type"]}

    response = {
        "airlines": airlines,
        "airports": airports,
        "continents": sorted(continents),
        "countries": sorted(countries),
        "counts": {
            "intercontinental": intercontinental,
            "international": international,
            "domestic": domestic
        },
        "flights": flights,
        "rankings": {
            "airlines": [],
            "types": [],
            "airports": []
        },
        "types": types
    }

    for category in response["rankings"]:
        for key in response[category]:
            individual = response[category][key]
            ranking_entry = {"icao": individual["icao"], "flights": individual["flights"]}
            if response["rankings"][category]:
                ranking_keys = [d["flights"] for d in response["rankings"][category]]
                rank = bisect_left(ranking_keys, ranking_entry["flights"])
            else:
                rank = 0
            response["rankings"][category].insert(rank, ranking_entry)
        response["rankings"][category].reverse()
        response["rankings"][category] = response["rankings"][category]

    return response

def csv():
    dict_table = lookup.get_my_flights_table()
    csv_table = "date,origin,destination,callsign,reg,type"

    for dict_row in dict_table:
        csv_row = "\n"
        for key, item in dict_row.items():
            if not item:
                item = ""
            csv_row += item + ","
        csv_table += csv_row[:-1]

    return csv_table
