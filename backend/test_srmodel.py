import unittest
import numpy as np
from srmodel import est_gp, calculate_sustainability_score, suggest_optimal_mode

class TestSymbolicRegressionModel(unittest.TestCase):
    
    def setUp(self):
        # Set up any initial data if necessary 
        print("Setting up test case...")
    
    def test_model_predict(self):
        # Test symbolic regression model with example inputs for time and distance
        print("Testing model prediction...")
        features = np.array([[0, 0, 0, 0, 30, 15]])  # Example input: [0, 0, 0, 0, time, distance]
        score = est_gp.predict(features)
        print(f"Predicted score: {score}")  # Debugging
        self.assertIsNotNone(score, "Expected non-null score")
        self.assertGreater(score[0], 0, f"Expected positive score, got {score[0]}")

        # Edge case: Test with extreme inputs (very short or long duration and distance)
        extreme_features = np.array([[0, 0, 0, 0, 1, 100]])  # Very short duration, long distance
        extreme_score = est_gp.predict(extreme_features)
        print(f"Predicted score for extreme input: {extreme_score}")  # Debugging
        self.assertIsNotNone(extreme_score, "Expected non-null score for extreme input")
    
    def test_sustainability_score(self):
        # Test sustainability score calculation
        print("Testing sustainability score calculation...")
        mode = 'cycle'
        distance = 10  # km
        duration = 30  # minutes
        score = calculate_sustainability_score(mode, distance, duration)
        print(f"Calculated score for {mode}: {score}")  # Debugging
        self.assertIsNotNone(score, "Expected non-null score")
        self.assertGreater(score, 0, "Expected a positive score for valid inputs")
        
        # Test edge cases for sustainability score
        invalid_mode = 'invalid_mode'
        invalid_score = calculate_sustainability_score(invalid_mode, distance, duration)
        self.assertEqual(invalid_score, 0, "Expected a score of 0 for an invalid mode")
    
    def test_suggest_optimal_mode(self):
        # Test mode suggestion
        print("Testing optimal mode suggestion...")
        start_lat, start_lon = 40.7128, -74.0060  # Example coordinates
        end_lat, end_lon = 40.7614, -73.9776
        api_key = '41e8bea6b216bd2ac0f8a004edd790f9'  
        optimal_mode, distance, duration = suggest_optimal_mode(start_lat, start_lon, end_lat, end_lon, api_key)
        print(f"Optimal mode: {optimal_mode}, Distance: {distance:.2f} km, Duration: {duration:.2f} min")
        self.assertIsNotNone(optimal_mode, "Expected an optimal mode to be suggested")
        self.assertGreater(distance, 0, "Expected positive distance")
        self.assertGreater(duration, 0, "Expected positive duration")
        
        # Edge case: Invalid coordinates
        invalid_lat, invalid_lon = 999, 999  # Invalid lat/lon values
        with self.assertRaises(Exception, msg="Expected an error for invalid coordinates"):
            suggest_optimal_mode(invalid_lat, invalid_lon, end_lat, end_lon, api_key)
    
    def tearDown(self):
        # Clean up after each test if necessary
        print("Cleaning up after test case...")

if __name__ == '__main__':
    unittest.main()
