import { expect, test } from "@playwright/test";

test("home and dashboard render without legacy branding", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: /SotuHire/i })).toBeVisible();
  await expect(page.locator("body")).not.toContainText("Career Compass");

  await page.goto("/dashboard");
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expect(page.locator("body")).not.toContainText("Career Compass");
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

test("compatibility demo shows a result", async ({ page }) => {
  await page.goto("/match");

  await page.getByRole("button", { name: /Rodar demo/i }).click();

  await expect(page.getByText(/Requisitos atendidos/i)).toBeVisible();
  await expect(page.getByText(/Ader.ncia/)).toBeVisible();
});

test("settings exposes AI providers without persisting browser secrets", async ({ page }) => {
  await page.goto("/settings");

  await expect(page.getByText("IA e Providers")).toBeVisible();
  await expect(page.getByRole("button", { name: "Gemini" })).toBeVisible();
  await expect(page.getByRole("button", { name: /OpenAI/i })).toBeVisible();

  const storage = await page.evaluate(() => ({
    local: Object.keys(localStorage),
    session: Object.keys(sessionStorage),
  }));
  expect(storage.local.join("\n")).not.toMatch(/api|key|gemini|openai/i);
  expect(storage.session.join("\n")).not.toMatch(/api|key|gemini|openai/i);
});

test("sources page shows local extension bridge panel", async ({ page }) => {
  await page.goto("/sources");

  await expect(page.getByText("Extensão Local", { exact: true })).toBeVisible();
  await expect(page.getByText(/Capturas recentes/i)).toBeVisible();
  await expect(
    page.locator("#authenticated-browser").getByText("Navegador autenticado autorizado", {
      exact: true,
    }),
  ).toBeVisible();
});
