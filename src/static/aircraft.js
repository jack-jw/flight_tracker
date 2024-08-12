// static/aircraft.js

//document.addEventListener('visibilitychange', function() {
//    if (!document.hidden) location.reload();
//});
// to prevent glitching of animations, not the best implementation

document.addEventListener('DOMContentLoaded', function() {
    let selection = null;
    let aircraft = {};
    const iconSizes = {
        "generic": 25,
        "BCS1": 25,
        "A320": 27,
        "A337": 30,
        "A345": 32,
        "A359": 30,
        "A388": 36,
        "AT72": 20,
        "B737": 26,
        "B753": 29,
        "B744": 32,
        "B773": 32,
        "DA40": 20
    };

    const socketio = io();
    socketio.on('disconnect', location.reload);

    // MARK: - Container
    function setContainerMobileScroll(scrollBehaviour) {
        if (window.innerWidth <= 500) {
            const containerTop = document.getElementById('main-container').getBoundingClientRect().top + window.pageYOffset;
            const scrollPosition = containerTop - (window.innerHeight - 335);
            window.scrollTo({
                top: scrollPosition,
                left: 0,
                behavior: scrollBehaviour
            });
        };
    };

    setContainerMobileScroll('instant');

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

        document.getElementById('orig-input').outerHTML = document.getElementById('orig-input').outerHTML;
        document.getElementById('dest-input').outerHTML = document.getElementById('dest-input').outerHTML;
        document.getElementById('orig-input').classList.remove('invalid');
        document.getElementById('dest-input').classList.remove('invalid');
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
            if (selection && selection.icao === i.icao) plotRoutes();
        };

        if (speed !== 0) marker.moveInterval = setInterval(fly, 100);
    };

    function plotRoutes() {
        try { map.removeLayer(selection.polylines.orig.line); } catch {};
        try { map.removeLayer(selection.polylines.dest.line); } catch {};

        selection.polylines = {};

        if (typeof selection.orig.lat !== 'undefined' && typeof selection.orig.lng !== 'undefined') {
            selection.polylines.orig = plotGreatCircleRoute(selection.orig, selection.marker.getLatLng(), 1);
        };

        if (typeof selection.dest.lat !== 'undefined' && typeof selection.dest.lng !== 'undefined') {
            selection.polylines.dest = plotGreatCircleRoute(selection.dest, selection.marker.getLatLng(), 0.5);
        };

        if (selection.polylines.orig && selection.polylines.dest) {
            document.getElementById('flight-progress').value = selection.polylines.orig.distance / (selection.polylines.orig.distance + selection.polylines.dest.distance);
        } else {
            document.getElementById('flight-progress').value = 0;
        };
    };

    generateMap(7);

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
    document.getElementById('aircraft-list-clear').addEventListener('click', function() {
        document.getElementById('aircraft-list-filter').value = '';
        document.getElementById('aircraft-list-filter').dispatchEvent(new Event('input', {bubbles: true}));
    });

    document.getElementById('aircraft-list-filter').addEventListener('input', function() {
        const visibleLatLngs = [];
        const filterValue = this.value.toUpperCase();
        if (filterValue !== '') {
            document.getElementById('aircraft-list-filter').style.width = 'calc(100% - 45px)';
            document.getElementById('pfp').classList.add('hidden');
            document.getElementById('aircraft-list-clear').classList.remove('hidden');
        } else {
            document.getElementById('aircraft-list-filter').style.width = '';
            document.getElementById('aircraft-list-clear').classList.add('hidden');
            document.getElementById('pfp').classList.remove('hidden');
        };

        Array.from(document.getElementById('aircraft-list').children).forEach(item => {
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

    socketio.on('aircraft', function(payload) {
        aircraft = {
            ...aircraft,
            ...payload
        };

        Object.values(aircraft).forEach(function(i) {
            i.marker = L.marker([i.lat, i.lng], {
                icon: L.divIcon({
                    className: 'aircraft-icon',
                    html: '<svg><use href="#' + i.icon + '"></use></svg>',
                    iconSize: [iconSizes[i.icon], iconSizes[i.icon]]
                })
            }).addTo(map);

            i.marker.setZIndexOffset(i.alt);
            i.marker.getElement().setAttribute('tabindex', '-1');

            set(i);

            let airlineLogo = '';
            if (!/\d/.test(i.csign.slice(0, 3))) {
                airlineLogo = 'background-image: url(https://www.flightaware.com/images/airline_logos/180px/' + i.csign.slice(0, 3) + '.png)'
            };


            i.listItem = document.createElement('div');
            i.listItem.innerHTML = `
                <div class="aircraft-list-airline-logo" style="${airlineLogo}">
                </div>

                <div>
                    <div class="aircraft-list-csign">${i.csign}</div>
                    <div class="aircraft-list-metrics">
                        <b>${i.reg ?? ''}</b> ${i.type ?? ''}
                    </div>
                    <div class="aircraft-list-metrics">
                        <span style="width: 1em; height: 1em">
                            <span style="transform: rotate(${i.hdg}deg); position: absolute">&uarr;</span>
                        </span>
                        <span style="margin-left: 1em">
                            ${Math.round(i.speed)} ${strings.units.aviation.speed}
                        </span>
                    </div>
                </div>
            `;

            document.getElementById('aircraft-list').appendChild(i.listItem);

            [i.listItem, i.marker.getElement()].forEach(element => {
                element.addEventListener('click', function(event) {
                    socketio.emit('select', i.icao, i.csign);
                    event.stopPropagation();
                }, true);
                element.classList.add('_' + i.icao);
            });

            i.marker.addEventListener('mouseover', function(event) {
                if (window.innerWidth >= 500 && !window.matchMedia('(pointer: coarse)').matches) {
                    i.listItem.scrollIntoView({behaviour: 'smooth'});
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
        countElement.textContent = Object.keys(aircraft).length + ' aircraft';
        document.getElementById('aircraft-list').appendChild(countElement);
    });

    // Check if an aircraft is selected in the URL
    const urlIcao = new URLSearchParams(window.location.search).get('icao');
    const urlCSign = new URLSearchParams(window.location.search).get('callsign');
    if (urlCSign && urlIcao && aircraft[urlIcao]) socketio.emit('select', urlIcao, urlCSign);

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
        console.log(selection);

        const url = new URL(window.location.href);
        const params = new URLSearchParams(url.search);
        params.delete('callsign');
        params.delete('icao');
        params.set('callsign', selection.csign);
        params.set('icao', selection.icao);
        url.search = params.toString();
        history.pushState({}, '', url.toString());

        selection.orig ||= {};
        selection.dest ||= {};

        Object.values(aircraft).forEach(function(i) {
            i.marker.getElement().style.opacity = '50%';
        });
        selection.marker.getElement().style.opacity = '100%';

        document.getElementById('main-container-main-view').style.display = 'none';

        document.getElementById('aircraft-img').src = selection.image.src;
        document.getElementById('aircraft-img-shadow').title = '© ' + selection.image.attr ?? ''; // for now until I find a better way to credit!
        document.getElementById('aircraft-img-shadow').href = selection.image.link;
        document.getElementById('aircraft-airline-logo').src = 'https://www.flightaware.com/images/airline_logos/180px/' + selection.csign.slice(0, 3) + '.png';
        document.getElementById('aircraft-airline-name').textContent = (selection.airline.name ?? '').replace('International', "Int'l");
        document.getElementById('aircraft-csign').textContent = selection.csign;
        document.getElementById('aircraft-csign').title = selection.route.radio;
        document.getElementById('aircraft-route-orig').textContent = selection.orig.muni ?? strings.ui.orig;
        document.getElementById('aircraft-route-dest').textContent = selection.dest.muni ?? strings.ui.dest;
        document.getElementById('orig-input').placeholder = selection.orig.iata ?? '';
        document.getElementById('orig-input').value = '';
        document.getElementById('dest-input').placeholder = selection.dest.iata ?? '';
        document.getElementById('dest-input').value = '';
        document.getElementById('flight-progress').value = 0;
        document.getElementById('aircraft-reg').textContent = selection.aircraft.reg;
        document.getElementById('aircraft-reg').title = selection.aircraft.radio;
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
        document.getElementById('aircraft-speed-indicator').style.strokeDashoffset = 188.4 - (Math.max(0, Math.min((selection.speed / 600), 1)) * 188.4); // max 600 KTS

        document.getElementById('aircraft-climb').textContent = Math.round(Math.abs(selection.climb));
        document.getElementById('aircraft-climb-indicator').textContent = Math.round(selection.climb) > 0 ? '▲' : Math.round(selection.climb) < 0 ? '▼' : '►';

        if (selection.alt > 18000) { // can safely assume above the transition alt globally
            document.getElementById('aircraft-alt-main').textContent = 'FL' + Math.floor(selection.alt / 100);
            document.getElementById('aircraft-alt-alt').textContent = Math.round(selection.alt) + ' ' + strings.units.aviation.alt;
        } else {
            document.getElementById('aircraft-alt-main').textContent = Math.round(selection.alt);
            document.getElementById('aircraft-alt-alt').textContent = strings.units.aviation.alt;
        };

        document.getElementById('aircraft-alt-indicator').style.strokeDashoffset = 75 - (Math.max(0, Math.min((selection.alt / 41000), 1)) * 75); // max 41000 FT

        document.getElementById('orig-input').addEventListener('input', function() {
            if (this.value.length === 3) {
                fetch('/info/airport/' + this.value + '.json').then(response => {
                    if (!response.ok) console.error(response.status);
                    return response.json();
                }).then(airport => {
                    if (airport.name) {
                        document.getElementById('aircraft-route-orig').textContent = airport.muni;
                        selection.orig = airport;
                        this.placeholder = airport.iata;
                        this.value = '';
                        socketio.emit('route', selection.csign, airport.icao, '')
                        document.getElementById('dest-input').focus();
                    } else {
                        this.classList.add('invalid');
                    };
                });
            } else {
                document.getElementById('aircraft-route-orig').textContent = strings.ui.orig;
                this.classList.remove('invalid');
            };
        });

        document.getElementById('dest-input').addEventListener('input', function() {
            if (this.value.length === 3) {
                fetch('/info/airport/' + this.value + '.json').then(response => {
                    if (!response.ok) console.error(response.status);
                    return response.json();
                }).then(airport => {
                    if (airport.name) {
                        document.getElementById('aircraft-route-dest').textContent = airport.muni;
                        selection.dest = airport;
                        this.placeholder = airport.iata;
                        this.value = '';
                        socketio.emit('route', selection.csign, '', airport.icao)
                        document.getElementById('dest-input').blur()
                    } else {
                        this.classList.add('invalid');
                    };
                });
            } else {
                document.getElementById('aircraft-route-dest').textContent = strings.ui.dest;
                this.classList.remove('invalid');
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
        setContainerMobileScroll('smooth');
        document.getElementById('back').addEventListener('click', clearMap);
        document.getElementById('main-container-aircraft-view').style.display = '';
    });
});
