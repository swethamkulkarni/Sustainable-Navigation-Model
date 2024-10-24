import pandas as pd
import numpy as np
from gplearn.genetic import SymbolicRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import joblib
import logging
from geopy.distance import great_circle  # To calculate distance

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Load data
logging.debug("Loading data...")
ebus_data = pd.read_excel('data/ebus_data.xlsx')
cycle_data = pd.read_csv('data/cycle_data.csv')
logging.debug(f"eBus Data Columns: {ebus_data.columns.tolist()}")
logging.debug(f"Cycle Data Columns: {cycle_data.columns.tolist()}")

# Ensure duration is in float32 format only for cycle data
cycle_data['Total duration (ms)'] = cycle_data['Total duration (ms)'].astype('float32')

# Preprocess data
def preprocess_data(ebus_data, cycle_data):
    logging.debug("Preprocessing data...")
    
    ebus_features = ebus_data[['latitude', 'longitude']].values
    cycle_features = cycle_data[['Start Latitude', 'Start Longitude', 'End Latitude', 'End Longitude', 'Total duration (ms)', 'Distance (km)']].values
    
    ebus_features_expanded = np.zeros((ebus_features.shape[0], cycle_features.shape[1]))
    ebus_features_expanded[:, :2] = ebus_features  
    
    X = np.vstack((ebus_features_expanded, cycle_features))
    y = np.concatenate((np.zeros(len(ebus_features)), np.ones(len(cycle_features))))
    
    logging.debug(f"Preprocessed data shape: X = {X.shape}, y = {y.shape}")
    return X, y
import requests

def get_weather(lat, lon, api_key):
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data['weather'][0]['description'], data['main']['temp']
    else:
        logging.error("Error fetching weather data")
        return None, None

X, y = preprocess_data(ebus_data, cycle_data)

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
logging.debug(f"Train-test split: X_train = {X_train.shape}, X_test = {X_test.shape}")

# Define and train the model
logging.debug("Defining and training the model...")
est_gp = SymbolicRegressor(population_size=2000,
                           generations=20,
                           stopping_criteria=0.01,
                           p_crossover=0.7,
                           p_subtree_mutation=0.1,
                           p_hoist_mutation=0.05,
                           p_point_mutation=0.1,
                           max_samples=0.9,
                           verbose=1,
                           parsimony_coefficient=0.01,
                           random_state=42)

est_gp.fit(X_train, y_train)

# Evaluate on training set
train_pred = est_gp.predict(X_train)
train_mse = mean_squared_error(y_train, train_pred)
logging.debug(f"Training mean squared error: {train_mse}")

# Evaluate on test set
y_pred = est_gp.predict(X_test)
test_mse = mean_squared_error(y_test, y_pred)
logging.debug(f"Test mean squared error: {test_mse}")

# Print the best program
logging.debug("Best program:")
logging.debug(est_gp._program)

# Save the model
model_filename = 'sustainable_navigation_model.joblib'
joblib.dump(est_gp, model_filename)
logging.debug(f"Model saved as {model_filename}")

# Function to calculate sustainability score
def calculate_sustainability_score(mode, distance, duration):
    logging.debug(f"Calculating sustainability score for mode: {mode}, distance: {distance}, duration: {duration}")
    
    emissions = {
        'walk': 0,
        'cycle': 0,
        'ebike': 15,
        'escooter': 20,
        'ebus': 80,
        'ecab': 100
    }
    
    if mode not in emissions:
        logging.error(f"Unknown mode: {mode}")
        return 0.0

    features = np.array([[0, 0, 0, 0, duration / 60, distance]])  
    
    base_score = est_gp.predict(features)[0]
    logging.debug(f"Base score for mode {mode}: {base_score}, Features: {features}")

    max_emission = max(emissions.values())
    emission_factor = emissions[mode] / max_emission if max_emission > 0 else 0
    score = base_score * (1 - emission_factor)

    if mode in ['walk', 'cycle'] and score == 0:
        score += 1e-5

    logging.debug(f"Calculated score: {score}")
    return score

# Function to suggest optimal mode
def suggest_optimal_mode(start_lat, start_lon, end_lat, end_lon, api_key):
    logging.debug(f"Suggesting optimal mode for route: ({start_lat}, {start_lon}) to ({end_lat}, {end_lon})")
    
    # Fetch weather data
    weather_desc, temperature = get_weather(start_lat, start_lon, api_key)
    logging.debug(f"Current weather: {weather_desc}, Temperature: {temperature}°C")
    
    modes = ['walk', 'cycle', 'ebike', 'escooter', 'ebus', 'ecab']
    distance = great_circle((start_lat, start_lon), (end_lat, end_lon)).kilometers
    durations = {
        'walk': distance * 15,
        'cycle': distance * 5,
        'ebike': distance * 6,
        'escooter': distance * 7,
        'ebus': distance * 10,
        'ecab': distance * 8
    }

    # Modify scores based on weather conditions
    scores = {}
    for mode in modes:
        score = calculate_sustainability_score(mode, distance, durations[mode])
        
        # Adjust scores based on weather (e.g., reduce cycling score if it's rainy)
        if 'rain' in weather_desc.lower() and mode in ['cycle', 'ebike', 'escooter']:
            score *= 0.5  # Reduce score by 50% if it's raining
        
        scores[mode] = score

    optimal_mode = max(scores, key=scores.get)
    logging.debug(f"Optimal mode: {optimal_mode}, Distance: {distance:.2f}, Duration: {durations[optimal_mode]:.2f}")
    return optimal_mode, distance, durations[optimal_mode]


# Example Usage
start_lat, start_lon = 40.7128, -74.0060  
end_lat, end_lon = 40.7614, -73.9776  


api_key = '41e8bea6b216bd2ac0f8a004edd790f9'
optimal_mode, distance, duration = suggest_optimal_mode(start_lat, start_lon, end_lat, end_lon, api_key)
print(f"Optimal mode: {optimal_mode}")
print(f"Estimated distance: {distance:.2f} km")
print(f"Estimated duration: {duration:.2f} minutes")
