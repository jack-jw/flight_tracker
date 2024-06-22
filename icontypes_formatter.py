# icontypes_formatter

"""
Generates a distributable .csv from icontypes.json

Development only
"""

import json
import csv

with open("icontypes.json", encoding="utf-8") as jf:
    icontypes = json.load(jf)

csv_contents = [["type", "icon", "size"]]

for icon_type, aircraft_types in icontypes.items():
    for aircraft in aircraft_types["types"]:
        csv_contents.append([aircraft, icon_type, aircraft_types["size"]])

with open("icontypes.csv", "w", newline="", encoding="utf-8") as cf:
    writer = csv.writer(cf)
    writer.writerows(csv_contents)
