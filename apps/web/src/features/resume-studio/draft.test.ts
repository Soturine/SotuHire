import { describe, expect, it } from "vitest";
import type { ResumeVariant } from "@/lib/api/types";
import { pickDraft } from "./draft";

const base = {
  resume_variant_id: "v1",
  master_resume_id: "m1",
  job_snapshot_id: "",
  title: "Variante",
  target_role: "Analista",
  sections: [],
  source_profile_item_ids: [],
  change_set: [],
  validation_warnings: [],
  created_at: "2026-11-01T10:00:00Z",
} satisfies Omit<ResumeVariant, "updated_at">;

const server: ResumeVariant = { ...base, updated_at: "2026-11-14T12:00:00Z", title: "Servidor" };

describe("pickDraft", () => {
  it("keeps the server copy when there is no draft", () => {
    expect(pickDraft(null, server)).toEqual({ variant: server, restoredDraft: false });
  });

  it("restores a draft of the same variant that is newer than the server copy", () => {
    const draft = { ...base, updated_at: "2026-11-14T12:05:00Z", title: "Rascunho" };
    expect(pickDraft(draft, server)).toEqual({ variant: draft, restoredDraft: true });
  });

  it("never lets an older draft overwrite newer server content", () => {
    // The bug: any stored draft used to win, so an edit saved elsewhere was silently replaced.
    const stale = { ...base, updated_at: "2026-11-13T09:00:00Z", title: "Velho" };
    expect(pickDraft(stale, server).variant.title).toBe("Servidor");
  });

  it("ignores a draft of another variant", () => {
    const other = { ...base, resume_variant_id: "v2", updated_at: "2026-11-15T00:00:00Z" };
    expect(pickDraft(other, server).restoredDraft).toBe(false);
  });
});
