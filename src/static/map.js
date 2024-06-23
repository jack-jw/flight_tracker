// static/map.js

//document.addEventListener("visibilitychange", function() {
//    if (!document.hidden) {
//        location.reload()
//        // to prevent glitching of animations, not the best implementation
//    }
//});

document.addEventListener("DOMContentLoaded", function() {
    let startContainerY, startContainerHeight, containerMomentum, maxContainerHeight;
    let selection = info = polylines = null;

    const socket = io();
    socket.emit('decoder.get')
    socket.on('disconnect', function() {
        location.reload();
    });

    // MARK: - Container

    const container = document.getElementById("main-container");

    function setContainerDefaultScroll(scrollBehaviour) {
        let scrollPosition;
        if (window.innerWidth > 500) {
            scrollPosition = document.body.scrollHeight;
        } else {
            scrollPosition = containerPosition - (window.innerHeight - 370);
        }

        window.scrollTo({
            top: scrollPosition,
            left: 0,
            behavior: scrollBehaviour
        });
    }
    setContainerDefaultScroll('instant')

    // MARK: - Map

    function clearMap() {
        map.eachLayer(function(layer) {
            if (layer instanceof L.Polyline) { map.removeLayer(layer) }
        });

        Object.keys(aircraft).forEach(function(key) {
            try {
                const marker = aircraft[key].marker;
                marker.getElement().style.opacity = null;
            } catch {}
        });

        const url = new URL(window.location.href);
        const params = new URLSearchParams(url.search);
        params.delete('callsign');
        params.delete('icao24');
        url.search = params.toString();
        history.pushState({}, '', url.toString());

        document.getElementById('origin-input').outerHTML = document.getElementById('origin-input').outerHTML;
        document.getElementById('destination-input').outerHTML = document.getElementById('destination-input').outerHTML;
        document.getElementById('aircraft-img').src = "/image/aircraft/placeholder"

        selection = info = polylines = null;
        document.getElementById('main-container-main-view').style.display = null;
        document.getElementById('main-container-aircraft-view').style.display = "none";
    }

    function setAircraft(anAircraft) {
        const marker = anAircraft.marker;

        const markerElement = marker.getElement();
        const markerElementInner = markerElement.querySelector('img');
        markerElementInner.style.transition = 'transform 0.5s ease';
        markerElementInner.style.transform = 'rotate(' + anAircraft.hdg + 'deg)';

        const speed = anAircraft.speed / (1.944 * 5);

        if (marker.moveInterval) {
            clearInterval(marker.moveInterval);
        }

        const radianAngle = anAircraft.hdg * (Math.PI / 180);

        function fly() {
            const changeInLat = Math.cos(radianAngle) * (speed / 111111);
            const changeInLng = Math.sin(radianAngle) * (speed / (111111 * Math.cos(marker.getLatLng().lat * (Math.PI / 180))));
            const currentLatLng = marker.getLatLng();
            const newLatLng = {
            lat: currentLatLng.lat + changeInLat,
            lng: currentLatLng.lng + changeInLng
            }
            marker.setLatLng(newLatLng);
            if (selection !== null && polylines !== null) {
                if (selection.icao24 === polylines.icao24) {
                    plotRoutes()
                }
            }
        }

        marker.moveInterval = setInterval(fly, 100);
    }

    function centreOnSelection() {
        const latlng = selection.marker.getLatLng();
        const point = map.latLngToContainerPoint(latlng);
        let xOffset = yOffset = 0;

        if (window.innerWidth > 500) {
            xOffset = -160;
        } else {
            yOffset = 180;
        }
        point.x += xOffset;
        point.y += yOffset;
        map.panTo(map.containerPointToLatLng(point));
    }

    function plotRoutes() {
        function plotGreatCircleRoute(startPoint, endPoint, opacity) {
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

            const line = L.polyline(curvePoints, { color: '#FF9500', weight: 2, opacity: opacity }).addTo(map);
            line.getElement().setAttribute('tabindex', '-1');
            const distance = startLatLng.distanceTo(endLatLng); // need to implement great circle distance calc

            return {'line': line, 'distance': distance};
        }

        try { map.removeLayer(polylines.origin.line); } catch {};
        try { map.removeLayer(polylines.destination.line); } catch {};

        let fromOrigin, toDestination;
        let percentage = 0;

        if (typeof info.origin.lat !== 'undefined' && typeof info.origin.lng !== 'undefined') {
            fromOrigin = plotGreatCircleRoute([info.origin.lat, info.origin.lng], selection.marker.getLatLng(), 1);
        }

        if (typeof info.destination.lat !== 'undefined' && typeof info.destination.lng !== 'undefined') {
            toDestination = plotGreatCircleRoute(selection.marker.getLatLng(), [info.destination.lat, info.destination.lng], 0.5);
        }

        if (typeof fromOrigin !== 'undefined' && typeof toDestination !== 'undefined') {
            percentage = fromOrigin.distance / (fromOrigin.distance + toDestination.distance);
            document.getElementById('flight-progress').value = percentage;
        }

        polylines = {'origin': fromOrigin, 'destination': toDestination, 'percentage': percentage, 'icao24': selection.icao24};
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
        document.getElementById('aircraft-list-map-credit').innerHTML = credit;
    }

    // MARK: Map definition
    const map = L.map('map', {
        center: [51.505, -0.09],
        zoom: 7,
        maxZoom: 15,
        zoomControl: false,
        attributionControl: false
    });

    const tileLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}').addTo(map);
    setTheme("satellite")

    map.on('click', function() {
        if (window.innerWidth <= 500) {
            window.scrollTo({
                top: 0,
                left: 0,
                behavior: 'smooth'
            });
        }
        clearMap()
    });

    document.getElementById('aircraft-list-clear').addEventListener('click', function() {
        document.getElementById('aircraft-list-filter').value = '';
        document.getElementById('aircraft-list-filter').dispatchEvent(new Event('input', { bubbles: true }));
    });

    document.getElementById('aircraft-list-filter').addEventListener('input', function() {
        const filterValue = this.value.toUpperCase();
        if (filterValue !== '') {
            document.getElementById('aircraft-list-filter').style.width = 'calc(100% - 45px)'
            document.getElementById('pfp').classList.add('hidden');
            document.getElementById('aircraft-list-clear').classList.remove('hidden');
        } else {
            document.getElementById('aircraft-list-filter').style.width = null;
            document.getElementById('aircraft-list-clear').classList.add('hidden');
            document.getElementById('pfp').classList.remove('hidden');
        }

        const aircraftList = document.getElementById('aircraft-list').children;
        Array.from(aircraftList).forEach(item => {
            if (item.tagName === 'DIV') {
                const callsign = item.querySelector('.aircraft-list-callsign').textContent;
                if (callsign.includes(filterValue)) {
                    item.style.display = null;
                } else {
                    item.style.display = 'none';
                }
            } else if (filterValue === '') {
                item.style.display = null;
            } else {
                item.style.display = 'none';
            }
        });
    });

    // MARK: - Aircraft
    let aircraft = {};
    let aircraftCount = 0;
    const aircraftList = document.getElementById('aircraft-list');

    // Check if an aircraft is selected in the URL
    const urlIcao24 = new URLSearchParams(window.location.search).get('icao24');
    const urlCallsign = new URLSearchParams(window.location.search).get('callsign');
    if (urlCallsign !== null && urlIcao24 !== null) {
        socket.emit("lookup.all", urlIcao24, urlCallsign);
    }

    socket.on('decoder.get', function(payload) {
        oldAircraft = { ...aircraft };
        aircraft = {
            ...aircraft,
            ...payload
        };
        for (const key in aircraft) {
            const individual = aircraft[key];
            aircraftCount++

            if (typeof oldAircraft[key] === 'undefined') {

                individual.marker = L.marker([individual.lat, individual.lng], {
                    icon: L.divIcon({
                        className: 'aircraft-icon',
                        html: `<img src="/image/icon/${individual.icon.icon}.svg"/>`,
                        iconSize: [individual.icon.size, individual.icon.size]
                    })
                }).addTo(map);

                individual.marker.getElement().classList.add(`_${individual.icao24}`);
                individual.marker.getElement().setAttribute('tabindex', '-1');
            }

            setAircraft(individual);

            const listItem = document.createElement('div');
            listItem.classList.add(`_${individual.icao24}`);
            listItem.innerHTML = `
                <div class="aircraft-list-airline-logo" style="background-image: url(https://www.flightaware.com/images/airline_logos/180px/${individual.callsign.slice(0,3)}.png)">
                </div>

                <div>
                    <div class="aircraft-list-callsign">${individual.callsign}</div>
                    <div class="aircraft-list-metrics">${individual.speed} KTS, ${individual.alt} FT, ${Math.round(individual.hdg)}º</div>
                </div>
            `;

            aircraftList.appendChild(listItem);

            document.querySelectorAll(`._${individual.icao24}`).forEach(element => {
                element.addEventListener('click', function(event) {
                    socket.emit("lookup.all", individual.icao24, individual.callsign);
                    event.stopPropagation();
                }, true);
            });
        }

        const countElement = document.createElement('footer');
        countElement.setAttribute('id', 'aircraft-list-count')
        countElement.innerHTML = `${aircraftCount} aircraft`;
        aircraftList.appendChild(countElement);
    });

    socket.on('lookup.all', function(response) {
        document.getElementById('aircraft-img').style.display = 'none'
        info = response;

        const url = new URL(window.location.href);
        const params = new URLSearchParams(url.search);
        params.delete('callsign');
        params.delete('icao24');
        params.set('callsign', info.callsign);
        params.set('icao24', info.aircraft.icao24);
        url.search = params.toString();
        history.pushState({}, '', url.toString());

        if (!info.origin) {
            info.origin = {};
            info.origin.iata = '';
            info.origin.muni = 'Origin';
        }

        if (!info.destination) {
            info.destination = {};
            info.destination.iata = '';
            info.destination.muni = 'Destination';
        }

        selection = aircraft[info.aircraft.icao24];

        Object.keys(aircraft).forEach(function(key) {
            try {
                const marker = aircraft[key].marker;
                marker.getElement().style.opacity = '50%';
            } catch {}
        });
        selection.marker.getElement().style.opacity = '100%';

        document.getElementById('main-container-main-view').style.display = 'none';
        aircraftView = document.getElementById('main-container-aircraft-view');

        document.getElementById('aircraft-img').src = '/image/aircraft/' + info.aircraft.reg;
        document.getElementById('aircraft-airline-logo').style.backgroundImage = 'url(https://www.flightaware.com/images/airline_logos/180px/' + info.callsign.slice(0,3) + '.png)';
        document.getElementById('aircraft-airline-name').textContent = info.airline.name;
        document.getElementById('aircraft-callsign').textContent = info.callsign;
        document.getElementById('aircraft-callsign').title = info.radio;
        document.getElementById('aircraft-route-origin').textContent = info.origin.muni;
        document.getElementById('aircraft-route-destination').textContent = info.destination.muni;

        document.getElementById('origin-input').placeholder = info.origin.iata;
        document.getElementById('origin-input').value = null;
        document.getElementById('destination-input').placeholder = info.destination.iata;
        document.getElementById('destination-input').value = null;

        document.getElementById('flight-progress').value = null;

        document.getElementById('aircraft-reg').textContent = info.aircraft.reg;
        document.getElementById('aircraft-reg-flag').className = 'fi fis fi-' + info.aircraft.country.toLowerCase();
        document.getElementById('aircraft-type').textContent = info.aircraft.type;

        document.getElementById('aircraft-speed').textContent = selection.speed;
        const speedBounded = Math.max(0, Math.min((selection.speed/600), 1));
        const dashoffset = 188.4 - (speedBounded * 188.4);
        document.getElementById('aircraft-speed-indicator').style.strokeDashoffset = dashoffset;

        document.getElementById("origin-input").addEventListener("input", function() {
            if (this.value.length == 3) {
                socket.emit("lookup.airport", this.value, 'origin');
                document.getElementById('destination-input').focus();
            } else {
                document.getElementById('aircraft-route-origin').innerHTML = 'Origin';
            }
        });

        document.getElementById("destination-input").addEventListener("input", function() {
            if (this.value.length == 3) {
                socket.emit("lookup.airport", this.value, 'destination');
                document.getElementById('destination-input').blur()
            } else {
                document.getElementById('aircraft-route-destination').innerHTML = 'Destination';
            }
        });

        plotRoutes();
        centreOnSelection();

        setContainerDefaultScroll('smooth');
        document.getElementById('back').addEventListener('click', clearMap);
        document.getElementById('aircraft-img').style.display = null;
        aircraftView.style.display = null;
    });

    socket.on('lookup.airport', function(airport) {
        if (airport.routing !== null) {
            if (airport.routing == 'origin') {
                if (selection.icao24 === polylines.icao24) {
                    info.origin = airport;
                }
                document.getElementById('aircraft-route-origin').textContent = airport.muni
                socket.emit("lookup.add_origin", selection.callsign, airport.icao);
            } else if (airport.routing == 'destination') {
                if (selection.icao24 === polylines.icao24) {
                    info.destination = airport;
                }
                document.getElementById('aircraft-route-destination').textContent = airport.muni
                socket.emit("lookup.add_destination", selection.callsign, airport.icao);
            }
        }
    });
});
