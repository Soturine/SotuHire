import { readFile } from "node:fs/promises";

import { expect, test, type Page } from "@playwright/test";

/**
 * Against a real Local API (not mocks): REAL_API_BOOTSTRAP=<pairing bootstrap> with
 * `python scripts/run_api.py` running on 127.0.0.1:8787 over an empty synthetic data dir.
 * Skipped otherwise, so CI is unaffected. It drives pairing, the cockpit (Career Copilot v2,
 * the layer whose requests never left the browser before CP-UX01), search and the Resume Studio
 * first use, with screenshots for the UX record when CAPTURE_UX_DIR is set.
 */

const bootstrap = process.env.REAL_API_BOOTSTRAP || "";

async function pair(page: Page, path: string) {
  await page.addInitScript(() => localStorage.setItem("sotuhire.api-mode", "real"));
  await page.goto(`${path}#sotuhire-pairing=${bootstrap}`);
  await expect(page.getByRole("link", { name: /API local conectada/ }).first()).toBeVisible({
    timeout: 15_000,
  });
}

test.describe("real local API", () => {
  // the second journey builds on the empty data dir the first one checks
  test.describe.configure({ mode: "serial" });
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

  test("profile fact → Master Resume → autosave → export → profile edit reconciled", async ({
    page,
  }) => {
    test.setTimeout(90_000);
    const fact = "Enfermeira assistencial (fictícia)";
    await pair(page, "/profile");

    // first use of the Profile: an empty state with a way in, not a blank list
    await expect(page.getByText("Seu perfil ainda não tem fatos")).toBeVisible();
    await page.getByRole("button", { name: "Adicionar o primeiro fato" }).click();
    const dialog = page.getByRole("dialog", { name: "Adicionar um fato ao Perfil" });
    await dialog.getByLabel("Tipo").selectOption("experience");
    await page.getByTestId("profile-item-title").fill(fact);
    await dialog.getByLabel(/Organização/).fill("Hospital Fictício");
    await page.getByTestId("profile-item-evidence").fill("Plantões em UTI adulto.");
    await page.getByTestId("profile-add-item").click();
    await expect(page.getByTestId("profile-items")).toContainText(fact);

    await page.goto("/resume-studio");
    await page.getByTestId("master-from-profile").click();
    await expect(page.getByTestId("resume-studio")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("resume-studio")).toContainText(fact);
    await page.getByLabel("Nome da variante").fill("Variante sintética E2E");
    await expect(page.getByRole("status").filter({ hasText: /^Salvo/ })).toBeVisible({
      timeout: 10_000,
    });

    // exports come from the API and carry the confirmed fact
    const jsonDownload = page.waitForEvent("download");
    await page.getByRole("button", { name: "JSON Resume" }).click();
    const json = await readFile((await (await jsonDownload).path())!, "utf8");
    expect(json).toContain(fact);
    const pdfDownload = page.waitForEvent("download");
    await page.getByRole("button", { name: "PDF", exact: true }).click();
    const pdf = await readFile((await (await pdfDownload).path())!);
    expect(pdf.subarray(0, 5).toString("latin1")).toBe("%PDF-");
    if (process.env.CAPTURE_UX_DIR) {
      await page.screenshot({
        path: `${process.env.CAPTURE_UX_DIR}/_states/real-api-resume-studio.png`,
      });
    }

    // a later edit in the Profile shows up as a reviewable difference, applied only on request
    await page.goto("/profile");
    await page.getByRole("button", { name: "Editar" }).first().click();
    await page.getByLabel("Evidência ou descrição").fill("Plantões em UTI adulto e pediátrica.");
    await page.getByRole("button", { name: "Salvar edição" }).click();
    await expect(page.getByTestId("profile-items")).toContainText("UTI adulto e pediátrica");

    await page.goto("/resume-studio");
    const changed = page.getByTestId("profile-changed");
    await expect(changed).toContainText("Plantões em UTI adulto e pediátrica.");
    await expect(changed).toContainText("Plantões em UTI adulto.");
    await changed.getByRole("checkbox").first().check();
    await page.getByTestId("refresh-profile-facts").click();
    await expect(changed).toHaveCount(0);
  });

  test("application created in the Tracker is found by the data search without accents", async ({
    page,
  }) => {
    await pair(page, "/tracker");
    await page.getByTestId("new-application-button").first().click();
    const dialog = page.getByTestId("create-application-dialog");
    await dialog.getByPlaceholder("Cargo").fill("Enfermeira Clínica Sintética");
    await dialog.getByPlaceholder("Empresa").fill("Hospital Fictício");
    await page.getByTestId("create-application-submit").click();
    await expect(page.getByText("Enfermeira Clínica Sintética").first()).toBeVisible();

    await page.keyboard.press("Control+K");
    await page.getByRole("combobox").fill("enfermeira clinica");
    const hit = page.getByRole("option", { name: /Enfermeira Clínica Sintética/ });
    await expect(hit).toContainText("Candidatura");
    await expect(hit).toContainText("Hospital Fictício");
    await page.keyboard.press("Enter");
    await expect(page).toHaveURL(/\/tracker$/);

    await page.getByRole("button", { name: /Lista/ }).click();
    await page
      .getByRole("combobox", { name: "Status de Enfermeira Clínica Sintética" })
      .selectOption("applied");
    await expect(page.getByText(/Candidatura movida para/).first()).toBeVisible();
    await page.reload();
    await page.getByRole("button", { name: /Lista/ }).click();
    await expect(
      page.getByRole("combobox", { name: "Status de Enfermeira Clínica Sintética" }),
    ).toHaveValue("applied");
  });
});
