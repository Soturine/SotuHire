import { expect, test, type Page } from "@playwright/test";
import fs from "node:fs/promises";
import path from "node:path";

const screenshotsDir = path.resolve(process.cwd(), "../../docs/assets/screenshots");

async function shot(page: Page, file: string) {
  await page.waitForTimeout(180);
  await page.screenshot({ path: path.join(screenshotsDir, file), fullPage: false });
}

test.describe.configure({ mode: "serial" });

test("captures the complete v1.9.8 guided application journey", async ({ page }, testInfo) => {
  test.setTimeout(90_000);
  test.skip(process.env.CAPTURE_V198 !== "1", "Set CAPTURE_V198=1 to generate release visuals.");
  test.skip(testInfo.project.name !== "chromium", "Release visuals are captured once in Chromium.");
  await fs.mkdir(screenshotsDir, { recursive: true });
  await page.setViewportSize({ width: 1440, height: 1000 });

  await page.goto(
    "/application-lab?novo=1&capture_id=capture-fictitious-198&job_snapshot_id=job-snapshot-fictitious-198",
  );
  await expect(page.getByTestId("application-lab-start")).toBeVisible();
  await shot(page, "sotuhire-v1.9.8-application-lab-start.png");
  await page.getByRole("button", { name: "Iniciar preparação" }).click();
  await expect(page.getByText(/Sessão/).first()).toBeVisible();

  await page.getByRole("button", { name: "Perfil e evidências", exact: true }).click();
  await shot(page, "sotuhire-v1.9.8-profile-evidence.png");
  await page.getByRole("button", { name: "Currículo Mestre", exact: true }).click();
  await shot(page, "sotuhire-v1.9.8-master-resume.png");
  await page.getByRole("button", { name: "Vaga", exact: true }).click();
  await shot(page, "sotuhire-v1.9.8-job-snapshot.png");

  await page.getByRole("button", { name: "Análise", exact: true }).click();
  await expect(page.getByTestId("readiness-report")).toBeVisible();
  await page.getByRole("button", { name: "Reexecutar somente a análise" }).click();
  await expect(page.getByText("Análise consolidada em andamento")).toBeVisible();
  await shot(page, "sotuhire-v1.9.8-analysis-progress.png");
  await expect(page.getByTestId("readiness-report")).toBeVisible();
  await shot(page, "sotuhire-v1.9.8-readiness-report.png");

  await page.getByRole("button", { name: /Melhorias$/ }).click();
  await shot(page, "sotuhire-v1.9.8-suggestions.png");
  await page.getByRole("button", { name: "Aceitar", exact: true }).first().click();
  await expect(page.getByText("Aceita", { exact: true })).toBeVisible();

  await page.getByRole("button", { name: /Variante$/ }).click();
  await page.getByRole("button", { name: "Criar variante" }).click();
  await expect(page.getByText("Antes", { exact: true }).first()).toBeVisible();
  await shot(page, "sotuhire-v1.9.8-variant-diff.png");

  await page.getByRole("button", { name: /Kit de candidatura$/ }).click();
  await page.getByRole("button", { name: "Criar kit" }).click();
  await expect(page.getByText("professional summary")).toBeVisible();
  await shot(page, "sotuhire-v1.9.8-application-kit.png");

  await page.getByRole("button", { name: /Plano de ação$/ }).click();
  await page.getByRole("button", { name: "Criar plano de 7 dias" }).click();
  await expect(page.getByText("Confirmar experiência com ISO 9001")).toBeVisible();
  await shot(page, "sotuhire-v1.9.8-action-plan.png");

  await page
    .getByRole("button", { name: /Salvar no Tracker$/ })
    .first()
    .click();
  await page.getByRole("checkbox").check();
  await shot(page, "sotuhire-v1.9.8-tracker-review.png");
  await page.getByRole("button", { name: "Salvar no Tracker", exact: true }).last().click();
  await expect(page.getByText("Candidatura salva", { exact: true })).toBeVisible();
  await shot(page, "sotuhire-v1.9.8-tracker-saved.png");

  await page.goto("/resume-studio");
  await expect(page.getByTestId("resume-studio")).toBeVisible();
  await shot(page, "sotuhire-v1.9.8-resume-studio.png");
  await page.getByRole("button", { name: "Preview" }).click();
  await expect(page.getByText("Preview em tempo real").last()).toBeVisible();
  await shot(page, "sotuhire-v1.9.8-resume-preview.png");

  await page.goto("/ai-quality");
  await expect(page.getByRole("heading", { name: "IA e Qualidade" })).toBeVisible();
  await shot(page, "sotuhire-v1.9.8-ai-quality.png");
  await page.getByRole("tab", { name: "Providers" }).click();
  await shot(page, "sotuhire-v1.9.8-provider-fallback.png");
});

test("captures the v1.9.8 mobile entry point", async ({ page }, testInfo) => {
  test.skip(process.env.CAPTURE_V198 !== "1", "Set CAPTURE_V198=1 to generate release visuals.");
  test.skip(testInfo.project.name !== "chromium", "Release visuals are captured once in Chromium.");
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/application-lab?novo=1&job_snapshot_id=job-snapshot-fictitious-mobile");
  await expect(page.getByTestId("application-lab-start")).toBeVisible();
  await shot(page, "sotuhire-v1.9.8-application-lab-mobile.png");
});
