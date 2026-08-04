import type { ResumeExportFormat, ResumeExportResult } from "@/lib/api/types";

const DEFAULT_MEDIA_TYPES: Record<ResumeExportFormat, string> = {
  json_resume: "application/json",
  pdf: "application/pdf",
  docx: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
};

export function resumeExportBlob(result: ResumeExportResult): Blob {
  if (result.export.status !== "ready" || !result.payload) {
    throw new Error(result.export.warnings[0] ?? "A exportação ainda não está pronta.");
  }
  if (result.export.format === "json_resume") {
    return new Blob([JSON.stringify(result.payload, null, 2)], {
      type: DEFAULT_MEDIA_TYPES.json_resume,
    });
  }

  const encoded = result.payload.content_base64;
  if (typeof encoded !== "string" || !encoded) {
    throw new Error("A API não retornou o conteúdo binário esperado.");
  }
  const binary = atob(encoded);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  const mediaType =
    typeof result.payload.media_type === "string"
      ? result.payload.media_type
      : DEFAULT_MEDIA_TYPES[result.export.format];
  return new Blob([bytes], { type: mediaType });
}

export function downloadResumeExport(result: ResumeExportResult): void {
  const href = URL.createObjectURL(resumeExportBlob(result));
  const link = document.createElement("a");
  link.href = href;
  link.download = result.export.file_name;
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(href), 0);
}
