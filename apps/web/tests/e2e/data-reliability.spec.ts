import { expect, test } from "@playwright/test";

test("data reliability panel validates before an explicitly confirmed restore", async ({
  page,
}) => {
  await page.goto("/privacy");

  await expect(page.getByRole("heading", { name: "Privacidade e dados" })).toBeVisible();
  await expect(page.getByText("Confiabilidade dos dados")).toBeVisible();
  await expect(page.getByText("Saudável", { exact: true })).toBeVisible();

  await page.getByTestId("validate-restore").click();
  await expect(page.getByTestId("restore-confirmation")).toBeVisible();
  await expect(page.getByTestId("apply-restore")).toBeDisabled();

  await page.getByTestId("restore-confirmation").fill("RESTAURAR");
  await expect(page.getByTestId("apply-restore")).toBeEnabled();
  await page.getByTestId("apply-restore").click();
  await expect(page.getByRole("alertdialog")).toBeVisible();
  await page.getByRole("button", { name: "Confirmar restauração" }).click();

  await expect(page.getByText("Restauração de demonstração concluída.")).toBeVisible();
});
