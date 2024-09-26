import csv
import os
import time

import requests
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


def get_driver():
    options = webdriver.ChromeOptions()
    options.headless = True
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    interval = 3


    while True:
        try:
            # Send a GET request to the URL
            response = requests.get('https://intuitive-kindness-production.up.railway.app')
            # Check if the response status code is 200 (OK)
            if response.status_code == 200:
                print("Received OK response, proceeding to initialize driver.")
                driver = webdriver.Remote('intuitive-kindness.railway.internal:4444/wd/hub', options=options)
                break
            else:
                print(f"Received response with status code {response.status_code}. Retrying...")
        except requests.RequestException as e:
            print(f"Error occurred: {e}. Retrying...")

        # Wait for the specified interval before retrying
        time.sleep(interval)

    driver.set_window_size(1920, 1080)

    return driver

# Fetch HTML content using Selenium
def get_listings_from_url(url):
    print("Trying to get from: " + url)

    chrome_prefs = {
        "profile.managed_default_content_settings.javascript": 2  # 2 means disable JavaScript
    }

    driver = get_driver()

    print("Got driver...")

    try:
        # Open the target URL
        driver.get(url)

        # Optionally wait for JavaScript to load and DOM to populate
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".listing-container"))
        )

        # Get the page source (the fully rendered HTML)
        html = driver.page_source

        elements_showcase = driver.find_elements(By.TAG_NAME, 'app-listing-showcase')
        elements_basic = driver.find_elements(By.TAG_NAME, 'app-listing-basic')
        elements_diamond = driver.find_elements(By.TAG_NAME, 'app-listing-diamond')

        elements = elements_diamond + elements_basic + elements_showcase

        listings = []

        for element in elements:
            title = element.find_element(By.CLASS_NAME, 'title').text
            description = element.find_element(By.CLASS_NAME, 'description').text
            # Use XPath to find the element with class "asking-price" that doesn't include "show-on-mobile"
            price = element.find_element(By.XPATH,
                                                 './/p[contains(@class, "asking-price") and not(contains(@class, "show-on-mobile"))]').text

            try:
                url = element.find_element(By.CLASS_NAME, 'showcase').get_attribute('href')
            except:
                try:
                    url = element.find_element(By.CLASS_NAME, 'diamond').get_attribute('href')
                except:
                    url = element.find_element(By.CLASS_NAME, 'basic').get_attribute('href')

            try:
                cash_flow = element.find_element(By.CLASS_NAME, 'cash-flow').text.replace('Cash Flow: ', '')
            except:
                cash_flow = ""
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