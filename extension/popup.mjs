import { extractListings } from './extract.mjs';
import { toCsv } from './csv.mjs';
const button = document.getElementById('export');
const status = document.getElementById('status');
button.addEventListener('click', async () => {
  button.disabled = true;
  status.className = '';
  status.textContent = 'Reading the listings in this tab…';
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab?.id) throw new Error('Select a BizBuySell search results tab first.');
    let hostname;
    try { hostname = new URL(tab.url).hostname; } catch { /* unsupported tab */ }
    if (!['bizbuysell.com', 'www.bizbuysell.com'].includes(hostname)) throw new Error('Open a BizBuySell search results page first.');
    const results = await chrome.scripting.executeScript({ target: { tabId: tab.id }, func: extractListings });
    const data = results[0]?.result;
    if (!data?.rows?.length) throw new Error('Could not read listings. Wait for the page to finish loading and try again.');
    const stamp = new Date().toISOString().replace(/[:.]/g, '-');
    await chrome.downloads.download({
      url: 'data:text/csv;charset=utf-8,' + encodeURIComponent(toCsv(data.rows)),
      filename: `bizzbot-${stamp}.csv`,
      conflictAction: 'uniquify'
    });
    status.textContent = `Download started: ${data.rows.length} listings. Check Chrome Downloads for your CSV.`;
  } catch (error) {
    status.className = 'error';
    status.textContent = error.message || 'Could not export this page. Please try again.';
  } finally { button.disabled = false; }
});
