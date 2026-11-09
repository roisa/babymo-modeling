// usage: node tests/shot.js URL OUT.png  -> waits for document.title READY, prints window.__out
const { chromium } = require('playwright');
(async () => {
  const [url, out] = process.argv.slice(2);
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 900, height: 600 } });
  const logs = []; p.on('console', m => logs.push(m.type() + ': ' + m.text())); p.on('pageerror', e => logs.push('PAGEERROR ' + e.message));
  await p.goto(url);
  try { await p.waitForFunction(() => document.title === 'READY' || window.__fail, null, { timeout: 120000 }); } catch (e) { logs.push('TIMEOUT'); }
  console.log(JSON.stringify(await p.evaluate(() => window.__out || null)));
  await p.screenshot({ path: out }); console.log(logs.filter(l => !l.includes('GPU stall')).slice(0, 15).join('\n'));
  await b.close();
})();
