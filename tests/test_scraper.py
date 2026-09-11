import csv
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, PropertyMock, patch

from selenium.common.exceptions import TimeoutException, WebDriverException
import bizzbot_scraper as scraper
from app import app


def card(kind='diamond', suffix='1', cash='Cash Flow: $10,000'):
    # Based on observed live markup: mobile price can precede desktop price.
    return f'''<app-listing-{kind}><a class="{kind}" href="https://www.bizbuysell.com/business-opportunity/shop/{suffix}/">
    <span class="title h3">Shop &amp; Goods</span>
    <p class="description">A retail shop.</p>
    <p class="hide-on-desktop hide-on-tablet asking-price" style="display:none">$100,000</p>
    <p class="asking-price">$100,000 </p>
    <p class="cash-flow show-on-mobile" style="display:none">{cash}</p>
    </a></app-listing-{kind}>'''


class ScraperTests(unittest.TestCase):
    def test_all_card_types_hidden_fields_and_duplicates(self):
        html = ''.join(card(kind, str(i)) for i, kind in enumerate(('diamond', 'basic', 'showcase')))
        rows = scraper.parse_listings(html + card('diamond', '0'))
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0].title, 'Shop & Goods')
        self.assertEqual(rows[0].price, '$100,000')
        self.assertEqual(rows[0].cash_flow, '$10,000')

    def test_missing_optional_fields(self):
        html = '<app-listing-basic><a class="basic" href="https://example.com"><span class="title">Shop</span></a></app-listing-basic>'
        row = scraper.parse_listings(html)[0]
        self.assertEqual((row.description, row.price, row.cash_flow), ('', '', ''))

    def test_ebitda_is_not_mislabeled_cash_flow(self):
        self.assertEqual(scraper.parse_listings(card(cash='EBITDA: $20,000'))[0].cash_flow, 'EBITDA: $20,000')

    @patch.object(scraper, 'get_driver')
    def test_waits_for_populated_cards_without_wrapper(self, get_driver):
        driver = get_driver.return_value
        type(driver).page_source = PropertyMock(side_effect=['<app-listing-basic></app-listing-basic>', card()])
        rows = scraper.get_listings_from_url('https://www.bizbuysell.com/')
        self.assertEqual(len(rows), 1)
        driver.quit.assert_called_once()

    @patch.object(scraper, 'save_diagnostics')
    @patch.object(scraper, 'get_driver')
    def test_blocked_page_is_actionable_and_closes_driver(self, get_driver, save):
        get_driver.return_value.page_source = '<html><title>Access Denied</title><body>Denied</body></html>'
        with self.assertRaisesRegex(scraper.ScrapeError, 'access-denied'):
            scraper.get_listings_from_url('https://www.bizbuysell.com/')
        save.assert_called_once()
        get_driver.return_value.quit.assert_called_once()

    @patch.object(scraper, 'save_diagnostics')
    @patch.object(scraper, 'get_driver')
    def test_timeouts_save_diagnostics_and_close_driver(self, get_driver, save):
        for navigation in (True, False):
            with self.subTest(navigation=navigation):
                driver = Mock(page_source='<html><body>No cards</body></html>')
                if navigation:
                    driver.get.side_effect = TimeoutException()
                get_driver.return_value = driver
                with patch.dict(os.environ, {'LISTINGS_WAIT_TIMEOUT': '0'}):
                    with self.assertRaisesRegex(scraper.ScrapeError, 'timeout'):
                        scraper.get_listings_from_url('https://www.bizbuysell.com/')
                driver.quit.assert_called_once()
        self.assertEqual(save.call_count, 2)

    def test_diagnostics_written_outside_static(self):
        with tempfile.TemporaryDirectory() as folder:
            driver = Mock(page_source='<html>Failed</html>', title='Failed', current_url='https://www.bizbuysell.com/')
            with patch.dict(os.environ, {'SCRAPER_DIAGNOSTICS_DIR': folder}):
                scraper.save_diagnostics(driver)
            self.assertEqual(len(list(Path(folder).glob('*.html'))), 1)
            driver.save_screenshot.assert_called_once()

    @patch.object(scraper.webdriver, 'Remote')
    def test_driver_configuration(self, remote):
        with patch.dict(os.environ, {'SELENIUM_REMOTE_URL': 'http://selenium:4444/wd/hub'}):
            scraper.get_driver()
        self.assertEqual(remote.call_args.args[0], 'http://selenium:4444/wd/hub')
        options = remote.call_args.kwargs['options']
        self.assertIn('--headless=new', options.arguments)
        self.assertEqual(options.page_load_strategy, 'eager')

    @patch.object(scraper, 'get_listings_from_url')
    def test_csv_written_and_preserved_on_failure(self, scrape):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(scraper, '__file__', str(Path(folder) / 'bizzbot_scraper.py')):
                scrape.return_value = scraper.parse_listings(card())
                scraper.get_csv_and_save('https://www.bizbuysell.com/')
                output = Path(folder) / 'static' / 'bizzbot_scrape.csv'
                before = output.read_bytes()
                with output.open(encoding='utf-8', newline='') as file:
                    rows = list(csv.reader(file))
                self.assertEqual(rows[1][3], '$100,000')
                scrape.side_effect = scraper.ScrapeError('Blocked')
                with self.assertRaises(scraper.ScrapeError):
                    scraper.get_csv_and_save('https://www.bizbuysell.com/')
                self.assertEqual(output.read_bytes(), before)


class AppTests(unittest.TestCase):
    @patch('app.get_csv_and_save')
    def test_success_returns_download(self, save):
        response = app.test_client().post('/generate_link', json={'input': 'https://www.bizbuysell.com/utah/retail-businesses-for-sale/?q=bHQ9MzAsNDAsODA%3D'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['link'], '/download/bizzbot_scrape.csv')
        save.assert_called_once()

    @patch('app.get_csv_and_save', side_effect=scraper.ScrapeError('Access denied'))
    def test_scrape_failure_returns_json(self, save):
        response = app.test_client().post('/generate_link', json={'input': 'https://www.bizbuysell.com/'})
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json, {'error': 'Access denied'})

    @patch('app.get_csv_and_save')
    def test_bad_input_does_not_start_browser(self, save):
        for data in ({}, [], {'input': 1}, {'input': 'http://localhost/'}, {'input': 'https://www.bizbuysell.com.evil.com/'}, {'input': 'https://['}):
            with self.subTest(data=data):
                response = app.test_client().post('/generate_link', json=data)
                self.assertEqual(response.status_code, 400)
        save.assert_not_called()


if __name__ == '__main__':
    unittest.main()
