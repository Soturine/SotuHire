import { expect, test } from "@playwright/test";

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

test("sidebar navigates across core screens", async ({ page }) => {
  await page.goto("/dashboard");

  const routes = [
    { label: "Curriculo", fallback: "Currículo", url: /\/resume$/, heading: /Curr.culo/ },
    { label: "Vaga", url: /\/job$/, heading: "Vaga" },
    { label: "Compatibilidade", url: /\/match$/, heading: /Compatibilidade/ },
    { label: "Fontes e Captura", url: /\/sources$/, heading: "Fontes e Captura" },
    {
      label: "Configuracoes",
      fallback: "Configurações",
      url: /\/settings$/,
      heading: /Configura..es/,
    },
  ];

  for (const route of routes) {
    const link = page
      .getByRole("link", { name: new RegExp(route.fallback ?? route.label, "i") })
      .first();
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
      page.getByText(/An.lise local|An.lise com IA|Fallback local/i).first(),
    ).toBeVisible();
  }
});

test("settings AI flow uses backend status shape and never stores secrets in browser storage", async ({
  page,
}) => {
  const fakeKey = "AIza-fake-playwright-secret";
  await page.goto("/settings");

  await expect(page.getByText("IA e Providers")).toBeVisible();
  await expect(page.getByText("Permitir IA na Análise de Compatibilidade")).toBeVisible();
  await page.getByRole("button", { name: "Gemini" }).click();
  await page.getByPlaceholder(/Cole a chave Gemini/i).fill(fakeKey);
  await page.getByRole("button", { name: /Testar conex/i }).click();
  await expect(page.getByText(/Provider configurado com sucesso/i).first()).toBeVisible();
  await page.getByRole("button", { name: /Salvar no backend local/i }).click();
  await expect(page.getByPlaceholder(/Cole a chave Gemini/i)).toHaveValue("");
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
  await expect(page.getByText("Extensão Local", { exact: true })).toBeVisible();
  await expect(page.getByTestId("extension-capture-row").first()).toBeVisible();
  await page.getByTestId("import-capture-job").first().click();
  await expect(page.getByText(/Captura enviada|Modo Demo/i).first()).toBeVisible();
  await page.getByTestId("import-capture-tracker").first().click();
  await expect(page.getByText(/Candidaturas|tracker/i).first()).toBeVisible();
  await page.getByTestId("import-capture-github").first().click();
  await expect(page.getByText(/GitHub Analysis|Analise de GitHub/i).first()).toBeVisible();
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
  await page.getByRole("button", { name: /Lista/i }).click();
  await page.getByTestId("application-status-select").first().selectOption("interview");
  await expect(page.locator("body")).toContainText(/Ultima analise|Sem analise/);
});
