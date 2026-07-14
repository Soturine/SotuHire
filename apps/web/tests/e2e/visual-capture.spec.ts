import { test, type Page } from "@playwright/test";
import fs from "node:fs/promises";
import path from "node:path";

const screenshotsDir = path.resolve(process.cwd(), "../../docs/assets/screenshots");

const shots: Array<{
  path: string;
  file: string;
  prepare?: (page: Page) => Promise<void>;
}> = [
  {
    path: "/ai-quality",
    file: "sotuhire-web-ai-quality-summary.png",
  },
  {
    path: "/ai-quality",
    file: "sotuhire-web-ai-quality-provider-comparison.png",
    prepare: async (page) => {
      await page.getByRole("tab", { name: "Providers" }).click();
    },
  },
  {
    path: "/ai-quality",
    file: "sotuhire-web-ai-quality-prompts.png",
    prepare: async (page) => {
      await page.getByRole("tab", { name: "Prompts" }).click();
    },
  },
  {
    path: "/ai-quality",
    file: "sotuhire-web-ai-quality-benchmarks.png",
    prepare: async (page) => {
      await page.getByRole("tab", { name: "Benchmarks" }).click();
    },
  },
  {
    path: "/ai-quality",
    file: "sotuhire-web-ai-quality-feedback.png",
    prepare: async (page) => {
      await page.getByRole("tab", { name: "Feedback", exact: true }).click();
    },
  },
  {
    path: "/ai-quality",
    file: "sotuhire-web-ai-quality-outcomes.png",
    prepare: async (page) => {
      await page.getByRole("tab", { name: "Resultados profissionais" }).click();
    },
  },
  {
    path: "/ai-quality",
    file: "sotuhire-web-ai-quality-trace-privacy.png",
    prepare: async (page) => {
      await page.getByRole("tab", { name: "Privacidade" }).click();
    },
  },
  {
    path: "/radar",
    file: "sotuhire-v1.8.1-web-radar-ai-wishlist.png",
    prepare: async (page) => {
      await page.locator("#radar-ai-wishlist").scrollIntoViewIfNeeded();
    },
  },
  {
    path: "/radar",
    file: "sotuhire-v1.8-web-radar-summary.png",
    prepare: async (page) => {
      await page.locator("#radar-summary").scrollIntoViewIfNeeded();
    },
  },
  {
    path: "/radar",
    file: "sotuhire-v1.8-web-radar-wishlist.png",
    prepare: async (page) => {
      await page.locator("#radar-wishlist").scrollIntoViewIfNeeded();
    },
  },
  {
    path: "/radar",
    file: "sotuhire-v1.8-web-radar-sources.png",
    prepare: async (page) => {
      await page.locator("#radar-sources").scrollIntoViewIfNeeded();
    },
  },
  {
    path: "/radar",
    file: "sotuhire-v1.8-web-radar-results.png",
    prepare: async (page) => {
      await page.locator("#radar-results").scrollIntoViewIfNeeded();
    },
  },
  {
    path: "/radar",
    file: "sotuhire-v1.8-web-radar-alerts.png",
    prepare: async (page) => {
      await page.locator("#radar-alerts").scrollIntoViewIfNeeded();
    },
  },
  {
    path: "/sources",
    file: "sotuhire-v1.8-web-inbox-radar.png",
    prepare: async (page) => {
      await page.locator("#opportunity-inbox").scrollIntoViewIfNeeded();
    },
  },
  {
    path: "/tracker",
    file: "sotuhire-v1.8-web-kanban-radar.png",
    prepare: async (page) => {
      await page.getByTestId("kanban-card").first().waitFor();
    },
  },
];

test.describe.configure({ mode: "serial" });

test("captures standardized v1.8 screenshots", async ({ page }, testInfo) => {
  test.skip(
    process.env.CAPTURE_VISUALS !== "1",
    "Set CAPTURE_VISUALS=1 to generate screenshot assets.",
  );
  test.skip(testInfo.project.name !== "chromium", "Screenshots are captured once in Chromium.");
  await fs.mkdir(screenshotsDir, { recursive: true });
  await page.setViewportSize({ width: 1440, height: 1000 });

  for (const shot of shots) {
    await page.goto(shot.path);
    if (shot.prepare) await shot.prepare(page);
    await page.waitForTimeout(700);
    await page.screenshot({
      path: path.join(screenshotsDir, shot.file),
      fullPage: false,
    });
  }
});
