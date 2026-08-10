import { expect, test } from "@playwright/test";

test("v2 journey keeps every write behind individual approval", async ({ page }) => {
  await page.goto("/dashboard");
  await expect(page.getByRole("heading", { name: "Cockpit de carreira" })).toBeVisible();
  await page.getByRole("button", { name: /Abrir Copilot contextual/i }).click();
  await expect(page.getByText("Copilot sob sua aprovação")).toBeVisible();
  await page.getByRole("button", { name: "Criar proposta" }).first().click();
  await page.keyboard.press("Escape");

  await page.goto("/approvals");
  await expect(page.getByText(/Não existe Aprovar tudo/)).toBeVisible();
  await expect(page.getByRole("button", { name: /Aprovar tudo/i })).toHaveCount(0);
  await expect(page.getByText("Antes").first()).toBeVisible();
  await expect(page.getByText("Depois da aprovação").first()).toBeVisible();
});

test("evidence review, portfolio and command palette are keyboard reachable", async ({ page }) => {
  await page.goto("/evidence");
  await expect(page.getByRole("heading", { name: "Caixa de evidências" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Confirmar" })).toBeVisible();
  await page.getByRole("button", { name: "Confirmar" }).click();

  await page.goto("/portfolio");
  await expect(page.getByRole("heading", { name: "Portfólio" })).toBeVisible();
  await expect(page.getByText("Projeto Aurora").first()).toBeVisible();

  await page.keyboard.press("Control+K");
  const search = page.getByPlaceholder("Buscar rotas, evidências, portfólio…");
  await expect(search).toBeFocused();
  await search.fill("Aurora");
  await expect(page.getByText("Projeto Aurora").last()).toBeVisible();
  await page.keyboard.press("Escape");
});

test("v2 mobile cockpit and Copilot have no page overflow", async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 800 });
  for (const path of ["/dashboard", "/evidence", "/portfolio", "/approvals"]) {
    await page.goto(path);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
    expect(overflow).toBeLessThanOrEqual(2);
  }
});
