// static/my_flights.js

document.addEventListener('DOMContentLoaded', function() {
    let totalDistance = 0;

    generateMap(3);

    function animateNumber(id, end, word, dp = 0) {
        let startTimestamp;
        const step = (timestamp) => {
            startTimestamp = startTimestamp || timestamp;
            const progress = Math.min((timestamp - startTimestamp) / 1000, 1);
            const displayedProgress = (progress * end).toFixed(dp);
            const description = Array.isArray(word) ? displayedProgress === '1' ? word[1] : word[0] : word;
            document.getElementById(id).textContent = description.replace('{}', parseFloat(displayedProgress).toLocaleString(strings.lang.code));
            if (progress < 1) window.requestAnimationFrame(step);
        };
        window.requestAnimationFrame(step);
    };

    function animateFlags(id, countryList) {
        const interval = 1000 / countryList.length;

        let index = 0;
        const addFlag = () => {
            if (index < countryList.length) {
                const flagElement = document.createElement('div');
                flagElement.classList.add('flag');
                flagElement.style.backgroundImage = 'url(/image/flag/' + countryList[index] + ')';
                document.getElementById(id).appendChild(flagElement);
                index++;
            } else {
                clearInterval(flagInterval);
            };
        };
        const flagInterval = setInterval(addFlag, interval);
    };

    map.flyTo(mf.entities.airports[0]);

    mf.flights.forEach(function(flight) {
        totalDistance += plotGreatCircleRoute(
            mf.entities.airports.find(obj => obj.icao === flight.orig),
            mf.entities.airports.find(obj => obj.icao === flight.dest),
            0.75
        ).distance;
    });

    animateNumber('my-flights-flight-count', mf.flights.length, strings.ui.myflightscounts.flight);
    animateNumber('my-flights-inc-count', mf.counts.inc, strings.ui.myflightscounts.inc);
    animateNumber('my-flights-int-count', mf.counts.int, strings.ui.myflightscounts.int);
    animateNumber('my-flights-dom-count', mf.counts.dom, strings.ui.myflightscounts.dom);
    animateNumber('my-flights-rnl-count', mf.counts.rnl, strings.ui.myflightscounts.rnl);

    animateNumber('my-flights-distance-count', totalDistance * 1.85, '{} ' + strings.units.metric.distance.toLowerCase());
    animateNumber('my-flights-distance-count-earth', totalDistance / 21620.65, strings.ui.myflightscounts.ofearth, 2);

    animateNumber('my-flights-country-count', mf.countries.length, strings.ui.myflightscounts.country);
    animateFlags('my-flights-country-count-flags', mf.countries);
    animateNumber('my-flights-continent-count', mf.continents.length, strings.ui.myflightscounts.ofcontinents);

    animateNumber('my-flights-airports-title', mf.entities.airports.length, strings.ui.myflightscounts.airport);
    animateNumber('my-flights-airlines-title', mf.entities.airlines.length, strings.ui.myflightscounts.airline);
    animateNumber('my-flights-types-title', mf.entities.types.length, strings.ui.myflightscounts.type);

    mf.entities.airports.forEach(function(airport) {
        const tooltipContent = `
            <div class="my-flights-airport-tooltip-title">
                <span class="flag" style="background-image: url('/image/flag/${airport.country}')"></span>
                <span class="my-flights-airport-tooltip-iata">${airport.iata}</span> ${airport.name.replace('International', "Int'l").replace('Airport', '').trim()}
            </div>
            <div class="my-flights-airport-tooltip-flights">${strings.ui.myflightscounts.flight[(airport.flights > 1 ? 0 : 1)].replace('{}', airport.flights)}</div>
        `;

        L.marker(airport, {
            icon: L.divIcon({
                className: 'airport-icon',
                html: '<div></div>',
                iconSize: [12, 12]
            })
        }).addTo(map).setZIndexOffset(airport.flights).bindTooltip(tooltipContent, {className: 'my-flights-airport-tooltip'});
    });

    (["airlines", "airports", "types"]).forEach(function(category) {
        const baseClass = 'my-flights-' + category + '-';
        for (let i = 0; i < 5; i++) {
            const rankItem = document.getElementById(baseClass + i);
            const rankIcon = rankItem.querySelector('.my-flights-rank-icon');
            let displayName, bg;

            if (category === 'airlines') {
                displayName = mf.entities.airlines[i].name.replace('International', "Int'l");
                bg = 'url("https://www.flightaware.com/images/airline_logos/180px/' + mf.entities.airlines[i].icao + '.png")';
            } else if (category === 'types') {
                displayName = mf.entities.types[i].icao;
                rankIcon.innerHTML = '<svg><use href="#' + mf.entities.types[i].icon + '"></use></svg>';
            } else if (category === 'airports') {
                displayName = mf.entities.airports[i].iata;
                bg = 'url("/image/flag/' + mf.entities.airports[i].country + '")';
            };

            rankIcon.style.backgroundImage = bg;
            rankItem.querySelector('.my-flights-rank-name').textContent = displayName;
            rankItem.querySelector('.my-flights-rank-amount').textContent = strings.ui.myflightscounts.flight[(mf.entities[category][i].flights > 1 ? 0 : 1)].replace('{}', mf.entities[category][i].flights);
        };
    });
});
