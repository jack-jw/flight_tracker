// static/my_flights.js

document.addEventListener('DOMContentLoaded', function() {
    let totalDistance = 0;

    // MARK: - Map

    function plotGreatCircleRoute(startPoint, endPoint) {
        function computeIntermediatePoint(start, end, ratio) {
            const lat1 = start.lat * Math.PI / 180;
            const lng1 = start.lng * Math.PI / 180;
            const lat2 = end.lat * Math.PI / 180;
            const lng2 = end.lng * Math.PI / 180;
            const d = 2 * Math.asin(Math.sqrt(Math.pow(Math.sin((lat1 - lat2) / 2), 2) + Math.cos(lat1) * Math.cos(lat2) * Math.pow(Math.sin((lng1 - lng2) / 2), 2)));
            const A = Math.sin((1 - ratio) * d) / Math.sin(d);
            const B = Math.sin(ratio * d) / Math.sin(d);
            const x = A * Math.cos(lat1) * Math.cos(lng1) + B * Math.cos(lat2) * Math.cos(lng2);
            const y = A * Math.cos(lat1) * Math.sin(lng1) + B * Math.cos(lat2) * Math.sin(lng2);
            const z = A * Math.sin(lat1) + B * Math.sin(lat2);
            const lat = Math.atan2(z, Math.sqrt(Math.pow(x, 2) + Math.pow(y, 2))) * 180 / Math.PI;
            const lng = Math.atan2(y, x) * 180 / Math.PI;
            return [lat, lng];
        };

        function computeGreatCircleDistance(start, end) {
            const R = 6371000;
            const lat1 = start.lat * Math.PI / 180;
            const lng1 = start.lng * Math.PI / 180;
            const lat2 = end.lat * Math.PI / 180;
            const lng2 = end.lng * Math.PI / 180;
            const deltaLat = lat2 - lat1;
            const deltalng = lng2 - lng1;
            const a = Math.sin(deltaLat / 2) * Math.sin(deltaLat / 2) + Math.cos(lat1) * Math.cos(lat2) * Math.sin(deltalng / 2) * Math.sin(deltalng / 2);
            const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
            const distance = R * c;
            return distance;
        };

        const startLatLng = L.latLng(startPoint);
        const endLatLng = L.latLng(endPoint);

        const curvePoints = [];
        for (let i = 0; i <= 100; i++) {
            const ratio = i / 100;
            const intermediatePoint = computeIntermediatePoint(startLatLng, endLatLng, ratio);
            curvePoints.push(intermediatePoint);
        };

        const line = L.polyline(curvePoints, { color: '#FF9500', weight: 2, opacity: 0.75 }).addTo(map);
        line.getElement().setAttribute('tabindex', '-1');
        const distance = computeGreatCircleDistance(startLatLng, endLatLng);
        return distance;
    };

    function setTheme(themeName) {
        let tileLayerURL;
        let credit;
        switch (themeName) {
            case 'standard':
                tileLayerURL = 'https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png';
                credit = 'Map data © OpenStreetMap contributors<br>Tiles © Humanitarian OpenStreetMap Team (HOT)';
                document.querySelector('.leaflet-tile-pane').style.filter = null;
                break;
            case 'osm':
                tileLayerURL = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
                credit = 'Map data © OpenStreetMap contributors';
                document.querySelector('.leaflet-tile-pane').style.filter = null;
                break;
            case 'watercolour':
                tileLayerURL = 'https://watercolormaps.collection.cooperhewitt.org/tile/watercolor/{z}/{x}/{y}.jpg';
                credit = 'Map data © OpenStreetMap contributors<br>Tiles © Stamen Design';
                document.querySelector('.leaflet-tile-pane').style.filter = 'none';
                break;
            case 'satellite':
                tileLayerURL = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}';
                credit = 'Map data © Esri, World Imagery';
                document.querySelector('.leaflet-tile-pane').style.filter = 'none';
                break;
            case 'atc':
                tileLayerURL = 'https://data2.geo-fs.com/osm/{z}/{x}/{y}.png';
                credit = 'Map data © OpenStreetMap contributors<br>Tiles © GeoFS';
                document.querySelector('.leaflet-tile-pane').style.filter = null;
                break;
            default:
                return;
        };
        tileLayer.setUrl(tileLayerURL);
        document.getElementById('my-flights-map-credit').innerHTML = credit;
    };

    // MARK: Map definition
    const map = L.map('map', {
        center: [51.505, -0.09],
        zoom: 3,
        maxZoom: 15,
        zoomControl: false,
        attributionControl: false
    });

    const tileLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
            detectRetina: true, // not good for some of the maps
        }).addTo(map);
    setTheme('satellite');

    // MARK: - Flights

    function animateNumber(element, end, singular, plural, dp) {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) { startTimestamp = timestamp; };
            const progress = Math.min((timestamp - startTimestamp) / 1000, 1);
            const displayedProgress = (progress * end).toFixed(dp);
            let description;
            if (displayedProgress === 1) { description = singular; };
                else { description = plural; };
            element.textContent = displayedProgress + description;
            if (progress < 1) { window.requestAnimationFrame(step); };
        };
        window.requestAnimationFrame(step);
    };

    function animateFlags(element, countryList) {
        const interval = 1000 / countryList.length;

        let index = 0;
        const addFlag = () => {
            if (index < countryList.length) {
                const flagElement = document.createElement('div');
                flagElement.classList = 'flag';
                flagElement.style.backgroundImage = 'url(/image/flag/' + countryList[index] + ')';
                element.appendChild(flagElement);
                index++;
            } else {
                clearInterval(flagInterval);
            };
        };
        const flagInterval = setInterval(addFlag, interval);
    };

    map.flyTo([myFlights.airports[myFlights.rankings.airports[0].icao].lat,
               myFlights.airports[myFlights.rankings.airports[0].icao].lng]);

    myFlights.flights.forEach(function(flight) {
        totalDistance += plotGreatCircleRoute(myFlights.airports[flight.orig], myFlights.airports[flight.dest]);
    });

    animateNumber(document.getElementById('my-flights-flight-count'), myFlights.flights.length, ' flight', ' flights', 0);
    animateNumber(document.getElementById('my-flights-intercontinental-count'), myFlights.counts.inc, ' intercontinental', ' intercontinental', 0);
    animateNumber(document.getElementById('my-flights-international-count'), myFlights.counts.int, ' international', ' international', 0);
    animateNumber(document.getElementById('my-flights-domestic-count'), myFlights.counts.dom, ' domestic', ' domestic', 0);

    animateNumber(document.getElementById('my-flights-distance-count'), totalDistance / 1000, ' km', ' km', 0);
    animateNumber(document.getElementById('my-flights-distance-count-earth'), totalDistance / 40030174, 'x around the Earth', 'x around the Earth', 2);

    animateNumber(document.getElementById('my-flights-country-count'), myFlights.countries.length, ' country', ' countries', 0);
    animateFlags(document.getElementById('my-flights-country-count-flags'), myFlights.countries);
    animateNumber(document.getElementById('my-flights-continent-count'), myFlights.continents.length, ' out of the 7 continents', ' out of the 7 continents', 0);

    animateNumber(document.getElementById('my-flights-airports-title'), Object.keys(myFlights.airports).length, ' airport', ' airports', 0);
    animateNumber(document.getElementById('my-flights-airlines-title'), Object.keys(myFlights.airlines).length, ' airline', ' airlines', 0);
    animateNumber(document.getElementById('my-flights-types-title'), Object.keys(myFlights.types).length, ' aircraft type', ' aircraft types', 0);

    Object.values(myFlights.airports).forEach(function(airport) {
        const tooltipContent = `
            <div class="my-flights-airport-tooltip-title">
                <span class="flag" style="background-image: url('/image/flag/${airport.country}')"></span>
                <span class="my-flights-airport-tooltip-iata">${airport.iata}</span> ${airport.name.replace('International', "Int'l").replace('Airport', '').trim()}
            </div>
            <div class="my-flights-airport-tooltip-flights">${airport.flights} flight${airport.flights > 1 ? 's' : ''}</div>
        `;

        L.marker([airport.lat, airport.lng], {
            icon: L.divIcon({
                className: 'my-flights-airport-icon',
                html: '<div></div>',
                iconSize: [12, 12]
            })
        }).addTo(map).setZIndexOffset(airport.flights).bindTooltip(tooltipContent, { className: 'my-flights-airport-tooltip' });
    });

    Object.keys(myFlights.rankings).forEach(function(category) {
        const baseClass = `my-flights-${category}-`;
        for (let i = 0; i < 5; i++) {
            const rankItem = document.getElementById(baseClass + i);
            const rankIcon = rankItem.querySelector('.my-flights-rank-icon');
            let displayName, bg;

            if (category === 'airlines') {
                displayName = myFlights.airlines[myFlights.rankings.airlines[i].icao].name;
                bg = 'url("https://www.flightaware.com/images/airline_logos/180px/' + myFlights.rankings.airlines[i].icao + '.png")';
            } else if (category === 'types') {
                displayName = myFlights.rankings.types[i].icao;
                rankIcon.innerHTML = '<svg><use href="#' + myFlights.types[myFlights.rankings.types[i].icao].icon +'"></use></svg>';
            } else if (category === 'airports') {
                displayName = myFlights.airports[myFlights.rankings.airports[i].icao].iata;
                bg = 'url("/image/flag/' + myFlights.airports[myFlights.rankings.airports[i].icao].country + '")';
            };

            rankIcon.style.backgroundImage = bg;
            rankItem.querySelector('.my-flights-rank-name').textContent = displayName;
            rankItem.querySelector('.my-flights-rank-amount').textContent = myFlights.rankings[category][i].flights + ' flight' + `${myFlights.rankings[category][i].flights > 1 ? 's' : ''}`;
        };
    });
});
