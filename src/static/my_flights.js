// static/my_flights.js

document.addEventListener('DOMContentLoaded', function() {
    let flightAmount = 0;
    let polylines;

    const socket = io();
    socket.emit('my_flights.get')
    socket.on('disconnect', function() {
        location.reload();
    });

    // MARK: - Map

    function plotGreatCircleRoute(startPoint, endPoint) {
        function computeIntermediatePoint(start, end, ratio) {
            const lat1 = start.lat * Math.PI / 180;
            const lon1 = start.lng * Math.PI / 180;
            const lat2 = end.lat * Math.PI / 180;
            const lon2 = end.lng * Math.PI / 180;
            const d = 2 * Math.asin(Math.sqrt(Math.pow(Math.sin((lat1 - lat2) / 2), 2) + Math.cos(lat1) * Math.cos(lat2) * Math.pow(Math.sin((lon1 - lon2) / 2), 2)));
            const A = Math.sin((1 - ratio) * d) / Math.sin(d);
            const B = Math.sin(ratio * d) / Math.sin(d);
            const x = A * Math.cos(lat1) * Math.cos(lon1) + B * Math.cos(lat2) * Math.cos(lon2);
            const y = A * Math.cos(lat1) * Math.sin(lon1) + B * Math.cos(lat2) * Math.sin(lon2);
            const z = A * Math.sin(lat1) + B * Math.sin(lat2);
            const lat = Math.atan2(z, Math.sqrt(Math.pow(x, 2) + Math.pow(y, 2))) * 180 / Math.PI;
            const lon = Math.atan2(y, x) * 180 / Math.PI;
            return [lat, lon];
        }

        const startLatLng = L.latLng(startPoint);
        const endLatLng = L.latLng(endPoint);

        const curvePoints = [];
        for (let i = 0; i <= 100; i++) {
            const ratio = i / 100;
            const intermediatePoint = computeIntermediatePoint(startLatLng, endLatLng, ratio);
            curvePoints.push(intermediatePoint);
        }

        const line = L.polyline(curvePoints, { color: '#FF9500', weight: 2 }).addTo(map);
        line.getElement().setAttribute('tabindex', '-1');
        return line
    }

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
                    credit = 'Map data © OpenStreetMap contributors'
                    document.querySelector('.leaflet-tile-pane').style.filter = null;
                    break;
                case 'watercolour':
                    tileLayerURL = 'https://watercolormaps.collection.cooperhewitt.org/tile/watercolor/{z}/{x}/{y}.jpg';
                    credit = 'Map data © OpenStreetMap contributors<br>Tiles © Stamen Design';
                    document.querySelector('.leaflet-tile-pane').style.filter = 'none';
                    break;
                case 'satellite':
                    tileLayerURL = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}';
                    credit = 'Map data © Esri, World Imagery'
                    document.querySelector('.leaflet-tile-pane').style.filter = 'none';
                    break;
                case 'atc':
                    tileLayerURL = 'https://data2.geo-fs.com/osm/{z}/{x}/{y}.png'
                    credit = 'Map data © OpenStreetMap contributors<br>Tiles © GeoFS'
                    document.querySelector('.leaflet-tile-pane').style.filter = null;
                    break;
                default:
                    return;
        }
        tileLayer.setUrl(tileLayerURL);
//        document.getElementById('aircraft-list-map-credit').innerHTML = credit;
    }

    // MARK: Map definition
    const map = L.map('map', {
        center: [51.505, -0.09],
        zoom: 3,
        maxZoom: 15,
        zoomControl: false,
        attributionControl: false
    });

    const tileLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}').addTo(map);
    setTheme('satellite')

    // MARK: - Flights

    function animateNumber(element, start, end, duration) {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            element.textContent = Math.floor(progress * (end - start) + start);
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    }

    socket.on('my_flights.get', function(payload) {

        payload.flights.forEach(function(flight) {
            plotGreatCircleRoute(payload.airports[flight.origin], payload.airports[flight.destination]);
        });

        Object.values(payload.airports).forEach(function(airport) {
            const tooltipContent = `
                <div class="my-flights-airport-tooltip-title">
                    <span class="fi fis fi-${airport.country.toLowerCase()}"></span>
                    <span class="my-flights-airport-tooltip-iata">${airport.iata}</span> ${airport.name}
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

        animateNumber(document.getElementById('my-flights-count'), 0, payload.flights.length, 1000);

        Object.keys(payload.rankings).forEach(function(category) {
            const baseClass = `my-flights-${category}-`;
            for (let i = 0; i < payload.rankings[category].length; i++) {
                const rankItem = document.getElementById(baseClass + i);
                const rankIcon = rankItem.querySelector('.my-flights-rank-icon');
                let displayName, imageUrl;

                if (category === 'airlines') {
                    displayName = payload.airlines[payload.rankings.airlines[i].icao].name;
                    imageUrl = 'https://www.flightaware.com/images/airline_logos/180px/' + payload.rankings.airlines[i].icao + '.png';
                } else if (category === 'aircraft') {
                    displayName = payload.rankings.aircraft[i].icao;
//                    imageUrl =
                } else if (category === 'airports') {
                    displayName = payload.airports[payload.rankings.airports[i].icao].iata;
                    imageUrl = 'https://cdn.jsdelivr.net/gh/lipis/flag-icons@7.0.0/flags/1x1/' + payload.airports[payload.rankings.airports[i].icao].country.toLowerCase() + '.svg';
                }


                rankItem.querySelector('.my-flights-rank-name').textContent = displayName;
                rankItem.querySelector('.my-flights-rank-icon').style.backgroundImage = 'url(' + imageUrl + ')';
            }
        });

    });

});
