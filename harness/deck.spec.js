// Walks a built deck key press by key press and compares each settled state with its reference screenshot.
// Decks: harness/decks.json (built into harness/.out/<name>.html by check.py), or one deck via DECK_NAME + DECK_HTML.
const { test, expect } = require("@playwright/test");
const path = require("path");
const fs = require("fs");

const decks = process.env.DECK_HTML
  ? [{ name: process.env.DECK_NAME || "deck", html: path.resolve(process.env.DECK_HTML) }]
  : Object.keys(JSON.parse(fs.readFileSync(path.join(__dirname, "decks.json"), "utf8"))).map(name => ({ name, html: path.join(__dirname, ".out", name + ".html") }));

// Wait until every GSAP tween has finished (the global timeline drops finished children), then one more frame.
async function settle(page) {
  await page.waitForFunction(() => !window.gsap || gsap.globalTimeline.getChildren(true, true, false).length === 0, null, { timeout: 8000 }).catch(() => {});
  await page.evaluate(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))));
}

async function open(page, deck, role) {
  await page.addInitScript(r => { try { sessionStorage.setItem("deck-role", r); localStorage.setItem("prompter-learn", "off"); } catch (e) {} }, role);
  const errors = [];
  page.on("pageerror", e => errors.push(String(e)));
  page.on("console", m => { if (m.type() === "error") errors.push(m.text()); });
  await page.goto("file://" + deck.html);
  await page.evaluate(() => document.fonts.ready);
  return errors;
}

for (const deck of decks) {
  test.describe(deck.name, () => {
    test("every scene and key press matches its reference", async ({ page }) => {
      expect(fs.existsSync(deck.html), `built deck missing: ${deck.html}`).toBeTruthy();
      const errors = await open(page, deck, "deck");
      await page.waitForFunction(() => window.Reveal && Reveal.isReady(), null, { timeout: 20000 }).catch(() => { throw new Error("the deck never started: " + errors.join(" | ")); });
      await page.mouse.move(640, 360); // away from the presenter tools corner
      let prev = null;
      for (let n = 0; ; n++) {
        expect(n, "too many key presses; the deck never reached its end").toBeLessThan(400);
        await settle(page);
        const st = await page.evaluate(() => ({ h: Reveal.getState().indexh, scene: Reveal.getCurrentSlide().dataset.scene, f: (Reveal.getState().indexf ?? -1) + 1, end: Reveal.isLastSlide() && !Reveal.availableFragments().next }));
        expect(`${st.h}.${st.f}`, `a key press didn't advance the deck (${errors.join(" | ")})`).not.toBe(prev);
        prev = `${st.h}.${st.f}`;
        const name = `${String(n).padStart(3, "0")}-${st.scene.replace(/\//g, "_")}-${st.f}.png`;
        await expect.soft(page).toHaveScreenshot([deck.name, name], { animations: "disabled", mask: [page.locator(".reveal section.present video, #presenter video")] });
        if (st.end) break;
        await page.keyboard.press("ArrowRight");
      }
      expect(errors, "console errors while presenting").toEqual([]);
    });

    test("teleprompter follows speech on the notes screen", async ({ page }) => {
      const errors = await open(page, deck, "notes");
      await page.waitForFunction(() => window.__tele);
      const before = await page.evaluate(() => __tele.cursor);
      const phrase = await page.evaluate(() => { const first = Object.values(NOTES)[0][0].items.find(i => i.t === "p"); return first.x.split(" ").slice(0, 12).join(" "); });
      await page.evaluate(p => __tele.say(p, true), phrase);
      expect(await page.evaluate(() => __tele.cursor)).toBeGreaterThan(before);
      expect(errors).toEqual([]);
    });
  });
}
