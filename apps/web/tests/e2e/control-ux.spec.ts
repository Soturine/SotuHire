import { expect, test } from "@playwright/test";

/**
 * CP-UX04: human control made visible. Before, "Aprovar" in sample mode reloaded the static queue
 * and seemed to do nothing, a failed transition said nothing, statuses and risks were raw English
 * ids, and the change preview was raw JSON.
 */

test("a proposal goes approve → run → undo, each step in its own list, never all at once", async ({
  page,
}) => {
  await page.goto("/approvals");
  const card = page.getByRole("article").first();
  await expect(card).toContainText("risco baixo");
  // checked once the queue has rendered: before, it ran before loading and could never fail
  await expect(page.getByRole("button", { name: /Aprovar tudo/i })).toHaveCount(0);
  await expect(card).toContainText("proposta");
  await expect(card.getByRole("table")).toBeVisible();

  await card.getByRole("button", { name: "Aprovar" }).click();
  await expect(page.getByText("Aprovada. Nada foi executado ainda.")).toBeVisible();
  await page.getByRole("button", { name: /^Aprovadas/ }).click();
  const approved = page.getByRole("article").first();
  await expect(approved).toContainText("aprovada");
  await approved.getByRole("button", { name: "Executar localmente" }).click();
  await expect(page.getByText("Executada localmente.")).toBeVisible();

  await page.getByRole("button", { name: /^Encerradas/ }).click();
  const done = page.getByRole("article").first();
  await done.getByRole("button", { name: "Desfazer" }).click();
  await expect(page.getByText("Desfeita.")).toBeVisible();
  await expect(page.getByRole("article").first()).toContainText("desfeita");
});

test("a refused transition is said, and the proposal stays where it was", async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem("sotuhire.api-mode", "real"));
  const envelope = (data: unknown) => ({ ok: true, data, request_id: "fixture", warnings: [] });
  const proposal = {
    proposal_id: "p1",
    action_type: "create_task",
    title: "Criar tarefa de revisão",
    description: "",
    reason: "Uma evidência aguarda confirmação.",
    evidence_refs: ["e1"],
    affected_entities: ["task"],
    before_snapshot: {},
    after_preview: { title: "Revisar evidência" },
    risk: "low",
    reversible: true,
    undo_strategy: "Remover a tarefa criada",
    status: "proposed",
    created_at: "2026-11-15T10:00:00Z",
  };
  await page.route("http://127.0.0.1:8787/**", async (route) => {
    const url = new URL(route.request().url());
    if (url.pathname === "/api/v2/approvals") return route.fulfill({ json: envelope([proposal]) });
    if (url.pathname === "/api/v2/approvals/p1/approve")
      return route.fulfill({
        status: 409,
        json: { ok: false, error: { message: "A proposta ficou desatualizada." } },
      });
    return route.fulfill({ json: envelope({}) });
  });
  await page.goto("/approvals");
  const card = page.getByRole("article").first();
  await card.getByRole("button", { name: "Aprovar" }).click();
  await expect(
    page.getByText("A ação não foi feita: A proposta ficou desatualizada."),
  ).toBeVisible();
  await expect(card).toContainText("proposta");
  await expect(card.getByRole("button", { name: "Aprovar" })).toBeEnabled();
});

test("settings say where the text goes for the chosen AI provider", async ({ page }) => {
  await page.goto("/settings");
  const destination = page.getByTestId("ai-data-destination");
  await expect(destination).toContainText("Nada sai da sua máquina");
  await expect(page.getByTestId("ai-provider-local")).toHaveAttribute("aria-pressed", "true");
  await page.getByTestId("ai-provider-anthropic").click();
  await expect(destination).toContainText("para Claude pelo backend local");
  await expect(destination).toContainText("A chave fica só no backend");
  await expect(page.getByTestId("ai-provider-anthropic")).toHaveAttribute("aria-pressed", "true");
});

test("the Copilot drawer names suggestions and its proposal lands in the approval queue", async ({
  page,
}) => {
  await page.goto("/dashboard");
  await expect(page.getByRole("heading", { name: "Cockpit de carreira" })).toBeVisible();
  await page.getByRole("button", { name: "Abrir Copilot contextual" }).click();
  const drawer = page.getByRole("dialog");
  await expect(drawer).toContainText("Contexto: Cockpit de carreira");
  await expect(
    drawer.getByRole("heading", { name: "Preparar a próxima entrevista" }),
  ).toBeVisible();
  await expect(drawer).not.toContainText("INTERVIEW");
  await drawer.getByRole("button", { name: "Criar proposta" }).first().click();
  await expect(page.getByText(/Proposta criada/)).toBeVisible();
  await drawer.getByRole("link", { name: "Ver em Aprovações" }).click();
  await expect(page).toHaveURL(/\/approvals$/);
  await expect(page.getByRole("article").first()).toContainText("Revisar recomendação do Copilot");
});

test("lab tells advice apart from changes, and a change without evidence cannot be accepted", async ({
  page,
}) => {
  await page.goto("/application-lab?novo=1");
  await page.getByRole("button", { name: "Iniciar preparação" }).click();
  await expect(page.getByText("Sessão salva neste computador")).toBeVisible();
  await page.getByRole("button", { name: /Melhorias$/ }).click();
  const advice = page
    .getByRole("article")
    .filter({ hasText: "Orientação: não altera o currículo" });
  await expect(advice.getByRole("button", { name: "Entendi" })).toBeVisible();
  await expect(advice).not.toContainText("não pode virar fato");
  const change = page.getByRole("article").filter({ hasText: "Antes" }).first();
  await expect(change.getByRole("button", { name: "Aceitar", exact: true })).toBeEnabled();
  // a new claim without confirmed evidence: the interlock is visible, not only enforced by the API
  const claim = page.getByRole("article").filter({ hasText: "ISO 9001 na unidade" });
  await expect(claim).toContainText("Sem evidência — não pode virar fato");
  await expect(claim.getByRole("button", { name: "Aceitar", exact: true })).toBeDisabled();
});
