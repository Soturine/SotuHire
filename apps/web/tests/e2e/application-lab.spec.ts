import { expect, test } from "@playwright/test";

test("Application Lab completes the guided human-approved journey", async ({ page }) => {
  test.setTimeout(60_000);
  await page.goto("/application-lab?novo=1&capture_id=capture-demo");
  await expect(page.getByTestId("application-lab-start")).toBeVisible();
  await expect(page.getByText("Vaga recebida da extensão.")).toBeVisible();
  await expect(page.getByText("0 auto-apply")).toBeVisible();
  await page.getByRole("button", { name: "Iniciar preparação" }).click();

  await expect(page.getByText(/Sessão/).first()).toBeVisible();
  await page.getByRole("button", { name: "Análise", exact: true }).click();
  await expect(page.getByTestId("readiness-report")).toBeVisible();
  await expect(page.getByText("Uma análise consolidada em três perspectivas")).toBeVisible();
  await expect(page.getByText(/não é probabilidade de entrevista/i).first()).toBeVisible();

  await page.getByRole("button", { name: /Melhorias$/ }).click();
  await page.getByRole("button", { name: "Aceitar", exact: true }).first().click();
  await expect(page.getByText("Aceita", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Desfazer decisão" }).click();
  await expect(page.getByText("Pendente", { exact: true }).first()).toBeVisible();
  await page.getByRole("button", { name: "Aceitar", exact: true }).first().click();

  await page.getByRole("button", { name: /Variante$/ }).click();
  await page.getByRole("button", { name: "Criar variante" }).click();
  await expect(page.getByText("Variante — Analista de Qualidade")).toBeVisible();
  await expect(page.getByText("Antes", { exact: true }).first()).toBeVisible();
  await expect(page.getByText("Depois", { exact: true }).first()).toBeVisible();

  await page.getByRole("button", { name: /Kit de candidatura$/ }).click();
  await page.getByRole("button", { name: "Criar kit" }).click();
  await expect(page.getByText("professional summary")).toBeVisible();

  await page.getByRole("button", { name: /Plano de ação$/ }).click();
  await page.getByRole("button", { name: "Criar plano de 7 dias" }).click();
  await expect(page.getByText("Confirmar experiência com ISO 9001")).toBeVisible();

  await page
    .getByRole("button", { name: /Salvar no Tracker$/ })
    .first()
    .click();
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Salvar no Tracker", exact: true }).last().click();
  await expect(page.getByText("Candidatura salva", { exact: true })).toBeVisible();
  await expect(page.getByText(/snapshots/i).first()).toBeVisible();
});

test("Resume Studio edits, reorders, previews and exports without changing the master", async ({
  page,
}) => {
  await page.goto("/resume-studio");
  await expect(page.getByTestId("resume-studio")).toBeVisible();
  await expect(page.getByText(/Derivada de/)).toBeVisible();
  const title = page.getByLabel("Nome da variante");
  await title.fill("Variante fictícia E2E");
  await page.getByRole("button", { name: "Desfazer" }).click();
  await expect(title).toHaveValue("Variante — Analista de Qualidade");
  await page.getByRole("button", { name: "Refazer" }).click();
  await expect(title).toHaveValue("Variante fictícia E2E");

  await page.getByRole("button", { name: /Mover Competências para cima/ }).click();
  await page.getByRole("button", { name: "Preview" }).click();
  await expect(page.getByText("Preview em tempo real").last()).toBeVisible();
  await expect(page.getByText(/~1 pág/).last()).toBeVisible();
  await expect(page.locator(".resume-print-preview").last()).toContainText("Qualidade");

  await page.getByRole("button", { name: "Diff" }).click();
  await expect(page.getByText("Evidência confirmada em destaque.")).toBeVisible();

  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "JSON Resume" }).click();
  expect((await download).suggestedFilename()).toBe("curriculo-demo.resume.json");
  const pdfDownload = page.waitForEvent("download");
  await page.getByRole("button", { name: "PDF", exact: true }).click();
  expect((await pdfDownload).suggestedFilename()).toBe("curriculo-demo.pdf");
  const docxDownload = page.waitForEvent("download");
  await page.getByRole("button", { name: "DOCX", exact: true }).click();
  expect((await docxDownload).suggestedFilename()).toBe("curriculo-demo.docx");
});

test("new workflow remains usable on mobile and at 200% zoom", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/application-lab?novo=1");
  await expect(page.getByTestId("application-lab-start")).toBeVisible();
  await page.evaluate(() => {
    document.documentElement.style.zoom = "2";
  });
  await expect(page.getByRole("button", { name: "Iniciar preparação" })).toBeVisible();
  await expect(page.locator("body")).not.toHaveCSS("overflow-x", "scroll");

  await page.goto("/resume-studio");
  await expect(page.getByTestId("resume-studio")).toBeVisible();
  await expect(page.getByRole("button", { name: "Preview" })).toBeVisible();
});

test("captured job opens Application Lab with identifiers, not profile payload", async ({
  page,
}) => {
  await page.goto("/sources");
  const prepare = page.getByTestId("prepare-capture-application").first();
  await expect(prepare).toBeVisible();
  await prepare.click();

  await expect(page).toHaveURL(/\/application-lab\?/);
  const url = new URL(page.url());
  expect(url.searchParams.get("capture_id")).toBe("demo-capture-1");
  expect(url.searchParams.get("job_snapshot_id")).toBe("job-snapshot-demo");
  expect(url.search).not.toMatch(/profile|resume|visible_text/i);
  await expect(page.getByTestId("application-lab-start")).toBeVisible();
});
