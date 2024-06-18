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
    const digitWords = ['ZERO', 'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN', 'EIGHT', 'NINER'];

    const socket = io();
    socket.on('disconnect', function() {
        location.reload();
    });

    // MARK: - Container

    const container = document.getElementById("main-container");
    const minContainerHeight = 80;

    container.addEventListener("wheel", resizeContainer);
    container.addEventListener("touchstart", touchStartResizeContainer);
    container.addEventListener("touchmove", touchResizeContainer);
    container.addEventListener("touchend", touchEndResizeContainer);

    function setMaxContainerHeight() {
        const elements = container.children;
        maxContainerHeight = 60
        for (let i = 0; i < elements.length; i++) {
            if (window.getComputedStyle(elements[i]).display !== 'none') {
                maxContainerHeight += elements[i].offsetHeight;
            }
        }

        if (maxContainerHeight < window.innerHeight) {
            if (window.innerWidth > 500) {
                maxContainerHeight = window.innerHeight - 10;
            } else {
                maxContainerHeight = window.innerHeight;
            }
        }

        if (window.getComputedStyle(container).height > maxContainerHeight) {
            container.style.height = maxContainerHeight + "px";
            setContainerRadius()
        }
    }

    window.addEventListener('resize', setMaxContainerHeight);
    setMaxContainerHeight();

    function setContainerRadius() {
        if (container.clientHeight >= window.innerHeight) {
            container.style.borderRadius = '0';
        } else {
            container.style.borderRadius = null;
        }
    }

    function resizeContainer(e) {
        container.style.transition = null;
        const newHeight = container.clientHeight + e.deltaY;
        if (newHeight >= minContainerHeight && newHeight <= maxContainerHeight) {
            container.style.height = newHeight + "px";
        } else if (newHeight < minContainerHeight) {
            container.style.height = minContainerHeight + "px";
        } else if (newHeight > maxContainerHeight) {
            container.style.height = maxContainerHeight + "px";
        }
        e.preventDefault();
        setContainerRadius();
    }

    function touchStartResizeContainer(e) {
        container.style.transition = null;
        startY = e.touches[0].clientY;
        startHeight = container.clientHeight;
        containerMomentum = 0;
    }
    function touchResizeContainer(e) {
        if (!startY) {
            return;
        }
        const changeInY = startY - e.touches[0].clientY;
        containerMomentum = changeInY * 0.2; // 0.2 is scroll multiplier
        const newHeight = startHeight + changeInY;
        if (newHeight >= minContainerHeight && newHeight <= maxContainerHeight) {
            container.style.height = newHeight + "px";
        } else if (newHeight < minContainerHeight) {
            container.style.height = minContainerHeight + "px";
        } else if (newHeight > maxContainerHeight) {
            container.style.height = maxContainerHeight + "px";
        }
        e.preventDefault();
        setContainerRadius();
    }
    function touchEndResizeContainer() {
        startY = startHeight = null;
        if (containerMomentum !== 0) {
            const interval = setInterval(function() {
                const newHeight = container.clientHeight + containerMomentum;
                if (newHeight >= minContainerHeight && newHeight <= maxContainerHeight) {
                    container.style.height = newHeight + "px";
                    containerMomentum *= 0.9; // 0.9 is decay rate
                } else {
                    clearInterval(interval);
                }
            }, 32);
        }
        setContainerRadius()
    }

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

        document.getElementById('main-container-main-view').style.display = null;
        document.getElementById('main-container-aircraft-view').style.display = "none";
        document.getElementById('main-container-aircraft-view').innerHTML = null;
        selection = info = polylines = null;
        setMaxContainerHeight();
    }

    function setAircraft(anAircraft) {
        const marker = anAircraft.marker;

        if (anAircraft.icon !== 'helicopter') {
            const iconHeading = anAircraft.hdg - 90;
            const markerElement = marker.getElement();
            const markerElementInner = markerElement.querySelector('div');
            markerElementInner.style.transition = 'transform 0.5s ease';
            markerElementInner.style.transform = 'rotate(' + iconHeading + 'deg)';
        }

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

        container.style.transition = 'height 0.3s ease';
        if (window.innerWidth > 500) {
            container.style.height = (window.innerHeight - 10) + "px";
            xOffset = -160;
        } else {
            container.style.height = "335px";
            yOffset = 160;
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
        switch (themeName) {
                case 'standard':
                    tileLayerURL = 'https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png';
                    document.querySelector('.leaflet-tile-pane').style.filter = null;
                    break;
                case 'osm':
                    tileLayerURL = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
                    document.querySelector('.leaflet-tile-pane').style.filter = null;
                    break;
                case 'watercolour':
                    tileLayerURL = 'https://watercolormaps.collection.cooperhewitt.org/tile/watercolor/{z}/{x}/{y}.jpg';
                    document.querySelector('.leaflet-tile-pane').style.filter = 'none';
                    break;
                case 'satellite':
                    tileLayerURL = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}';
                    document.querySelector('.leaflet-tile-pane').style.filter = 'none';
                    break;
                case 'atc':
                    tileLayerURL = 'https://data2.geo-fs.com/osm/{z}/{x}/{y}.png'
                    document.querySelector('.leaflet-tile-pane').style.filter = null;
                    break;
                default:
                    return;
        }
        tileLayer.setUrl(tileLayerURL);
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
    document.querySelector('.leaflet-tile-pane').style.filter = 'none';

    map.on('click', function() {
        if (window.innerWidth <= 500) {
            container.style.transition = 'height 0.3s ease';
            container.style.height = minContainerHeight + "px";
            container.style.borderRadius = null;
        }
        clearMap()
    });

    // Define icons
    const icons = {};

    icons.plane = L.divIcon({
    className: 'aircraft-icon',
    html: '<div>&#x2708;</div>',
    iconSize: [32, 32]
    });

    icons.helicopter = L.divIcon({
    className: 'aircraft-icon',
    html: '<div class="helicopter-icon">&#xFF0B;</div>',
    iconSize: [32, 32]
    });

    icons.other = L.divIcon({
    className: 'aircraft-icon',
    html: '<div>&#x27A4;</div>',
    iconSize: [32, 32]
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
                individual.marker = L.marker([individual.lat, individual.lng], { icon: icons[individual.icon] }).addTo(map);
                individual.marker.getElement().classList.add(`_${individual.icao24}`);
                individual.marker.getElement().setAttribute('tabindex', '-1');
            }

            setAircraft(individual);

            const listItem = document.createElement('div');
            listItem.setAttribute('class', `_${individual.icao24}`);
            listItem.innerHTML = `
                <div height="95px">

                    <div style="position: absolute; margin-left: 5px; background-image: url(https://www.flightaware.com/images/airline_logos/180px/${individual.callsign.slice(0,3)}.png); background-size: contain; background-position: center; background-repeat: no-repeat; height: 75px; width: 75px;"></div>

                    <div style="margin-left: 100px">
                        <h3>${individual.callsign}</h3>
                        <p>${individual.speed} KTS, ${individual.alt} FT, ${individual.hdg}º</p>
                    </div>
                </div>
            `;

            aircraftList.appendChild(listItem);

            document.querySelectorAll(`._${individual.icao24}`).forEach(element => {
                element.addEventListener('click', function() {
                    socket.emit("lookup.all", individual.icao24, individual.callsign);
                });
            });
        }

        const countElement = document.createElement('footer');
        countElement.innerHTML = `${aircraftCount} aircraft`;
        aircraftList.appendChild(countElement);

        setMaxContainerHeight();
    });

    socket.on('lookup.all', function(response) {
        info = response;

        const url = new URL(window.location.href);
        const params = new URLSearchParams(url.search);
        params.delete('callsign');
        params.delete('icao24');
        params.set('callsign', info.callsign);
        params.set('icao24', info.aircraft.icao24);
        url.search = params.toString();
        history.pushState({}, '', url.toString());

        if (info.origin === null) {
            info.origin = {};
            info.origin.iata = '';
            info.origin.muni = 'Origin';
        }

        if (info.destination === null) {
            info.destination = {};
            info.destination.iata = '';
            info.destination.muni = 'Destination';
        }

        try {
            info.radioCallsign = info.airline.radio + ' ';
            const flightNumber = info.callsign.slice(3).trim();
            for (let i = 0; i < flightNumber.length; i++) {
                const digit = parseInt(flightNumber[i]);  // only works with numerical callsigns
                info.radioCallsign += digitWords[digit] + ' ';
            }
            info.radioCallsign = info.radioCallsign.trim();
        } catch {}

        if (typeof info.aircraft.reg == 'undefined') { info.aircraft.reg = 'Unknown Reg' }
        if (typeof info.aircraft.type == 'undefined') { info.aircraft.type = 'Unknown Type' }
        if (typeof info.airline.name == 'undefined') { info.airline.name = 'Unknown Airline' }

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
        aircraftView.style.display = null;

        // really messy - find alternative
        aircraftView.innerHTML = `
            <div id="back">&larr;</div>
            <div id="info">i</div>
            <div class="aircraft-img-shadow"><img class="aircraft-img" src="/image/${info.aircraft.reg}"></div>
            <div class="aircraft-info">

                <div style="position: relative; top: 0; padding-bottom: 25px; padding-top: 15px">
                    <div style="position: absolute; margin-left: 5px; background-image: url(https://www.flightaware.com/images/airline_logos/180px/${info.callsign.slice(0,3)}.png); background-size: contain; background-position: center; background-repeat: no-repeat; height: 2ch; aspect-ratio: 1;"></div>
                    <span style="position: absolute; margin-left: 3ch">${info.airline.name}</span>
                    <span style="position: absolute; right: 0; cursor: help" title="${info.radioCallsign}"> ${info.callsign}</span>
                </div>
                <hr>
                <div style="position: relative; color: grey; padding: 10px 0">
                    <span id="origin-${info.callsign}" style="position: absolute; left: 0">${info.origin.muni}</span>

                    <span id="destination-${info.callsign}" style="position: absolute; right: 0">${info.destination.muni}</span>
                </div>

                <div style="position: relative; margin: 0; padding-bottom: 50px;">
                    <input id="origin-input" class="iata-input" style="position: absolute; left: 0" placeholder="${info.origin.iata}" contenteditable="true" required maxlength="3" minlength="3">

                    <input id="destination-input" class="iata-input" style="text-align: right; position: absolute; right: 0" placeholder="${info.destination.iata}" contenteditable="true" required maxlength="3" minlength="3">

                    <h1 style="position: absolute; left: 50%; transform: translateX(-50%)">&#x2708;</h1>
                </div>
                <progress id="flight-progress" value="0"></progress>

                <div style="position: relative; padding: 10px 0">
                    <span style="position: absolute; left: 0"><span class="fi fis fi-${info.aircraft.country.toLowerCase()}"></span> ${info.aircraft.reg}</span>

                    <span style="position: absolute; right: 0">${info.aircraft.type}</span>
                </div>


                <div style="position: relative; padding: 30px 0">
                    <div style="position: absolute; left: 0; width: calc(50% - 7.5px); aspect-ratio: 2; border-radius: 10px">
                        <div style="position: absolute; left: 0; width: calc(50% - 7.5px); aspect-ratio: 1;">
                            <svg width="100%" height="100%" viewBox="0 7.5 100 100" class="metre">
                                <path d="M 20,90 A 40,40 0 1,1 80,90" fill="none" stroke="var(--hover-colour)" stroke-width="10"/>

                                <text x="50%" y="70%" text-anchor="middle" class="metre-value">${selection.speed}</text>
                                <text x="50%" y="90%" text-anchor="middle" class="metre-unit">KTS</text>

                                <path d="M 20,90 A 40,40 0 1,1 80,90" fill="none" stroke="dodgerblue" stroke-width="10" stroke-dasharray="188.4,251.2" stroke-dashoffset="188.4" class="metre-progress" id="speed-indicator"/>
                            </svg>
                        </div>
                        <div style="position: absolute; right: 0; width: calc(50% - 7.5px); background-color: var(--hover-colour); aspect-ratio: 1; border-radius: 10px"></div>
                    </div>

                    <div style="position: absolute; right: 0; width: calc(50% - 7.5px); aspect-ratio: 2; border-radius: 10px">
                        <div style="position: absolute; left: 0; width: calc(50% - 7.5px); background-color: var(--hover-colour); aspect-ratio: 1; border-radius: 10px"></div>
                        <div style="position: absolute; right: 0; width: calc(50% - 7.5px); background-color: var(--hover-colour); aspect-ratio: 1; border-radius: 10px"></div>
                    </div>
                </div>

            </div>`;

        plotRoutes();
        centreOnSelection();

        const speedBounded = Math.max(0, Math.min((selection.speed/600), 1));
        const dashoffset = 188.4 - (speedBounded * 188.4);
        document.getElementById('speed-indicator').style.strokeDashoffset = dashoffset;

        document.getElementById("origin-input").addEventListener("input", function() {
            if (this.value.length >= parseInt(this.getAttribute("maxlength"))) {
                socket.emit("lookup.airport", this.value, `origin-${info.callsign}`);
                document.getElementById('destination-input').focus()
            } else {
                document.getElementById(`origin-${info.callsign}`).innerHTML = 'Origin';
            }
        });

        document.getElementById("destination-input").addEventListener("input", function() {
            if (this.value.length >= parseInt(this.getAttribute("maxlength"))) {
                socket.emit("lookup.airport", this.value, `destination-${info.callsign}`);
                document.getElementById('destination-input').blur()
            } else {
                document.getElementById(`destination-${info.callsign}`).innerHTML = 'Destination';
            }
        });

        container.style.borderRadius = null;
        setMaxContainerHeight()
        document.getElementById('back').addEventListener('click', clearMap);
    });

    socket.on('lookup.airport', function(airport) {
        if (airport.routing !== null) {
            if (typeof airport.muni !== 'undefined') {
                document.getElementById(airport.routing).innerHTML = airport.muni;
            }

            if (airport.routing.startsWith('origin-')) {
                if (selection.icao24 === polylines.icao24) {
                    info.origin = airport;
                }
                socket.emit("lookup.add_origin", selection.callsign, airport.icao);
            } else if (airport.routing.startsWith('destination-')) {
                if (selection.icao24 === polylines.icao24) {
                    info.destination = airport;
                }
                socket.emit("lookup.add_destination", selection.callsign, airport.icao);
            }
        }
    });
});