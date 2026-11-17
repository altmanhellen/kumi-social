// Render every <slug>.svg in a week folder to <slug>.png (1080x1350) for publishing.
// Usage: node pipeline/svg2png.js weeks/<week> [slug ...]
const {chromium} = require('playwright'); const fs = require('fs'); const path = require('path');
(async () => {
  const [dir, ...only] = process.argv.slice(2);
  const names = only.length ? only : fs.readdirSync(dir).filter(f => f.endsWith('.svg')).map(f => f.slice(0, -4));
  const b = await chromium.launch(); const p = await b.newPage({viewport: {width: 1080, height: 1350}});
  for (const n of names) {
    await p.goto('file://' + path.resolve(dir, n + '.svg')); await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(300);
    await p.screenshot({path: path.resolve(dir, n + '.png'), type: 'png'}); console.log('png', n);
  }
  await b.close();
})();
