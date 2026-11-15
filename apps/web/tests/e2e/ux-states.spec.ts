import { expect, test, type Page } from "@playwright/test";
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

/**
 * Interaction and state evidence for the redesign (CP-UX00 baseline, CP-UX06 after). Runs only
 * with CAPTURE_UX=1. Each case drives the real app into one state a person meets (first visit,
 * search, mobile navigation, Local API down, Resume Studio first use, Copilot drawer) and writes
 * a screenshot plus what it measured: how many controls/links the screen offers, how many search
 * results, what the person is told. Same fixture and viewport before and after.
 */

const outDir = join(process.env.CAPTURE_UX_DIR || "ux-capture", "_states");

async function settle(page: Page) {
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(400);
}

async function record(page: Page, name: string, facts: Record<string, unknown>) {
  mkdirSync(outDir, { recursive: true });
  await page.screenshot({ path: join(outDir, `${name}.png`) });
  writeFileSync(join(outDir, `${name}.json`), JSON.stringify(facts, null, 2));
}

test.describe("ux states", () => {
  test.skip(() => process.env.CAPTURE_UX !== "1", "Set CAPTURE_UX=1 to capture UX evidence.");
  test.beforeEach(async ({ page }) => {
    await page.emulateMedia({ colorScheme: "light", reducedMotion: "reduce" });
  });

  test("first visit", async ({ page }) => {
    await page.addInitScript(() => localStorage.removeItem("sotuhire.onboarding.v1.complete"));
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto("/");
    await settle(page);
    const dialog = page.getByRole("dialog");
    await record(page, "first-visit-desktop", {
      dialog_open: await dialog.isVisible().catch(() => false),
      dialog_text: (await dialog.innerText().catch(() => "")).slice(0, 600),
      buttons_in_dialog: await dialog.getByRole("button").count(),
    });
  });

  test("navigation inventory desktop", async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto("/dashboard");
    await settle(page);
    const nav = page.getByRole("navigation").first();
    await record(page, "navigation-desktop", {
      nav_links: await nav.getByRole("link").count(),
      nav_text: (await nav.innerText()).split("\n").filter(Boolean),
      header_controls: await page.locator("header").first().getByRole("button").count(),
    });
  });

  test("mobile navigation open", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/dashboard");
    await settle(page);
    await page
      .getByRole("button", { name: /menu|navega|^mais$|^more$/i })
      .first()
      .click();
    await page.waitForTimeout(300);
    const dialog = page.getByRole("dialog");
    await record(page, "navigation-mobile-open", {
      links: await dialog.getByRole("link").count(),
      text: (await dialog.innerText()).split("\n").filter(Boolean).slice(0, 60),
    });
  });

  for (const query of ["", "curriculo", "currículo", "vaga"]) {
    test(`search palette "${query}"`, async ({ page }) => {
      await page.setViewportSize({ width: 1440, height: 900 });
      await page.goto("/dashboard");
      await settle(page);
      await page.keyboard.press("Control+k");
      const input = page.getByRole("combobox").first();
      await expect(input).toBeVisible();
      if (query) await input.fill(query);
      await page.waitForTimeout(700);
      const options = page.getByRole("option");
      await record(page, `search-${query || "empty"}`, {
        query,
        options: await options.count(),
        option_text: (await options.allInnerTexts()).slice(0, 30),
        empty_message: await page
          .getByText(/nenhum resultado|no results/i)
          .isVisible()
          .catch(() => false),
      });
    });
  }

  test("local api unreachable", async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem("sotuhire.api-mode", "real");
      localStorage.setItem("sotuhire.api-url", "http://127.0.0.1:8787");
    });
    await page.route("http://127.0.0.1:8787/**", (route) => route.abort("connectionrefused"));
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto("/dashboard");
    await settle(page);
    await page.waitForTimeout(1500);
    await record(page, "api-unreachable-dashboard", {
      main_text: (await page.locator("main").innerText()).slice(0, 800),
    });
  });

  test("resume studio first use (api mode, no master)", async ({ page }) => {
    await page.addInitScript(() => localStorage.setItem("sotuhire.api-mode", "real"));
    await page.route("http://127.0.0.1:8787/api/v1/**", (route) => {
      const path = new URL(route.request().url()).pathname.replace("/api/v1", "");
      if (path === "/resume-studio/master")
        return route.fulfill({
          status: 404,
          json: {
            ok: false,
            error: { code: "http_error", message: "Currículo Mestre ainda não foi criado." },
          },
        });
      if (path === "/resume-studio/templates")
        return route.fulfill({
          json: { ok: true, data: { items: [] }, request_id: "", warnings: [] },
        });
      return route.fulfill({ json: { ok: true, data: {}, request_id: "", warnings: [] } });
    });
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto("/resume-studio");
    await settle(page);
    await record(page, "resume-studio-first-use", {
      main_text: (await page.locator("main").innerText()).slice(0, 800),
      primary_actions: await page.locator("main").getByRole("button").count(),
    });
  });

  test("copilot drawer", async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto("/profile");
    await settle(page);
    await page
      .getByRole("button", { name: /copilot/i })
      .first()
      .click();
    await page.waitForTimeout(400);
    const dialog = page.getByRole("dialog");
    await record(page, "copilot-drawer", {
      text: (await dialog.innerText()).slice(0, 800),
      buttons: await dialog.getByRole("button").count(),
    });
  });
});
