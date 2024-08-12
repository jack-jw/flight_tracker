# get.py

"""
Get things for flight_tracker
"""

from csv import reader
from getpass import getuser
from json import load
from locale import getlocale
from os import makedirs
from os.path import dirname, exists, expanduser
from re import Match, search
from sys import platform
from typing import Callable, cast, Iterator, TypedDict
import sqlite3
import requests
from bs4 import BeautifulSoup, NavigableString, Tag

__all__: list[str] = [
    "DEFAULTS",
    "preferences",
    "settings",
    "STRINGS",
    "update_db",
    "check_dbs",
    "add_route",
    "info",
    "radio",
    "image",
    "my_flights",
    "mfr24_to_mf"
]

_URLS: dict[str, str] = {
    "airlines_wiki": "https://en.wikipedia.org/wiki/List_of_airline_codes",
    "aircraft": "https://opensky-network.org/datasets/metadata/aircraftDatabase.csv",
    "airports": "https://davidmegginson.github.io/ourairports-data/airports.csv",
    "icontypes": "https://raw.githubusercontent.com/jack-jw/flight_tracker/main/icontypes.csv",
    "prefixes": "https://raw.githubusercontent.com/jack-jw/flight_tracker/main/prefixes.csv"
}

# really bad paths, settings and strings implementation. fix!!
# paths
_paths: dict[str, str] = {file: expanduser("~") for file in ("instance", "local", "settings")}
if platform == "darwin":
    import plistlib

    _paths["instance"] += "/Library/Application Support/flight_tracker.db"
    _paths["local"] += "/Library/Caches/flight_tracker.db"
    _paths["settings"] += "/Library/Preferences/flight_tracker.plist"
else:
    from json import dump

    # not the best implementation?
    _paths["instance"] += "/.flight_tracker/instance.db"
    _paths["local"] += "/.flight_tracker/local.db"
    _paths["settings"] += "/.flight_tracker/settings.json"
for file in _paths.values():
    makedirs(dirname(file), exist_ok=True)

locale: tuple[str | None, str | None] = getlocale()
if isinstance(locale[0], str):
    SYS_LANG = locale[0][:2]
else:
    SYS_LANG = "en"

# settings
DEFAULTS: dict[str, str | int | bool] = {
    "name": getuser(),
    "colour": "#3478F6",
    "port": 5003,
    "usewikimedia": False,
    "fontdisambiguation": False,
    "language": SYS_LANG
}
if not exists(_paths["settings"]):
    if platform == "darwin":
        with open(_paths["settings"], "wb") as psfr:
            plistlib.dump({}, psfr)
    else:
        with open(_paths["settings"], "w", encoding="utf-8") as jsfr:
            dump({}, jsfr)

preferences: dict[str, str | int | bool]
if platform == "darwin":
    with open(_paths["settings"], "rb") as psfw:
        preferences = plistlib.load(psfw)
else:
    with open(_paths["settings"], "r", encoding="utf-8") as jsfw:
        preferences = load(jsfw)

settings: dict[str, str | int | bool] = {**DEFAULTS, **preferences}

# strings
class UIStrings(TypedDict):
    """TypedDict for UI localised strings"""
    dest: str
    filter: str
    map: str
    myflights: str
    myflightscounts: dict[str, list[str]]
    orig: str

class Strings(TypedDict):
    """TypedDict for localised strings"""
    acknowledgements: dict[str, str]
    logs: dict[str, str]
    ui: UIStrings
    units: dict[str, dict[str, str]]

with open("strings.json", "r", encoding="utf-8") as sfr:
    STRINGS: Strings = load(sfr)[settings.get("language", "en")]

# MARK: - Internal functions
def _csv_to_db(database: str,
               url: str,
               table_name: str,
               column_names: tuple[str, ...],
               index_column: str = "") -> None:
    """
    Internal, use update_db()
    Get a CSV from the web and add it to a database
    """
    try:
        response: requests.Response = requests.get(url, timeout=300)
        if not response.ok:
            return
    except requests.exceptions.ReadTimeout:
        return

    data: list[str] = response.text.splitlines()

    fil_columns: list[str] = [col for col in column_names if not col.startswith("del_")]
    fil_indices: list[int] = [i for i, col in enumerate(column_names) if not col.startswith("del_")]

    db: sqlite3.Connection = sqlite3.connect(database)
    cursor: sqlite3.Cursor = db.cursor()

    try:
        cursor.execute(f"DROP TABLE {table_name}")
    except sqlite3.OperationalError:
        pass

    columns_str: str = ", ".join([f"'{col}' TEXT" for col in fil_columns])
    cursor.execute(f"CREATE TABLE {table_name} ({columns_str})")

    csv_reader: Iterator[list[str]] = reader(data)
    next(csv_reader)
    for row in csv_reader:
        fil_row = [row[i] for i in fil_indices]
        cursor.execute(f"INSERT INTO {table_name} "
                       f"VALUES ({', '.join(['?' for _ in range(len(fil_columns))])}"
                       ")", fil_row)

    if index_column:
        cursor.execute(f"CREATE INDEX idx_{index_column} ON {table_name}({index_column})")

    cursor.close()
    db.commit()
    db.close()

def _get_row(table: str,
             search_column: str,
             query: str,
             loopback: bool = False) -> dict[str, str]:
    """
    Internal, use info()
    Get a row from the DB (instance if table is routes, else local)
    If loopback is True, always returns the search column with the value of the query
    """
    db: sqlite3.Connection = sqlite3.connect(_paths["instance"] if table == "routes"
                                             else _paths["local"])
    db.row_factory = sqlite3.Row
    cursor: sqlite3.Cursor = db.cursor()

    while True:
        try:
            cursor.execute(f"SELECT * FROM {table} WHERE `{search_column}` = '{query}'")
            break
        except sqlite3.OperationalError:
            update_db(table)

    result: sqlite3.Row | None = cursor.fetchone()
    cursor.close()
    db.close()

    row: dict[str, str] = {}

    if isinstance(result, sqlite3.Row):
        row = dict(result)
        for key, value in row.copy().items():
            if not value:
                del row[key]
    elif loopback:
        row[search_column] = query

    return row

def _get_country_from_reg(reg: str) -> str:
    """
    Internal, use info()
    Get the corresponding ISO 2-letter country code for an aircraft registration
    """
    db = sqlite3.connect(_paths["local"])
    cursor = db.cursor()

    while True:
        try:
            cursor.execute("SELECT country FROM prefixes WHERE ? LIKE prefix || '%'", (reg,))
            break
        except sqlite3.OperationalError:
            update_db("prefixes")

    result: tuple | None = cursor.fetchone()
    cursor.close()
    db.close()
    return result[0] if isinstance(result, tuple) else ""

# MARK: - Public functions
def update_db(table: str) -> None:
    """
    Update a table in the database
    Takes a table name (aircraft, airports, airlines, icontypes, prefixes, my_flights, routes)
    Passing "all" updates every table

    Updating the routes/my_flights table only creates the table if it doesn't exist
    """
    match table.lower():
        case "aircraft":
            _csv_to_db(_paths["local"],
                       _URLS["aircraft"],
                       "aircraft",
                       ("icao",
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
                        "del_categorydesc"),
                       "icao")

        case "airlines":
            try:
                response: requests.Response = requests.get(_URLS["airlines_wiki"], timeout=120)
                if not response.ok:
                    return
            except requests.exceptions.ReadTimeout:
                return

            airlines_table: Tag | NavigableString | None = BeautifulSoup(response.content,
                                                                         "html.parser").find(
                "table", class_="wikitable")

            if isinstance(airlines_table, Tag):
                adb: sqlite3.Connection = sqlite3.connect(_paths["local"])
                acursor: sqlite3.Cursor = adb.cursor()

                try:
                    acursor.execute("DROP TABLE airlines")
                except sqlite3.OperationalError:
                    pass

                acursor.execute("CREATE TABLE airlines "
                                "('iata' TEXT, "
                                "'icao' TEXT, "
                                "'name' TEXT, "
                                "'radio' TEXT, "
                                "'country' TEXT)")

                rows: list[Tag] = airlines_table.find_all("tr")[1:]

                noadd: tuple[str, str, str] = (
                    "defunct",
                    "no longer allocated",
                    "icao code in use by another company"
                )

                for row in rows:
                    columns: list[Tag] = row.find_all("td")
                    data: list[str | None] = [column.get_text(strip=True) for column in columns]
                    data += [""] * (6 - len(data))
                    if data[5] is None or not any(word in data[5].lower() for word in noadd):
                        acursor.execute("INSERT INTO airlines VALUES (?, ?, ?, ?, ?)", data[:5])

                acursor.close()
                adb.commit()
                adb.close()

        case "airports":
            _csv_to_db(_paths["local"],
                       _URLS["airports"],
                       "airports",
                       ("del_id",
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
                        "del_keywords"))

        case "icontypes":
            _csv_to_db(_paths["local"],
                       _URLS["icontypes"],
                       "icontypes",
                       ("type", "icon", "size"),
                       "type")

        case "prefixes":
            _csv_to_db(_paths["local"],
                       _URLS["prefixes"],
                       "prefixes",
                       ("prefix", "country"),
                       "prefix")

        case "my_flights" | "routes":
            idb: sqlite3.Connection = sqlite3.connect(_paths["instance"])
            icursor: sqlite3.Cursor = idb.cursor()

            icursor.execute("SELECT name FROM sqlite_master WHERE type='table' "
                            f"AND name = '{table.lower()}'")
            if icursor.fetchone() is None:
                if table.lower() == "my_flights":
                    icursor.execute("CREATE TABLE my_flights "
                                    "('date' TEXT, 'orig' TEXT, 'dest' TEXT, "
                                    "'csign' TEXT, 'reg' TEXT, 'type' TEXT)")
                else:
                    icursor.execute("CREATE TABLE routes "
                                    "('csign' TEXT, 'orig' TEXT, 'dest' TEXT)")

            icursor.close()
            idb.commit()
            idb.close()

        case "all":
            for table_name in ("aircraft", "airports", "airlines",
                               "icontypes", "prefixes", "routes"):
                update_db(table_name)

def check_dbs(output: Callable[[str], None] = print) -> None:
    """
    Check if all the databases and tables are present
    Takes a callable to output logs to (e.g. lambda l: print(l, file=sys.stderr) outputs to stderr)
    """
    dbs: dict[str, tuple[str, ...]] = {
        _paths["local"]: ("airlines", "aircraft", "airports", "icontypes", "prefixes"),
        _paths["instance"]: ("routes", "my_flights")
    }
    needs_update: list[tuple[str, str]] = []

    for db_path, tables in dbs.items():
        db: sqlite3.Connection = sqlite3.connect(db_path)
        cursor: sqlite3.Cursor = db.cursor()
        for table in tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if cursor.fetchone() is None:
                needs_update += [(db_path, table)]
        cursor.close()
        db.close()

    for index, (db_path, table) in enumerate(needs_update, start=1):
        output(STRINGS["logs"]["creatingtable"].format(i=index, l=len(needs_update),
                                                       t=table, p=db_path))
        update_db(table)

def add_route(csign: str, orig: str = "", dest: str = "") -> None:
    """
    Add the origin and/or destination of a route
    Can add both the origin and the destination or just one
    Only takes 4-letter ICAO codes for airports
    """
    if not (csign and (orig or dest)):
        return

    db: sqlite3.Connection = sqlite3.connect(_paths["instance"])
    cursor: sqlite3.Cursor = db.cursor()
    cursor.execute("SELECT * FROM routes WHERE csign = ?", (csign,))
    row_exists: tuple | None = cursor.fetchone()

    if isinstance(row_exists, tuple):
        if orig:
            cursor.execute("UPDATE routes SET orig = ? WHERE csign = ?", (orig, csign))
        if dest:
            cursor.execute("UPDATE routes SET dest = ? WHERE csign = ?", (dest, csign))
    else:
        cursor.execute("INSERT INTO routes ("
                       "csign, "
                       "orig, "
                       "dest"
                       ") VALUES (?, ?, ?)", (csign, orig, dest))

    db.commit()
    cursor.close()
    db.close()

def info(query: str, kind: str) -> dict[str, str]:
    """
    Get information from the database

    Kinds:
        aircraft - look up an aircraft from a 24-bit ICAO address
        airline - look up an airline from a callsign
        airport - look up an airport from a 4-digit ICAO or 3-digit IATA code (detects for you)
        basic - get an aircraft's type, reg, and icon type
        icontype - get the closest icon of an aircraft from its type
        route - look up a route from its callsign

    If the value can't be found:
        aircraft, route: returns the query as part of a dict
        airline: returns an empty dict
        airport: returns the query as part of a dict if it is 3/4 chars, else an empty dict
        basic: if aircraft info/icontype can't be found, just the icontype generic
        icontype: returns the query with icontype generic
    """
    result: dict[str, str] = {}

    match kind.lower():
        case "aircraft":
            query = query.lower()
            result = _get_row("aircraft", "icao", query, loopback=True)
            if "reg" in result:
                result["radio"] = radio(result["reg"].replace("-", ""))
                result["country"] = _get_country_from_reg(result["reg"])
        case "airline":
            query = query.upper()[:3]
            result = _get_row("airlines", "icao", query)
        case "airport":
            query = query.upper()
            if len(query) == 3:
                result = _get_row("airports", "iata", query, loopback=True)
            elif len(query) == 4:
                result = _get_row("airports", "icao", query, loopback=True)
        case "basic":
            aircraft_row: dict[str, str] = _get_row("aircraft", "icao", query)
            if "reg" in aircraft_row:
                result["reg"] = aircraft_row["reg"]

            result["icon"] = "generic"
            if "type" in aircraft_row:
                result["type"] = aircraft_row["type"]
                icon_row: dict[str, str] = _get_row("icontypes", "type", result["type"])
                if icon_row:
                    result["icon"] = icon_row["icon"]
        case "icontype":
            query = query.upper()
            result = _get_row("icontypes", "type", query, loopback=True)
            if "icon" not in result:
                result["icon"] = "generic"
        case "route":
            query = query.upper()
            result = _get_row("routes", "csign", query, loopback=True)

    return result

def radio(string: str) -> str:
    """
    Transpose a string to radio-friendly language
    (NATO phonetic for letters, sounded out + 'NINER' for numbers)
    Returns non-alphanumeric characters the same
    """
    maps: dict[str, str] = {
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

    return " ".join([maps.get(char, char) for char in string.upper()])

def image(query: str, kind: str, usewikimedia: bool = False) -> dict[str, str]:
    """
    Get an image of something
    Uses Planespotters.net to get images (or Wikimedia if usewikimedia = True)
    Returns a dict with keys src, attr, and link (link to the original page of the image)

    Kinds:
        hex - an aircraft's 24-bit ICAO address (Planespotters.net only)
        reg - an aircraft's registration (Planespotters.net or Wikimedia)
        other (Wikimedia only)
    """
    result: dict[str, str] = {
        "src": "",
        "attr": "",
        "link": ""
    }

    if not usewikimedia and kind in ("hex", "reg"):
        response: requests.Response = requests.get("https://api.planespotters.net/pub/photos/"
                                                   + kind + "/" + query, timeout=60)
        if "error" not in response.json() and len(response.json()["photos"]):
            result["src"] = response.json()["photos"][0]["thumbnail_large"]["src"]
            result["attr"] = response.json()["photos"][0]["photographer"]
            result["link"] = response.json()["photos"][0]["link"]

    elif usewikimedia and kind in ("reg", "other"):
        # initial search
        initial: requests.Response = requests.get("https://commons.wikimedia.org/w/api.php"
                                                  "?action=query&format=json&list=search"
                                                  "&srsearch=" + query +
                                                  "&srnamespace=6&srlimit=1", timeout=60)

        if not initial or initial.json()["query"]["searchinfo"]["totalhits"] == 0:
            return result

        title: str = initial.json()["query"]["search"][0]["title"]
        result["link"] = "https://commons.wikimedia.org/wiki/" + title

        # get url
        src: requests.Response = requests.get("https://commons.wikimedia.org/w/api.php"
                                              "?action=query&format=json&prop=imageinfo"
                                              "&iiprop=url&titles=" + title, timeout=60)
        result["src"] = list(src.json()["query"]["pages"].values())[0]["imageinfo"][0]["url"]

        # get attribution
        attr: requests.Response = requests.get("https://commons.wikimedia.org/w/api.php"
                                               "?action=query&titles=" + title +
                                               "&prop=imageinfo&iiprop=extmetadata"
                                               "&format=json", timeout=60)
        if attr and "-1" not in attr.json()["query"]["pages"]:
            meta: dict[str, dict[str, str | float]] = next(
                iter(attr.json()["query"]["pages"].values())
            )["imageinfo"][0]["extmetadata"]
            if str(meta["AttributionRequired"]["value"]).lower() == "true":
                attr_elem: str | float | None = meta.get("Artist", {}).get("value")
                if isinstance(attr_elem, str):
                    result["attr"] = BeautifulSoup(attr_elem, "html.parser").get_text()

    return result

def my_flights() -> dict[str, dict[str, list[dict[str, str | int]]] | dict[str, int] | list[str]
                              | list[dict[str, str]]]:
    """Get my flights"""
    update_db("my_flights")

    db: sqlite3.Connection = sqlite3.connect(_paths["instance"])
    db.row_factory = sqlite3.Row
    cursor: sqlite3.Cursor = db.cursor()
    cursor.execute("SELECT * FROM my_flights")
    rows: tuple[sqlite3.Row, ...] = tuple(cursor.fetchall())
    db.close()

    def idx(data: list[dict[str, str | int]],
            value: str,
            key: str = "icao") -> int:
        """Get the index of a dictionary in a list by one of its keys"""

        return next((n for n, data in enumerate(data) if data.get(key) == value), -1)

    entities: dict[str, list[dict[str, str | int]]] = {
        "airlines": [],
        "airports": [],
        "types": []
    }

    counts: dict[str, int] = {
        "inc": 0,
        "int": 0,
        "dom": 0,
        "rnl": 0
    }

    continents: list[str] = []
    countries: list[str] = []
    flights: list[dict[str, str]] = []

    if isinstance(rows, tuple):
        flights = [dict(row) for row in rows]
        i: int

        for flight in flights:
            origin_continent: str = ""
            origin_country: str = ""
            origin_region: str = ""
            for airport in ("orig", "dest"):
                i = idx(entities["airports"], flight[airport])
                if i != -1:
                    entities["airports"][i]["flights"] = 1 + cast(int,
                                                                  entities["airports"][i][
                                                                      "flights"])
                else:
                    entities["airports"].append({
                        **info(flight[airport], "airport"),
                        "flights": 1
                    })
                    if entities["airports"][i]["continent"] not in continents:
                        continents.append(cast(str, entities["airports"][i]["continent"]))
                    if entities["airports"][i]["country"] not in countries:
                        countries.append(cast(str, entities["airports"][i]["country"]))

                if airport == "orig":
                    origin_continent = cast(str, entities["airports"][i]["continent"])
                    origin_country = cast(str, entities["airports"][i]["country"])
                    origin_region = cast(str, entities["airports"][i]["region"])
                elif airport == "dest":
                    if origin_continent != entities["airports"][i]["continent"]:
                        counts["inc"] += 1
                    if origin_country == entities["airports"][i]["country"]:
                        counts["dom"] += 1
                    else:
                        counts["int"] += 1
                    if origin_region == entities["airports"][i]["region"]:
                        counts["rnl"] += 1

            if flight["csign"]:
                i = idx(entities["airlines"], flight["csign"][:3])
                if i != -1:
                    entities["airlines"][i]["flights"] = 1 + cast(int,
                                                                  entities["airlines"][i][
                                                                      "flights"])
                else:
                    entities["airlines"].append({
                        "name": flight["csign"][:3],
                        **info(flight["csign"][:3], "airline"),
                        "flights": 1
                    })

            if flight["type"]:
                i = idx(entities["types"], flight["type"])
                if i != -1:
                    entities["types"][i]["flights"] = 1 + cast(int, entities["types"][i]["flights"])
                else:
                    entities["types"].append({
                        "icon": info(flight["type"], "icontype")["icon"],
                        "icao": flight["type"],
                        "flights": 1
                    })

        continents = sorted(continents)
        countries = sorted(countries)
        entities = {c: sorted(e, key=lambda v: v["flights"], reverse=True)
                    for c, e in entities.items()}
    return {"entities": entities,
            "counts": counts,
            "continents": continents,
            "countries": countries,
            "flights": flights}

def mfr24_to_mf(mfr24: str) -> None:
    """Add flights from a My Flightradar24 CSV (as a string) to my_flights"""
    def brackets(string: str) -> str:
        """Get the text in brackets in a string (and remove slashes)"""
        match: Match[str] | None = search(r"\((.*?)\)", string)
        result: str = ""
        if match is not None:
            result = match.group().replace("/", "").strip()[1:-1]
        return result

    db: sqlite3.Connection = sqlite3.connect(_paths["instance"])
    cursor: sqlite3.Cursor = db.cursor()
    rows: list[str] = mfr24.replace('"',"").strip().splitlines()[1:]
    for row in rows:
        columns: list[str] = row.split(",")
        data: tuple[str, str, str, str, str, str] = (
            columns[0],                                 # data
            brackets(columns[2])[-4:],                   # orig
            brackets(columns[3])[-4:],                   # dest
            brackets(columns[7])[-3:] + columns[1][2:],  # csign
            columns[9],                                 # reg
            brackets(columns[8])                        # type
        )
        cursor.execute("INSERT INTO my_flights ("
                       "date, "
                       "orig, "
                       "dest, "
                       "csign, "
                       "reg, "
                       "type"
                       ") VALUES (?, ?, ?, ?, ?, ?)", data)
    cursor.close()
    db.commit()
    db.close()
