import { expect, test } from "@playwright/test";

/**
 * CP-UX02: first visit in two steps, the Profile organized by tabs with deep links, a fact that
 * cannot be removed by one stray click, and form fields whose labels name their controls.
 */

test("first visit takes two steps and leads straight to a starting path", async ({ page }) => {
  // a first visit only for the first page load of this tab, so the reload below is a return
  await page.addInitScript(() => {
    if (sessionStorage.getItem("first-visit-done")) return;
    localStorage.removeItem("sotuhire.onboarding.v1.complete");
    sessionStorage.setItem("first-visit-done", "1");
  });
  await page.goto("/");
  const dialog = page.getByRole("dialog");
  await expect(dialog.getByText("Etapa 1 de 2")).toBeVisible();
  await expect(dialog.getByText("Você mantém o controle")).toBeVisible();
  await dialog.getByRole("button", { name: "Próxima" }).click();
  await expect(dialog.getByRole("heading", { name: "Por onde começar" })).toBeVisible();
  await dialog.getByRole("link", { name: /Confirme seu perfil/ }).click();
  await expect(page).toHaveURL(/\/profile$/);
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await page.reload();
  await expect(page.getByRole("heading", { name: "Perfil", exact: true })).toBeVisible();
  await expect(page.getByRole("dialog")).toHaveCount(0);
});

test.describe("profile", () => {
  test("tabs are deep-linkable and every identity field is labelled", async ({ page }) => {
    await page.goto("/profile?tab=identity");
    await expect(page.getByRole("tab", { name: "Identidade e objetivos" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    // the accessible name is the label, plus "opcional" where it applies
    for (const label of ["Nome", "Headline", "Resumo", "Áreas principais", "Contrato"]) {
      await expect(page.getByLabel(new RegExp(`^${label}( opcional)?$`))).toBeVisible();
    }
    await page.getByRole("tab", { name: "Importar" }).click();
    await expect(page).toHaveURL(/tab=import/);
    await expect(page.getByTestId("profile-lattes-section")).toBeVisible();
  });

  test("removing a fact asks first, and keeping it changes nothing", async ({ page }) => {
    await page.goto("/profile");
    const items = page.getByTestId("profile-items").getByRole("listitem");
    await expect(items.first()).toBeVisible();
    const before = await items.count();
    expect(before).toBeGreaterThan(0);
    await items.first().getByRole("button", { name: "Remover" }).click();
    const confirm = page.getByRole("alertdialog");
    await expect(confirm).toContainText("Remover");
    await confirm.getByRole("button", { name: "Manter" }).click();
    await expect(confirm).toHaveCount(0);
    await expect(items).toHaveCount(before);
    // sample mode does not persist deletes, so the count alone cannot tell: no removal was sent.
    // A one-shot count, not expect(...).toHaveCount(0): that retries until the 4 s toast fades
    // and passed with the delete firing (found by the remove-without-confirm UI mutant).
    await page.waitForTimeout(1_200);
    expect(await page.getByText("Item removido.").count()).toBe(0);
  });
});

test("a fact changed in the Profile reaches the Master only after it is chosen", async ({
  page,
}) => {
  await page.goto("/resume-studio");
  const changed = page.getByTestId("profile-changed");
  await expect(changed).toContainText("Projeto de extensão (DEMO)");
  await expect(changed).toContainText("Mestre");
  await expect(changed).toContainText("Perfil");
  const refresh = page.getByTestId("refresh-profile-facts");
  // nothing is pre-selected: the Master keeps its text until the person picks
  await expect(refresh).toBeDisabled();
  await changed.getByRole("checkbox").first().check();
  await expect(refresh).toBeEnabled();
  await refresh.click();
  await expect(page.getByText(/atualizado\(s\) com o texto do Perfil/)).toBeVisible();
});
