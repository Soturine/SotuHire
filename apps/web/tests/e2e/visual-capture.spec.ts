import { expect, test, type Page } from "@playwright/test";
import fs from "node:fs/promises";
import path from "node:path";

const screenshotsDir = path.resolve(process.cwd(), "../../docs/assets/screenshots");

const shots: Array<{
  path: string;
  file: string;
  prepare?: (page: Page) => Promise<void>;
}> = [
  { path: "/", file: "sotuhire-v1.5.1-web-home.png" },
  { path: "/dashboard", file: "sotuhire-v1.5.1-web-dashboard.png" },
  {
    path: "/resume",
    file: "sotuhire-v1.5.1-web-resume.png",
    prepare: clickDemo,
  },
  { path: "/job", file: "sotuhire-v1.5.1-web-job.png", prepare: clickDemo },
  {
    path: "/match",
    file: "sotuhire-v1.5.1-web-compatibility.png",
    prepare: clickDemo,
  },
  { path: "/ats", file: "sotuhire-v1.5.1-web-ats.png", prepare: clickDemo },
  { path: "/tailor", file: "sotuhire-v1.5.1-web-tailor.png", prepare: clickDemo },
  { path: "/github", file: "sotuhire-v1.5.1-web-github.png", prepare: clickDemo },
  {
    path: "/sources",
    file: "sotuhire-v1.5.1-web-sources.png",
    prepare: async (page) => {
      await page.locator("#local-extension").scrollIntoViewIfNeeded();
    },
  },
  { path: "/tracker", file: "sotuhire-v1.5.1-web-applications.png" },
  { path: "/intelligence", file: "sotuhire-v1.5.1-web-intelligence.png" },
  {
    path: "/settings",
    file: "sotuhire-v1.5.1-web-settings-ai.png",
    prepare: async (page) => {
      await expect(page.getByText("IA e Providers")).toBeVisible();
    },
  },
  { path: "/privacy", file: "sotuhire-v1.5.1-web-privacy.png" },
];

test.describe.configure({ mode: "serial" });

test("captures standardized v1.5.1 screenshots", async ({ page }) => {
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
