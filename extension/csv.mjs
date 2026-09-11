export function toCsv(rows) {
  const escape = (value) => {
    let text = String(value ?? '');
    // Keep listing text from being interpreted as spreadsheet formulas.
    if (/^[\s\uFEFF]*[=+@-]/u.test(text)) text = "'" + text;
    return '"' + text.replaceAll('"', '""') + '"';
  };
  const header = ['Title', 'Description', 'Cash Flow', 'Price', 'URL', 'EBITDA'];
  return '\uFEFF' + [header, ...rows.map(row => [row.title, row.description, row.cashFlow, row.price, row.url, row.ebitda])]
    .map(row => row.map(escape).join(',')).join('\r\n') + '\r\n';
}
