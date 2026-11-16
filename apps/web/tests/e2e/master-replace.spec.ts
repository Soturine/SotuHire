import { expect, test } from "@playwright/test";

// Re-importing a resume while a Master Resume exists replaces it only after the person says so.
test("re-importing a resume asks before it replaces the current Master Resume", async ({
  page,
}) => {
  await page.goto("/resume-studio");
  await expect(page.getByTestId("resume-studio")).toBeVisible();

  await page.getByText("Importar outro currículo para o Mestre").click();
  await page.locator('input[type="file"]').setInputFiles({
    name: "curriculo-ficticio.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("Experiência\n\nAnalista fictícia de dados, projeto sintético."),
  });
  await page.getByRole("button", { name: "Extrair com segurança" }).click();
  await page.getByLabel(/Revisei os blocos selecionados/).check();

  const warning = page.getByTestId("master-replace-warning");
  await expect(warning).toContainText("Isto substitui o Currículo Mestre atual");
  await expect(warning).toContainText("não é apagado");
  const replace = page.getByRole("button", { name: "Substituir o Currículo Mestre" });
  await expect(replace).toBeDisabled();

  await page.getByTestId("master-replace-confirm").check();
  await expect(replace).toBeEnabled();
});
