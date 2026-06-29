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
  { path: "/radar", heading: "Radar de Vagas" },
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
    { label: /Radar/i, url: /\/radar$/, heading: "Radar de Vagas" },
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
  await expect(
    page.getByText(/Companion offline|Companion conectado|API Real sem oportunidades/i).first(),
  ).toBeVisible();

  await page.getByRole("link", { name: "Configurações", exact: true }).click();
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
  await expect(page.getByTestId("demo-data-badge")).toContainText("Dados de demonstração");
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

test("job radar creates wishlist/source, runs demo and saves results", async ({ page }) => {
  await page.goto("/radar");

  await expect(page.getByRole("heading", { name: "Radar de Vagas" })).toBeVisible();
  await expect(page.getByTestId("radar-demo-badge")).toContainText("Dados de demonstração");
  await expect(page.getByTestId("radar-summary")).toBeVisible();
  await expect(page.getByTestId("radar-wishlist-ai-text")).toBeVisible();
  await page
    .getByTestId("radar-wishlist-ai-text")
    .fill(
      "Sou estudante de engenharia e busco estágio em operações ou qualidade com Excel. Prefiro remoto e não quero PJ.",
    );
  await page.getByTestId("radar-generate-wishlist-draft").click();
  await expect(page.getByTestId("radar-draft-mode-badge")).toBeVisible();
  await expect(
    page.getByText(/rascunho de wishlist gerado|Wishlist sugerida/i).first(),
  ).toBeVisible();
  await expect(page.getByText(/wishlist criada/i)).toHaveCount(0);
  await page.getByLabel("Nome").first().fill("Wishlist revisada E2E");
  await page.getByTestId("radar-create-wishlist").click();
  await expect(page.getByText(/wishlist criada|Modo Demo/i).first()).toBeVisible();
  await page.getByTestId("radar-create-source").click();
  await expect(page.getByText(/fonte criada|Modo Demo/i).first()).toBeVisible();
  await page.getByTestId("radar-run-now").first().click();
  await expect(page.getByTestId("radar-result-card").first()).toBeVisible();
  await expect(page.getByText(/Nova vaga|Radar concluido|Modo Demo/i).first()).toBeVisible();
  await page.getByTestId("radar-save-inbox").first().click();
  await expect(page.getByText(/Caixa de Entrada|salvo/i).first()).toBeVisible();
  await page.getByTestId("radar-save-tracker").first().click();
  await expect(page.getByText(/Candidaturas|salvo/i).first()).toBeVisible();
  await page.getByTestId("radar-mark-alert-read").first().click();
  await expect(page.getByText(/Alerta atualizado|lido|Modo Demo/i).first()).toBeVisible();
});

test("sources supports browser CSV/JSON upload preview, duplicate merge, export and source directory", async ({
  page,
}) => {
  await page.goto("/sources");

  await page.getByTestId("source-upload-csv-input").setInputFiles({
    name: "vagas-ficticias.csv",
    mimeType: "text/csv",
    buffer: Buffer.from(
      'cargo,empresa,link,local,descricao,fonte,status,observacoes\nAnalista de Dados,Empresa Exemplo,https://example.com/jobs/123,Remoto,"Python e SQL",CSV Manual,nova,"vaga ficticia"',
    ),
  });
  await expect(page.getByTestId("source-file-preview")).toContainText("Preview antes de confirmar");
  await page.getByTestId("source-upload-confirm").click();
  await expect(page.getByTestId("source-file-preview")).toBeHidden();
  await expect(page.getByText(/CSV importado|Modo Demo/i).first()).toBeVisible();

  await page.getByTestId("source-upload-json-input").setInputFiles({
    name: "vagas-ficticias.json",
    mimeType: "application/json",
    buffer: Buffer.from(
      JSON.stringify([
        {
          cargo: "Desenvolvedor Backend",
          empresa: "Tech Exemplo",
          link: "https://example.com/jobs/456",
          local: "Hibrido",
          descricao: "APIs, testes e bancos de dados.",
          fonte: "JSON Manual",
        },
      ]),
    ),
  });
  await expect(page.getByTestId("source-file-preview")).toContainText("JSON");
  await page.getByTestId("source-upload-confirm").click();
  await expect(page.getByTestId("source-file-preview")).toBeHidden();
  await expect(page.getByText(/JSON importado|Modo Demo/i).first()).toBeVisible();

  await page.getByTestId("source-upload-csv-input").setInputFiles({
    name: "arquivo-invalido.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("nao e csv"),
  });
  await expect(page.getByTestId("source-upload-error")).toContainText("Formato inválido");
  await page.getByTestId("source-upload-cancel").click();

  await expect(page.getByTestId("source-duplicate-panel").first()).toBeVisible();
  await page.getByTestId("source-merge-duplicate").first().click();
  await expect(page.getByText(/mesclada|histórico preservado|Modo Demo/i).first()).toBeVisible();

  await page.getByTestId("source-select-item").first().check();
  await page.getByTestId("source-export-selected").click();
  await expect(page.getByText(/Exportação concluída|Modo Demo/i).first()).toBeVisible();

  await expect(page.getByTestId("source-directory-panel")).toBeVisible();
  await page.getByTestId("source-directory-search").fill("RSS");
  await expect(page.getByTestId("source-directory-panel")).toContainText("Feeds RSS públicos");
});

test("API Real empty states do not silently show demo opportunity data", async ({ page }) => {
  await page.route("**/api/v1/sources/imports", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        ok: true,
        data: { items: [], batches: [] },
        warnings: [],
        request_id: "e2e",
      }),
    });
  });
  await page.route("**/api/v1/sources/stats", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        ok: true,
        data: {
          total: 0,
          duplicates: 0,
          errors: 0,
          saved_to_tracker: 0,
          by_status: {},
          by_origin: {},
        },
        warnings: [],
        request_id: "e2e",
      }),
    });
  });
  await page.route("**/api/v1/sources/directory**", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        ok: true,
        data: { sources: [], query: "", warnings: [] },
        warnings: [],
        request_id: "e2e",
      }),
    });
  });
  await page.route("**/api/v1/tracker/jobs", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ ok: true, data: { jobs: [] }, warnings: [], request_id: "e2e" }),
    });
  });

  await page.goto("/settings");
  await page.getByRole("button", { name: "API Real" }).click();
  await page.getByRole("link", { name: /Fontes e Captura/i }).click();
  await expect(page.getByTestId("source-real-empty")).toContainText("API Real sem oportunidades");
  await expect(page.locator("body")).not.toContainText("Empresa Exemplo");

  await page
    .getByRole("navigation")
    .getByRole("link", { name: /Candidaturas/i })
    .click();
  await expect(page.getByText("Nenhuma candidatura ainda")).toBeVisible();
  await expect(page.locator("body")).not.toContainText("Empresa Demo");
});

test("API Real radar empty state does not show demo radar results silently", async ({ page }) => {
  await page.route("**/api/v1/radar/wishlists", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ ok: true, data: { wishlists: [] }, warnings: [], request_id: "e2e" }),
    });
  });
  await page.route("**/api/v1/radar/sources", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        ok: true,
        data: { sources: [], adapters: [] },
        warnings: [],
        request_id: "e2e",
      }),
    });
  });
  await page.route("**/api/v1/radar/results", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ ok: true, data: { results: [] }, warnings: [], request_id: "e2e" }),
    });
  });
  await page.route("**/api/v1/radar/alerts", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ ok: true, data: { alerts: [] }, warnings: [], request_id: "e2e" }),
    });
  });
  await page.route("**/api/v1/radar/runs", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ ok: true, data: { runs: [] }, warnings: [], request_id: "e2e" }),
    });
  });
  await page.route("**/api/v1/radar/stats", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        ok: true,
        data: {
          active_sources: 0,
          total_sources: 0,
          total_results: 0,
          new_results: 0,
          matched_results: 0,
          unread_alerts: 0,
          duplicates: 0,
          source_errors: 0,
        },
        warnings: [],
        request_id: "e2e",
      }),
    });
  });

  await page.goto("/settings");
  await page.getByRole("button", { name: "API Real" }).click();
  await page.getByRole("link", { name: /Radar/i }).click();
  await expect(page.getByTestId("radar-real-empty")).toContainText("API Real sem Radar");
  await expect(page.locator("body")).not.toContainText("Empresa Exemplo");
  await expect(page.locator("body")).not.toContainText("Desenvolvedor Backend Python");
});

test("public UI does not contain common mojibake sequences", async ({ page }) => {
  const mojibakePattern =
    /\u00c3[\u0080-\u00bf\u0160\u0161\u2018-\u201d\u2020-\u2022]|\u00c2|\u00e2\u20ac/;

  for (const screen of coreScreens) {
    await page.goto(screen.path);
    const bodyText = await page.locator("body").innerText();
    expect(bodyText, `${screen.path} should render valid UTF-8 copy`).not.toMatch(mojibakePattern);
  }
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
  await expect(page.locator("body")).toContainText(/Última análise|Sem análise/);
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
