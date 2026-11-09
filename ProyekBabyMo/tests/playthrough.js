// Plays the whole game like a child would (taps every button; tries answers until right) and screenshots each job.
// usage: node tests/playthrough.js URL OUTDIR
const { chromium } = require('playwright');
(async () => {
  const [url, out] = process.argv.slice(2);
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 1000, height: 640 } });
  const errs = [];
  p.on('pageerror', e => errs.push('PAGEERROR ' + e.message));
  p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await p.goto(url);
  await p.waitForFunction(() => window.__ready || window.__fail, null, { timeout: 180000 });
  const fail = await p.evaluate(() => window.__fail);
  if (fail) console.log('FAIL', fail);
  await p.screenshot({ path: `${out}/00_start.png` });
  await p.click('#go');
  const t0 = Date.now(); let lastLevel = -1, shots = 0, finale = false;
  while (Date.now() - t0 < 900000) {
    const st = await p.evaluate(() => ({
      lvl: window.__game.game.level, say: document.getElementById('sayTxt').textContent,
      btns: [...document.querySelectorAll('#dock button')].map(b => ({ cls: b.className, dis: b.disabled })) }));
    if (st.lvl !== lastLevel) { lastLevel = st.lvl; await p.waitForTimeout(6000); await p.screenshot({ path: `${out}/L${st.lvl + 1}_a.png` }); }
    if (/Alhamdulillah! Taman/.test(st.say) && !finale) { finale = true; await p.waitForTimeout(5000); await p.screenshot({ path: `${out}/finale.png` }); break; }
    const live = st.btns.findIndex(x => !x.dis);
    if (live >= 0) {
      const cls = st.btns[live].cls; const btns = await p.$$('#dock button');
      if (cls.includes('num') || cls.includes('chip')) {
        for (const bt of btns) {
          const before = await p.evaluate(() => document.getElementById('sayTxt').textContent);
          await bt.click().catch(() => {}); await p.waitForTimeout(700);
          const moved = await p.evaluate(b4 => !!document.querySelector('#dock .yes') || document.querySelectorAll('#dock button').length === 0 || (document.getElementById('sayTxt').textContent !== b4 && !/coba|Try|bukan|not/i.test(document.getElementById('sayTxt').textContent)), before);
          if (moved) { if (shots < 40) { await p.waitForTimeout(4500); await p.screenshot({ path: `${out}/s${String(++shots).padStart(2, '0')}_L${st.lvl + 1}_pick.png` }); } break; }
        }
      } else {
        await btns[live].click().catch(() => {});
        if (shots < 40) { await p.waitForTimeout(2500); await p.screenshot({ path: `${out}/s${String(++shots).padStart(2, '0')}_L${st.lvl + 1}.png` }); }
      }
    }
    await p.waitForTimeout(500);
  }
  console.log('finished', finale, 'seconds', Math.round((Date.now() - t0) / 1000));
  console.log(errs.slice(0, 10).join('\n'));
  await b.close();
})();
