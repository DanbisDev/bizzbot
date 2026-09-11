# Bizzbot

Install `requirements.txt`, run `python app.py`, and submit a BizBuySell search
URL. The export contains the listings on that page (no automatic pagination).

## Selenium deployment

Run Selenium Standalone Chrome as a separate service reachable by the app.
`SELENIUM_REMOTE_URL` defaults to
`http://intuitive-kindness.railway.internal:4444/wd/hub`. Set it to the full
HTTP URL of your Grid if the service name changes. The app connects directly
to Grid; a successful HTTP response from its public homepage does not verify
that BizBuySell loaded in the browser.

`PAGE_LOAD_TIMEOUT` and `LISTINGS_WAIT_TIMEOUT` default to 30 seconds each.
The latter waits for populated listing cards, rather than their outer wrapper.
Keep JavaScript enabled: the search results are rendered by Angular.

On failure, the app returns a readable JSON error (shown in the UI) and saves
HTML and a screenshot under `diagnostics/`, outside the public static folder.
Set `SCRAPER_DIAGNOSTICS_DIR` to a persistent private volume if needed. Logs
include the diagnostic ID, page title, and actual browser URL. Remove old
diagnostic files periodically.

The reported deployment traceback shows a successful Chrome session followed
by a 10-second element timeout. The original `.listing-container` selector was
still present when checked on the supplied Utah URL. Without the failed
deployment's HTML, a slow response and a blocked/challenge page cannot be
distinguished. If diagnostics show access denial or human verification, a
longer wait will not fix it: check permitted access with BizBuySell from the
deployment. This app does not bypass access controls.

## Tests

Run `python -m unittest discover -s tests -v`. Tests use rendered HTML fixtures
and simulated browser failures; they do not require Railway or a live Grid.
