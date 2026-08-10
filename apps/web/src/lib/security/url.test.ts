import { describe, expect, it } from "vitest";
import { hasExactWebHost, isGitHubWebUrl } from "./url";

describe("structural URL allowlists", () => {
  it("accepts only the exact host", () => {
    expect(isGitHubWebUrl("https://github.com/Soturine/SotuHire")).toBe(true);
    expect(isGitHubWebUrl("https://evil-github.com/repo")).toBe(false);
    expect(isGitHubWebUrl("https://github.com.evil.net/repo")).toBe(false);
    expect(isGitHubWebUrl("https://github.com@evil.net/repo")).toBe(false);
    expect(isGitHubWebUrl("https://evil.net/github.com/repo")).toBe(false);
  });

  it("rejects credentials and non-web protocols", () => {
    expect(hasExactWebHost("https://user@example.com", ["example.com"])).toBe(false);
    expect(hasExactWebHost("file://example.com/path", ["example.com"])).toBe(false);
  });
});
