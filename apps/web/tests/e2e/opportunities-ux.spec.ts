import { expect, test } from "@playwright/test";

/**
 * CP-UX03: opportunities and applications as a person uses them. Each case failed before: the
 * Tracker filter was accent-sensitive and phone users only got an 11-column board scrolled
 * sideways; data search results showed raw type ids; and nothing guarded the palette against a
 * slow answer to an older query arriving last.
 */

test("tracker filter ignores accents and case, and the funnel filters by stage", async ({
  page,
}) => {
  await page.goto("/tracker");
  const cards = page.getByTestId("kanban-card");
  await expect(cards.first()).toBeVisible();
  const total = await cards.count();

  const filter = page.getByLabel("Filtrar candidaturas");
  await filter.fill("INDUSTRIA processos");
  await expect(cards).toHaveCount(1);
  await expect(cards.first()).toContainText("Estágio em Engenharia de Processos");
  await filter.fill("");
  await expect(cards).toHaveCount(total);

  const funnel = page.getByRole("region", { name: "Funil de candidaturas" });
  await funnel.getByRole("button", { name: /Resultado/ }).click();
  await expect(page.getByRole("heading", { name: "Novas oportunidades" })).toHaveCount(0);
  await funnel.getByRole("button", { name: /Resultado/ }).click();
  await expect(page.getByRole("heading", { name: "Novas oportunidades" })).toBeVisible();
});

test("on a phone the tracker opens as a list and the board is one tap away", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/tracker");
  await expect(page.getByRole("button", { name: /Lista/ })).toHaveAttribute("aria-pressed", "true");
  // each status control is named after its application (axe select-name, critical, before)
  await expect(
    page.getByRole("combobox", { name: /^Status de Estágio em Engenharia de Processos$/ }),
  ).toBeVisible();
  await page.getByRole("button", { name: /Quadro/ }).click();
  await expect(page.getByTestId("kanban-card").first()).toBeVisible();
});

test("radar summary shows its figures as links to the sections that handle them", async ({
  page,
}) => {
  await page.goto("/radar");
  const summary = page.getByTestId("radar-summary");
  await expect(summary.getByRole("link", { name: /Fontes ativas/ })).toHaveAttribute(
    "href",
    "#radar-sources",
  );
  await expect(summary.getByRole("link", { name: /Alertas novos/ })).toHaveAttribute(
    "href",
    "#radar-alerts",
  );
});

test("data search labels result types and ignores a slow answer to an older query", async ({
  page,
}) => {
  await page.addInitScript(() => localStorage.setItem("sotuhire.api-mode", "real"));
  const envelope = (data: unknown) => ({ ok: true, data, request_id: "fixture", warnings: [] });
  await page.route("http://127.0.0.1:8787/**", async (route) => {
    const url = new URL(route.request().url());
    if (url.pathname === "/api/v2/search") {
      const query = url.searchParams.get("query") ?? "";
      // the older, shorter query answers last
      await new Promise((resolve) => setTimeout(resolve, query === "pe" ? 1_500 : 100));
      return route.fulfill({
        json: envelope([
          {
            entity_type: query === "pe" ? "evidence" : "profile",
            entity_id: `id-${query}`,
            title: `Resultado para ${query}`,
            subtitle: "Universidade Fictícia",
            route: "/profile",
            review_status: "confirmed",
          },
        ]),
      });
    }
    return route.fulfill({ json: envelope({}) });
  });
  await page.goto("/help");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await page.keyboard.press("Control+K");
  const input = page.getByRole("combobox");
  await input.pressSequentially("pe", { delay: 30 });
  await page.waitForTimeout(400);
  await input.pressSequentially("squisa", { delay: 30 });

  const latest = page.getByRole("option", { name: /Resultado para pesquisa/ });
  await expect(latest).toBeVisible();
  await expect(latest).toContainText("Fato do Perfil");
  await expect(latest).toContainText("Universidade Fictícia");
  await page.waitForTimeout(1_800);
  await expect(page.getByRole("option", { name: /Resultado para pe$/ })).toHaveCount(0);
  await expect(latest).toBeVisible();
});
