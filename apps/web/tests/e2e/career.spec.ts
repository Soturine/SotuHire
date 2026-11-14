import { expect, test } from "@playwright/test";

// SH-NEW-004: a reminder used to be attached silently to whichever task was listed first.
test("career reminders link to a task only when the user chooses one", async ({ page }) => {
  await page.goto("/career");

  await page.getByLabel("Tarefa", { exact: true }).fill("Revisar portfólio E2E");
  await page.getByRole("button", { name: /Adicionar tarefa/ }).click();
  await expect(page.locator("body")).toContainText("Revisar portfólio E2E");

  const related = page.getByRole("combobox", { name: "Tarefa relacionada (opcional)" });
  await expect(related).toHaveValue("");
  await expect(related.locator("option", { hasText: "Revisar portfólio E2E" })).toHaveCount(1);

  await page.getByLabel("Título").fill("Lembrete sem tarefa E2E");
  await page.getByLabel("Data e hora").fill("2026-12-01T09:30");
  await page.getByRole("button", { name: /Agendar lembrete local/ }).click();
  await expect(page.locator("body")).toContainText("Lembrete sem tarefa E2E");
  await expect(related).toHaveValue("");
});
