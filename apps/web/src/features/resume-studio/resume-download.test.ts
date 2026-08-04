import { describe, expect, it } from "vitest";
import { resumeExportBlob } from "./resume-download";
import type { ResumeExportResult } from "@/lib/api/types";

function result(
  format: "json_resume" | "pdf",
  payload: Record<string, unknown>,
): ResumeExportResult {
  return {
    export: {
      export_id: "export-test",
      master_resume_id: "master-test",
      resume_variant_id: "variant-test",
      template_id: "classic",
      format,
      status: "ready",
      file_name: format === "pdf" ? "resume.pdf" : "resume.json",
      content_hash: "hash",
      warnings: [],
      created_at: "2026-08-03T00:00:00Z",
    },
    payload,
  };
}

describe("resumeExportBlob", () => {
  it("serializes JSON Resume as JSON", async () => {
    const blob = resumeExportBlob(result("json_resume", { basics: { name: "Pessoa Teste" } }));
    expect(blob.type).toBe("application/json");
    expect(await blob.text()).toContain("Pessoa Teste");
  });

  it("decodes the real binary payload returned by the API", async () => {
    const blob = resumeExportBlob(
      result("pdf", {
        content_base64: btoa("%PDF-1.4\nfixture"),
        media_type: "application/pdf",
      }),
    );
    expect(blob.type).toBe("application/pdf");
    expect(await blob.text()).toContain("%PDF-1.4");
  });

  it("rejects a ready binary export without content", () => {
    expect(() => resumeExportBlob(result("pdf", {}))).toThrow(/conteúdo binário/);
  });
});
