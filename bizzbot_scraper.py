import csv
import logging
import os
import time
from pathlib import Path
from uuid import uuid4

from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support.wait import WebDriverWait
from urllib3.exceptions import HTTPError

logger = logging.getLogger(__name__)
CARD_SELECTOR = 'app-listing-diamond, app-listing-basic, app-listing-showcase'
DEFAULT_REMOTE_URL = 'http://intuitive-kindness.railway.internal:4444/wd/hub'
CONNECTION_ERRORS = (WebDriverException, HTTPError, OSError)


class ScrapeError(Exception):
    """An upstream failure that can be shown to the user."""


class Listing:
    def __init__(self, title: str, description: str, cash_flow: str, price: str, url: str):
        self.title = title
        self.description = description
        self.cash_flow = cash_flow
        self.price = price
        self.url = url

    def __repr__(self):
        return f'Listing: {self.title} ({self.url})'


def wait_for_selenium(remote_url):
    """Wait for Grid readiness, waking the original Railway service if needed."""
    timeout = float(os.environ.get('SELENIUM_STARTUP_TIMEOUT', '30'))
    deadline = time.monotonic() + timeout
    status_url = remote_url.rstrip('/') + '/status'
    wake_url = os.environ.get('SELENIUM_WAKE_URL',
        'https://intuitive-kindness-production.up.railway.app'
        if remote_url == DEFAULT_REMOTE_URL else '')
    wake_attempted = False
    last_error = None
    while time.monotonic() < deadline:
        try:
            with requests.get(status_url, timeout=3) as response:
                response.raise_for_status()
                payload = response.json()
            if isinstance(payload, dict) and isinstance(payload.get('value'), dict):
                if payload['value'].get('ready') is True:
                    return
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
        if wake_url and not wake_attempted:
            wake_attempted = True
            try:
                # The public request can wake the service, but only Grid's
                # private status response can establish readiness.
                with requests.get(wake_url, timeout=3):
                    pass
            except requests.RequestException:
                logger.warning('Selenium wake request did not complete')
        remaining = deadline - time.monotonic()
        if remaining > 0:
            time.sleep(min(1, remaining))
    raise ScrapeError(
        'Selenium is not ready. Check that the Selenium service is running '
        'and SELENIUM_REMOTE_URL points to its listening port.'
    ) from last_error


def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    # DOM content is sufficient; third-party images/ads need not finish loading.
    options.page_load_strategy = 'eager'
    remote_url = os.environ.get(
        'SELENIUM_REMOTE_URL',
        DEFAULT_REMOTE_URL,
    )
    wait_for_selenium(remote_url)
    try:
        driver = webdriver.Remote(remote_url, options=options)
    except CONNECTION_ERRORS as exc:
        raise ScrapeError('Could not connect to Selenium. Check that the Selenium service is running.') from exc
    try:
        driver.set_page_load_timeout(float(os.environ.get('PAGE_LOAD_TIMEOUT', '30')))
    except CONNECTION_ERRORS as exc:
        try:
            driver.quit()
        except CONNECTION_ERRORS:
            logger.warning('Could not close the Selenium session', exc_info=True)
        raise ScrapeError('Selenium disconnected while configuring the browser. Please try again.') from exc
    return driver


def parse_listings(html):
    """Read text from rendered HTML, including fields hidden at this viewport."""
    soup = BeautifulSoup(html, 'html.parser')
    cards = soup.select(CARD_SELECTOR)
    listings = []
    seen = set()
    for card in cards:
        def field(selector):
            node = card.select_one(selector)
            return node.get_text(' ', strip=True) if node else ''

        link = card.select_one('a.diamond[href], a.basic[href], a.showcase[href]')
        title = field('.title')
        if not title or not link:
            # Angular may have inserted a card before its data is ready.
            return []
        url = link['href']
        if url in seen:
            continue
        seen.add(url)
        cash_flow = field('.cash-flow')
        if cash_flow.startswith('Cash Flow:'):
            cash_flow = cash_flow[len('Cash Flow:'):].strip()
        listings.append(Listing(title, field('.description'), cash_flow,
                                field('.asking-price'), url))
    return listings


def check_page(html):
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.title.get_text(' ', strip=True).lower() if soup.title else ''
    body = soup.body.get_text(' ', strip=True).lower() if soup.body else ''
    if ('access denied' in title or 'just a moment' in title
            or "you don't have permission to access" in body
            or 'verify you are human' in body
            or 'verify that you are human' in body):
        raise ScrapeError(
            'BizBuySell returned an access-denied or verification page to the scraper. '
            'No CSV was generated. Check the scraper logs and access from the deployment.'
        )


def save_diagnostics(driver):
    """Keep failure evidence outside the publicly served static directory."""
    diagnostic_id = uuid4().hex
    try:
        folder = Path(os.environ.get('SCRAPER_DIAGNOSTICS_DIR', 'diagnostics'))
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f'{diagnostic_id}.html').write_text(driver.page_source, encoding='utf-8')
        driver.save_screenshot(str(folder / f'{diagnostic_id}.png'))
        logger.error('Scrape failed: id=%s title=%r url=%s diagnostics=%s',
                     diagnostic_id, driver.title, driver.current_url, folder)
    except Exception:
        logger.exception('Could not save scrape diagnostics: %s', diagnostic_id)


def get_listings_from_url(url):
    driver = get_driver()
    try:
        driver.get(url)

        def listings_ready(browser):
            html = browser.page_source
            check_page(html)
            return parse_listings(html) or False

        return WebDriverWait(
            driver, float(os.environ.get('LISTINGS_WAIT_TIMEOUT', '30'))
        ).until(listings_ready)
    except TimeoutException as exc:
        save_diagnostics(driver)
        raise ScrapeError(
            'BizBuySell did not load listing data before the timeout. '
            'No CSV was generated. Try again; if this persists, check the saved '
            'page and screenshot in the scraper diagnostics.'
        ) from exc
    except ScrapeError:
        save_diagnostics(driver)
        raise
    except CONNECTION_ERRORS as exc:
        save_diagnostics(driver)
        raise ScrapeError('The browser could not load BizBuySell. Please try again.') from exc
    finally:
        try:
            driver.quit()
        except CONNECTION_ERRORS:
            logger.warning('Could not close the Selenium session', exc_info=True)


def get_csv_and_save(url):
    listings = get_listings_from_url(url)
    if not listings:
        raise ScrapeError('No listings were found. No CSV was generated.')
    static_folder = Path(__file__).parent / 'static'
    static_folder.mkdir(exist_ok=True)
    csv_file_path = static_folder / 'bizzbot_scrape.csv'
    # Replace only a fully written file; failed scrapes preserve the last export.
    temporary_path = static_folder / f'.{uuid4().hex}.csv'
    try:
        with temporary_path.open(mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Title', 'Description', 'Cash Flow', 'Price', 'URL'])
            for listing in listings:
                writer.writerow([listing.title, listing.description, listing.cash_flow,
                                 listing.price, listing.url])
        os.replace(temporary_path, csv_file_path)
    finally:
        temporary_path.unlink(missing_ok=True)
    logger.info('CSV file saved to %s', csv_file_path)
