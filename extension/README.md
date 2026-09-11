# Bizzbot Chrome extension

## Install

1. Extract the ZIP into a permanent folder (not the ZIP preview).
2. Open chrome://extensions in Chrome.
3. Turn on Developer mode in the top right.
4. Click Load unpacked and select the folder containing manifest.json.
5. Pin Bizzbot CSV Export using Chrome's Extensions puzzle-piece menu.

## Export

Open your BizBuySell search results normally and wait for the listing cards to
load. Click Bizzbot, then Download CSV. Chrome saves a timestamped CSV to your
normal download location (or asks where if that is your Chrome setting).

Only listing cards loaded on the current page are exported. The total result
count can span multiple pages. Navigate to the next page yourself and export
again. Franchise advertisements and duplicate URLs are excluded. This extension
does not scroll, navigate, request listings from a server, or read cookies.

Columns: Title, Description, Cash Flow, Price, URL, EBITDA. Missing optional
fields stay blank; EBITDA is not substituted for cash flow. UTF-8 with BOM works
with Excel; CSV quotes, commas and line endings are escaped. Potential formula
text is prefixed with an apostrophe for spreadsheet safety.

## Permissions and privacy

activeTab and scripting allow reading the current page when you invoke Bizzbot.
downloads allows saving the generated CSV. No background worker, permanent
website access, account, API key, analytics or remote service is used. All data
stays in your browser and the downloaded file. The Railway app is not needed.

If the tab shows Access Denied, a verification page, or no listing cards, open
the search normally before exporting. If the site's markup changes, the
extension may need an update. Keep the unpacked folder in place; use Reload in
chrome://extensions after replacing its files with an updated version.
