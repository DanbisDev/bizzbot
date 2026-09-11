// Self-contained: Chrome serializes this function into the active tab.
export function extractListings() {
  if (!['bizbuysell.com', 'www.bizbuysell.com'].includes(location.hostname)) {
    throw new Error('Open a BizBuySell search results page first.');
  }
  const text = (node) => (node?.textContent || '').replace(/\s+/g, ' ').trim();
  if (/access denied|just a moment/i.test(document.title)) {
    throw new Error('This tab is showing an access or verification page. Load the listings first.');
  }
  const cards = [...document.querySelectorAll('app-listing-diamond, app-listing-basic, app-listing-showcase')];
  const rows = [];
  const seen = new Set();
  let incomplete = 0;
  for (const card of cards) {
    const link = card.querySelector('a.diamond[href], a.basic[href], a.showcase[href]');
    const title = text(card.querySelector('.title'));
    if (!link || !title) { incomplete++; continue; }
    const url = new URL(link.getAttribute('href'), location.href);
    if (!['http:', 'https:'].includes(url.protocol) || !['bizbuysell.com', 'www.bizbuysell.com'].includes(url.hostname)) { incomplete++; continue; }
    // Franchise advertisements interspersed with search results aren't resale listings.
    if (url.pathname.startsWith('/franchise-for-sale/')) continue;
    url.hash = '';
    if (seen.has(url.href)) continue;
    seen.add(url.href);
    const earnings = text(card.querySelector('.cash-flow'));
    rows.push({
      title,
      description: text(card.querySelector('.description')),
      cashFlow: /^Cash Flow\s*:/i.test(earnings) ? earnings.replace(/^Cash Flow\s*:\s*/i, '') : '',
      price: text(card.querySelector('.asking-price')),
      url: url.href,
      ebitda: /^EBITDA\s*:/i.test(earnings) ? earnings.replace(/^EBITDA\s*:\s*/i, '') : ''
    });
  }
  if (incomplete) throw new Error('Some listings are still loading or have changed format. Wait for the page to finish and try again.');
  if (!rows.length) throw new Error('No listings found. Open a search results page and wait for the listings to load.');
  return { rows };
}
