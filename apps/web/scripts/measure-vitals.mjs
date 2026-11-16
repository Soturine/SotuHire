// Web Vitals on the production build (CP-UX06).
//
//   npm run build && npx vite preview --host 127.0.0.1 --port 4173 --strictPort
//   node scripts/measure-vitals.mjs [baseUrl] [runs]
//
// Chromium, 1440x900, sample-data mode, onboarding already completed. For each route and CPU
// profile (no throttling, 4x slowdown via CDP) it loads the page `runs` times in a fresh context
// and reports the median of: LCP (largest-contentful-paint), CLS (sum of layout-shift entries
// without recent input, whole visit), and an interaction latency proxy (event-timing duration of
// one click on the first link of the main navigation, which is what INP measures for that click).
// Lab numbers on one machine: they compare builds, they are not field data.
import { chromium } from "@playwright/test";

const baseUrl = process.argv[2] || "http://127.0.0.1:4173";
const runs = Number(process.argv[3] || 5);
const routes = ["/", "/dashboard", "/profile", "/resume-studio", "/tracker", "/radar"];
const profiles = [
  { name: "cpu-1x", rate: 1 },
  { name: "cpu-4x", rate: 4 },
];

const observe = () => {
  window.__vitals = { lcp: 0, cls: 0, inp: 0 };
  new PerformanceObserver((list) => {
    for (const entry of list.getEntries()) window.__vitals.lcp = entry.startTime;
  }).observe({ type: "largest-contentful-paint", buffered: true });
  new PerformanceObserver((list) => {
    for (const entry of list.getEntries())
      if (!entry.hadRecentInput) window.__vitals.cls += entry.value;
  }).observe({ type: "layout-shift", buffered: true });
  new PerformanceObserver((list) => {
    for (const entry of list.getEntries())
      window.__vitals.inp = Math.max(window.__vitals.inp, entry.duration);
  }).observe({ type: "event", buffered: true, durationThreshold: 16 });
};

const median = (values) => {
  const sorted = [...values].sort((a, b) => a - b);
  return sorted[Math.floor(sorted.length / 2)];
};

const browser = await chromium.launch();
const results = [];
for (const profile of profiles) {
  for (const route of routes) {
    const samples = [];
    for (let run = 0; run < runs; run += 1) {
      const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
      await context.addInitScript(() => {
        localStorage.setItem("sotuhire.onboarding.v1.complete", "true");
        localStorage.setItem("sotuhire.api-mode", "demo");
      });
      await context.addInitScript(observe);
      const page = await context.newPage();
      const cdp = await context.newCDPSession(page);
      await cdp.send("Emulation.setCPUThrottlingRate", { rate: profile.rate });
      await page.goto(baseUrl + route, { waitUntil: "networkidle" });
      await page.waitForTimeout(1500); // demo calls simulate up to 800 ms of latency
      const link = page.getByRole("navigation").first().getByRole("link").first();
      if (await link.count()) {
        await link.click({ trial: false }).catch(() => {});
        await page.waitForTimeout(500);
      }
      samples.push(await page.evaluate(() => window.__vitals));
      await context.close();
    }
    results.push({
      profile: profile.name,
      route,
      lcp_ms: Math.round(median(samples.map((s) => s.lcp))),
      cls: Number(median(samples.map((s) => s.cls)).toFixed(4)),
      interaction_ms: Math.round(median(samples.map((s) => s.inp))),
      runs,
    });
  }
}
await browser.close();
console.log(JSON.stringify(results, null, 2));
