import { expect, test, type Page } from "@playwright/test";

/**
 * CP-DATA01, as a new user sees it in API mode: no Master Resume yet must not be an error screen,
 * and the resume is built from facts already confirmed in the Profile instead of a second import.
 * Demo mode always returns a master, which is how the dead end went unnoticed.
 */

const master = {
  master_resume_id: "master-fixture",
  profile_id: "default",
  title: "Currículo Mestre",
  target_role: "Enfermeira UTI",
  summary: "Enfermeira com foco em segurança do paciente.",
  raw_text: "",
  source_type: "profile",
  source_refs: ["profile:default"],
  source_profile_item_ids: ["item-work"],
  sections: [
    {
      section_id: "s1",
      section_type: "experience",
      title: "Experiência",
      position: 0,
      enabled: true,
      content: "",
      entries: [
        {
          entry_id: "e1",
          entry_type: "experience",
          title: "Enfermeira assistencial",
          subtitle: "Hospital Fictício",
          content: "Plantões em UTI adulto.",
          start_date: "2021-03",
          end_date: "",
          position: 0,
          enabled: true,
          source_profile_item_ids: ["item-work"],
          source_refs: [],
          review_status: "confirmed",
          confirmed_by_user: true,
          created_at: "2026-11-14T10:00:00Z",
          updated_at: "2026-11-14T10:00:00Z",
        },
      ],
      created_at: "2026-11-14T10:00:00Z",
      updated_at: "2026-11-14T10:00:00Z",
    },
  ],
  validation_warnings: [],
  created_at: "2026-11-14T10:00:00Z",
  updated_at: "2026-11-14T10:00:00Z",
};

async function mockLocalApi(page: Page, calls: string[]) {
  let created = false;
  let applied = false;
  const envelope = (data: unknown) => ({ ok: true, data, request_id: "fixture", warnings: [] });
  await page.addInitScript(() => localStorage.setItem("sotuhire.api-mode", "real"));
  await page.route("http://127.0.0.1:8787/api/v1/**", async (route) => {
    const url = new URL(route.request().url());
    const method = route.request().method();
    calls.push(`${method} ${url.pathname}`);
    const path = url.pathname.replace("/api/v1", "");
    if (path.endsWith("/security/pairing/start"))
      return route.fulfill({ json: envelope({ challenge_id: "c", proof: "p" }) });
    if (path.endsWith("/security/pairing/complete"))
      return route.fulfill({ json: envelope({ csrf_token: "memory-only" }) });
    if (path === "/resume-studio/master" && method === "GET")
      return created
        ? route.fulfill({ json: envelope({ resume: master }) })
        : route.fulfill({
            status: 404,
            json: { ok: false, error: { message: "Currículo Mestre ainda não foi criado." } },
          });
    if (path === "/resume-studio/master/from-profile") {
      created = true;
      return route.fulfill({ status: 201, json: envelope({ resume: master }) });
    }
    if (path === "/resume-studio/master/profile-updates" && method === "GET")
      return route.fulfill({
        json: envelope({
          master_resume_id: master.master_resume_id,
          items: applied
            ? []
            : [
                {
                  item_id: "item-lang",
                  item_type: "language",
                  title: "Inglês intermediário",
                  subtitle: "",
                  section_title: "Idiomas",
                },
              ],
        }),
      });
    if (path === "/resume-studio/master/profile-updates" && method === "POST") {
      applied = true;
      return route.fulfill({ json: envelope({ resume: master }) });
    }
    if (path.startsWith("/resume-studio/variants") && method === "GET")
      return route.fulfill({
        json: envelope({
          items: [],
          pagination: { limit: 25, offset: 0, total: 0, has_more: false },
        }),
      });
    if (path.startsWith("/resume-studio/templates"))
      return route.fulfill({ json: envelope({ items: [] }) });
    return route.fulfill({ json: envelope({ items: [] }) });
  });
}

test("a new user builds the Master Resume from the Profile, then reviews later profile facts", async ({
  page,
}) => {
  const calls: string[] = [];
  await mockLocalApi(page, calls);
  await page.goto("/resume-studio");

  await expect(
    page.getByRole("heading", { name: "Seu Currículo Mestre ainda não existe" }),
  ).toBeVisible();
  await expect(page.getByText(/Não foi possível|Erro HTTP 404/)).toHaveCount(0);
  await page.getByTestId("master-from-profile").click();

  await expect(page.getByTestId("resume-studio")).toBeVisible();
  expect(calls).toContain("POST /api/v1/resume-studio/master/from-profile");

  const updates = page.getByTestId("profile-updates");
  await expect(updates).toContainText("Inglês intermediário");
  await expect(updates.getByRole("checkbox", { name: /Inglês intermediário/ })).toBeChecked();
  await page.getByTestId("apply-profile-updates").click();
  await expect(updates).toHaveCount(0);
  expect(calls).toContain("POST /api/v1/resume-studio/master/profile-updates");
});
