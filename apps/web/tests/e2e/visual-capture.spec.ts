import { expect, test, type Page } from "@playwright/test";
import fs from "node:fs/promises";
import path from "node:path";

const screenshotsDir = path.resolve(process.cwd(), "../../docs/assets/screenshots");

const shots: Array<{
  path: string;
  file: string;
  prepare?: (page: Page) => Promise<void>;
}> = [
  { path: "/", file: "sotuhire-v1.7-web-home.png" },
  { path: "/dashboard", file: "sotuhire-v1.7-web-dashboard.png" },
  {
    path: "/sources",
    file: "sotuhire-v1.7-web-sources-inbox.png",
    prepare: async (page) => {
      await page.locator("#opportunity-inbox").scrollIntoViewIfNeeded();
    },
  },
  {
    path: "/sources",
    file: "sotuhire-v1.7-web-import-csv.png",
    prepare: async (page) => {
      await page.locator("[data-testid='source-csv-input']").scrollIntoViewIfNeeded();
    },
  },
  {
    path: "/sources",
    file: "sotuhire-v1.7-web-import-details.png",
    prepare: async (page) => {
      await page.locator("[data-testid='source-inbox-row']").first().scrollIntoViewIfNeeded();
    },
  },
  {
    path: "/match",
    file: "sotuhire-v1.7-web-analysis.png",
    prepare: clickDemo,
  },
  {
    path: "/tracker",
    file: "sotuhire-v1.7-web-kanban-source.png",
  },
  {
    path: "/intelligence",
    file: "sotuhire-v1.7-web-intelligence.png",
  },
  {
    path: "/sources",
    file: "sotuhire-v1.7-web-extension-history.png",
    prepare: async (page) => {
      await page.locator("#local-extension").scrollIntoViewIfNeeded();
    },
  },
  {
    path: "/settings",
    file: "sotuhire-v1.7-web-settings-ai.png",
    prepare: async (page) => {
      await expect(page.getByText("IA e Providers")).toBeVisible();
    },
  },
];

test.describe.configure({ mode: "serial" });

test("captures standardized v1.7 screenshots", async ({ page }, testInfo) => {
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

async function clickDemo(page: Page) {
  await page
    .getByRole("button", { name: /Rodar demo/i })
    .first()
    .click();
  await page.waitForLoadState("networkidle").catch(() => undefined);
  await page.waitForTimeout(700);
}
