import { expect, test } from "@playwright/test";

/**
 * Against a real Local API (not mocks): REAL_API_BOOTSTRAP=<pairing bootstrap> with
 * `python scripts/run_api.py` running on 127.0.0.1:8787 over an empty synthetic data dir.
 * Skipped otherwise, so CI is unaffected. It drives pairing, the cockpit (Career Copilot v2,
 * the layer whose requests never left the browser before CP-UX01), search and the Resume Studio
 * first use, with screenshots for the UX record when CAPTURE_UX_DIR is set.
 */

const bootstrap = process.env.REAL_API_BOOTSTRAP || "";

test.describe("real local API", () => {
  test.skip(
    !bootstrap,
    "Set REAL_API_BOOTSTRAP and run scripts/run_api.py to exercise the real API.",
  );

  test("pairs, opens the cockpit from v2, searches and reaches Resume Studio first use", async ({
    page,
  }) => {
    const v2: number[] = [];
    page.on("response", (response) => {
      if (response.url().includes("/api/v2/")) v2.push(response.status());
    });
    await page.addInitScript(() => localStorage.setItem("sotuhire.api-mode", "real"));
    await page.goto(`/dashboard#sotuhire-pairing=${bootstrap}`);

    await expect(page.getByRole("link", { name: /API local conectada/ }).first()).toBeVisible({
      timeout: 15_000,
    });
    // empty data dir: the cockpit renders real (empty) state, not an error and not demo data
    await expect(page.getByRole("heading", { name: "Próximos passos" })).toBeVisible({
      timeout: 15_000,
    });
    await expect(page.getByRole("alert")).toHaveCount(0);
    // 401 first is the pairing handshake (401 -> pair -> retry); the retried calls answer 200
    expect(v2).toContain(200);
    expect(v2.filter((status) => status >= 400 && status !== 401)).toEqual([]);
    if (process.env.CAPTURE_UX_DIR) {
      await page.screenshot({
        path: `${process.env.CAPTURE_UX_DIR}/_states/real-api-dashboard.png`,
      });
    }

    await page.keyboard.press("Control+K");
    await page.getByRole("combobox").fill("perfil");
    await expect(page.getByRole("option", { name: /Perfil profissional/ })).toBeVisible();
    await page.keyboard.press("Escape");

    await page.goto("/resume-studio");
    await expect(page.getByText(/Currículo Mestre ainda não existe/)).toBeVisible({
      timeout: 15_000,
    });
    if (process.env.CAPTURE_UX_DIR) {
      await page.screenshot({
        path: `${process.env.CAPTURE_UX_DIR}/_states/real-api-resume-studio-first-use.png`,
      });
    }
  });
});
