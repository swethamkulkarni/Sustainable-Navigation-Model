import pytest
from app import carbon_footprint, find_nearby_stops, get_weather, app

from unittest.mock import patch

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# Test Emission Calculation for Different Transport Modes
def test_emission_calculation():
    print("Testing emission calculation for different modes of transport...")  # Debugging
    e_bus_emission = carbon_footprint('e-bus')
    print(f"Emission for e-bus: {e_bus_emission}")  # Debugging
    assert e_bus_emission == 0.082, f"Expected 0.082, got {e_bus_emission}"

    eco_cab_emission = carbon_footprint('eco-cab')
    print(f"Emission for eco-cab: {eco_cab_emission}")  # Debugging
    assert eco_cab_emission == 0.14, f"Expected 0.14, got {eco_cab_emission}"

    walk_emission = carbon_footprint('walk')  # Updated to 'walk' for consistency
    print(f"Emission for walk: {walk_emission}")  # Debugging
    assert walk_emission == 0, f"Expected 0, got {walk_emission}"

# Test Route Calculation Based on User Input (Restricted to London)
def test_route_calculation_london(client):
    # Debugging statement before using client fixture
    print("Test started: test_route_calculation_london")  # Debugging

    # Use the passed client directly
    print("Sending POST request to /green_route")
    response = client.post('/green_route', json={
        'originLat': 51.5074,  # Example latitude for London (Westminster)
        'originLng': -0.1278,  # Example longitude for London
        'destLat': 51.5155,    # Another location in London (Farringdon)
        'destLng': -0.1026     # Another London-based coordinate
    })
    print(f"Received response: {response}")  # Debugging
    assert response is not None, "No response received"
    assert response.status_code == 200, f"Expected status 200, got {response.status_code}"
    data = response.get_json()
    print(f"Response data: {data}")  # Debugging
    assert 'route' in data, "Expected 'route' in response data"

# Test Weather Data Integration (Mocking API Response)
@patch('app.get_weather')  # Mock the weather API call
def test_weather_data(mock_get_weather):
    mock_get_weather.return_value = {
        'weather': [{'description': 'clear sky'}],
        'main': {'temp': 15.0}
    }  # Mocked response
    print("Testing weather data retrieval...")  # Debugging
    weather = get_weather(51.5074, -0.1278)  # Test with London coordinates
    print(f"Weather data: {weather}")  # Debugging
    assert weather is not None, "Expected non-null weather data"
    assert 'main' in weather, "Expected 'main' in weather data"
    assert 'weather' in weather, "Expected 'weather' in weather data"

# Test eBus Stop Detection
def test_nearby_stops():
    print("Testing nearby eBus stops detection...")  # Debugging
    nearby_stops = find_nearby_stops(51.5074, -0.1278, 1)  # Search within 1 km in London
    print(f"Found nearby stops: {nearby_stops}")  # Debugging
    assert len(nearby_stops) > 0, "Expected to find at least one eBus stop"
