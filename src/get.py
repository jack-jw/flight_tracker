# get.py (called lookup.py on this commit to see diff from original lookup.py)

"""
Get things:
  * Info about aircraft/airports/airlines/routes
  * Images from Planespotters.net and Wikimedia Commons
  * The My Flights JSON for the webpage

Functions:
  - Database management
    update_db() - update a specific table in a DB
    check_dbs() - check all DBs are present
    add_route() - add a route to the DB with its origin and/or destination

  - Lookup (using local DBs)
    info() - get info about something specific from the DB
    basic() - basic general lookup done for all aircraft before they are added to the map

    radio() - transpose something to radio-friendly language
    image() - get an image from a search query
    my_flights() - get the JSON for the webpage
"""

from bisect import bisect_left
from csv import reader
import sqlite3
import requests
from bs4 import BeautifulSoup
from instance import Path as P

_URLS = {
    "airlines_wiki": "https://en.wikipedia.org/wiki/List_of_airline_codes",
    "aircraft": "https://opensky-network.org/datasets/metadata/aircraftDatabase.csv",
    "airports": "https://davidmegginson.github.io/ourairports-data/airports.csv",
    "icontypes": "https://raw.githubusercontent.com/jack-jw/flight_tracker/main/icontypes.csv",
    "prefixes": "https://raw.githubusercontent.com/jack-jw/flight_tracker/main/prefixes.csv"
}

# MARK: - Internal functions
def _get_airlines_table():
    """
    Internal, use update_db("airlines")

    Get the airlines table from Wikipedia and add it to the database
    """

    try:
        response = requests.get(_URLS["airlines_wiki"], timeout=120)
        if not response.ok:
            return
    except requests.exceptions.ReadTimeout:
        return

    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.find("table", class_="wikitable")

    main_db = sqlite3.connect(P.localdb)
    cursor = main_db.cursor()

    try:
        cursor.execute("DROP TABLE airlines")
    except sqlite3.OperationalError:
        pass

    cursor.execute("CREATE TABLE airlines "
                   "('iata' TEXT, "
                   "'icao' TEXT, "
                   "'name' TEXT, "
                   "'radio' TEXT, "
                   "'country' TEXT)")

    rows = table.find_all("tr")[1:]

    noadd = (
        "defunct",
        "no longer allocated",
        "icao code in use by another company"
    )

    for row in rows:
        cols = row.find_all("td")
        data = [col.get_text(strip=True) for col in cols]
        data += [None] * (6 - len(data))
        if data[5] is None or not any(word in data[5].lower() for word in noadd):
            cursor.execute("INSERT INTO airlines VALUES (?, ?, ?, ?, ?)", data[:5])

    cursor.close()
    main_db.commit()
    main_db.close()

def _csv_to_db(database, url, table_name, column_names, index_column=False):
    """
    Internal, use update_db() function to update a DB

    Get a CSV from the web and add it to the database
    Takes a database, a URL and a table name as a string and column names as a tuple
    """

    try:
        response = requests.get(url, timeout=300)
        if not response.ok:
            return
    except requests.exceptions.ReadTimeout:
        return

    data = response.text.splitlines()

    fil_columns = [col for col in column_names if not col.startswith("del_")]
    fil_indices = [i for i, col in enumerate(column_names) if not col.startswith("del_")]

    main_db = sqlite3.connect(database)
    cursor = main_db.cursor()

    try:
        cursor.execute(f"DROP TABLE {table_name}")
    except sqlite3.OperationalError:
        pass

    columns_str = ", ".join([f"'{col}' TEXT" for col in fil_columns])
    cursor.execute(f"CREATE TABLE {table_name} ({columns_str})")

    csv_reader = reader(data)
    next(csv_reader)
    for row in csv_reader:
        fil_row = [row[i] for i in fil_indices]
        cursor.execute(f"INSERT INTO {table_name} "
                       f"VALUES ({', '.join(['?' for _ in range(len(fil_columns))])}"
                       ")", fil_row)

    if index_column:
        cursor.execute(f"CREATE INDEX idx_{index_column} ON {table_name}({index_column})")

    cursor.close()
    main_db.commit()
    main_db.close()

def _get_row(table, search_column, query):
    """
    Internal, use the lookup functions

    Get a row from the DB as a dictionary
    Takes a table, search column, and query as strings
    Returns the row as a dictionary
    """

    db_path = P.instancedb if table == "routes" else P.localdb
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    while True:
        try:
            cursor.execute(f"SELECT * FROM {table} WHERE `{search_column}` = '{query}'")
            break
        except sqlite3.OperationalError:
            update_db(table)

    result = cursor.fetchone()
    cursor.close()
    db.close()

    if result:
        result = dict(result)
        for key, value in result.copy().items():
            if not value:
                del result[key]
    else:
        result = {}
        result[search_column] = query

    return result

def _get_country_from_reg(reg):
    """
    Internal, use aircraft() function

    Look up the country an aircraft's reg prefix corresponds to
    Takes the aircraft's registration number as a string
    Returns a country code as a string
    """

    if not reg:
        return None

    main_db = sqlite3.connect(P.localdb)
    cursor = main_db.cursor()

    while True:
        try:
            cursor.execute("SELECT country FROM prefixes WHERE ? LIKE prefix || '%'", (reg,))
            break
        except sqlite3.OperationalError:
            update_db("prefixes")

    result = cursor.fetchone()
    cursor.close()
    main_db.close()
    if result:
        result = result[0]
    return result

# MARK: Database management
def update_db(table):
    """
    Update a table in the database
    Takes a table name as a string

    Updating the routes table just creates it if it doesn't exist
    Use add_routes("/path/to/csv") to add routes
    """

    match table.lower():
        case "aircraft":
            aircraft_headers = (
                "icao",
                "reg",
                "man",
                "del_man_name",
                "del_model",
                "type",
                "del_serial",
                "del_linenum",
                "del_typecode",
                "operator",
                "del_operatorcsign",
                "operatoricao",
                "del_operatoriata",
                "owner",
                "del_test_reg",
                "reged",
                "del_reged_until",
                "del_status",
                "built",
                "firstflight",
                "del_seat_config",
                "del_engines",
                "del_modes",
                "del_adsb",
                "del_acars",
                "del_notes",
                "del_categorydesc"
            )

            _csv_to_db(P.localdb, _URLS["aircraft"], "aircraft", aircraft_headers, "icao")

        case "airports":
            airport_headers = (
                "del_id",
                "del_ident",
                "del_type",
                "name",
                "lat",
                "lng",
                "alt",
                "continent",
                "country",
                "region",
                "muni",
                "airlines",
                "icao",
                "iata",
                "del_local",
                "website",
                "wiki",
                "del_keywords"
            )

            _csv_to_db(P.localdb, _URLS["airports"], "airports", airport_headers)

        case "airlines":
            _get_airlines_table()

        case "icontypes":
            icontypes_headers = (
                "type",
                "icon",
                "size"
            )

            _csv_to_db(P.localdb, _URLS["icontypes"], "icontypes", icontypes_headers, "type")

        case "prefixes":
            prefix_headers = (
                "prefix",
                "country"
            )

            _csv_to_db(P.localdb, _URLS["prefixes"], "prefixes", prefix_headers, "prefix")

        case "my_flights":
            instance_db = sqlite3.connect(P.instancedb)
            cursor = instance_db.cursor()

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' "
                           "AND name = 'my_flights'")
            if cursor.fetchone() is None:
                cursor.execute("CREATE TABLE my_flights "
                               "('date' TEXT, 'orig' TEXT, 'dest' TEXT, "
                               "'csign' TEXT, 'reg' TEXT, 'type' TEXT)")

            cursor.close()
            instance_db.commit()
            instance_db.close()

        case "routes":
            instance_db = sqlite3.connect(P.instancedb)
            cursor = instance_db.cursor()

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' "
                           "AND name = 'routes'")
            if cursor.fetchone() is None:
                cursor.execute("CREATE TABLE routes "
                               "('csign' TEXT, 'orig' TEXT, 'dest' TEXT)")

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_csign ON routes(csign)")

            cursor.close()
            instance_db.commit()
            instance_db.close()

        case "all":
            for table_name in ("aircraft", "airports", "airlines",
                               "icontypes", "prefixes", "routes"):
                update_db(table_name)

def check_dbs(output=print):
    """
    Check if the databases and tables are present
    Takes a log outputting method as a function (e.g. print)
    """

    dbs = {
        P.localdb: ("airlines", "aircraft", "airports", "icontypes", "prefixes"),
        P.instancedb: ("routes", "my_flights")
    }
    needs_update = []

    for db_path, tables in dbs.items():
        db = sqlite3.connect(db_path)
        cursor = db.cursor()
        for table in tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if cursor.fetchone() is None:
                needs_update.append(table)
        cursor.close()
        db.close()

    for index, table in enumerate(needs_update):
        output(f"{index + 1}/{len(needs_update)} creating {table} table")
        update_db(table)

def add_route(csign, orig=None, dest=None):
    """
    Add the origin and/or destination of a route
    Takes the callsign of the route and one or both of the route's origin/destination
    """

    if not (csign and (orig or dest)):
        return

    instance_db = sqlite3.connect(P.instancedb)
    cursor = instance_db.cursor()
    cursor.execute("SELECT * FROM routes WHERE csign = ?", (csign,))
    row_exists = cursor.fetchone()

    if row_exists:
        if orig:
            cursor.execute("UPDATE routes SET orig = ? WHERE csign = ?", (orig, csign))
        if dest:
            cursor.execute("UPDATE routes SET dest = ? WHERE csign = ?", (dest, csign))
    else:
        cursor.execute("INSERT INTO Routes ("
                       "csign, "
                       "orig, "
                       "dest"
                       ") VALUES (?, ?, ?)", (csign, orig, dest))

    instance_db.commit()
    cursor.close()
    instance_db.close()

# MARK: Lookup
def info(query, kind):
    """
    Get information from the database
    Takes a query and a kind as a string

    Kinds:
        airline - look up an airline from a callsign
        aircraft - look up an aircraft from a 24-bit ICAO address
        icontype - get the closest icon of an aircraft from its type
        airport - look up an airport from a 4-digit ICAO or 3-digit IATA code
        route - look up a route from its callsign

    Returns a dictionary or None
    """

    if not (query or kind):
        return None

    match kind.lower():
        case "airline":
            query = query.upper()[:3]
            result = _get_row("airlines", "icao", query)
        case "aircraft":
            query = query.lower()
            result = _get_row("aircraft", "icao", query)
            if "reg" in result:
                result["country"] = _get_country_from_reg(result["reg"])
        case "icontype":
            query = query.upper()
            result = _get_row("icontypes", "type", query)
            if "icon" not in result:
                result = {"icon": "generic", "size": 28}
        case "airport":
            query = query.upper()
            if len(query) == 3:
                result = _get_row("airports", "iata", query)
            elif len(query) == 4:
                result = _get_row("airports", "icao", query)
            else:
                result = None
        case "route":
            query = query.upper()
            result = _get_row("routes", "csign", query)
        case _:
            result = None

    return result

def basic(icao):
    """
    Get basic info for an aircraft (icontype, tail number, type code)
    Takes the aircraft's ICAO 24-bit address as a string
    Returns aircraft info as a dictionary with keys icon, reg, type
    """

    result = {}

    aircraft_info = info(icao, "aircraft")
    if "reg" in aircraft_info:
        result["reg"] = aircraft_info["reg"]

    if "type" in aircraft_info:
        result["type"] = aircraft_info["type"]
        result["icon"] = info(result["type"], "icontype")
        if "type" in result["icon"]:
            del result["icon"]["type"]
    else:
        result["icon"] = {"icon": "generic", "size": 28}

    return result

# MARK: Radio
def radio(thing):
    """
    Transpose something to radio-friendly language
    (NATO phonetic for letters, sounded out + 'NINER' for numbers)
    Returns the phonetic equivalent as a string
    """

    maps = {
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
        "A": "ALFA",
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

    string = str(thing).upper()
    if not string.isalnum() or not string:
        return ""

    result = ""
    for char in string.upper():
        result += maps[char] + " "

    return result.strip()

# MARK: Image
def image(query, kind, usewikimedia=False):
    """
    Get an image of something
    Takes a query, a kind, and whether to use Wikimedia to get the images (Planespotters otherwise)
    Returns a dictionary with keys src, attr, and link (link to the original page of the image)

    Kinds:
        hex - an aircraft's 24-bit ICAO address, works with Planespotters.net only
        reg - an aircraft's registration
        other - something else, works with Wikimedia only
    """

    src = None
    attr = None
    link = None

    if not usewikimedia and kind in ("hex", "reg"):
        response = requests.get("https://api.planespotters.net/pub/photos/"
                                + kind + "/" + query, timeout=60)
        if "error" not in response.json() and len(response.json()["photos"]):
            src = response.json()["photos"][0]["thumbnail_large"]["src"]
            attr = response.json()["photos"][0]["photographer"]
            link = response.json()["photos"][0]["link"]

    elif usewikimedia and kind in ("reg", "other"):
        # initial search
        response = requests.get("https://commons.wikimedia.org/w/api.php"
                                "?action=query&format=json&list=search&srsearch="
                                + query + "&srnamespace=6&srlimit=1", timeout=60)

        if not response or response.json()["query"]["searchinfo"]["totalhits"] == 0:
            return None

        title = response.json()["query"]["search"][0]["title"]
        link = "https://commons.wikimedia.org/wiki/" + title

        # get url
        response = requests.get("https://commons.wikimedia.org/w/api.php"
                                "?action=query&format=json&prop=imageinfo&iiprop=url&titles="
                                + title, timeout=60)
        src = list(response.json()["query"]["pages"].values())[0]["imageinfo"][0]["url"]

        # get attribution
        response = requests.get("https://commons.wikimedia.org/w/api.php"
                                "?action=query&titles=" + title +
                                "&prop=imageinfo&iiprop=extmetadata&format=json",
                                timeout=60)
        if response and not "-1" in response.json()["query"]["pages"]:
            metadata = next(iter(response.json()["query"]["pages"].values()))["imageinfo"][0]["extmetadata"]
            if metadata["AttributionRequired"]["value"] == "true":
                attr = metadata.get("Artist", {}).get("value")
                if attr:
                    attr = BeautifulSoup(attr, "html.parser").get_text()

    return {"src": src, "attr": attr, "link": link}

# MARK: My Flights
def my_flights():
    """
    Get my flights

    Returns a dictionary with keys:
        airlines - dict with information about airlines flown (ICAO code keys)
              - individual airline dicts have same keys as get.info(kind="airline")
        airports - dict with information about airports visited (ICAO code keys)
              - individual airport dicts have same keys as get.info(kind="airport")
        continents - list of visited continents
        countries - list of visited countries
        counts - dict with amounts of intercontinental, international and domestic flights
                 (keys inc, int, dom)
        flights - list of flights
              - individual flight dicts have keys orig and dest
        rankings - dict with keys airlines, types, airports
              - individual ranking lists are ordered destcending
                - rank items contain keys 'flights' and 'icao'
        type - dict with information about aircraft types flown (ICAO code keys)
    """

    update_db("my_flights")

    db = sqlite3.connect(P.instancedb)
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    cursor.execute("SELECT * FROM my_flights")
    rows = cursor.fetchall()
    db.close()

    mfl_table = [dict(row) for row in rows]

    mfl = {
        "airlines": {},
        "airports": {},
        "continents": [],
        "countries": [],
        "counts": {
            "inc": 0,
            "int": 0,
            "dom": 0
        },
        "flights": [],
        "rankings": {
            "airlines": [],
            "types": [],
            "airports": []
        },
        "types": {}
    }

    for flight in mfl_table:
        mfl["flights"].append({"orig": flight["orig"], "dest": flight["dest"]})

        for airport in (flight["orig"], flight["dest"]):
            if airport in mfl["airports"]:
                mfl["airports"][airport]["flights"] += 1
            else:
                mfl["airports"][airport] = info(airport, "airport")
                mfl["airports"][airport]["flights"] = 1
                if mfl["airports"][airport]["continent"] not in mfl["continents"]:
                    mfl["continents"].append(mfl["airports"][airport]["continent"])
                if mfl["airports"][airport]["country"] not in mfl["countries"]:
                    mfl["countries"].append(mfl["airports"][airport]["country"])

        if mfl["airports"][flight["orig"]]["country"] == mfl["airports"][flight["dest"]]["country"]:
            mfl["counts"]["dom"] += 1
        else:
            mfl["counts"]["int"] += 1

        if mfl["airports"][flight["orig"]]["continent"] != mfl["airports"][flight["dest"]]["continent"]:
            mfl["counts"]["inc"] += 1

        if flight["csign"]:
            if flight["csign"][:3] in mfl["airlines"]:
                mfl["airlines"][flight["csign"][:3]]["flights"] += 1
            else:
                mfl["airlines"][flight["csign"][:3]] = info(flight["csign"][:3], "airline")
                mfl["airlines"][flight["csign"][:3]]["flights"] = 1

        if flight["type"]:
            if flight["type"] in mfl["types"]:
                mfl["types"][flight["type"]]["flights"] += 1
            else:
                mfl["types"][flight["type"]] = {
                    "flights": 1,
                    "icao": flight["type"],
                    "icon": info(flight["type"], "icontype")["icon"]
                }

    mfl["continents"] = sorted(mfl["continents"])
    mfl["countries"] = sorted(mfl["countries"])

    for cat in mfl["rankings"]:
        for key in mfl[cat]:
            i = mfl[cat][key]
            rankings_entry = {"icao": i["icao"], "flights": i["flights"]}
            if mfl["rankings"][cat]:
                rankings_keys = [k["flights"] for k in mfl["rankings"][cat]]
                rankings = bisect_left(rankings_keys, rankings_entry["flights"])
            else:
                rankings = 0
            mfl["rankings"][cat].insert(rankings, rankings_entry)
        mfl["rankings"][cat].reverse()

    return mfl
