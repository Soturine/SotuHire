import { describe, expect, it } from "vitest";

import { messages } from "@/lib/i18n/messages";
import { NAV_ENTRIES } from "@/lib/navigation";
import { highlight, normalize, rank, search } from "./search";

const pt = messages["pt-BR"];
const routes = NAV_ENTRIES.map((entry) => ({
  path: entry.path,
  label: pt[entry.label],
  keywords: entry.keywords,
}));

describe("search", () => {
  it("ignores accents and case in both directions", () => {
    expect(normalize("Estúdio de Currículo")).toBe("estudio de curriculo");
    expect(rank("curriculo", { label: "Estúdio de Currículo" })).toBeGreaterThan(0);
    expect(rank("CURRÍCULO", { label: "Estudio de curriculo" })).toBeGreaterThan(0);
  });

  it("finds the screens people ask for, best first", () => {
    // These queries returned nothing in the previous palette (baseline CP-UX00).
    expect(
      search("curriculo", routes, (r) => r)
        .slice(0, 2)
        .map((r) => r.path)
        .sort(),
    ).toEqual(["/resume", "/resume-studio"]);
    expect(search("vaga", routes, (r) => r).map((r) => r.path)).toContain("/job");
    expect(search("concurso", routes, (r) => r)[0].path).toBe("/public-exams");
    expect(search("aprovar", routes, (r) => r)[0].path).toBe("/approvals");
  });

  it("requires every word and returns nothing for nonsense", () => {
    expect(search("curriculo zzz", routes, (r) => r)).toEqual([]);
    expect(search("", routes, (r) => r)).toEqual([]);
  });

  it("ranks a label start above a keyword hit", () => {
    expect(rank("radar", { label: "Radar" })).toBeGreaterThan(
      rank("radar", { label: "Vagas", keywords: "radar" }),
    );
  });

  it("every registered screen is reachable by its own label", () => {
    for (const route of routes) {
      expect(search(route.label, routes, (r) => r)[0].path, route.label).toBe(route.path);
    }
  });

  it("highlights without changing the text and without HTML", () => {
    const parts = highlight("Estúdio de Currículo", "curriculo");
    expect(parts.map((p) => p.text).join("")).toBe("Estúdio de Currículo");
    expect(parts.filter((p) => p.match).map((p) => p.text)).toEqual(["Currículo"]);
    expect(
      highlight("<b>x</b>", "b")
        .map((p) => p.text)
        .join(""),
    ).toBe("<b>x</b>");
  });
});

// Ranking and folding rules pinned one by one (StrykerJS survivors, CP-UX06).
describe("search rules", () => {
  it("folds accents, case and surrounding spaces", () => {
    expect(normalize("  Ação RÁPIDA ")).toBe("acao rapida");
  });

  it("scores where each word matched, and 0 when any word is missing", () => {
    const item = { label: "Pós-graduação clínica", keywords: "residencia", detail: "plantões" };
    expect(rank("pos", item)).toBe(100); // label start
    expect(rank("graduacao", item)).toBe(60); // word start after a hyphen
    expect(rank("linica", item)).toBe(40); // substring
    expect(rank("resid", item)).toBe(25); // keyword
    expect(rank("plantoes", item)).toBe(10); // detail, accent-folded
    expect(rank("pos inexistente", item)).toBe(0); // every word must match
    expect(rank("   ", item)).toBe(0);
  });

  it("highlights the accented original text from an unaccented query", () => {
    const parts = highlight("Currículo", "curriculo");
    expect(
      parts
        .filter((part) => part.match)
        .map((part) => part.text)
        .join(""),
    ).toBe("Currículo");
    expect(highlight("Currículo", "  ")).toEqual([{ text: "Currículo", match: false }]);
  });
});
