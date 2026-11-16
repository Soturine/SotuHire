import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

/**
 * UX before/after evidence (2026-11 audit). Runs only with CAPTURE_UX=1 so normal CI is unaffected.
 * For every route and viewport it writes a full-page screenshot and a metrics record: horizontal
 * overflow, axe violations by impact (WCAG 2.x A/AA rules) and console errors. Same demo data, theme,
 * locale and viewport on both sides; CAPTURE_UX_DIR names the output folder (before/ or after/).
 *
 * Matrix (env, comma-separated): CAPTURE_UX_VIEWPORTS (desktop,tablet,mobile,small; default
 * desktop,mobile), CAPTURE_UX_THEMES (light,dark; default light), CAPTURE_UX_LOCALES (pt-BR,en-US;
 * default pt-BR). The file name is <viewport>[-<theme>][-<locale>].png, so the 2026-11 default
 * capture keeps its original names.
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
  // added in CP-UX00 after reconciling with src/routes: these three were never captured
  "/interviews",
  "/ai-quality",
  "/help",
];

const ALL_VIEWPORTS = [
  { name: "desktop", width: 1440, height: 900 },
  { name: "tablet", width: 1024, height: 768 },
  { name: "mobile", width: 390, height: 844 },
  { name: "small", width: 360, height: 800 },
];
const pick = (name: string, fallback: string) =>
  (process.env[name] || fallback).split(",").map((value) => value.trim());
const wanted = pick("CAPTURE_UX_VIEWPORTS", "desktop,mobile");
const VIEWPORTS = ALL_VIEWPORTS.filter((viewport) => wanted.includes(viewport.name));
const THEMES = pick("CAPTURE_UX_THEMES", "light") as ("light" | "dark")[];
const LOCALES = pick("CAPTURE_UX_LOCALES", "pt-BR");

const outDir = process.env.CAPTURE_UX_DIR || "ux-capture";

const combos = VIEWPORTS.flatMap((viewport) =>
  THEMES.flatMap((theme) => LOCALES.map((locale) => ({ viewport, theme, locale }))),
);

for (const { viewport, theme, locale } of combos) {
  const suffix = `${theme === "light" ? "" : `-${theme}`}${locale === "pt-BR" ? "" : `-${locale}`}`;
  for (const route of ROUTES) {
    test(`ux evidence ${viewport.name}${suffix} ${route}`, async ({ page }) => {
      test.skip(process.env.CAPTURE_UX !== "1", "Set CAPTURE_UX=1 to capture UX evidence.");
      const errors: string[] = [];
      page.on("console", (message) => {
        if (message.type() === "error") errors.push(message.text().slice(0, 200));
      });
      page.on("pageerror", (error) => errors.push(String(error).slice(0, 200)));
      await page.addInitScript((value) => {
        localStorage.setItem(
          "sotuhire.ui-preferences.v1",
          JSON.stringify({ locale: value, theme: "system" }),
        );
      }, locale);
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.emulateMedia({ colorScheme: theme, reducedMotion: "reduce" });
      await page.goto(route);
      await expect(page.locator("main, [role=main], body").first()).toBeVisible();
      await page.waitForLoadState("networkidle");
      // demo calls simulate 400-800 ms of latency and networkidle does not wait for them; at
      // 400 ms axe could catch a control in the middle of its disabled -> enabled switch
      await page.waitForTimeout(1_000);

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
      await page.screenshot({ path: join(dir, `${viewport.name}${suffix}.png`), fullPage: true });
      writeFileSync(
        join(dir, `${viewport.name}${suffix}.json`),
        JSON.stringify(
          {
            route,
            viewport,
            theme,
            locale,
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
