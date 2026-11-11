// Usage: node frames.js page.html OUT_DIR DURATION_S FPS
const {chromium} = require('playwright'); const path = require('path');
(async () => {
  const [page, out, dur, fps] = process.argv.slice(2);
  const b = await chromium.launch();
  const p = await b.newPage({viewport: {width: 1080, height: 1920}});
  await p.goto('file://' + path.resolve(page)); await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(500);
  const n = Math.round(dur * fps);
  for (let i = 0; i < n; i++) {
    await p.evaluate(t => window.render(t), i / fps);
    await p.screenshot({path: path.join(out, String(i).padStart(5, '0') + '.jpg'), type: 'jpeg', quality: 92});
  }
  await b.close();
})();
