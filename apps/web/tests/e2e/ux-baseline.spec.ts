import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

/**
 * UX before/after evidence (2026-11 audit). Runs only with CAPTURE_UX=1 so normal CI is unaffected.
 * For every route and viewport it writes a full-page screenshot and a metrics record: horizontal
 * overflow, axe violations by impact (WCAG 2.x A/AA rules) and console errors. Same demo data, theme,
 * locale and viewport on both sides; CAPTURE_UX_DIR names the output folder (before/ or after/).
 */

const ROUTES = [
  "/",
  "/dashboard",
  "/evidence",
  "/portfolio",
  "/approvals",
  "/profile",
  "/resume",
  "/resume-studio",
  "/application-lab",
  "/job",
  "/match",
  "/ats",
  "/tailor",
  "/github",
  "/tracker",
  "/career",
  "/radar",
  "/public-exams",
  "/intelligence",
  "/sources",
  "/settings",
  "/privacy",
];

const VIEWPORTS = [
  { name: "desktop", width: 1440, height: 900 },
  { name: "mobile", width: 390, height: 844 },
];

const outDir = process.env.CAPTURE_UX_DIR || "ux-capture";

for (const viewport of VIEWPORTS) {
  for (const route of ROUTES) {
    test(`ux evidence ${viewport.name} ${route}`, async ({ page }) => {
      test.skip(process.env.CAPTURE_UX !== "1", "Set CAPTURE_UX=1 to capture UX evidence.");
      const errors: string[] = [];
      page.on("console", (message) => {
        if (message.type() === "error") errors.push(message.text().slice(0, 200));
      });
      page.on("pageerror", (error) => errors.push(String(error).slice(0, 200)));
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.emulateMedia({ colorScheme: "light", reducedMotion: "reduce" });
      await page.goto(route);
      await expect(page.locator("main, [role=main], body").first()).toBeVisible();
      await page.waitForLoadState("networkidle");
      await page.waitForTimeout(400);

      const overflow = await page.evaluate(() => {
        const width = document.documentElement.clientWidth;
        const offenders = [...document.querySelectorAll("body *")]
          .filter((el) => el.getBoundingClientRect().right > width + 1)
          .slice(0, 5)
          .map((el) => `${el.tagName.toLowerCase()}${el.id ? `#${el.id}` : ""}`);
        return {
          scrollWidth: document.documentElement.scrollWidth,
          clientWidth: width,
          offenders,
        };
      });
      const axe = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"])
        .analyze();
      const byImpact: Record<string, number> = {};
      for (const violation of axe.violations) {
        const impact = violation.impact || "unknown";
        byImpact[impact] = (byImpact[impact] || 0) + violation.nodes.length;
      }

      const slug = route === "/" ? "home" : route.slice(1).replaceAll("/", "-");
      const dir = join(outDir, slug);
      mkdirSync(dir, { recursive: true });
      await page.screenshot({ path: join(dir, `${viewport.name}.png`), fullPage: true });
      writeFileSync(
        join(dir, `${viewport.name}.json`),
        JSON.stringify(
          {
            route,
            viewport,
            horizontal_overflow_px: Math.max(0, overflow.scrollWidth - overflow.clientWidth),
            overflow_offenders: overflow.offenders,
            axe_rules: axe.violations.map((v) => ({
              id: v.id,
              impact: v.impact,
              nodes: v.nodes.length,
              targets: v.nodes.slice(0, 8).map((node) => ({
                target: node.target.join(" "),
                html: node.html.slice(0, 160),
                data: (node.any[0]?.data ?? null) as unknown,
              })),
            })),
            axe_nodes_by_impact: byImpact,
            console_errors: errors,
          },
          null,
          2,
        ),
      );
    });
  }
}
