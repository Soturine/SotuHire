import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowDown,
  ArrowUp,
  CheckCircle2,
  Download,
  Eye,
  FileJson,
  FileText,
  History,
  Loader2,
  MonitorUp,
  Redo2,
  Save,
  Undo2,
} from "lucide-react";
import { useEffect, useMemo, useReducer, useRef, useState } from "react";
import { AppShell } from "@/components/app-shell";
import {
  approximatePageCount,
  createResumeEditorState,
  resumeEditorReducer,
} from "@/components/resume-editor-state";
import { EmptyState, ErrorState, LoadingState } from "@/components/states";
import { ResumeImport } from "@/features/document-ingestion/resume-import";
import { ProfessionalAssetsPanel } from "@/features/professional-assets/professional-assets-panel";
import { downloadResumeExport } from "@/features/resume-studio/resume-download";
import { useApi } from "@/lib/api/hooks";
import { useApiMode } from "@/lib/api/mode";
import type {
  MasterResume,
  ResumeExportFormat,
  ResumeSection,
  ResumeVariant,
} from "@/lib/api/types";
import { toast } from "@/lib/notify";
import { cn } from "@/lib/utils";

type ResumeStudioSearch = {
  capture_id?: string;
  job_snapshot_id?: string;
};

export const Route = createFileRoute("/resume-studio")({
  validateSearch: (search: Record<string, unknown>): ResumeStudioSearch => ({
    capture_id: typeof search.capture_id === "string" ? search.capture_id : undefined,
    job_snapshot_id:
      typeof search.job_snapshot_id === "string" ? search.job_snapshot_id : undefined,
  }),
  head: () => ({ meta: [{ title: "Resume Studio — SotuHire" }] }),
  component: ResumeStudioPage,
});

type StudioView = "editor" | "preview" | "diff";

function ResumeStudioPage() {
  const api = useApi();
  const { mode } = useApiMode();
  const queryClient = useQueryClient();
  const search = Route.useSearch();
  const masterQ = useQuery({
    queryKey: ["resume-studio-master", mode],
    queryFn: () => api.resumeStudioMaster(),
  });
  const variantsQ = useQuery({
    queryKey: ["resume-studio-variants", mode, masterQ.data?.resume.master_resume_id],
    queryFn: () => api.resumeStudioVariants(masterQ.data?.resume.master_resume_id),
    enabled: Boolean(masterQ.data?.resume),
  });
  const templatesQ = useQuery({
    queryKey: ["resume-studio-templates", mode],
    queryFn: () => api.resumeStudioTemplates(),
  });
  const [view, setView] = useState<StudioView>("editor");
  const [templateId, setTemplateId] = useState("classic");
  const [pageSize, setPageSize] = useState<"A4" | "Letter">("A4");
  const [loaded, setLoaded] = useState(false);
  const fallback = useMemo(() => emptyVariant(), []);
  const [state, dispatch] = useReducer(resumeEditorReducer, fallback, createResumeEditorState);
  const autosaveTimer = useRef<number | undefined>(undefined);

  useEffect(() => {
    if (loaded || !masterQ.data?.resume || !variantsQ.data) return;
    const storageKey = `sotuhire:resume-draft:${masterQ.data.resume.master_resume_id}`;
    const stored = localStorage.getItem(storageKey);
    let selected = variantsQ.data.items[0] ?? variantFromMaster(masterQ.data.resume);
    if (stored) {
      try {
        selected = JSON.parse(stored) as ResumeVariant;
      } catch {
        localStorage.removeItem(storageKey);
      }
    }
    dispatch({ type: "replace", variant: selected });
    setLoaded(true);
  }, [loaded, masterQ.data, variantsQ.data]);

  const autosave = useMutation({
    mutationFn: (variant: ResumeVariant) =>
      variantsQ.data?.items.some((item) => item.resume_variant_id === variant.resume_variant_id)
        ? api.resumeStudioUpdateVariant(variant.resume_variant_id, {
            title: variant.title,
            target_role: variant.target_role,
            sections: variant.sections,
            validation_warnings: variant.validation_warnings,
          })
        : api.resumeStudioSaveVariant(variant),
    onSuccess: () => dispatch({ type: "saved" }),
    onError: (error: Error) => toast.warning(`Rascunho salvo no navegador. API: ${error.message}`),
  });

  useEffect(() => {
    if (!loaded || !state.dirty) return;
    window.clearTimeout(autosaveTimer.current);
    autosaveTimer.current = window.setTimeout(() => {
      const storageKey = `sotuhire:resume-draft:${state.present.master_resume_id}`;
      localStorage.setItem(storageKey, JSON.stringify(state.present));
      if (navigator.onLine) autosave.mutate(state.present);
    }, 650);
    return () => window.clearTimeout(autosaveTimer.current);
  }, [autosave, loaded, state.dirty, state.present]);

  const exportMutation = useMutation({
    mutationFn: (format: ResumeExportFormat) =>
      api.resumeStudioExport(state.present.resume_variant_id, format, templateId, pageSize),
    onSuccess: (result) => {
      try {
        downloadResumeExport(result);
        toast.success(
          mode === "demo"
            ? "DEMO: artefato fictício exportado; nenhum dado real foi alterado."
            : `${result.export.format.toUpperCase()} exportado com o conteúdo renderizado.`,
        );
      } catch (error) {
        toast.warning(error instanceof Error ? error.message : String(error));
      }
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const validation = useMemo(() => validateVariant(state.present), [state.present]);
  const pages = approximatePageCount(state.present, pageSize);

  return (
    <AppShell
      title="Resume Studio"
      description="Currículo Mestre, variantes rastreáveis, preview ATS-safe e export honesto."
      actions={
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          {autosave.isPending ? (
            <>
              <Loader2 className="h-3.5 w-3.5 animate-spin" /> Salvando…
            </>
          ) : state.dirty ? (
            <>
              <History className="h-3.5 w-3.5" /> Rascunho local
            </>
          ) : (
            <>
              <CheckCircle2 className="h-3.5 w-3.5 text-success" /> Salvo
            </>
          )}
        </div>
      }
    >
      {masterQ.isLoading || variantsQ.isLoading || templatesQ.isLoading || !loaded ? (
        <LoadingState label="Abrindo seu estúdio local…" />
      ) : masterQ.isError ? (
        <ErrorState error={masterQ.error} onRetry={() => masterQ.refetch()} />
      ) : !masterQ.data?.resume ? (
        <EmptyState
          title="Crie seu Currículo Mestre"
          description="Confirme dados do Perfil ou importe um texto antes de criar variantes."
        />
      ) : (
        <div className="space-y-5" data-testid="resume-studio">
          {search.capture_id && (
            <div className="rounded-xl border border-accent/30 bg-accent/5 px-4 py-3 text-xs">
              <strong>Vaga vinculada pela extensão.</strong> Somente identificadores seguros foram
              recebidos: captura <code>{search.capture_id}</code>
              {search.job_snapshot_id && (
                <>
                  {" "}
                  · snapshot <code>{search.job_snapshot_id}</code>
                </>
              )}
              . Importe o currículo diretamente aqui; a extensão nunca lê documentos locais.
            </div>
          )}
          <ResumeImport
            onImported={(resume) => {
              queryClient.setQueryData(["resume-studio-master", mode], { resume });
              dispatch({ type: "replace", variant: variantFromMaster(resume) });
            }}
          />
          <StudioToolbar
            view={view}
            onView={setView}
            templateId={templateId}
            onTemplateId={setTemplateId}
            pageSize={pageSize}
            onPageSize={setPageSize}
            templates={templatesQ.data?.items ?? []}
            onUndo={() => dispatch({ type: "undo" })}
            onRedo={() => dispatch({ type: "redo" })}
            canUndo={state.past.length > 0}
            canRedo={state.future.length > 0}
            onExport={(format) => exportMutation.mutate(format)}
            exporting={exportMutation.isPending}
          />

          <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(360px,0.8fr)]">
            <div className="min-w-0 space-y-4">
              <MasterBanner master={masterQ.data.resume} variant={state.present} />
              {view === "editor" ? (
                <ResumeEditor variant={state.present} dispatch={dispatch} validation={validation} />
              ) : view === "diff" ? (
                <VariantDiff variant={state.present} />
              ) : (
                <div className="xl:hidden">
                  <ResumePreview variant={state.present} pageSize={pageSize} pages={pages} />
                </div>
              )}
            </div>
            <div className={cn("min-w-0", view === "preview" ? "block" : "hidden xl:block")}>
              <ResumePreview variant={state.present} pageSize={pageSize} pages={pages} />
            </div>
          </div>
          <ProfessionalAssetsPanel />
        </div>
      )}
    </AppShell>
  );
}

function StudioToolbar({
  view,
  onView,
  templateId,
  onTemplateId,
  pageSize,
  onPageSize,
  templates,
  onUndo,
  onRedo,
  canUndo,
  canRedo,
  onExport,
  exporting,
}: {
  view: StudioView;
  onView: (view: StudioView) => void;
  templateId: string;
  onTemplateId: (value: string) => void;
  pageSize: "A4" | "Letter";
  onPageSize: (value: "A4" | "Letter") => void;
  templates: Array<{ template_id: string; name: string }>;
  onUndo: () => void;
  onRedo: () => void;
  canUndo: boolean;
  canRedo: boolean;
  onExport: (format: ResumeExportFormat) => void;
  exporting: boolean;
}) {
  return (
    <div className="sticky top-[65px] z-20 flex flex-wrap items-center gap-2 rounded-xl border bg-background/95 p-2 shadow-[var(--shadow-soft)] backdrop-blur">
      <div className="flex rounded-md border p-0.5">
        {(
          [
            ["editor", "Editor", FileText],
            ["preview", "Preview", Eye],
            ["diff", "Diff", History],
          ] as const
        ).map(([id, label, Icon]) => (
          <button
            key={id}
            type="button"
            onClick={() => onView(id)}
            className={cn(
              "inline-flex items-center gap-1.5 rounded px-2.5 py-1.5 text-xs font-semibold",
              view === id ? "bg-primary text-primary-foreground" : "hover:bg-muted",
            )}
          >
            <Icon className="h-3.5 w-3.5" /> {label}
          </button>
        ))}
      </div>
      <button
        type="button"
        onClick={onUndo}
        disabled={!canUndo}
        aria-label="Desfazer"
        className="grid h-8 w-8 place-items-center rounded-md border hover:bg-muted disabled:opacity-30"
      >
        <Undo2 className="h-3.5 w-3.5" />
      </button>
      <button
        type="button"
        onClick={onRedo}
        disabled={!canRedo}
        aria-label="Refazer"
        className="grid h-8 w-8 place-items-center rounded-md border hover:bg-muted disabled:opacity-30"
      >
        <Redo2 className="h-3.5 w-3.5" />
      </button>
      <div className="ml-auto flex flex-wrap items-center gap-2">
        <label className="sr-only" htmlFor="template-select">
          Template
        </label>
        <select
          id="template-select"
          value={templateId}
          onChange={(event) => onTemplateId(event.target.value)}
          className="h-8 rounded-md border bg-background px-2 text-xs"
        >
          {templates.map((template) => (
            <option key={template.template_id} value={template.template_id}>
              {template.name} · ATS-safe
            </option>
          ))}
        </select>
        <select
          aria-label="Tamanho da página"
          value={pageSize}
          onChange={(event) => onPageSize(event.target.value as "A4" | "Letter")}
          className="h-8 rounded-md border bg-background px-2 text-xs"
        >
          <option value="A4">A4</option>
          <option value="Letter">Letter</option>
        </select>
        <button
          type="button"
          onClick={() => onExport("json_resume")}
          disabled={exporting}
          className="inline-flex h-8 items-center gap-1.5 rounded-md bg-primary px-3 text-xs font-semibold text-primary-foreground disabled:opacity-50"
        >
          {exporting ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <FileJson className="h-3.5 w-3.5" />
          )}
          JSON Resume
        </button>
        <button
          type="button"
          onClick={() => onExport("pdf")}
          className="inline-flex h-8 items-center gap-1.5 rounded-md border px-3 text-xs font-semibold"
        >
          <Download className="h-3.5 w-3.5" /> PDF · pendente
        </button>
      </div>
    </div>
  );
}

function MasterBanner({ master, variant }: { master: MasterResume; variant: ResumeVariant }) {
  return (
    <div className="rounded-xl border border-accent/20 bg-accent/5 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-wider text-accent">
            Variante ativa
          </p>
          <h2 className="mt-1 font-semibold">{variant.title}</h2>
          <p className="mt-1 text-xs text-muted-foreground">
            Derivada de “{master.title}”. Remover daqui nunca remove do mestre.
          </p>
        </div>
        <span className="rounded-full bg-success/15 px-2 py-1 text-[10px] font-semibold text-success">
          {variant.source_profile_item_ids.length} vínculo(s) de origem
        </span>
      </div>
    </div>
  );
}

function ResumeEditor({
  variant,
  dispatch,
  validation,
}: {
  variant: ResumeVariant;
  dispatch: React.Dispatch<Parameters<typeof resumeEditorReducer>[1]>;
  validation: string[];
}) {
  return (
    <div className="space-y-4">
      <div className="grid gap-3 rounded-xl border bg-card p-4 sm:grid-cols-2">
        <label className="text-xs font-semibold">
          Nome da variante
          <input
            value={variant.title}
            onChange={(event) =>
              dispatch({ type: "edit-meta", field: "title", value: event.target.value })
            }
            className="mt-2 h-9 w-full rounded-md border bg-background px-3 text-sm font-normal"
          />
        </label>
        <label className="text-xs font-semibold">
          Cargo-alvo
          <input
            value={variant.target_role}
            onChange={(event) =>
              dispatch({ type: "edit-meta", field: "target_role", value: event.target.value })
            }
            className="mt-2 h-9 w-full rounded-md border bg-background px-3 text-sm font-normal"
          />
        </label>
      </div>
      {validation.length > 0 && (
        <div className="rounded-xl border border-warning/30 bg-warning/5 p-4 text-xs">
          <strong>Validação:</strong>
          <ul className="mt-2 space-y-1 text-muted-foreground">
            {validation.map((item) => (
              <li key={item}>• {item}</li>
            ))}
          </ul>
        </div>
      )}
      {variant.sections.map((section, sectionIndex) => (
        <EditorSection
          key={section.section_id}
          section={section}
          index={sectionIndex}
          total={variant.sections.length}
          dispatch={dispatch}
        />
      ))}
    </div>
  );
}

function EditorSection({
  section,
  index,
  total,
  dispatch,
}: {
  section: ResumeSection;
  index: number;
  total: number;
  dispatch: React.Dispatch<Parameters<typeof resumeEditorReducer>[1]>;
}) {
  return (
    <article className={cn("rounded-xl border bg-card", !section.enabled && "opacity-60")}>
      <header className="flex flex-wrap items-center gap-2 border-b bg-muted/30 px-4 py-3">
        <div className="mr-auto">
          <h3 className="text-sm font-semibold">{section.title}</h3>
          <p className="text-[10px] text-muted-foreground">{section.section_type}</p>
        </div>
        <button
          type="button"
          onClick={() =>
            dispatch({ type: "move-section", sectionId: section.section_id, direction: -1 })
          }
          disabled={index === 0}
          aria-label={`Mover ${section.title} para cima`}
          className="grid h-7 w-7 place-items-center rounded border disabled:opacity-30"
        >
          <ArrowUp className="h-3 w-3" />
        </button>
        <button
          type="button"
          onClick={() =>
            dispatch({ type: "move-section", sectionId: section.section_id, direction: 1 })
          }
          disabled={index === total - 1}
          aria-label={`Mover ${section.title} para baixo`}
          className="grid h-7 w-7 place-items-center rounded border disabled:opacity-30"
        >
          <ArrowDown className="h-3 w-3" />
        </button>
        <label className="flex items-center gap-2 text-xs">
          <input
            type="checkbox"
            checked={section.enabled}
            onChange={() => dispatch({ type: "toggle-section", sectionId: section.section_id })}
          />
          Ativa
        </label>
      </header>
      <div className="space-y-4 p-4">
        <label className="block text-xs font-semibold">
          Texto da seção
          <textarea
            value={section.content}
            onChange={(event) =>
              dispatch({
                type: "edit-section",
                sectionId: section.section_id,
                content: event.target.value,
              })
            }
            className="mt-2 min-h-20 w-full rounded-md border bg-background p-3 text-sm font-normal"
          />
        </label>
        {section.entries.map((entry, entryIndex) => (
          <div key={entry.entry_id} className="rounded-lg border p-3">
            <div className="mb-2 flex items-center gap-2">
              <strong className="mr-auto text-xs">{entry.title || "Entrada sem título"}</strong>
              <span className="text-[10px] text-muted-foreground">
                {entry.confirmed_by_user ? "confirmada" : "revisão pendente"}
              </span>
              <button
                type="button"
                onClick={() =>
                  dispatch({
                    type: "move-entry",
                    sectionId: section.section_id,
                    entryId: entry.entry_id,
                    direction: -1,
                  })
                }
                disabled={entryIndex === 0}
                aria-label={`Mover ${entry.title} para cima`}
                className="grid h-6 w-6 place-items-center rounded border disabled:opacity-30"
              >
                <ArrowUp className="h-3 w-3" />
              </button>
              <button
                type="button"
                onClick={() =>
                  dispatch({
                    type: "move-entry",
                    sectionId: section.section_id,
                    entryId: entry.entry_id,
                    direction: 1,
                  })
                }
                disabled={entryIndex === section.entries.length - 1}
                aria-label={`Mover ${entry.title} para baixo`}
                className="grid h-6 w-6 place-items-center rounded border disabled:opacity-30"
              >
                <ArrowDown className="h-3 w-3" />
              </button>
            </div>
            <textarea
              aria-label={`Conteúdo de ${entry.title}`}
              value={entry.content}
              onChange={(event) =>
                dispatch({
                  type: "edit-entry",
                  sectionId: section.section_id,
                  entryId: entry.entry_id,
                  content: event.target.value,
                })
              }
              className="min-h-20 w-full rounded-md border bg-background p-3 text-sm"
            />
            <p className="mt-2 text-[10px] text-muted-foreground">
              {entry.source_refs.length} fonte(s) · {entry.source_profile_item_ids.length} item(ns)
              do Perfil
            </p>
          </div>
        ))}
      </div>
    </article>
  );
}

function ResumePreview({
  variant,
  pageSize,
  pages,
}: {
  variant: ResumeVariant;
  pageSize: "A4" | "Letter";
  pages: number;
}) {
  return (
    <div className="xl:sticky xl:top-40">
      <div className="mb-2 flex items-center justify-between text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-1.5">
          <MonitorUp className="h-3.5 w-3.5" /> Preview em tempo real
        </span>
        <span>
          ~{pages} pág. · {pageSize}
        </span>
      </div>
      <article
        className={cn(
          "resume-print-preview mx-auto overflow-hidden border bg-white p-8 text-slate-900 shadow-[var(--shadow-elevated)]",
          pageSize === "A4" ? "aspect-[210/297]" : "aspect-[8.5/11]",
        )}
      >
        <header className="border-b-2 border-slate-900 pb-4">
          <h2 className="font-serif text-2xl font-bold">{variant.title}</h2>
          <p className="mt-1 text-sm text-slate-600">{variant.target_role}</p>
        </header>
        <div className="mt-5 space-y-5">
          {variant.sections
            .filter((section) => section.enabled)
            .map((section) => (
              <section key={section.section_id} className="break-inside-avoid">
                <h3 className="border-b border-slate-300 pb-1 text-xs font-bold uppercase tracking-wider">
                  {section.title}
                </h3>
                {section.content && <p className="mt-2 text-[11px] leading-5">{section.content}</p>}
                <div className="mt-2 space-y-2">
                  {section.entries
                    .filter((entry) => entry.enabled)
                    .map((entry) => (
                      <div key={entry.entry_id}>
                        <h4 className="text-[11px] font-bold">{entry.title}</h4>
                        {entry.subtitle && (
                          <p className="text-[10px] text-slate-500">{entry.subtitle}</p>
                        )}
                        <p className="mt-1 text-[10px] leading-4">{entry.content}</p>
                      </div>
                    ))}
                </div>
              </section>
            ))}
        </div>
      </article>
    </div>
  );
}

function VariantDiff({ variant }: { variant: ResumeVariant }) {
  if (!variant.change_set.length)
    return (
      <EmptyState
        title="Nenhuma mudança registrada"
        description="O editor continuará rastreando as mudanças salvas nesta variante."
      />
    );
  return (
    <div className="space-y-3">
      {variant.change_set.map((change) => (
        <article key={change.change_id} className="overflow-hidden rounded-xl border bg-card">
          <header className="border-b bg-muted/30 px-4 py-3 text-xs font-semibold">
            {change.section} · {change.change_type}
          </header>
          <div className="grid md:grid-cols-2">
            <div className="bg-destructive/5 p-4 text-xs">
              <strong className="text-[10px] uppercase text-muted-foreground">Antes</strong>
              <p className="mt-2 leading-5">{change.before || "—"}</p>
            </div>
            <div className="bg-success/5 p-4 text-xs">
              <strong className="text-[10px] uppercase text-muted-foreground">Depois</strong>
              <p className="mt-2 leading-5">{change.after || "—"}</p>
            </div>
          </div>
          <footer className="border-t px-4 py-3 text-xs text-muted-foreground">
            {change.reason} · {change.evidence_used.length} evidência(s)
          </footer>
        </article>
      ))}
    </div>
  );
}

function variantFromMaster(master: MasterResume): ResumeVariant {
  const now = new Date().toISOString();
  return {
    resume_variant_id: crypto.randomUUID().replaceAll("-", ""),
    master_resume_id: master.master_resume_id,
    job_snapshot_id: "",
    title: `${master.title} — Variante`,
    target_role: master.target_role,
    sections: structuredClone(master.sections),
    source_profile_item_ids: master.source_profile_item_ids,
    change_set: [],
    validation_warnings: [],
    created_at: now,
    updated_at: now,
  };
}

function emptyVariant(): ResumeVariant {
  const now = new Date().toISOString();
  return {
    resume_variant_id: "loading",
    master_resume_id: "",
    job_snapshot_id: "",
    title: "Carregando…",
    target_role: "",
    sections: [],
    source_profile_item_ids: [],
    change_set: [],
    validation_warnings: [],
    created_at: now,
    updated_at: now,
  };
}

function validateVariant(variant: ResumeVariant): string[] {
  const warnings: string[] = [];
  if (!variant.title.trim()) warnings.push("A variante precisa de um título.");
  if (!variant.target_role.trim()) warnings.push("Defina o cargo-alvo.");
  if (!variant.sections.some((section) => section.enabled))
    warnings.push("Ative ao menos uma seção.");
  if (
    variant.sections.some((section) =>
      section.entries.some(
        (entry) => entry.enabled && entry.content.trim() && !entry.confirmed_by_user,
      ),
    )
  )
    warnings.push("Há entradas ainda não confirmadas; revise antes de exportar.");
  return warnings;
}
