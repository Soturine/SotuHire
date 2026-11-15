import { describe, expect, it } from "vitest";

import { profileSourceLabel, profileTypeLabel } from "./profile-labels";

describe("profile labels", () => {
  it("names known types in Portuguese, including academic ones from the Lattes parser", () => {
    expect(profileTypeLabel("higher_education")).toBe("Formação superior");
    expect(profileTypeLabel("experience")).toBe("Experiência");
  });

  it("never shows a raw snake_case identifier", () => {
    expect(profileTypeLabel("some_new_type")).toBe("Some new type");
    expect(profileSourceLabel("demo_resume")).toBe("Currículo de exemplo");
    expect(profileSourceLabel("future_source")).toBe("Future source");
    expect(profileSourceLabel(undefined)).toBe("Informado por você");
  });
});
