# flight\_tracker

Hopefully eventually an ADSB decoder and web flight tracking interface. At the moment uses [OpenSky Network](https://opensky-network.org) API states instead of decoding from a hardware reciever.

![Demo](demo/demo-light.png#gh-light-mode-only)
![Demo](demo/demo-dark.png#gh-dark-mode-only)
_Image of aircraft © Bahnfrend under CC BY-SA 4.0_

## Installation & usage for now
1. Clone this repository and run `pip install -r requirements.txt` (preferably in a virtual environment) and then `cd` to `src/`
2. For a fresh install, run:
```zsh
python3 opensky.py | python3 main.py
```
This runs [opensky.py](src/opensky.py), which, after downloading necessary datasets for you (just over 100MB to download about worldwide aircraft, airlines etc., just under 50MB when stored locally) sends a GET request to OpenSky and converts it to the format used by flight\_tracker, then the converted API response is passed to [main.py](src/main.py) which will load the API response and start the site.

To conserve your OpenSky API limit of 100 worldwide aircraft requests per day (and improve start time) run:
```zsh
python3 opensky.py > aircraft.json
```
And then pass the file to main.py.

3. The site will be put up at http://localhost:5003
4. The converted API response can be downloaded at http://localhost:5003/aircraft.json if you didn't save it in step 2, this file can then be passed to main.py
5. To quit, `KeyboardInterrupt` with `⌃C`.

### Options
* To change options, use the `defaults` command with the domain flight_tracker.
* To view the default settings (to know what you can change), `cd` to `src/` and run:
```python
>>> from instance import Settings
>>> Settings.defaults
```
in the Python shell, to see the default settings printed as a dictionary.

## To-do
* Make web interface (using opensky api demo json files for testing)
    * Map
        * ~~Add aircraft~~
        * ~~Make aircraft animate across the map even without being updated~~
            * Fix animations bugging over time - is this just because there are a lot of aircraft in the OS API state?
        * ~~Add special icons for aircraft (by type)~~
            * Rear-mounted engine narrowbody, small twin turboprop (use AT72? too big?), and helicopter (animate!) icons
        * Make it so more than 500-ish aircraft can be on the map at once (performance limitation) - server or client side selection of aircraft based on client view area?
        * ~~State saving - JSONs~~ through the web interface
    * Aircraft list/sidebar
        * ~~Add callsigns and metrics~~
        * ~~Add airline logos from FlightAware~~
        * ~~Reorganise (airline logos too big?)~~
        * ~~Change metrics shown?~~
        * ~~Optimise and fix buggy scrolling on mobile~~
        * ~~Simple filter~~
            * Improve filter
        * Profile pic menu
    * Flight detail view
        * ~~Fix horrendous implementation in JS~~
        * ~~Callsign~~
            * ~~Radio callsign in tooltip~~
                * Not visible in mobile! find workaround!
        * ~~Tail number identification from database~~
            * ~~Plane image from JetPhotos~~
            * Add algorithms for specific countries when the tails are not on OpenSky database, e.g. US N-numbers?
        * ~~Country identification from tail number~~
            * ~~Add flag~~
            * Change algorithm/DB to identify countries by their ICAO24 address and not the tail number (more reliable and can identify things tail numbers can't e.g. Taiwan)
        * ~~Basic routing with airport code identification and route plotting~~
            * Fix when routes go past the intl date line
        * Advanced routing (e.g. multi stop routes, bidirectional routes)
            * Do based on heading or location or both?
            * Built in routes? Or algorithms to find routes? Legality of this?
        * Metrics
            * ~~Speed in a dial~~
                * Add colour to make it nicer?
                * ~~Change position?~~
            * ~~Vertical speed~~
            * ~~Altitude - how to represent nicely?~~
            * ~~Heading - nice compass design?~~
                * ~~Change smooth circle to ticks like an actual compass?~~
    * Other detail pages? e.g. airlines, airports, aircraft? universal lookup (get) function?
    * Personal flight log page
    * Preferences page
        * Potential preferences: map theme (already implemented in JS but not visibly), theme colour, font disambiguation, units, use of IATA or ICAO codes for airlines and airports, plane pictures and airline icons sources, caching options, internet free mode?, possibly also local system settings (if run on RPi etc.)
    * Design
        * ~~Implement dark mode~~
            * ~~Make dark mode for the OSM map by inverting and then rotating the hue~~
        * ~~Use Inter and self made plane icon instead of SF for open source and consistency~~
        * New favicon - ~~add stuff for iOS web apps?~~
        * ~~Design special icons (as mentioned)~~
    * Implementation of weather info? Possible without cost?
* Database management
    * ~~Basic functions (downloading, converting to SQLite, accessing)~~
    * Automatic updating
* Later on, make actual ADSB decoder software to locally decode things

## Data sources
Downloaded as needed by [get.py](src/get.py)
* Aircraft table from [opensky-network.org](https://opensky-network.org/datasets/metadata) under [their license](https://opensky-network.org/datasets/LICENSE.txt)
* Airports table from [ourairports.com](https://ourairports.com/data) under the Unlicense
* Codes table from [wikipedia.org](https://en.wikipedia.org/wiki/List_of_airline_codes) under CC BY-SA 3.0
