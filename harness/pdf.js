// Exports a built deck as a PDF leave-behind: one page per slide, every step showing, vignettes on their last frame.
// Usage (from harness/): node pdf.js <built deck .html> <out .pdf>
const { chromium } = require("@playwright/test");
const path = require("path");
(async () => {
  const [html, out] = process.argv.slice(2).map(p => path.resolve(p));
  const browser = await chromium.launch({ channel: "chrome" });
  const page = await browser.newPage({ viewport: { width: 1600, height: 900 } }); // the deck's own size: headlines split into lines at this width
  await page.goto("file://" + html + "?print-pdf");
  await page.evaluate(() => new Promise(r => (window.Reveal && Reveal.isReady && Reveal.isReady() ? r() : addEventListener("load", r))));
  await page.evaluate(() => document.fonts.ready);
  await page.waitForFunction(() => document.querySelector(".pdf-page"), null, { timeout: 30000 });
  await page.waitForTimeout(1500); // late layout: SplitText, images
  // Chrome embeds every raster image at full size, once per use: shrink each to 1.5x its printed size first (keeps the PDF mailable)
  const shrunk = await page.evaluate(async () => {
    let n = 0; const cache = new Map();
    const one = async (el, src, set) => {
      const r = el.getBoundingClientRect(); if (!src || !src.startsWith("data:image/") || !r.width || !r.height) return;
      const img = new Image(); img.src = src; try { await img.decode(); } catch (e) { return; }
      const w = Math.ceil(r.width * 1.5), h = Math.ceil(r.height * 1.5); if (img.naturalWidth <= w * 1.05) return;
      const k = src.length + ":" + w + "x" + h; if (!cache.has(k)) { const c = document.createElement("canvas"); c.width = w; c.height = Math.round(w * img.naturalHeight / img.naturalWidth); c.getContext("2d").drawImage(img, 0, 0, c.width, c.height); cache.set(k, c.toDataURL("image/png")); }
      set(cache.get(k)); n++;
    };
    for (const el of document.querySelectorAll("img")) await one(el, el.getAttribute("src"), v => el.setAttribute("src", v));
    for (const el of document.querySelectorAll("image")) await one(el, el.getAttribute("href"), v => el.setAttribute("href", v));
    return n;
  });
  await page.waitForTimeout(500);
  await page.pdf({ path: out, printBackground: true, preferCSSPageSize: true });
  console.log("pdf: " + out + " (" + shrunk + " images shrunk, " + (await page.evaluate(() => document.querySelectorAll(".pdf-page").length)) + " pages)");
  await browser.close();
})();
