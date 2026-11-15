import { expect, type Page } from "@playwright/test";

/**
 * Navigate the way a person does with the journey sidebar: if the screen's journey is closed,
 * open it first, then follow the link. Client-side navigation keeps in-memory state (API mode
 * switched a moment ago, for instance), which a page.goto would reset.
 */
export async function navTo(page: Page, name: string | RegExp) {
  const nav = page.getByRole("navigation", { name: /Navegação principal|Main navigation/ });
  await expect(nav).toBeVisible();
  const section = nav
    .locator(":scope > ul > li")
    .filter({ has: page.locator("a", { hasText: name }) });
  const closed = section.locator('button[aria-expanded="false"]');
  if (await closed.count()) await closed.first().click();
  await nav.getByRole("link", { name }).first().click();
}

/** A toast with this text appeared (not any text anywhere on the page). */
export async function expectToast(page: Page, text: RegExp) {
  await expect(page.locator("[data-sonner-toast]").filter({ hasText: text }).first()).toBeVisible();
}
