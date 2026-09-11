import assert from 'node:assert/strict';
import { toCsv } from './csv.mjs';
const csv = toCsv([{title:'Shop, "A"',description:'line 1\nline 2',cashFlow:'$10',price:'$20',url:'https://www.bizbuysell.com/business-opportunity/a/1/',ebitda:''}]);
assert.ok(csv.startsWith('\uFEFF"Title"'));
assert.ok(csv.includes('"Shop, ""A"""'));
assert.ok(csv.includes('"line 1\nline 2"'));
assert.ok(csv.endsWith('\r\n'));
for (const title of ['=1+1','  +SUM(A1:A2)','@SUM(1)','-1+1','\t=1']) assert.ok(toCsv([{title}]).includes('"\''+title+'"'));
console.log('CSV quoting, Unicode BOM, newlines and formula protection passed.');
