import { describe, expect, it } from "vitest";

import { sampleLabel } from "./ai-quality";

describe("AI quality sample labels", () => {
  it("does not imply comparison with a small sample", () => {
    expect(sampleLabel("insufficient")).toBe("insuficiente");
    expect(sampleLabel("indicative")).toBe("indicativo");
    expect(sampleLabel("comparable")).toBe("comparável");
  });
});
