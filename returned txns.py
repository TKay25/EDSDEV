


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Initialize WebDriver
driver = webdriver.Chrome()

# Open the target webpage
driver.get("http://192.168.1.134:9502/xmlpserver/Adhoc/Central+Operations/Interim/RTGS/Returned+RTGS+Account.xdo")  # Replace with actual URL

try:
    # Check for iframe and switch if necessary
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    if iframes:
        print("Iframe detected, switching to it...")
        driver.switch_to.frame(iframes[0])  # Switch to first iframe

    # Wait until input field is present & visible
    input_element = WebDriverWait(driver, 30).until(
        EC.visibility_of_element_located((By.ID, "_paramsREF"))
    )
    print("Input field found!")

    # Set the title attribute using JavaScript
    driver.execute_script("arguments[0].setAttribute('title', '2505913362058000');", input_element)

    # Also update the value
    driver.execute_script("arguments[0].value = arguments[1];", input_element, "2505913362058000")

    # Trigger change event
    driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", input_element)

    print("Title and value updated!")

    # Wait for Apply button to be clickable
    apply_button = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.ID, "reportViewApply"))
    )
    print("Apply button found!")

    # Ensure button is enabled
    driver.execute_script("arguments[0].removeAttribute('disabled');", apply_button)

    # Click the Apply button
    apply_button.click()
    print("Apply button clicked! Waiting for processing...")

    # *** WAIT FOR PROCESSING TO FINISH ***
    WebDriverWait(driver, 60).until(
        lambda d: apply_button.is_enabled()  # Wait until Apply button is re-enabled
    )
    
    print("Processing complete!")

    # Click the "Actions" button
    actions_button = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.ID, "reportViewMenu"))
    )
    actions_button.click()
    print("Actions button clicked!")

except Exception as e:
    print("Error:", e)

# Keep browser open (optional)
input("Press Enter to exit...")

# Close the browser
driver.quit()