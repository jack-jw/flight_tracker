# flight tracker

very much a work in progress is not functional yet at all!!

Hopefully eventually an ADSB decoder and web flight tracking interface

## Installation & usage for now
1. Clone this repository and run `pip install -r requirements.txt` (preferably in a virtual environment)
2. Get an API response from [the OpenSky Network](https://opensky-network.org/api/states/all) and save it to your computer as a JSON file
3. `cd` to `src/` and then `python3 main.py /path/to/JSON/file`
4. Visit the site at http://localhost:5003

## To-do
* Make web interface (using opensky api demo json files for testing)
    * Map
        * ~~Add aircraft~~
        * ~~Make aircraft animate across the map even without being updated~~
            * Fix animations bugging over time - is this just because there are a lot of aircraft in the OS API state?
        * ~~Add special icons for aircraft (by type)~~
            * Rear-mounted engine narrowbody, small twin turboprop (use AT72? too big?), and helicopter (animate!) icons
        * Make it so more than 500-ish aircraft can be on the map at once (performance limitation) - server or client side selection of aircraft?
        * ~~Add UI to import from opensky, not just locally?~~ OpenSky is only for development so this would be a waste of time
        * State saving - JSONs or through the web interface?
    * Aircraft list/sidebar
        * ~~Add callsigns and metrics~~
        * ~~Add airline logos from FlightAware~~
        * ~~Reorganise (airline logos too big?)~~
        * ~~Change metrics shown?~~
        * ~~Optimise and fix buggy scrolling on mobile~~
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
                * Change smooth circle to ticks like an actual compass?
    * Other detail pages? e.g. airlines, airports, aircraft? universal lookup function?
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
* Aircraft table from [opensky-network.org](https://opensky-network.org/datasets/metadata)
* Airports table from [ourairports.com](https://ourairports.com/data)
* Codes table from [wikipedia.org](https://en.wikipedia.org/wiki/List_of_airline_codes)
