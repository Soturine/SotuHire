import { beforeEach, describe, expect, it, vi } from "vitest";

import { detectBrowserLocale, formatDate, translate } from "@/lib/i18n";
import { applyStoredAppearance, preferenceStorageKeys } from "@/lib/preferences";

describe("local UI preferences", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.className = "";
    Object.defineProperty(window, "matchMedia", {
      configurable: true,
      value: vi.fn().mockReturnValue({ matches: false }),
    });
  });

  it("resolves browser locale and uses locale-aware formatting", () => {
    expect(detectBrowserLocale(["pt-PT", "en-US"])).toBe("pt-BR");
    expect(detectBrowserLocale(["en-GB"])).toBe("en-US");
    expect(translate("en-US", "route.help.title")).toBe("Help center");
    expect(formatDate("2026-08-10T12:00:00Z", "pt-BR")).toContain("2026");
  });

  it("applies persisted theme and language before rendering", () => {
    localStorage.setItem(
      preferenceStorageKeys.preferences,
      JSON.stringify({ locale: "en-US", theme: "dark" }),
    );

    applyStoredAppearance();

    expect(document.documentElement.lang).toBe("en-US");
    expect(document.documentElement).toHaveClass("dark");
    expect(document.documentElement.style.colorScheme).toBe("dark");
  });
});
