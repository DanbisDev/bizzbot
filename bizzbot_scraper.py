import csv
import os
from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options


# Initialize Selenium WebDriver (Chrome in this case)

class Listing:
    def __init__(self, title: str, description: str, cash_flow: str, price: str, url: str):
        self.title = title
        self.description = description
        self.cash_flow = cash_flow
        self.price = price
        self.url = url

    def __repr__(self):
        return f"Listing:\nTitle - {self.title}\nDescription - {self.description}\nCash flow - {self.cash_flow}\nPrice - {self.price}\nURL - {self.url}\n"


# Fetch HTML content using Selenium
def get_listings_from_url(url):
    print("Trying to get from: " + url)

    chrome_prefs = {
        "profile.managed_default_content_settings.javascript": 2  # 2 means disable JavaScript
    }

    options = webdriver.ChromeOptions()
    driver = webdriver.Remote("http://127.0.0.1:4444/wd/hub", options=options)

    try:
        # Open the target URL
        driver.get(url)

        # Optionally wait for JavaScript to load and DOM to populate
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".listing-container"))
        )

        # Get the page source (the fully rendered HTML)
        html = driver.page_source

        elements = driver.find_elements(By.TAG_NAME, 'app-listing-showcase')


        listings = []

        for element in elements:
            title = element.find_element(By.CLASS_NAME, 'title').text
            description = element.find_element(By.CLASS_NAME, 'description').text
            price = element.find_element(By.CLASS_NAME, 'asking-price').text
            url = element.find_element(By.CLASS_NAME, 'showcase').get_attribute('href')
            try:
                cash_flow = element.find_element(By.CLASS_NAME, 'cash-flow').text
            except:
                cash_flow = "Not found"
            listings.append(Listing(title, description, cash_flow, price, url))

    finally:
        # Close the WebDriver session
        driver.quit()

    return listings



def get_csv_and_save(url):
    # Fetch the listings from the provided URL
    listings = get_listings_from_url(url)

    # Define the path to the "static" folder and ensure it exists
    static_folder = 'static'
    os.makedirs(static_folder, exist_ok=True)

    # Define the CSV file path
    csv_file_path = os.path.join(static_folder, 'bizzbot_scrape.csv')

    # Write the listings to the CSV file
    with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # Write the header row
        writer.writerow(['Title', 'Description', 'Cash Flow', 'Price', 'URL'])

        # Write the data rows
        for listing in listings:
            writer.writerow([listing.title, listing.description, listing.cash_flow, listing.price, listing.url])

    print(f"CSV file saved to {csv_file_path}")