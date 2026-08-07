import { expect, test, type Page } from "@playwright/test";
import fs from "node:fs/promises";
import path from "node:path";

const screenshotsDir = path.resolve(process.cwd(), "../../docs/assets/screenshots");

async function shot(page: Page, file: string) {
  await page.waitForTimeout(180);
  await page.screenshot({ path: path.join(screenshotsDir, file), fullPage: false });
}

async function focusAndShot(page: Page, testId: string, file: string) {
  const target = page.getByTestId(testId);
  await expect(target).toBeVisible();
  await target.scrollIntoViewIfNeeded();
  await shot(page, file);
}

test.describe.configure({ mode: "serial" });

test("captures v1.9.9 API Real and protected local pairing", async ({ page }, testInfo) => {
  test.skip(process.env.CAPTURE_V199 !== "1", "Set CAPTURE_V199=1 to generate release visuals.");
  test.skip(testInfo.project.name !== "chromium", "Release visuals are captured once in Chromium.");
  await fs.mkdir(screenshotsDir, { recursive: true });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.addInitScript(() => localStorage.setItem("sotuhire.api-mode", "real"));

  let paired = false;
  await page.route("http://127.0.0.1:8787/api/v1/**", async (route) => {
    const url = new URL(route.request().url());
    const envelope = (data: unknown) => ({
      ok: true,
      data,
      request_id: "visual-fixture-request",
      warnings: [],
    });
    if (url.pathname.endsWith("/security/pairing/start")) {
      await route.fulfill({
        json: envelope({ challenge_id: "visual-fixture", proof: "redacted-fixture-proof" }),
      });
      return;
    }
    if (url.pathname.endsWith("/security/pairing/complete")) {
      paired = true;
      await route.fulfill({ json: envelope({ csrf_token: "memory-only-fixture" }) });
      return;
    }
    if (!paired) {
      await route.fulfill({
        status: 401,
        json: { ok: false, error: { message: "pairing required" } },
      });
      return;
    }
    if (url.pathname.endsWith("/health")) {
      await route.fulfill({
        json: envelope({
          status: "ok",
          version: "1.9.9",
          local_first: true,
          environment: "visual-fixture",
          capabilities: ["secure_pairing", "resume_studio", "document_ingestion"],
        }),
      });
      return;
    }
    if (url.pathname.endsWith("/ai/settings")) {
      await route.fulfill({
        json: envelope({
          provider: "local",
          model: "local",
          configured: true,
          status: "ready",
          use_ai: false,
          preset: "local_safe",
        }),
      });
      return;
    }
    if (url.pathname.endsWith("/ai/providers")) {
      await route.fulfill({ json: envelope({ items: [{ provider: "local", available: true }] }) });
      return;
    }
    if (url.pathname.includes("/ai/models")) {
      await route.fulfill({ json: envelope({ items: [{ id: "local", label: "Local" }] }) });
      return;
    }
    await route.fulfill({ json: envelope({}) });
  });

  await page.goto("/settings");
  await expect.poll(() => paired).toBe(true);
  await expect(page.getByText("API Real", { exact: true }).first()).toBeVisible();
  await shot(page, "sotuhire-v1.9.9-api-real.png");
  await focusAndShot(page, "local-pairing-status", "sotuhire-v1.9.9-local-pairing.png");
});

test("captures the secure document-to-resume workflow", async ({ page }, testInfo) => {
  test.setTimeout(90_000);
  test.skip(process.env.CAPTURE_V199 !== "1", "Set CAPTURE_V199=1 to generate release visuals.");
  test.skip(testInfo.project.name !== "chromium", "Release visuals are captured once in Chromium.");
  await fs.mkdir(screenshotsDir, { recursive: true });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto("/resume-studio");
  await expect(page.getByTestId("resume-studio")).toBeVisible();
  await shot(page, "sotuhire-v1.9.9-resume-studio.png");

  await page.locator('input[type="file"]').setInputFiles({
    name: "curriculo-ficticio-v199.pdf",
    mimeType: "application/pdf",
    buffer: Buffer.from("%PDF-1.4\n% fictional visual fixture\n%%EOF"),
  });
  await page.getByRole("button", { name: "Extrair com segurança" }).click();
  await expect(page.getByText(/PDF · \d+ bloco/)).toBeVisible();
  await shot(page, "sotuhire-v1.9.9-import-pdf.png");
  await focusAndShot(page, "ingestion-block-review", "sotuhire-v1.9.9-block-review.png");
  await focusAndShot(page, "ingestion-provenance", "sotuhire-v1.9.9-provenance.png");

  await page.getByLabel(/Revisei os blocos selecionados/).check();
  await page.getByRole("button", { name: "Adotar rascunho como Currículo Mestre" }).click();
  await expect(page.getByText(/alteração apenas simulada/)).toBeVisible();
  await page.getByText(/Derivada de/).scrollIntoViewIfNeeded();
  await shot(page, "sotuhire-v1.9.9-master-resume.png");

  // Reload restores the independent fictional variant, whose audited change-set
  // makes the before/after view meaningful after the ingestion review was recorded.
  await page.reload();
  await expect(page.getByTestId("resume-studio")).toBeVisible();
  await page.getByRole("button", { name: "Diff" }).click();
  await expect(page.getByText("Antes", { exact: true }).first()).toBeVisible();
  await shot(page, "sotuhire-v1.9.9-variant-diff.png");

  await page.getByRole("button", { name: "Preview" }).click();
  await expect(page.getByText("Preview em tempo real").last()).toBeVisible();
  await shot(page, "sotuhire-v1.9.9-resume-preview.png");

  const pdfDownload = page.waitForEvent("download");
  await page.getByRole("button", { name: "PDF", exact: true }).click();
  expect((await pdfDownload).suggestedFilename()).toBe("curriculo-demo.pdf");
  await shot(page, "sotuhire-v1.9.9-pdf-export.png");
  const docxDownload = page.waitForEvent("download");
  await page.getByRole("button", { name: "DOCX", exact: true }).click();
  expect((await docxDownload).suggestedFilename()).toBe("curriculo-demo.docx");
  await shot(page, "sotuhire-v1.9.9-docx-export.png");

  await focusAndShot(page, "professional-assets", "sotuhire-v1.9.9-professional-assets.png");
});

test("captures the reviewable v1.9.9 Application Lab", async ({ page }, testInfo) => {
  test.setTimeout(120_000);
  test.skip(process.env.CAPTURE_V199 !== "1", "Set CAPTURE_V199=1 to generate release visuals.");
  test.skip(testInfo.project.name !== "chromium", "Release visuals are captured once in Chromium.");
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto(
    "/application-lab?novo=1&capture_id=capture-fictitious-199&job_snapshot_id=job-snapshot-fictitious-199",
  );
  await page.getByRole("button", { name: "Iniciar preparação" }).click();

  await page.getByRole("button", { name: "Perfil e evidências", exact: true }).click();
  await focusAndShot(page, "evidence-review-states", "sotuhire-v1.9.9-confirmed-potential.png");

  await page.getByRole("button", { name: "Análise", exact: true }).click();
  await focusAndShot(
    page,
    "application-analysis-bundle",
    "sotuhire-v1.9.9-application-analysis-bundle.png",
  );
  await shot(page, "sotuhire-v1.9.9-independent-scores.png");
  await expect(page.getByText(/requisito\(s\) unknown/)).toBeVisible();
  await shot(page, "sotuhire-v1.9.9-requirement-unknown.png");

  await page.getByRole("button", { name: /Melhorias$/ }).click();
  await page.getByRole("button", { name: "Aceitar", exact: true }).first().click();
  await page.getByRole("button", { name: /Variante$/ }).click();
  await page.getByRole("button", { name: "Criar variante" }).click();
  await expect(page.getByText("Antes", { exact: true }).first()).toBeVisible();
  await shot(page, "sotuhire-v1.9.9-application-variant-diff.png");

  await page.getByRole("button", { name: /Kit de candidatura$/ }).click();
  await page.getByRole("button", { name: "Criar kit" }).click();
  await expect(page.getByTestId("application-kit-review")).toContainText("8 item(ns)");
  await focusAndShot(page, "application-kit-review", "sotuhire-v1.9.9-application-kit-review.png");

  await page.getByRole("button", { name: /Plano de ação$/ }).click();
  await page.getByRole("button", { name: "Criar plano de 7 dias" }).click();
  await page
    .getByRole("button", { name: /Salvar no Tracker$/ })
    .first()
    .click();
  await page.getByRole("checkbox").check();
  await shot(page, "sotuhire-v1.9.9-tracker-review.png");
});

test.skip("captures the persisted Tracker result without visual-I/O races", async ({
  page,
}, testInfo) => {
  test.setTimeout(90_000);
  test.skip(process.env.CAPTURE_V199 !== "1", "Set CAPTURE_V199=1 to generate release visuals.");
  test.skip(testInfo.project.name !== "chromium", "Release visuals are captured once in Chromium.");
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto("/application-lab?novo=1&job_snapshot_id=job-snapshot-fictitious-tracker");
  await page.getByRole("button", { name: "Iniciar preparação" }).click();
  await page.getByRole("button", { name: "Análise", exact: true }).click();
  await page.getByRole("button", { name: /Melhorias$/ }).click();
  await page.getByRole("button", { name: "Aceitar", exact: true }).first().click();
  await page.getByRole("button", { name: /Variante$/ }).click();
  await page.getByRole("button", { name: "Criar variante" }).click();
  await page.getByRole("button", { name: /Kit de candidatura$/ }).click();
  await page.getByRole("button", { name: "Criar kit" }).click();
  await page.getByRole("button", { name: /Plano de ação$/ }).click();
  await page.getByRole("button", { name: "Criar plano de 7 dias" }).click();
  await page
    .getByRole("button", { name: /Salvar no Tracker$/ })
    .first()
    .click();
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Salvar no Tracker", exact: true }).last().click();
  await expect(page.getByText("Candidatura salva", { exact: true })).toBeVisible();
  await shot(page, "sotuhire-v1.9.9-tracker-saved.png");
});

test("captures deterministic stale invalidation", async ({ page }, testInfo) => {
  test.setTimeout(60_000);
  test.skip(process.env.CAPTURE_V199 !== "1", "Set CAPTURE_V199=1 to generate release visuals.");
  test.skip(testInfo.project.name !== "chromium", "Release visuals are captured once in Chromium.");
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto("/application-lab?novo=1&job_snapshot_id=job-snapshot-demo");
  await page.getByRole("button", { name: "Iniciar preparação" }).click();
  await page.getByRole("button", { name: "Vaga", exact: true }).click();
  await page
    .getByLabel("Identificador imutável da vaga")
    .fill("job-snapshot-fictitious-199-revised");
  await page.getByRole("button", { name: "Continuar" }).click();
  await page.getByRole("button", { name: "Análise", exact: true }).click();
  await expect(page.getByText(/Artefato stale/)).toBeVisible();
  await shot(page, "sotuhire-v1.9.9-stale-analysis.png");
});

test("captures provider degraded state", async ({ page }, testInfo) => {
  test.skip(process.env.CAPTURE_V199 !== "1", "Set CAPTURE_V199=1 to generate release visuals.");
  test.skip(testInfo.project.name !== "chromium", "Release visuals are captured once in Chromium.");
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto("/ai-quality");
  await page.getByRole("tab", { name: "Providers" }).click();
  await shot(page, "sotuhire-v1.9.9-provider-degraded.png");
});
