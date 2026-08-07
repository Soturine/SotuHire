import { AlertTriangle, CheckCircle2, FileUp, Loader2 } from "lucide-react";
import { useState } from "react";
import { useApi } from "@/lib/api/hooks";
import { useApiMode } from "@/lib/api/mode";
import type { MasterResume, ResumeIngestionResult } from "@/lib/api/types";
import { toast } from "@/lib/notify";

const MAX_BYTES = 10 * 1024 * 1024;

export async function fileToBase64(file: File): Promise<string> {
  const bytes = new Uint8Array(await file.arrayBuffer());
  let binary = "";
  for (let offset = 0; offset < bytes.length; offset += 32_768) {
    binary += String.fromCharCode(...bytes.subarray(offset, offset + 32_768));
  }
  return btoa(binary);
}

export function ResumeImport({ onImported }: { onImported: (resume: MasterResume) => void }) {
  const api = useApi();
  const { mode } = useApiMode();
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<ResumeIngestionResult | null>(null);
  const [includedEntryIds, setIncludedEntryIds] = useState<Set<string>>(new Set());
  const [reviewConfirmed, setReviewConfirmed] = useState(false);
  const [busy, setBusy] = useState<"ingest" | "save" | null>(null);

  async function inspect(): Promise<void> {
    if (!file) return;
    if (file.size > MAX_BYTES) {
      toast.error("O arquivo excede o limite local de 10 MiB.");
      return;
    }
    setBusy("ingest");
    try {
      const imported = await api.resumeStudioIngest(file.name, await fileToBase64(file));
      setResult(imported);
      setIncludedEntryIds(
        new Set(
          imported.master_resume_draft.sections.flatMap((section) =>
            section.entries.map((entry) => entry.entry_id),
          ),
        ),
      );
      setReviewConfirmed(false);
      toast.success(
        mode === "demo"
          ? "DEMO: prévia fictícia criada; nenhum dado real foi alterado."
          : "Documento extraído localmente. Revise antes de adotar o rascunho.",
      );
    } catch (error) {
      toast.error(error instanceof Error ? error.message : String(error));
    } finally {
      setBusy(null);
    }
  }

  async function adopt(): Promise<void> {
    if (!result) return;
    if (!reviewConfirmed) {
      toast.warning("Confirme a revisão dos blocos antes de criar o Currículo Mestre.");
      return;
    }
    if (includedEntryIds.size === 0) {
      toast.warning("Selecione ao menos um bloco para o Currículo Mestre.");
      return;
    }
    setBusy("save");
    try {
      const reviewedResume: MasterResume = {
        ...result.master_resume_draft,
        raw_text: result.master_resume_draft.sections
          .flatMap((section) => section.entries)
          .filter((entry) => includedEntryIds.has(entry.entry_id))
          .map((entry) => entry.content)
          .filter(Boolean)
          .join("\n\n"),
        sections: result.master_resume_draft.sections.map((section) => ({
          ...section,
          entries: section.entries.map((entry) => {
            const accepted = includedEntryIds.has(entry.entry_id);
            return {
              ...entry,
              enabled: accepted,
              confirmed_by_user: accepted,
              review_status: accepted ? ("confirmed" as const) : ("rejected" as const),
            };
          }),
        })),
      };
      const saved = await api.resumeStudioSaveMaster(reviewedResume);
      onImported(saved.resume);
      toast.success(
        mode === "demo"
          ? "DEMO: alteração apenas simulada; nenhum currículo real foi salvo."
          : "Rascunho adotado como Currículo Mestre.",
      );
    } catch (error) {
      toast.error(error instanceof Error ? error.message : String(error));
    } finally {
      setBusy(null);
    }
  }

  return (
    <section className="rounded-2xl border bg-card p-5 shadow-[var(--shadow-soft)]">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-accent">
            Ingestão segura
          </p>
          <h2 className="mt-1 text-display text-lg">Importar e revisar</h2>
          <p className="mt-1 text-xs text-muted-foreground">
            PDF, DOCX, HTML, TXT ou JSON Resume · até 10 MiB · sem macros, scripts ou rede.
          </p>
        </div>
        <label className="inline-flex cursor-pointer items-center gap-2 rounded-md border px-3 py-2 text-xs font-semibold hover:bg-muted">
          <FileUp className="h-4 w-4" /> Escolher arquivo
          <input
            type="file"
            className="sr-only"
            accept=".pdf,.docx,.html,.htm,.txt,.json"
            onChange={(event) => {
              setFile(event.target.files?.[0] ?? null);
              setResult(null);
            }}
          />
        </label>
      </div>

      {mode === "demo" && (
        <p className="mt-4 rounded-lg border border-warning/30 bg-warning/10 p-3 text-xs">
          <strong>DEMO:</strong> a leitura é simulada e nenhum dado real é enviado ou persistido.
        </p>
      )}

      {file && (
        <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-lg bg-muted/40 p-3 text-xs">
          <span>
            <strong>{file.name}</strong> · {(file.size / 1024).toFixed(1)} KiB
          </span>
          <button
            type="button"
            onClick={inspect}
            disabled={Boolean(busy)}
            className="inline-flex items-center gap-2 rounded-md bg-primary px-3 py-2 font-semibold text-primary-foreground disabled:opacity-50"
          >
            {busy === "ingest" && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            Extrair com segurança
          </button>
        </div>
      )}

      {result && (
        <div className="mt-4 space-y-3 rounded-xl border p-4">
          <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
            <span className="inline-flex items-center gap-1.5 font-semibold">
              {result.document.status === "accepted" ? (
                <CheckCircle2 className="h-4 w-4 text-success" />
              ) : (
                <AlertTriangle className="h-4 w-4 text-warning-foreground" />
              )}
              {result.document.document_type.toUpperCase()} · {result.document.text_blocks.length}{" "}
              bloco(s) · {result.document.pages.length} página(s)
            </span>
            <code title="Hash SHA-256 do arquivo de origem">
              SHA-256 {result.document.source_hash.slice(0, 12)}…
            </code>
          </div>
          <div className="space-y-2" data-testid="ingestion-block-review">
            <p className="text-xs font-semibold">Revisão de blocos</p>
            {result.master_resume_draft.sections.flatMap((section) =>
              section.entries.map((entry) => (
                <label
                  key={entry.entry_id}
                  className="flex items-start gap-3 rounded-lg bg-muted/40 p-3 text-xs leading-5"
                >
                  <input
                    type="checkbox"
                    checked={includedEntryIds.has(entry.entry_id)}
                    onChange={() => {
                      setIncludedEntryIds((current) => {
                        const next = new Set(current);
                        if (next.has(entry.entry_id)) next.delete(entry.entry_id);
                        else next.add(entry.entry_id);
                        return next;
                      });
                      setReviewConfirmed(false);
                    }}
                  />
                  <span>
                    <strong>{entry.title || section.title}</strong>
                    <span className="ml-2 rounded bg-accent/10 px-1.5 py-0.5 text-[10px] text-accent">
                      sourced · confirmar ou rejeitar
                    </span>
                    <span className="mt-1 block whitespace-pre-wrap">{entry.content}</span>
                  </span>
                </label>
              )),
            )}
          </div>
          <div className="rounded-lg border p-3 text-xs" data-testid="ingestion-provenance">
            <strong>Proveniência preservada</strong>
            <ul className="mt-2 space-y-1 text-muted-foreground">
              {result.document.provenance.slice(0, 6).map((item) => (
                <li key={`${item.source_ref}-${JSON.stringify(item.location)}`}>
                  {item.extraction_method} · {item.source} · {item.source_ref}
                  {Object.keys(item.location).length > 0
                    ? ` · ${Object.entries(item.location)
                        .map(([key, value]) => `${key}=${value}`)
                        .join(", ")}`
                    : ""}
                </li>
              ))}
            </ul>
          </div>
          {result.document.warnings.map((warning) => (
            <p key={warning} className="text-xs text-warning-foreground">
              {warning}
            </p>
          ))}
          <label className="flex items-start gap-2 text-xs">
            <input
              type="checkbox"
              checked={reviewConfirmed}
              onChange={(event) => setReviewConfirmed(event.target.checked)}
            />
            Revisei os blocos selecionados; eles podem entrar como evidência confirmada no Currículo
            Mestre.
          </label>
          <button
            type="button"
            onClick={adopt}
            disabled={Boolean(busy) || !reviewConfirmed || includedEntryIds.size === 0}
            className="inline-flex items-center gap-2 rounded-md border px-3 py-2 text-xs font-semibold hover:bg-muted disabled:opacity-50"
          >
            {busy === "save" && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            Adotar rascunho como Currículo Mestre
          </button>
        </div>
      )}
    </section>
  );
}
