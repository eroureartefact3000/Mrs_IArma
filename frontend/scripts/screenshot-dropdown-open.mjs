// One-off: advance to step 2 (category), open the dropdown, screenshot.

import { chromium } from "playwright";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { mkdirSync } from "node:fs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT_DIR = resolve(__dirname, "..", "screenshots");
mkdirSync(OUT_DIR, { recursive: true });

const mockCategories = {
  categories: [
    { key: "Outdoor", label: "Outdoor", family: "Classic", enabled: true },
    { key: "PR", label: "PR", family: "Engagement", enabled: true },
    { key: "Print & Publishing", label: "Print & Publishing", family: "Classic", enabled: true },
    { key: "Design", label: "Design", family: "Craft", enabled: true },
    { key: "Direct", label: "Direct", family: "Engagement", enabled: true },
    { key: "Industry Craft", label: "Industry Craft", family: "Craft", enabled: true },
    { key: "Media", label: "Media", family: "Engagement", enabled: true },
    { key: "Brand Experience & Activation", label: "Brand Experience & Activation", family: "Experience", enabled: true },
    { key: "Health & Wellness", label: "Health & Wellness", family: "Health", enabled: true },
    { key: "Sustainable Development Goals", label: "Sustainable Development Goals", family: "Good", enabled: true },
    { key: "Entertainment Lions for Sport", label: "Entertainment Lions for Sport", family: "Entertainment", enabled: true },
    { key: "Entertainment", label: "Entertainment", family: "Entertainment", enabled: true },
    { key: "Social & Influencer", label: "Social & Influencer", family: "Engagement", enabled: true },
    { key: "Film", label: "Film", family: "Classic", enabled: true },
    { key: "Creative Strategy", label: "Creative Strategy", family: "Strategy", enabled: true },
  ],
};

const browser = await chromium.launch();
const ctx = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  deviceScaleFactor: 2,
});
const page = await ctx.newPage();

await page.route("**/api/categories", (route) =>
  route.fulfill({ contentType: "application/json", body: JSON.stringify(mockCategories) }),
);

await page.goto("http://localhost:5173", { waitUntil: "domcontentloaded" });
await page.waitForTimeout(800);

// Step 1: campaign name
await page.fill("input[type=text]", "Test campaign");
await page.keyboard.press("Enter");
await page.waitForTimeout(400);

// Step 2: click the dropdown trigger
await page.click("button[aria-haspopup='listbox']");
await page.waitForTimeout(300);

const out = resolve(OUT_DIR, "form-2-dropdown-open.png");
await page.screenshot({ path: out, fullPage: true });
console.log(`Wrote ${out}`);

await browser.close();
