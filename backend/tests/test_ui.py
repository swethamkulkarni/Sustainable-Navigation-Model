from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service

def test_green_mode_only_for_london():
    # Create a Service object and pass the path to chromedriver
    service = Service('C:\\Users\\smk10\\Desktop\\dissertation\\chromedriver-win64\\chromedriver-win64\\chromedriver.exe')
    
    
    driver = webdriver.Chrome(service=service)

    # Test case 1: Green mode inside London (should work)
    driver.get('http://localhost:5000/')
    origin_input = driver.find_element(By.ID, 'origin-input')
    destination_input = driver.find_element(By.ID, 'destination-input')
    
    # Enter a route within London
    origin_input.send_keys('51.5074, -0.1278')  # London
    destination_input.send_keys('51.509865, -0.118092')  # Another point in London

    mode_selector = driver.find_element(By.ID, 'mode')
    mode_selector.send_keys('green')

    calculate_button = driver.find_element(By.ID, 'calculate-button')
    calculate_button.click()

    # Wait for route calculation (6 min max)
    WebDriverWait(driver, 400).until(
        EC.presence_of_element_located((By.ID, 'directions-list'))
    )
    print("Green mode route within London calculated successfully.")
    
    # Test case 2: Green mode outside London (should show error)
    origin_input.clear()
    destination_input.clear()
    
    origin_input.send_keys('London')
    destination_input.send_keys('Cambridge')  # Outside London

    calculate_button.click()

    try:
        WebDriverWait(driver, 10).until(
            EC.alert_is_present()
        )
        alert = driver.switch_to.alert
        assert "Green mode is only available for routes within London." in alert.text
        print("Correctly blocked green mode for route outside London.")
        alert.accept()
    except:
        print("Test failed: No alert for route outside London.")

    driver.quit()
