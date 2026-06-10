// Headless screenshot utility for visual iteration on the Mrs Airma frontend.
// Usage:
//   pnpm exec node scripts/screenshot.mjs form [step]    → form step 1..5
//   pnpm exec node scripts/screenshot.mjs loading        → loading view (mocked slow API)
//   pnpm exec node scripts/screenshot.mjs result [tier]  → result view (mocked, tier: GP/Gold/Silver/Bronze/No Medal)
//   pnpm exec node scripts/screenshot.mjs error          → error view (mocked 500)
//
// Output: screenshots/<view>[-<step>].png

import { chromium } from "playwright";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { mkdirSync, readFileSync } from "node:fs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT_DIR = resolve(__dirname, "..", "screenshots");
mkdirSync(OUT_DIR, { recursive: true });

const view = process.argv[2] || "form";
const arg = process.argv[3];

const BASE_URL = process.env.FRONTEND_URL || "http://localhost:5173";

// Mock responses for the API endpoints.
const mockCategories = {
  categories: [
    { key: "Outdoor", label: "Outdoor", family: "Classic", enabled: true },
    { key: "PR", label: "PR", family: "Engagement", enabled: true },
    { key: "Print & Publishing", label: "Print & Publishing", family: "Classic", enabled: true },
  ],
};

function buildMockResult(tier = "Gold") {
  const tierData = {
    "Grand Prix": { label: "GRAND PRIX LION", score: 92, verdict: "The stars align. Your campaign will carry the highest honour." },
    Gold: { label: "GOLD LION", score: 87, verdict: "The stars bow. Your campaign will carry gold." },
    Silver: { label: "SILVER LION", score: 72, verdict: "A promising spark. Silver opens its arms to you." },
    Bronze: { label: "BRONZE LION", score: 58, verdict: "The promise of a flicker. Still to be polished." },
    "No Medal": { label: "NO LION", score: 34, verdict: "The stars remain silent. Will you return next year?" },
  };
  const t = tierData[tier] || tierData.Gold;
  return {
    evaluation_id: "deadbeef-cafe-1234-5678-90abcdef0000",
    elapsed_seconds: 42.7,
    tier_prediction: {
      predicted_tier: tier,
      tier_label: t.label,
      tier_probabilities: { "Grand Prix": 0.05, Gold: 0.55, Silver: 0.25, Bronze: 0.1, "No Medal": 0.05 },
      confidence: "medium",
      score_percent: t.score,
      mystic_verdict: t.verdict,
      axes: [
        { key: "idea", label: "Creative Idea", score: 92, weight: 0.35 },
        { key: "strategy", label: "Strategy", score: 84, weight: 0.1 },
        { key: "execution", label: "Execution", score: 88, weight: 0.3 },
        { key: "impact", label: "Impact & Results", score: 79, weight: 0.25 },
      ],
      presages: [
        { type: "aesthetic", kind: "favorable", title: "Polished Board", detail: "Readable composition, careful hierarchy.", malus_pct: 0 },
        { type: "client", kind: "favorable", title: "International Client", detail: "Brand recognised beyond its borders.", malus_pct: 0 },
        { type: "network", kind: "favorable", title: "Agency of the Inner Circle", detail: "Publicis network — favorable presage.", malus_pct: 0 },
      ],
      synthesis: "Memorable idea and clean execution; the impact case is strong on cultural pickup but light on hard business numbers — the cited percentages aren't anchored to absolute bases, which slightly caps the jury read.",
    },
  };
}

const browser = await chromium.launch();
const ctx = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  deviceScaleFactor: 2,
});
const page = await ctx.newPage();

// Mock the API. Categories endpoint always works. /api/evaluate behaviour varies by view.
await page.route("**/api/categories", (route) =>
  route.fulfill({ contentType: "application/json", body: JSON.stringify(mockCategories) }),
);

if (view === "result") {
  const tier = arg || "Gold";
  await page.route("**/api/evaluate", async (route) => {
    await new Promise((r) => setTimeout(r, 200)); // tiny fake latency
    route.fulfill({ contentType: "application/json", body: JSON.stringify(buildMockResult(tier)) });
  });
} else if (view === "error") {
  await page.route("**/api/evaluate", (route) =>
    route.fulfill({
      status: 500,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Internal server error: vision model timed out" }),
    }),
  );
} else if (view === "loading") {
  // Never resolve the request — we'll screenshot mid-flight
  await page.route("**/api/evaluate", () => {
    /* hang */
  });
}

await page.goto(BASE_URL, { waitUntil: "domcontentloaded" });
await page.waitForTimeout(800); // fonts settle

async function advanceToFinalStep() {
  const tinyPng = Buffer.from(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGNkYGD4DwAB/QH/eHcA/QAAAABJRU5ErkJggg==",
    "base64",
  );
  // Step 1
  await page.fill("input[type=text]", "Test campaign");
  await page.keyboard.press("Enter");
  await page.waitForTimeout(300);
  // Step 2
  await page.keyboard.press("Enter");
  await page.waitForTimeout(300);
  // Step 3
  await page.fill("input[type=text]", "Test client");
  await page.keyboard.press("Enter");
  await page.waitForTimeout(300);
  // Step 4
  await page.fill("input[type=text]", "Test agency");
  await page.keyboard.press("Enter");
  await page.waitForTimeout(300);
  // Step 5: file upload
  await page.setInputFiles('input[type="file"]', {
    name: "board.png",
    mimeType: "image/png",
    buffer: tinyPng,
  });
  await page.waitForTimeout(200);
}

if (view === "form") {
  const step = parseInt(arg || "1", 10);
  if (step > 1) {
    await page.fill("input[type=text]", "Test campaign");
    await page.keyboard.press("Enter");
    if (step > 2) {
      await page.waitForTimeout(300);
      await page.keyboard.press("Enter");
    }
    if (step > 3) {
      await page.waitForTimeout(300);
      await page.fill("input[type=text]", "Test client");
      await page.keyboard.press("Enter");
    }
    if (step > 4) {
      await page.waitForTimeout(300);
      await page.fill("input[type=text]", "Test agency");
      await page.keyboard.press("Enter");
    }
    await page.waitForTimeout(300);
  }
} else if (view === "loading") {
  await advanceToFinalStep();
  await page.click("button:has-text('Consult the oracle')");
  await page.waitForTimeout(800); // let the loading view render fully
} else if (view === "result" || view === "error") {
  await advanceToFinalStep();
  await page.click("button:has-text('Consult the oracle')");
  // Wait for either the result page or error page to render
  await page.waitForTimeout(1500);
}

const filename = view === "form"
  ? `form-${arg || 1}.png`
  : view === "result" && arg
    ? `result-${arg.replace(/\s+/g, "-").toLowerCase()}.png`
    : `${view}.png`;
const out = resolve(OUT_DIR, filename);
await page.screenshot({ path: out, fullPage: true });
console.log(`Wrote ${out}`);

await browser.close();
