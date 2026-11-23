// Story deck harness: one screenshot per scene and key press, compared with refs/<deck>/.
const { defineConfig } = require("@playwright/test");

module.exports = defineConfig({
  testDir: ".",
  testMatch: "deck.spec.js",
  timeout: 600000,
  workers: 1,
  reporter: [["list"]],
  snapshotPathTemplate: "{testDir}/refs/{arg}{ext}",
  expect: {
    // Two captures of an unchanged deck differ by 0 to 1 pixels. A ratio of 0.1% (921 px) let a four-letter footer
    // label change through (2026-11-22), so the limit is an absolute pixel count: Chrome noise passes, words don't.
    toHaveScreenshot: { maxDiffPixels: 20, threshold: 0.2 },
  },
  use: {
    // The installed Google Chrome (no browser download). A Chrome update can move pixels slightly: refs/CHROME
    // records the version the references were taken with, so a failure right after an update is easy to read.
    channel: "chrome",
    viewport: { width: 1280, height: 720 },
    deviceScaleFactor: 1,
  },
});
