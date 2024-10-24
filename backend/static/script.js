let map;
let directionsService;
let directionsRenderer;
let routePolylines = [];
let routeMarkers = [];
let infoWindows = [];
let previousRoutes = [];
let previousRouteIndex = -1;

function initMap() {
    map = new google.maps.Map(document.getElementById('map'), {
        center: { lat: 51.5074, lng: -0.1278 }, // London coordinates
        zoom: 12
    });

    directionsService = new google.maps.DirectionsService();
    directionsRenderer = new google.maps.DirectionsRenderer({
        suppressMarkers: true,
        map: map
    });

    const trafficLayer = new google.maps.TrafficLayer();
    trafficLayer.setMap(map);

    const originInput = document.getElementById("origin-input");
    const destinationInput = document.getElementById("destination-input");

    const originAutocomplete = new google.maps.places.Autocomplete(originInput);
    const destinationAutocomplete = new google.maps.places.Autocomplete(destinationInput);

    originAutocomplete.bindTo("bounds", map);
    destinationAutocomplete.bindTo("bounds", map);
}

// Initialize the map when the window loads
window.onload = initMap;

document.addEventListener('DOMContentLoaded', function() {
    const calculateButton = document.getElementById('calculate-button');
    const startRouteButton = document.getElementById('start-route-button');
    const backButton = document.getElementById('back-button');

    if (calculateButton) {
        calculateButton.addEventListener('click', calculateRoute);
    } else {
        console.error('Calculate button element not found.');
    }

    if (startRouteButton) {
        startRouteButton.addEventListener('click', startRoute);
    } else {
        console.error('Start Route button element not found.');
    }

    if (backButton) {
        backButton.addEventListener('click', goBack);
    } else {
        console.error('Back button element not found.');
    }
});

function calculateGreenRoute(origin, destination) {
    const data = {
        origin: { lat: origin.lat(), lng: origin.lng() },
        destination: { lat: destination.lat(), lng: destination.lng() }
    };

    console.log("Sending data to server:", data);

    fetch('/green_route', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        console.log('Received result from server:', result);
        if (result.error) {
            throw new Error(result.error);
        }
        displayGreenModeResults(result, origin, destination);
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while fetching the green route. Defaulting to standard route.');
        calculateStandardRoute(origin, destination);
    });
}

function clearMarkersPolylinesAndInfoWindows() {
    routeMarkers.forEach(marker => marker.setMap(null));
    routeMarkers = [];

    routePolylines.forEach(polyline => polyline.setMap(null));
    routePolylines = [];

    infoWindows.forEach(infoWindow => infoWindow.close());
    infoWindows = [];
}

function addMarker(position, title, icon = null) {
    const marker = new google.maps.Marker({
        position: position,
        map: map,
        title: title,
        icon: icon
    });
    routeMarkers.push(marker);
}

function createInfoWindow(content, position) {
    const infoWindow = new google.maps.InfoWindow({
        content: content,
        position: position
    });
    infoWindow.open(map);
    infoWindows.push(infoWindow);
}

function calculateRoute() {
    const loadingSpinner = document.getElementById('loading-spinner');
    loadingSpinner.style.display = 'block';  // Show spinner while route is calculated

    // Clear previous UI elements
    clearMarkersPolylinesAndInfoWindows();

    const origin = document.getElementById('origin-input').value;
    const destination = document.getElementById('destination-input').value;
    const mode = document.getElementById('mode').value;

    if (!origin || !destination) {
        alert('Please enter both origin and destination.');
        loadingSpinner.style.display = 'none';  // Hide spinner if error
        return;
    }

    if (mode === 'green') {
        handleGreenMode(origin, destination);
        loadingSpinner.style.display = 'none';  // Hide spinner after green mode route is calculated
        return;
    }

    const request = {
        origin: origin,
        destination: destination,
        travelMode: google.maps.TravelMode[mode.toUpperCase()],
        provideRouteAlternatives: true
    };

    directionsService.route(request, (result, status) => {
        loadingSpinner.style.display = 'none';  // Hide spinner after route is calculated

        if (status === google.maps.DirectionsStatus.OK) {
            previousRoutes = result.routes;  // Store routes
            displayRouteDetails(result, mode); // Call displayRouteDetails to handle the result
            populateRouteSelection(result);
        } else {
            alert('Error: ' + status);
        }
    });
}


function displayRouteDetails(result, mode) {
    clearMarkersPolylinesAndInfoWindows();

    result.routes.forEach((route, index) => {
        const leg = route.legs[0];
        const routeData = {
            mode: mode,
            distance: leg.distance.value / 1000, // distance in km
            route: route.overview_path
        };

        // Keep track of the route for navigation
        previousRoutes.push(routeData);
        previousRouteIndex++;

        const polyline = new google.maps.Polyline({
            path: routeData.route,
            geodesic: true,
            strokeColor: index === 0 ? '#FF0000' : '#00FF00', // Different color for each route
            strokeOpacity: 1.0,
            strokeWeight: 5
        });
        polyline.setMap(map);
        routePolylines.push(polyline);

        addMarker(leg.start_location, 'Start');
        addMarker(leg.end_location, 'End');

        const infoContent = `<div><strong>Route ${index + 1}</strong><br>Distance: ${routeData.distance.toFixed(2)} km<br>Mode: ${mode}</div>`;
        createInfoWindow(infoContent, leg.start_location);

        displayStepByStepDirections(leg);
    });
}

function populateRouteSelection(result) {
    const routeSelection = document.getElementById('route-selection');
    if (!routeSelection) {
        console.error('Route selection element not found');
        return;
    }
    routeSelection.innerHTML = '';
    routeSelection.style.display = 'block';

    if (result && result.routes && Array.isArray(result.routes)) {
        result.routes.forEach((route, index) => {
            if (route && route.legs && route.legs[0] && route.legs[0].distance) {
                const option = document.createElement('option');
                option.value = index;
                option.textContent = `Route ${index + 1} - Distance: ${route.legs[0].distance.text}`;
                routeSelection.appendChild(option);
            } else {
                console.error(`Invalid route data for route ${index}:`, route);
            }
        });
    } else {
        console.error('Invalid result structure:', result);
    }
}
function isWithinLondon(lat, lng) {
    console.log(`Checking coordinates: Lat: ${lat}, Lng: ${lng}`);
    const londonBounds = {
        north: 51.6918741,
        south: 51.2867602,
        east: 0.3340155,
        west: -0.5103751
    };

    return lat <= londonBounds.north && lat >= londonBounds.south &&
           lng <= londonBounds.east && lng >= londonBounds.west;
}

function handleGreenMode(origin, destination) {
    const geocoder = new google.maps.Geocoder();

    geocoder.geocode({ address: origin }, function(resultsOrigin, statusOrigin) {
        if (statusOrigin === google.maps.GeocoderStatus.OK) {
            geocoder.geocode({ address: destination }, function(resultsDest, statusDest) {
                if (statusDest === google.maps.GeocoderStatus.OK) {
                    const data = {
                        originLat: resultsOrigin[0].geometry.location.lat(),
                        originLng: resultsOrigin[0].geometry.location.lng(),
                        destLat: resultsDest[0].geometry.location.lat(),
                        destLng: resultsDest[0].geometry.location.lng()
                    };

                    console.log('Sending data to server:', data);
                    if (!isWithinLondon(data.originLat, data.originLng) || !isWithinLondon(data.destLat, data.destLng)) {
                        alert('Both origin and destination must be within London.');
                        return;
                    }

                    // Only make the fetch request if we have valid coordinates
                    fetch('/green_route', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(data)
                    })
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Network response was not ok');
                        }
                        return response.json();
                    })
                    .then(result => {
                        console.log('Received result from server:', result);
                        if (result.error) {
                            alert('Error: ' + result.error);
                        } else {
                            // Process the route directly as an array
                            if (Array.isArray(result)) {
                                // Display green route results
                                displayGreenModeResults(result, origin, destination);
                            } else {
                                console.error('Unexpected result format:', result);
                                alert('Unexpected result format from server.');
                            }
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('An error occurred while fetching the green route. Defaulting to standard route.');
                        calculateRoute(); // Fallback to standard route
                    });
                } else {
                    console.error('Error with destination geocode:', statusDest);
                    alert('Unable to geocode destination address.');
                }
            });
        } else {
            console.error('Error with origin geocode:', statusOrigin);
            alert('Unable to geocode origin address.');
        }
    });
}


const icons = {
    walk: "http://maps.google.com/mapfiles/ms/icons/blue-dot.png",
    bicycle: "http://maps.google.com/mapfiles/ms/icons/yellow-dot.png",
    "e-bus": "http://maps.google.com/mapfiles/ms/icons/green-dot.png",
    "eco-cab": "http://maps.google.com/mapfiles/ms/icons/red-dot.png",
};

const polylineColors = {
    walk: "#0000FF",   // Blue for walking
    bicycle: "#FFD700", // Yellow for cycling
    "e-bus": "#008000",  // Green for e-bus
    "eco-cab": "#FF0000" // Red for eco-cab
};

function displayGreenModeResults(result, origin, destination) {
    clearMarkersPolylinesAndInfoWindows(); // Clear previous markers and polylines

    if (!Array.isArray(result)) {
        console.error('Invalid result structure:', result);
        return;
    }

    result.forEach((segment, index) => {
        const [mode, coordinates, distance, emissions] = segment;

        // Create polyline for this segment
        const polylinePath = coordinates.map(coord => ({ lat: coord[0], lng: coord[1] }));
        const polyline = new google.maps.Polyline({
            path: polylinePath,
            strokeColor: polylineColors[mode],
            strokeOpacity: 0.8,
            strokeWeight: 5,
            map: map
        });
        routePolylines.push(polyline);

        // Add markers with custom icons for start of each segment
        const startCoord = coordinates[0];
        addCustomModeMarker({ lat: startCoord[0], lng: startCoord[1] }, mode, distance, emissions);

        // Add marker for the end of the trip (destination)
        if (index === result.length - 1) {
            const endCoord = coordinates[coordinates.length - 1];
            addCustomModeMarker({ lat: endCoord[0], lng: endCoord[1] }, "destination", distance, emissions, true);
        }
    });

    // Display route details in the sidebar
    displayGreenRouteDetails(result);
}

function addCustomModeMarker(position, mode, distance, emissions, isDestination = false) {
    const icon = isDestination ? "http://maps.google.com/mapfiles/ms/icons/red-dot.png" : icons[mode];

    const marker = new google.maps.Marker({
        position: position,
        map: map,
        title: mode,
        icon: icon
    });
    routeMarkers.push(marker);

    const infoWindowContent = isDestination
        ? `<div><strong>Destination</strong></div>`
        : `<div><strong>Mode: ${mode.toUpperCase()}</strong><br>
           Distance: ${distance.toFixed(2)} km<br>
           Emissions: ${emissions.toFixed(2)} kg CO2</div>`;

    const infoWindow = new google.maps.InfoWindow({
        content: infoWindowContent
    });

    // Show info window on hover
    marker.addListener('mouseover', () => {
        infoWindow.open(map, marker);
    });

    // Close info window when mouse leaves
    marker.addListener('mouseout', () => {
        infoWindow.close();
    });
}

function displayGreenRouteDetails(route) {
    let detailsHtml = '<h4>Green Route Details</h4><ul>';
    
    route.forEach((segment, index) => {
        const [mode, coords, distance, emissions] = segment;
        detailsHtml += `
            <li>
                <strong>Segment ${index + 1}:</strong><br>
                Mode: ${mode}<br>
                Distance: ${distance.toFixed(2)} km<br>
                Emissions: ${emissions.toFixed(2)} kg CO2<br>
                Duration: ${calculateDuration(route)}min
            </li>`;
    });

    detailsHtml += '</ul>';
    document.getElementById('directions-list').innerHTML = detailsHtml;
}
function populateGreenRouteSelection(result) {
    const routeData = result.route; // Access the route array
    const greenRouteSelection = document.getElementById('green-route-selection');
    
    if (!greenRouteSelection) {
        console.error('Green route selection element not found.');
        return; // Early exit if the element is not found
    }

    greenRouteSelection.innerHTML = ''; // Clear previous options
    greenRouteSelection.style.display = 'block'; // Show the selection dropdown

    routeData.forEach((route, index) => {
        const mode = route[0]; // Mode of transport
        const distance = route[2].toFixed(2) + " km"; // Distance
        const duration = calculateDuration(route); // Duration
        const emissions = route[3].toFixed(2) + " kg CO2"; 

        const opt = document.createElement('option');
        opt.value = index;
        opt.textContent = `Green Route ${index + 1} - Mode: ${mode}, Distance: ${distance}, Duration: ${duration}`;
        greenRouteSelection.appendChild(opt);
    });
}




// Function to calculate duration based on distance and mode
function calculateDuration(route) {
    const mode = route[0]; // Mode of transport (e.g., bicycle, e-bus, walk)
    const distance = route[2]; // Distance in km
    let speed; // Speed in km/h

    switch (mode) {
        case 'bicycle':
            speed = 15; // Average cycling speed
            break;
        case 'e-bus':
            speed = 40; // Average bus speed
            break;
        case 'walk':
            speed = 5; // Average walking speed
            break;
        default:
            speed = 10; // Default speed
    }

    const durationInHours = distance / speed;
    const durationInMinutes = Math.round(durationInHours * 60);
    return `${durationInMinutes} mins`;
}

// Example fetch function to get route data
fetch('/green_route', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        // No hardcoded coordinates
        originLat: null, // Placeholder for origin latitude
        originLng: null, // Placeholder for origin longitude
        destLat: null,   // Placeholder for destination latitude
        destLng: null    // Placeholder for destination longitude
    })
})
.then(response => response.json())
.then(routeData => {
    console.log('Route data:', routeData);
    
    // Check if routeData has the expected structure
    if (routeData && routeData.route && Array.isArray(routeData.route)) {
        routeData.route.forEach(route => {
            const mode = route[0]; // Mode of transport
            const coordinates = route[1]; // Coordinates array
            const distance = route[2]; // Distance

            
            const duration = calculateDuration(route);
            
            // Log the extracted details
            console.log(`Mode: ${mode}, Start: ${coordinates[0]}, End: ${coordinates[1]}, Distance: ${distance} km, Duration: ${duration}`);
            
            
            populateGreenRouteSelection(route); 
        });
    } else {
        console.error('Invalid route data structure:', routeData);
    }
})
.catch(error => console.error('Error fetching route data:', error));




function startRoute() {
    // Check if there are any routes available
    if (previousRoutes.length > 0) {
        // Get the selected route index from the first dropdown (regular routes)
        const regularRouteIndex = document.getElementById('route-selection').value;
        // Get the selected route index from the green route dropdown
        const greenRouteIndex = document.getElementById('green-route-selection').value;

        // Determine which route is selected
        let selectedRouteIndex = regularRouteIndex !== "" ? regularRouteIndex : greenRouteIndex;

        // Check if a valid route is selected from either dropdown
        if (selectedRouteIndex !== "") {
            // Display the selected route using the directions renderer
            directionsRenderer.setRouteIndex(parseInt(selectedRouteIndex));

            // Show step-by-step directions
            const steps = previousRoutes[selectedRouteIndex].legs[0].steps; // Adjust this based on your data structure
            const directionsList = document.getElementById('directions-list');
            directionsList.innerHTML = ''; // Clear previous directions

            // Loop through each step and create list items for the directions
            steps.forEach((step, index) => {
                const li = document.createElement('li');
                // Use innerHTML to correctly render any HTML tags within instructions
                li.innerHTML = `${step.instructions} (${step.distance.text}, ${step.duration.text})`;
                directionsList.appendChild(li);
            });
        } else {
            alert('No route selected. Please select a route from either dropdown.');
        }
    } else {
        alert('No route available to start.');
    }
}


function displayStepByStepDirections(leg) {
    let stepsHtml = '<h4>Directions</h4><ul>';

    leg.steps.forEach((step) => {
        const instruction = step.instructions;
        const distance = step.distance.text;

        if (step.travel_mode === 'TRANSIT') {
            const lineName = step.transit.line.short_name || step.transit.line.name;
            const departureStop = step.transit.departure_stop.name;
            const arrivalStop = step.transit.arrival_stop.name;
            const numStops = step.transit.num_stops;
            stepsHtml += `
                <li>
                    <strong>${lineName}</strong><br>
                    From: ${departureStop}<br>
                    To: ${arrivalStop}<br>
                    Number of Stops: ${numStops}<br>
                    Distance: ${distance}
                </li>`;
        } else {
            stepsHtml += `<li>${instruction} (${distance})</li>`;
        }
    });

    stepsHtml += '</ul>';
    document.getElementById('directions-list').innerHTML = stepsHtml;
}


function goBack() {
    if (previousRouteIndex > 0) {
        previousRouteIndex--;
        displayRouteDetails(previousRoutes[previousRouteIndex], 'standard'); // Modify if you need to handle differently
    } else {
        alert('No previous route to go back to.');
    }
}
