// Render the block diagram SVGs to PNG at twice their size.
// Usage: node svg_to_png.js    (needs Playwright with Chromium)
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 940, height: 965 }, deviceScaleFactor: 2 });
  for (const name of ['block-diagram-with-switch', 'block-diagram-without-switch']) {
    const svg = fs.readFileSync(path.join(__dirname, name + '.svg'), 'utf8');
    await page.setContent('<body style="margin:0">' + svg + '</body>');
    await (await page.$('svg')).screenshot({ path: path.join(__dirname, name + '.png') });
    console.log('wrote', name + '.png');
  }
  await browser.close();
})();
