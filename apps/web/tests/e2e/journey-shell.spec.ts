import { expect, test } from "@playwright/test";

/**
 * CP-UX01: the journey shell, the unified search and the API-down state, as a person uses them.
 * Each case failed on the pre-redesign build (459ffa9): the search found 0 screens for
 * "curriculo", there was no tab bar, and with the API down the cockpit showed zeros as data.
 */

test("search finds screens without accents and opens one from the keyboard", async ({ page }) => {
  await page.goto("/dashboard");
  await expect(page.getByRole("heading", { name: "Cockpit de carreira" })).toBeVisible();
  await page.keyboard.press("Control+K");
  const input = page.getByRole("combobox");
  await expect(input).toBeFocused();
  await input.fill("estudio curriculo");
  const option = page.getByRole("option", { name: /Estúdio de Currículo/ });
  await expect(option).toBeVisible();
  await expect(option).toHaveAttribute("aria-selected", "true");
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/\/resume-studio$/);
  await expect(page.getByRole("combobox")).toHaveCount(0);
});

test("search says so when nothing matches, and Escape closes it", async ({ page }) => {
  await page.goto("/dashboard");
  await expect(page.getByRole("heading", { name: "Cockpit de carreira" })).toBeVisible();
  await page.keyboard.press("Control+K");
  await page.getByRole("combobox").fill("xyzzy");
  await expect(page.getByText(/Nada encontrado para “xyzzy”/)).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("combobox")).toHaveCount(0);
});

test("the sidebar groups screens by journey and keeps the current one open", async ({ page }) => {
  await page.goto("/resume-studio");
  const nav = page.getByRole("navigation", { name: "Navegação principal" });
  await expect(nav.getByRole("button", { name: /Currículos/ })).toHaveAttribute(
    "aria-expanded",
    "true",
  );
  await expect(nav.getByRole("link", { name: "Estúdio de Currículo" })).toHaveAttribute(
    "aria-current",
    "page",
  );
  // other journeys are one click away, not hidden behind a menu
  const opportunities = nav.getByRole("button", { name: /Oportunidades/ });
  await expect(opportunities).toHaveAttribute("aria-expanded", "false");
  await opportunities.click();
  await nav.getByRole("link", { name: "Radar" }).click();
  await expect(page).toHaveURL(/\/radar$/);
});

test("on a phone the journeys are a tab bar and every screen is under Mais", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/dashboard");
  const tabs = page.getByRole("navigation", { name: "Jornadas" });
  await expect(tabs.getByRole("link")).toHaveCount(5);
  await tabs.getByRole("link", { name: "Currículos" }).click();
  await expect(page).toHaveURL(/\/resume-studio$/);
  await expect(page.getByRole("heading", { level: 1, name: "Resume Studio" })).toBeVisible();
  await tabs.getByRole("button", { name: "Mais" }).click();
  const sheet = page.getByRole("dialog");
  await expect(sheet.getByRole("link", { name: "Privacidade" })).toBeVisible();
});

test("with the local API down the cockpit shows the failure, not zeros", async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem("sotuhire.api-mode", "real"));
  await page.route("http://127.0.0.1:8787/**", (route) => route.abort("connectionrefused"));
  await page.goto("/dashboard");
  await expect(page.getByRole("status").filter({ hasText: "API local fora do ar" })).toBeVisible();
  await expect(page.getByRole("alert")).toContainText("A API local não respondeu", {
    timeout: 15_000,
  });
  await expect(page.getByText("candidaturas ativas")).toHaveCount(0);
  // a way out that does not need a terminal
  await page.getByRole("button", { name: "Dados de exemplo" }).click();
  await expect(page.getByText("candidaturas ativas")).toBeVisible();
});
