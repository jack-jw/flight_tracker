// static/map.js

let tileLayer = null;
let map = null;

const themes = {
    satellite: {
        url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        credit: strings.acknowledgements.mapdata + ' © Esri, World Imagery',
        filter: 'none',
        retina: true
    },
    standard: {
        url: 'https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png',
        credit: strings.acknowledgements.mapdata + ' © OpenStreetMap contributors<br>' +
                strings.acknowledgements.maptiles +  ' © Humanitarian OpenStreetMap Team (HOT)',
        filter: '',
        retina: false
    },
    geofs: {
        url: 'https://data2.geo-fs.com/osm/{z}/{x}/{y}.png',
        credit: strings.acknowledgements.mapdata + ' © OpenStreetMap contributors<br>' +
                strings.acknowledgements.maptiles + ' © GeoFS',
        filter: '',
        retina: false
    },
    watercolour: {
        url: 'https://watercolormaps.collection.cooperhewitt.org/tile/watercolor/{z}/{x}/{y}.jpg',
        credit: strings.acknowledgements.mapdata + ' © OpenStreetMap contributors<br>' +
                strings.acknowledgements.maptiles + ' © Stamen Design',
        filter: 'none',
        retina: true
    }
};

function generateMap(zoom) {
    map = L.map('map', {
        center: [51.505, -0.09],
        zoom: zoom,
        maxZoom: 15,
        zoomControl: false,
        attributionControl: false
    });
    setTheme('satellite')
};

function setTheme(themeName) {
    if (themes[themeName]) {
        try { map.removeLayer(tileLayer); } catch {};

        tileLayer = L.tileLayer(themes[themeName].url, {
            detectRetina: themes[themeName].retina
        }).addTo(map);
        document.querySelector('.leaflet-tile-pane').style.filter = themes[themeName].filter;
        document.getElementById('map-credit').innerHTML = themes[themeName].credit;
    };
};

function plotGreatCircleRoute(start, end, opacity) {
    const s = {};
    const e = {};
    [s.lat, s.lng, e.lat, e.lng] = [start.lat, start.lng, end.lat, end.lng].map(c => c * Math.PI / 180);
    const d = 2 * Math.asin(Math.sqrt(Math.pow(Math.sin((e.lat - s.lat) / 2), 2) + Math.cos(s.lat) * Math.cos(e.lat) * Math.pow(Math.sin((e.lng - s.lng) / 2), 2)));

    const curvePoints = [];
    for (let i = 0; i <= 100; i++) {
        const r = i / 100;
        s.weight = Math.sin(d * (1 - r)) / Math.sin(d);
        e.weight = Math.sin(d * r) / Math.sin(d);

        const c = {
            x: s.weight * Math.cos(s.lat) * Math.cos(s.lng) + e.weight * Math.cos(e.lat) * Math.cos(e.lng),
            y: s.weight * Math.cos(s.lat) * Math.sin(s.lng) + e.weight * Math.cos(e.lat) * Math.sin(e.lng),
            z: s.weight * Math.sin(s.lat) + e.weight * Math.sin(e.lat)
        };

        curvePoints.push([
            Math.atan2(c.z, Math.sqrt(c.x ** 2 + c.y ** 2)) * 180 / Math.PI,
            Math.atan2(c.y, c.x) * 180 / Math.PI
        ]);
    };


    const line = L.polyline(curvePoints, {
        color: '#FF9500',
        weight: 2,
        opacity: opacity
    }).addTo(map);
    return {'line': line, 'distance': d * 3440.065};
};
