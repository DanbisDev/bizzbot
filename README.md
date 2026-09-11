# Bizzbot

Install `requirements.txt`, run `python app.py`, and submit a BizBuySell search
URL. The export contains the listings on that page (no automatic pagination).

## Selenium deployment

Run Selenium Standalone Chrome as a separate service reachable by the app.
`SELENIUM_REMOTE_URL` defaults to
`http://intuitive-kindness.railway.internal:4444/wd/hub`. Set it to the full
HTTP URL of your Grid if the service name changes. Before creating a session,
the app polls Grid's status endpoint for `value.ready: true`, for up to
`SELENIUM_STARTUP_TIMEOUT` seconds (default 30, plus any in-flight request).
Status requests have a 3-second socket timeout.

If the original Railway Grid is unavailable, the app first attempts one public
wake request. Set `SELENIUM_WAKE_URL` to your Selenium service's public URL
if it changes, or to an empty string to disable waking. Custom Grid URLs do
not wake the original service by default. A public HTTP 200 does not establish
Grid readiness or verify that BizBuySell loaded.

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
distinguished. Subsequent deployment logs confirmed an `Access Denied` page
for `/utah-businesses-for-sale/?q=bHQ9MzAsNDAsODA%3D`, separately from an
initial refused Selenium connection. If diagnostics show access denial or human verification, a
longer wait will not fix it: check permitted access with BizBuySell from the
deployment. This app does not bypass access controls.

## Tests

Run `python -m unittest discover -s tests -v`. Tests use rendered HTML fixtures
and simulated browser failures; they do not require Railway or a live Grid.
