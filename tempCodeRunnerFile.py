from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import sys

sys.stdout.reconfigure(encoding='utf-8')  # Ensure utf-8 encoding for console output

# URL of the page containing the table
url = "https://production.egp.gov.et/egp/bids/all"

# Set up Selenium WebDriver (ensure you have the correct driver installed)
driver = webdriver.Chrome()  # Or use webdriver for your browser
driver.get(url)

# Wait for the table rows to load
WebDriverWait(driver, 30).until(
    EC.presence_of_all_elements_located((By.TAG_NAME, "tr"))
)

# Initialize data storage
data = []
headers = []

# Initialize page number for debugging
page_number = 1

# Loop through all pages
while True:
    print(f"Scraping page {page_number}...")
    page_number += 1

    # Get the page source and parse it with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, "html.parser")

    # Find the table
    table = soup.find("table", class_="ant-table-fixed")  # Adjust class name if needed
    if not table:
        print("Table not found. Check the structure.")
        break

    # Extract table headers (only once)
    if not headers:
        headers = [th.text.strip() for th in table.find_all("th")]
        print("Extracted Headers:", headers)  # Debugging: Print headers

    # Extract table rows
    for row in table.find_all("tr")[1:]:  # Skip header row
        cols = row.find_all("td")
        cols = [col.text.strip() for col in cols]
        if cols:
            data.append(cols)

    # Check if a "Next" button exists and is enabled
    try:
        next_button = driver.find_element(By.CSS_SELECTOR, ".ant-pagination-next")
        if "disabled" in next_button.get_attribute("class"):
            break  # Exit loop if "Next" button is disabled
        next_button.click()  # Click the "Next" button
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, "tr"))
        )
    except Exception as e:
        print("Pagination ended or error occurred:", e)
        break

# Convert to DataFrame
df = pd.DataFrame(data, columns=headers)
print("Extracted DataFrame:\n", df)

# Save the data for manual inspection
df.to_csv("scraped_data.csv", index=False)

# Filter for active bids by "Ministry of Defense"
if "Procuring Entity" in df.columns:
    print("Unique Procuring Entities:", df["Procuring Entity"].unique())  # Debugging: Print unique values
    df["Procuring Entity"] = df["Procuring Entity"].str.strip()  # Remove extra spaces
    active_bids = df[df["Procuring Entity"].str.contains("Ministry of Defense", case=False, na=False)]
    if not active_bids.empty:
        print("Filtered Active Bids:\n", active_bids)
        active_bids.to_csv("ministry_of_defense_bids.csv", index=False)  # Save filtered data
    else:
        print("No active bids found for 'Ministry of Defense'.")
else:
    print("Column 'Procuring Entity' not found in the table.")

# Close the browser
driver.quit()