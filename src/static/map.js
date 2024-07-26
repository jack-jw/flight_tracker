// static/map.js

//document.addEventListener('visibilitychange', function() {
//    if (!document.hidden) {
//        location.reload()
//        // to prevent glitching of animations, not the best implementation
//    };
//});

document.addEventListener('DOMContentLoaded', function() {
    let selection = null;

    const socketio = io();
    socketio.on('disconnect', function() {
        location.reload();
    });

    // MARK: - Container

    const container = document.getElementById('main-container');

    function setContainerDefaultScroll(scrollBehaviour) {
        if (window.innerWidth <= 500) {
            const containerTop = container.getBoundingClientRect().top + window.pageYOffset;
            const scrollPosition = containerTop - (window.innerHeight - 335);
            window.scrollTo({
                top: scrollPosition,
                left: 0,
                behavior: scrollBehaviour
            });
        };
    };
    setContainerDefaultScroll('instant');

    // MARK: - Map

    function clearMap() {
        try { map.removeLayer(selection.polylines.orig.line); } catch {};
        try { map.removeLayer(selection.polylines.dest.line); } catch {};

        Object.values(aircraft).forEach(function(each) {
            each.marker.getElement().style.opacity = '';
        });

        const url = new URL(window.location.href);
        const params = new URLSearchParams(url.search);
        params.delete('callsign');
        params.delete('icao');
        url.search = params.toString();
        history.pushState({}, '', url.toString());

        document.getElementById('origin-input').outerHTML = document.getElementById('origin-input').outerHTML;
        document.getElementById('destination-input').outerHTML = document.getElementById('destination-input').outerHTML;
        document.getElementById('aircraft-img').src = '';

        document.getElementById('main-container-main-view').style.display = '';
        document.getElementById('main-container-aircraft-view').style.display = 'none';

        selection = null;
    };

    function set(i) {
        const marker = i.marker;

        const markerElement = marker.getElement();
        const markerElementInner = markerElement.firstElementChild;
        markerElementInner.style.transition = 'transform 0.5s ease';
        markerElementInner.style.transform = 'rotate(' + i.hdg + 'deg)';

        const speed = i.speed / (1.944 * 5);

        if (marker.moveInterval) {
            clearInterval(marker.moveInterval);
        };

        const radianAngle = i.hdg * (Math.PI / 180);

        function fly() {
            const changeInLat = Math.cos(radianAngle) * (speed / 111111);
            const changeInLng = Math.sin(radianAngle) * (speed / (111111 * Math.cos(marker.getLatLng().lat * (Math.PI / 180))));
            const currentLatLng = marker.getLatLng();
            const newLatLng = {
                lat: currentLatLng.lat + changeInLat,
                lng: currentLatLng.lng + changeInLng
            };
            marker.setLatLng(newLatLng);
            if (selection !== null) {
                plotRoutes();
            };
        };

        marker.moveInterval = setInterval(fly, 100);
    };

    function plotRoutes() {
        function plotGreatCircleRoute(startPoint, endPoint, opacity) {
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
                const R = 6371e3;
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

            const line = L.polyline(curvePoints, { color: '#FF9500', weight: 2, opacity: opacity }).addTo(map);
            line.getElement().setAttribute('tabindex', '-1');
            const distance = computeGreatCircleDistance(startLatLng, endLatLng);
            return {'line': line, 'dist': distance};
        };

        try { map.removeLayer(selection.polylines.orig.line); } catch {};
        try { map.removeLayer(selection.polylines.dest.line); } catch {};

        selection.polylines = {};
        let percentage = 0;

        if (typeof selection.orig.lat !== 'undefined' && typeof selection.orig.lng !== 'undefined') {
            selection.polylines.orig = plotGreatCircleRoute(selection.orig, selection.marker.getLatLng(), 1);
        };

        if (typeof selection.dest.lat !== 'undefined' && typeof selection.dest.lng !== 'undefined') {
            selection.polylines.dest = plotGreatCircleRoute(selection.dest, selection.marker.getLatLng(), 0.5);
        };

        if (selection.polylines.orig && selection.polylines.dest) {
            percentage = selection.polylines.orig.dist / (selection.polylines.orig.dist + selection.polylines.dest.dist);
            document.getElementById('flight-progress').value = percentage;
        };
    };

    function setTheme(themeName) {
        let tileLayerURL;
        let credit;
        switch (themeName) {
            case 'standard':
                tileLayerURL = 'https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png';
                credit = 'Map data © OpenStreetMap contributors<br>Tiles © Humanitarian OpenStreetMap Team (HOT)';
                document.querySelector('.leaflet-tile-pane').style.filter = '';
                break;
            case 'osm':
                tileLayerURL = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
                credit = 'Map data © OpenStreetMap contributors'
                document.querySelector('.leaflet-tile-pane').style.filter = '';
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
                document.querySelector('.leaflet-tile-pane').style.filter = '';
                break;
            default:
                return;
        };
        tileLayer.setUrl(tileLayerURL);
        document.getElementById('aircraft-list-map-credit').innerHTML = credit;
    };

    // MARK: Map definition
    const map = L.map('map', {
        center: [51.505, -0.09],
        zoom: 7,
        maxZoom: 15,
        zoomControl: false,
        attributionControl: false
    });

    const tileLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        detectRetina: true // not good for some of the maps
    }).addTo(map);
    setTheme('satellite');

    map.on('click', function() {
        if (window.innerWidth <= 500) {
            window.scrollTo({
                top: 0,
                left: 0,
                behavior: 'smooth'
            });
        };
        clearMap();
    });

    // MARK: - Aircraft list filter
    const aircraftList = document.getElementById('aircraft-list');

    document.getElementById('aircraft-list-clear').addEventListener('click', function() {
        document.getElementById('aircraft-list-filter').value = '';
        document.getElementById('aircraft-list-filter').dispatchEvent(new Event('input', { bubbles: true }));
    });

    document.getElementById('aircraft-list-filter').addEventListener('input', function() {
        const visibleLatLngs = [];
        const filterValue = this.value.toUpperCase();
        if (filterValue !== '') {
            document.getElementById('aircraft-list-filter').style.width = 'calc(100% - 45px)'
            document.getElementById('pfp').classList.add('hidden');
            document.getElementById('aircraft-list-clear').classList.remove('hidden');
        } else {
            document.getElementById('aircraft-list-filter').style.width = '';
            document.getElementById('aircraft-list-clear').classList.add('hidden');
            document.getElementById('pfp').classList.remove('hidden');
        };

        Array.from(aircraftList.children).forEach(item => {
            if (item.tagName === 'DIV') {
                const icao = item.className.substring(1);
                if (item.textContent.includes(filterValue)) {
                    item.style.display = '';
                    visibleLatLngs.push(aircraft[icao].marker.getLatLng());
                    aircraft[icao].marker.getElement().style.display = '';
                } else {
                    item.style.display = 'none';
                    aircraft[icao].marker.getElement().style.display = 'none';
                };
            } else if (filterValue === '') {
                item.style.display = '';
            } else {
                item.style.display = 'none';
            };
        });
        map.fitBounds(L.latLngBounds(visibleLatLngs));
    });

    // MARK: - Aircraft
    let aircraft = {};

    socketio.on('aircraft', function(payload) {
        aircraft = {
            ...aircraft,
            ...payload
        };

        Object.values(aircraft).forEach(function(i) {
            i.marker = L.marker([i.lat, i.lng], {
                icon: L.divIcon({
                    className: 'aircraft-icon',
                    html: '<svg><use href="#' + i.icon.icon +'"></use></svg>',
                    iconSize: [i.icon.size, i.icon.size]
                })
            }).addTo(map);

            i.marker.setZIndexOffset(i.alt);
            i.marker.getElement().setAttribute('tabindex', '-1');

            set(i);

            let airlineLogo = '';
            if (!/\d/.test(i.csign.slice(0,3))) {
                airlineLogo = 'background-image: url(https://www.flightaware.com/images/airline_logos/180px/' + i.csign.slice(0,3) + '.png)'
            };

            i.listItem = document.createElement('div');
            i.listItem.innerHTML = `
                <div class="aircraft-list-airline-logo" style="${airlineLogo}">
                </div>

                <div>
                    <div class="aircraft-list-callsign">${i.csign}</div>
                    <div class="aircraft-list-metrics">
                        <b>${i.reg ?? ''}</b> ${i.type ?? ''}
                    </div>
                    <div class="aircraft-list-metrics">
                        <span style="width: 1em; height: 1em">
                            <span style="transform: rotate(${i.hdg}deg); position: absolute">&uarr;</span>
                        </span>
                        <span style="margin-left: 1em">
                            ${Math.round(i.speed)} KTS
                        </span>
                    </div>
                </div>
            `;

            aircraftList.appendChild(i.listItem);

            [i.listItem, i.marker.getElement()].forEach(element => {
                element.addEventListener('click', function(event) {
                    socketio.emit('select', i.icao, i.csign);
                    event.stopPropagation();
                }, true);
                element.classList.add('_' + i.icao);
            });

            i.marker.addEventListener('mouseover', function(event) {
                if (window.innerWidth >= 500 && !window.matchMedia('(pointer: coarse)').matches) {
                    i.listItem.scrollIntoView({ behaviour: 'smooth' });
                    i.listItem.setAttribute('id', 'aircraft-list-div-hover');
                };
            });

            i.marker.addEventListener('mouseout', function(event) {
                if (window.innerWidth >= 500 && !window.matchMedia('(pointer: coarse)').matches) {
                    i.listItem.setAttribute('id', '');
                };
            });
        });

        const countElement = document.createElement('footer');
        countElement.setAttribute('id', 'aircraft-list-count');
        countElement.innerHTML = Object.keys(aircraft).length + ' aircraft';
        aircraftList.appendChild(countElement);
    });

    // Check if an aircraft is selected in the URL
    const urlIcao = new URLSearchParams(window.location.search).get('icao');
    const urlCSign = new URLSearchParams(window.location.search).get('callsign');
    if (urlCSign && urlIcao && urlIcao in aircraft) {
        socketio.emit('select', urlIcao, urlCSign);
    };

    document.getElementById('aircraft-img').onload = function() {
        document.getElementById('aircraft-img').style.display = '';
    };
    document.getElementById('aircraft-img').onerror = function() {
        document.getElementById('aircraft-img').style.display = 'none';
    };

    document.getElementById('aircraft-airline-logo').onload = function() {
        document.getElementById('aircraft-airline-logo').style.display = '';
    };
    document.getElementById('aircraft-airline-logo').onerror = function() {
        document.getElementById('aircraft-airline-logo').style.display = 'none';
    };

    socketio.on('select', function(response) {
        document.getElementById('aircraft-img').src = ''
        try { map.removeLayer(selection.polylines.orig.line); } catch {};
        try { map.removeLayer(selection.polylines.dest.line); } catch {};

        selection = {
            ...aircraft[response.aircraft.icao],
            ...response
        };

        const url = new URL(window.location.href);
        const params = new URLSearchParams(url.search);
        params.delete('callsign');
        params.delete('icao');
        params.set('callsign', selection.csign);
        params.set('icao', selection.icao);
        url.search = params.toString();
        history.pushState({}, '', url.toString());

        if (!selection.orig) {
            selection.orig = {};
            selection.orig.iata = '';
            selection.orig.muni = 'Origin';
        };

        if (!selection.dest) {
            selection.dest = {};
            selection.dest.iata = '';
            selection.dest.muni = 'Destination';
        };

        Object.values(aircraft).forEach(function(i) {
            try {
                i.marker.getElement().style.opacity = '50%';
            } catch {};
        });
        selection.marker.getElement().style.opacity = '100%';

        document.getElementById('main-container-main-view').style.display = 'none';

        document.getElementById('aircraft-img').src = selection.image.src;
        if (selection.image.attr) {
            document.getElementById('aircraft-img-shadow').title = '© ' + selection.image.attr;
            // for now until I find a better way to credit!
        } else {
            document.getElementById('aircraft-img-shadow').title = '';
        };
        document.getElementById('aircraft-img-shadow').href = selection.image.link;
        document.getElementById('aircraft-airline-logo').src = 'https://www.flightaware.com/images/airline_logos/180px/' + selection.csign.slice(0,3) + '.png';
        document.getElementById('aircraft-airline-name').textContent = (selection.airline.name ?? '').replace('International', "Int'l");
        document.getElementById('aircraft-callsign').textContent = selection.csign;
        document.getElementById('aircraft-callsign').title = selection.radio ?? '';
        document.getElementById('aircraft-route-origin').textContent = selection.orig.muni;
        document.getElementById('aircraft-route-destination').textContent = selection.dest.muni;

        document.getElementById('origin-input').placeholder = selection.orig.iata;
        document.getElementById('origin-input').value = '';
        document.getElementById('destination-input').placeholder = selection.dest.iata;
        document.getElementById('destination-input').value = '';

        document.getElementById('flight-progress').value = 0;

        document.getElementById('aircraft-reg').textContent = selection.aircraft.reg;
        if (selection.aircraft.country) {
            document.getElementById('aircraft-reg-flag').style.backgroundImage = 'url(/image/flag/' + selection.aircraft.country + ')';
            document.getElementById('aircraft-reg-flag').style.display = '';
        } else {
            document.getElementById('aircraft-reg-flag').style.display = 'none';
        };
        document.getElementById('aircraft-type').textContent = selection.aircraft.type;
        if (selection.aircraft.reg || selection.aircraft.country || selection.aircraft.type) {
            document.getElementById('aircraft-type').parentNode.style.display = '';
        } else {
            document.getElementById('aircraft-type').parentNode.style.display = 'none';
        };

        document.getElementById('aircraft-hdg').textContent = Math.round(selection.hdg) + 'º';
        document.getElementById('aircraft-hdg-indicator').style.transform = 'rotate(' + selection.hdg + 'deg)';

        document.getElementById('aircraft-speed').textContent = Math.round(selection.speed);
        const speedBounded = Math.max(0, Math.min((selection.speed/600), 1)); // max 600 KT
        const speedDashoffset = 188.4 - (speedBounded * 188.4);
        document.getElementById('aircraft-speed-indicator').style.strokeDashoffset = speedDashoffset;

        document.getElementById('aircraft-climb').textContent = Math.round(Math.abs(selection.climb));
        let indicator;
        if (Math.round(selection.climb) > 0) {
            indicator = '▲';
        } else if (Math.round(selection.climb) === 0) {
            indicator = '►';
        } else if (Math.round(selection.climb) < 0) {
            indicator = '▼';
        };
        document.getElementById('aircraft-climb-indicator').textContent = indicator;

        if (selection.alt > 18000) { // can safely assume above the T. alt globally
            document.getElementById('aircraft-alt-main').textContent = 'FL' + Math.floor(selection.alt/100);
            document.getElementById('aircraft-alt-alt').textContent = Math.round(selection.alt) + ' FT';
        } else {
            document.getElementById('aircraft-alt-main').textContent = Math.round(selection.alt);
            document.getElementById('aircraft-alt-alt').textContent = 'FT';
        };
        const altBounded = Math.max(0, Math.min((selection.alt/41000), 1));
        const altDashoffset = 75 - (altBounded * 75);
        document.getElementById('aircraft-alt-indicator').style.strokeDashoffset = altDashoffset;

        document.getElementById('origin-input').addEventListener('input', function() {
            if (this.value.length == 3) {
                socketio.emit('lookup.airport', this.value, 'origin');
                document.getElementById('destination-input').focus();
            } else {
                document.getElementById('aircraft-route-origin').innerHTML = 'Origin';
            };
        });

        document.getElementById('destination-input').addEventListener('input', function() {
            if (this.value.length == 3) {
                socketio.emit('lookup.airport', this.value, 'destination');
                document.getElementById('destination-input').blur()
            } else {
                document.getElementById('aircraft-route-destination').innerHTML = 'Destination';
            };
        });

        plotRoutes();

        const point = map.latLngToContainerPoint(selection.marker.getLatLng());
        if (window.innerWidth <= 500) {
            point.y += 180;
        } else {
            point.x -= 160;
        };
        map.panTo(map.containerPointToLatLng(point));

        setContainerDefaultScroll('smooth');
        document.getElementById('back').addEventListener('click', clearMap);
        document.getElementById('main-container-aircraft-view').style.display = '';
    });

    socketio.on('lookup.airport', function(airport) {
        if (airport.routing !== null) {
            selection[airport.routing.substring(0, 4)] = airport;
            document.getElementById('aircraft-route-' + airport.routing).textContent = airport.muni;
            socketio.emit('lookup.add_' + airport.routing.substring(0, 4), selection.csign, airport.icao);
        };
    });
});
