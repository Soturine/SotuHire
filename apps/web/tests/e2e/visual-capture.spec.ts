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
    path: "/sources",
    file: "sotuhire-v1.7.1-web-sources-inbox.png",
    prepare: async (page) => {
      await page.locator("#opportunity-inbox").scrollIntoViewIfNeeded();
    },
  },
  {
    path: "/sources",
    file: "sotuhire-v1.7.1-web-upload-csv.png",
    prepare: async (page) => {
      await page.getByTestId("source-upload-csv-input").setInputFiles({
        name: "vagas-ficticias.csv",
        mimeType: "text/csv",
        buffer: Buffer.from(
          'cargo,empresa,link,local,descricao,fonte,status,observacoes\nAnalista de Dados,Empresa Exemplo,https://example.com/jobs/123,Remoto,"Python e SQL",CSV Manual,nova,"vaga ficticia"',
        ),
      });
      await page.getByTestId("source-file-preview").scrollIntoViewIfNeeded();
    },
  },
  {
    path: "/sources",
    file: "sotuhire-v1.7.1-web-dedupe-merge.png",
    prepare: async (page) => {
      await page.getByTestId("source-duplicate-panel").first().scrollIntoViewIfNeeded();
    },
  },
  {
    path: "/sources",
    file: "sotuhire-v1.7.1-web-source-directory.png",
    prepare: async (page) => {
      await page.getByTestId("source-directory-panel").scrollIntoViewIfNeeded();
    },
  },
  {
    path: "/tracker",
    file: "sotuhire-v1.7.1-web-kanban-source.png",
  },
];

test.describe.configure({ mode: "serial" });

test("captures standardized v1.7.1 screenshots", async ({ page }, testInfo) => {
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
