from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
from geopy.distance import geodesic
from flask_cors import CORS
import requests
import joblib
from flask_caching import Cache
 
app = Flask(__name__)
CORS(app)
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 600})
# Load the trained symbolic regression model
model = joblib.load('sustainable_navigation_model.joblib')
 
# Constants
SEARCH_RADIUS = 1  # Max distance to search for nearby eBus stops (in km)
CARBON_FOOTPRINT = {'walk': 0, 'bicycle': 0, 'e-bus': 0.082, 'eco-cab': 0.14}
WEATHER_API_KEY = '41e8bea6b216bd2ac0f8a004edd790f9'  # Replace with your weather API key
CYCLE_API_URL = 'https://api.tfl.gov.uk/BikePoint?app_id=ad685628863948f586cb0f3b22c37778'
 
# Load eBus data
ebus_data = pd.read_excel('data/ebus_data.xlsx')
 
# Fetch and store cycle stations from the TfL API
def get_cycle_data():
    response = requests.get(CYCLE_API_URL)
    if response.status_code == 200:
        return pd.json_normalize(response.json())
    else:
        print("Failed to fetch cycle data:", response.status_code)
        return pd.DataFrame()  # Return an empty DataFrame on failure
 
cycle_stations = get_cycle_data()
 
# Function to get weather conditions
def get_weather(lat, lon):
    url = f'http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None
 
# Function to find nearby eBus stops
def find_nearby_stops(lat, lon, radius_km):
    nearby_stops = []
    for _, stop in ebus_data.iterrows():
        stop_lat, stop_lon = stop['latitude'], stop['longitude']
        distance = geodesic((lat, lon), (stop_lat, stop_lon)).km
        if distance <= radius_km:
            nearby_stops.append(stop)
    return nearby_stops
 
# Function to find the nearest cycle station
def nearest_cycle_station(location):
    nearest_station = None
    min_distance = float('inf')
   
    for _, station in cycle_stations.iterrows():
        station_location = (station['lat'], station['lon'])
        distance = geodesic(location, station_location).km
       
        if distance < min_distance:
            min_distance = distance
            nearest_station = station
   
    return nearest_station, min_distance
 
# Function to estimate time based on mode and distance
def estimate_time(mode, distance):
    speeds = {
        'walk': 5,  # km/h
        'bicycle': 15,  # km/h
        'e-bus': 20,  # km/h
        'eco-cab': 30  # km/h
    }
    return distance / speeds[mode] * 60  # Return time in minutes
 
# Function to get carbon footprint for the specified mode
def carbon_footprint(mode):
    return CARBON_FOOTPRINT[mode]
 
# Function to score a route using the SR model
def score_route_with_sr(route, weather_start, weather_end):
    total_distance = sum(geodesic(point[0], point[1]).km for mode, points, _, _ in route for point in zip(points[:-1], points[1:]))
    total_time = sum(estimate_time(mode, distance) for mode, points, distance, _ in route)
    total_carbon = sum(carbon_footprint(mode) for mode, _, _, _ in route)
 
    # Use the SR model to predict a sustainability score
    score = model.predict(np.array([[0, 0, 0, 0, total_time, total_distance]]))[0]
 
    # Adjust based on weather conditions (e.g., reduce cycling score if it's rainy)
    if weather_start and 'rain' in weather_start['weather'][0]['description'].lower():
        for mode, _, _, _ in route:
            if mode == 'bicycle':
                score *= 0.5  # Penalize cycling score in rainy weather
 
    return score
 
# Multi-modal route suggestion logic with SR model scoring
def sustainable_route(start, end, weather_start, weather_end):
    print("Calculating multi-mode sustainable route...")
    routes = []  # Store all potential routes
 
    # Find nearby eBus stops
    nearby_start_stops = find_nearby_stops(start['lat'], start['lng'], SEARCH_RADIUS)
    nearby_end_stops = find_nearby_stops(end['lat'], end['lng'], SEARCH_RADIUS)
    print(f"Nearby start stops: {nearby_start_stops}")
    print(f"Nearby end stops: {nearby_end_stops}")
 
    # Find nearest cycle stations
    cycle_station_start, distance_to_cycle_start = nearest_cycle_station((start['lat'], start['lng']))
    cycle_station_end, _ = nearest_cycle_station((end['lat'], end['lng']))
    print(f"Nearest cycle station start: {cycle_station_start}")
    print(f"Nearest cycle station end: {cycle_station_end}")
 
    # Check for eBus route options
    if nearby_start_stops and nearby_end_stops:
        for start_stop in nearby_start_stops:
            for end_stop in nearby_end_stops:
                # Option 1: Walk to eBus stop, take bus, walk to destination
                route = []
                route.append(('walk', [(start['lat'], start['lng']), (start_stop['latitude'], start_stop['longitude'])],
                              geodesic((start['lat'], start['lng']), (start_stop['latitude'], start_stop['longitude'])).km,
                              CARBON_FOOTPRINT['walk']))
                route.append(('e-bus', [(start_stop['latitude'], start_stop['longitude']), (end_stop['latitude'], end_stop['longitude'])],
                              geodesic((start_stop['latitude'], start_stop['longitude']), (end_stop['latitude'], end_stop['longitude'])).km,
                              CARBON_FOOTPRINT['e-bus']))
                route.append(('walk', [(end_stop['latitude'], end_stop['longitude']), (end['lat'], end['lng'])],
                              geodesic((end_stop['latitude'], end_stop['longitude']), (end['lat'], end['lng'])).km,
                              CARBON_FOOTPRINT['walk']))
                routes.append(route)
 
                # Option 2: Cycle to bus stop, take bus, walk to destination
                route = []
                route.append(('bicycle', [(start['lat'], start['lng']), (start_stop['latitude'], start_stop['longitude'])],
                              geodesic((start['lat'], start['lng']), (start_stop['latitude'], start_stop['longitude'])).km,
                              CARBON_FOOTPRINT['bicycle']))
                route.append(('e-bus', [(start_stop['latitude'], start_stop['longitude']), (end_stop['latitude'], end_stop['longitude'])],
                              geodesic((start_stop['latitude'], start_stop['longitude']), (end_stop['latitude'], end_stop['longitude'])).km,
                              CARBON_FOOTPRINT['e-bus']))
                route.append(('walk', [(end_stop['latitude'], end_stop['longitude']), (end['lat'], end['lng'])],
                              geodesic((end_stop['latitude'], end_stop['longitude']), (end['lat'], end['lng'])).km,
                              CARBON_FOOTPRINT['walk']))
                routes.append(route)
 
    # If no eBus stops, check for cycle stations
    if cycle_station_start is not None and distance_to_cycle_start <= 1.0:
        # Option 3: Walk to cycle dock, cycle to end station, then walk to destination
        route = []
        route.append(('walk', [(start['lat'], start['lng']), (cycle_station_start['lat'], cycle_station_start['lon'])],
                      geodesic((start['lat'], start['lng']), (cycle_station_start['lat'], cycle_station_start['lon'])).km,
                      CARBON_FOOTPRINT['walk']))
        route.append(('bicycle', [(cycle_station_start['lat'], cycle_station_start['lon']), (end['lat'], end['lng'])],
                      geodesic((cycle_station_start['lat'], cycle_station_start['lon']), (end['lat'], end['lng'])).km,
                      CARBON_FOOTPRINT['bicycle']))
        routes.append(route)
 
    # Evaluate all routes and calculate scores using the SR model
    scored_routes = []
    for route in routes:
        score = score_route_with_sr(route, weather_start, weather_end)
        scored_routes.append((route, score))
 
    # Select the route with the lowest score
    best_route = min(scored_routes, key=lambda x: x[1])[0] if scored_routes else []
 
    print("Best route details:", best_route)
    return best_route
 
# Flask routes
@app.route('/')
def index():
    return render_template('index.html')
 
@app.route('/green_route', methods=['POST'])
@cache.cached(timeout=600, key_prefix=lambda: f"green_route_{request.json['originLat']}_{request.json['originLng']}_{request.json['destLat']}_{request.json['destLng']}")  # Cache for 10 minutes
def green_route():
    try:
        data = request.json
        print(data)
        if not all(data.get(key) for key in ['originLat', 'originLng', 'destLat', 'destLng']):
            return jsonify({'error': 'Missing or invalid coordinates'}), 400
        print(f"Received data: {data}")
        source = {'lat': data['originLat'], 'lng': data['originLng']}
        destination = {'lat': data['destLat'], 'lng': data['destLng']}
       
        print("Fetching weather data...")
        weather_start = get_weather(source['lat'], source['lng'])
        weather_end = get_weather(destination['lat'], destination['lng'])
        print("Weather data fetched:", weather_start, weather_end)
        print("Calculating sustainable route...")
        best_route = sustainable_route(source, destination, weather_start, weather_end)
       
        return jsonify(best_route), 200
    except Exception as e:
        print("Error occurred:", str(e))
        return jsonify({'error': 'An error occurred during route calculation'}), 500
 
 
if __name__ == '__main__':
    app.run(debug=True)
 
