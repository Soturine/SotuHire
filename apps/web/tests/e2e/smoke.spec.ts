import { expect, test } from "@playwright/test";

const coreScreens = [
  { path: "/", heading: /SotuHire/i },
  { path: "/dashboard", heading: "Dashboard" },
  { path: "/resume", heading: /Curr.culo/ },
  { path: "/job", heading: "Vaga" },
  { path: "/match", heading: /Compatibilidade/ },
  { path: "/ats", heading: /ATS/ },
  { path: "/tailor", heading: /Ajuste/ },
  { path: "/github", heading: /GitHub/ },
  { path: "/tracker", heading: "Candidaturas" },
  { path: "/intelligence", heading: /Intelig.ncia/ },
  { path: "/sources", heading: "Fontes e Captura" },
  { path: "/settings", heading: /Configura..es/ },
  { path: "/privacy", heading: "Privacidade" },
];

test("home, dashboard and guided flow render without legacy branding", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: /SotuHire/i }).first()).toBeVisible();
  await expect(page.getByTestId("guided-flow").first()).toBeVisible();
  await expect(page.locator("body")).not.toContainText("Career Compass");
  await expect(page.locator("body")).not.toContainText("Match Engine 2.0");

  await page.goto("/dashboard");
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expect(page.getByText("Fluxo guiado")).toBeVisible();
  await expect(page.getByText("Adicionar curriculo")).toBeVisible();
  await expect(page.getByText("Acompanhar no Kanban")).toBeVisible();
});

test("core screens open in every configured browser", async ({ page }) => {
  for (const screen of coreScreens) {
    await page.goto(screen.path);
    await expect(page.getByRole("heading", { name: screen.heading }).first()).toBeVisible();
    await expect(page.locator("body")).not.toContainText("Career Compass");
    await expect(page.locator("body")).not.toContainText("Match Engine 2.0");
  }
});

test("sidebar navigates across core screens", async ({ page }) => {
  await page.goto("/dashboard");

  const routes = [
    { label: /Curr.culo/i, url: /\/resume$/, heading: /Curr.culo/ },
    { label: /Vaga/i, url: /\/job$/, heading: "Vaga" },
    { label: /Compatibilidade/i, url: /\/match$/, heading: /Compatibilidade/ },
    { label: /Fontes e Captura/i, url: /\/sources$/, heading: "Fontes e Captura" },
    { label: /Configura..es/i, url: /\/settings$/, heading: /Configura..es/ },
  ];

  for (const route of routes) {
    const link = page.getByRole("link", { name: route.label }).first();
    await link.click();
    await expect(page).toHaveURL(route.url);
    await expect(page.getByRole("heading", { name: route.heading }).first()).toBeVisible();
  }
});

test("analysis demo buttons show results", async ({ page }) => {
  const demos = [
    { path: "/resume", result: /Perfil extra.do|Pessoa Fict/ },
    { path: "/job", result: /Vaga estruturada|Desenvolvedor Backend/ },
    { path: "/match", result: /Requisitos atendidos|Assistente de a..o para compatibilidade/ },
    { path: "/ats", result: /Pontua..o ATS|Assistente de a..o ATS/ },
    { path: "/tailor", result: /Bullets seguros|Assistente de a..o para ajuste/ },
    { path: "/github", result: /fictitious-api-lab|Assistente de a..o para GitHub/ },
  ];

  for (const demo of demos) {
    await page.goto(demo.path);
    await page
      .getByRole("button", { name: /Rodar demo/i })
      .first()
      .click();
    await expect(page.locator("body")).toContainText(demo.result);
    await expect(
      page.getByText(/Analise local|Analise com IA|Fallback local/i).first(),
    ).toBeVisible();
  }
});

test("settings AI flow uses backend status shape and never stores secrets in browser storage", async ({
  page,
}) => {
  const fakeKey = "AIza-fake-playwright-secret";
  await page.goto("/settings");

  await expect(page.getByText("IA e Providers")).toBeVisible();
  await expect(page.getByText(/Permitir IA na An.lise de Compatibilidade/)).toBeVisible();
  await expect(page.getByText(/Provider local/i).first()).toBeVisible();
  const keyInput = page.getByTestId("ai-api-key-input");
  await expect(async () => {
    await page.getByRole("button", { name: "Gemini" }).click();
    await expect(keyInput).toBeEnabled({ timeout: 1_000 });
    await keyInput.fill(fakeKey, { timeout: 1_000 });
  }).toPass({ timeout: 10_000 });
  await page.getByRole("button", { name: /Testar conex/i }).click();
  await expect(page.getByText(/Provider configurado com sucesso/i).first()).toBeVisible();
  await page.getByRole("button", { name: /Salvar no backend local/i }).click();
  await expect(keyInput).toHaveValue("");
  await page.getByRole("button", { name: /Remover chave/i }).click();

  const storage = await page.evaluate(() => ({
    local: JSON.stringify(localStorage),
    session: JSON.stringify(sessionStorage),
  }));
  expect(storage.local).not.toContain(fakeKey);
  expect(storage.session).not.toContain(fakeKey);
});

test("sources page handles local extension offline and fake capture imports", async ({ page }) => {
  await page.goto("/settings");
  await page.getByRole("button", { name: "API Real" }).click();
  await page.getByRole("link", { name: /Fontes e Captura/i }).click();
  await expect(page.getByText("Companion offline", { exact: true })).toBeVisible();

  await page.getByRole("link", { name: /Configura/i }).click();
  await page.getByRole("button", { name: "Demo" }).click();
  await page.getByRole("link", { name: /Fontes e Captura/i }).click();
  await expect(page.getByText(/Extens.o Local/).first()).toBeVisible();
  await expect(page.getByTestId("extension-capture-row").first()).toBeVisible();
  await page.getByTestId("import-capture-job").first().click();
  await expect(page.getByText(/Captura enviada|Modo Demo/i).first()).toBeVisible();
  await page.getByTestId("import-capture-tracker").first().click();
  await expect(page.getByText(/Candidaturas|tracker/i).first()).toBeVisible();
  await page.getByTestId("import-capture-github").first().click();
  await expect(page.getByText(/GitHub Analysis|Analise de GitHub/i).first()).toBeVisible();
  await page.getByTestId("ignore-capture-local").first().click();
  await expect(page.getByTestId("extension-capture-row")).toHaveCount(1);
});

test("sources inbox imports fake text csv json and connects to tracker", async ({ page }) => {
  await page.goto("/sources");

  await expect(page.getByText("Caixa de Entrada de Oportunidades")).toBeVisible();
  await expect(page.getByTestId("source-inbox-row").first()).toBeVisible();
  await page.getByTestId("source-import-text").click();
  await expect(page.getByText(/importacao concluida|Modo Demo/i).first()).toBeVisible();
  await page.getByTestId("source-import-csv").click();
  await expect(page.getByText(/CSV|duplicado/i).first()).toBeVisible();
  await page.getByTestId("source-import-json").click();
  await expect(page.getByText(/JSON|importacao/i).first()).toBeVisible();
  await page.getByTestId("source-run-dedupe").click();
  await expect(page.getByText(/possiveis duplicatas|duplicata/i).first()).toBeVisible();
  await page.getByTestId("source-import-to-job").first().click();
  await expect(page.getByText(/Item enviado para Vaga|Modo Demo/i).first()).toBeVisible();
  await page.getByTestId("source-save-tracker").first().click();
  await expect(page.getByText(/Candidaturas|tracker|Modo Demo/i).first()).toBeVisible();
  await page.getByTestId("source-archive-item").first().click();
  await expect(page.getByText(/Item atualizado|Modo Demo/i).first()).toBeVisible();

  await page.goto("/tracker");
  await expect(page.getByRole("heading", { name: "Candidaturas" })).toBeVisible();
  await expect(page.locator("body")).toContainText(/Fonte|Origem|CSV|Manual|Demo/);
});

test("kanban creates and moves a fake application", async ({ page }) => {
  await page.goto("/tracker");

  await page.getByTestId("new-application-button").first().click();
  const dialog = page.getByTestId("create-application-dialog");
  await expect(dialog).toBeVisible();
  await dialog.getByPlaceholder("Cargo").fill("Backend Python E2E");
  await dialog.getByPlaceholder("Empresa").fill("Empresa Ficticia E2E");
  await dialog.getByPlaceholder("Origem").fill("Manual E2E");
  await dialog.getByPlaceholder("Notas").fill("Nota ficticia criada pelo smoke test.");
  await page.getByTestId("create-application-submit").click();
  await expect(page.getByTestId("create-application-dialog")).toBeHidden();

  const firstCard = page.getByTestId("kanban-card").first();
  await expect(firstCard).toBeVisible();
  await firstCard.dragTo(page.getByTestId("kanban-column-interview"));
  await expect(page.getByTestId("kanban-column-interview")).toContainText("Backend Python E2E");
  await page.getByRole("button", { name: /Lista/i }).click();
  await page.getByTestId("application-status-select").first().selectOption("interview");
  await expect(page.locator("body")).toContainText(/Ultima analise|Sem analise/);
});

test("responsive layouts avoid page-level horizontal overflow", async ({ page }, testInfo) => {
  test.skip(
    testInfo.project.name !== "chromium",
    "Responsive matrix is captured once in Chromium.",
  );
  const viewports = [
    { width: 390, height: 844 },
    { width: 768, height: 1024 },
    { width: 1440, height: 1000 },
  ];

  for (const viewport of viewports) {
    await page.setViewportSize(viewport);
    for (const screen of coreScreens) {
      await page.goto(screen.path);
      await expect(page.getByRole("heading", { name: screen.heading }).first()).toBeVisible();
      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth - window.innerWidth,
      );
      expect(overflow).toBeLessThanOrEqual(2);
    }
  }
});
