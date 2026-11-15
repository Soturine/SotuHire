import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowDown,
  ArrowUp,
  CheckCircle2,
  ChevronDown,
  CircleDot,
  Download,
  Eye,
  FileJson,
  FileText,
  FileUp,
  History,
  Link2,
  Loader2,
  MonitorUp,
  Redo2,
  TriangleAlert,
  Undo2,
} from "lucide-react";
import { useEffect, useId, useMemo, useReducer, useRef, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { Field, controlClass, textareaClass } from "@/components/field";
import {
  approximatePageCount,
  createResumeEditorState,
  resumeEditorReducer,
} from "@/components/resume-editor-state";
import { EmptyState, ErrorState, LoadingState } from "@/components/states";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { ResumeImport } from "@/features/document-ingestion/resume-import";
import { MasterOnboarding, ProfileUpdatesPanel } from "@/features/resume-studio/profile-sync";
import { ApiHttpError, isNotFound } from "@/lib/api/client";
import { draftKey, pickDraft, readDraft, safeStorage } from "@/features/resume-studio/draft";
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

const FORMAT_NAME: Record<string, string> = {
  pdf: "PDF",
  docx: "DOCX",
  json_resume: "JSON Resume",
  markdown: "Markdown",
  txt: "Texto",
};

type SaveState = "saving" | "dirty" | "conflict" | "saved";

function ResumeStudioPage() {
  const api = useApi();
  const { mode, baseUrl } = useApiMode();
  const queryClient = useQueryClient();
  const search = Route.useSearch();
  const masterQ = useQuery({
    queryKey: ["resume-studio-master", mode, baseUrl],
    queryFn: () => api.resumeStudioMaster(),
  });
  const variantsQ = useQuery({
    queryKey: ["resume-studio-variants", mode, baseUrl, masterQ.data?.resume.master_resume_id],
    queryFn: () => api.resumeStudioVariants(masterQ.data?.resume.master_resume_id),
    enabled: Boolean(masterQ.data?.resume),
  });
  const templatesQ = useQuery({
    queryKey: ["resume-studio-templates", mode, baseUrl],
    queryFn: () => api.resumeStudioTemplates(),
  });
  const [view, setView] = useState<StudioView>("editor");
  const [templateId, setTemplateId] = useState("classic");
  const [pageSize, setPageSize] = useState<"A4" | "Letter">("A4");
  const [loaded, setLoaded] = useState(false);
  const fallback = useMemo(() => emptyVariant(), []);
  const [state, dispatch] = useReducer(resumeEditorReducer, fallback, createResumeEditorState);
  const autosaveTimer = useRef<number | undefined>(undefined);
  // updated_at of the stored copy this editor is based on; null while the variant is not stored.
  const serverVersion = useRef<string | null>(null);
  const [conflict, setConflict] = useState(false);
  const [savedAt, setSavedAt] = useState<string | null>(null);

  useEffect(() => {
    if (loaded || !masterQ.data?.resume || !variantsQ.data) return;
    const storageKey = draftKey(masterQ.data.resume.master_resume_id);
    const stored = variantsQ.data.items[0];
    const server = stored ?? variantFromMaster(masterQ.data.resume);
    serverVersion.current = stored?.updated_at ?? null;
    const { variant: selected, restoredDraft } = pickDraft(readDraft(storageKey), server);
    if (!restoredDraft) safeStorage(() => localStorage.removeItem(storageKey));
    else
      toast.info(
        "Rascunho local mais recente que o salvo foi restaurado; ele será salvo em seguida.",
      );
    // A restored draft is newer than the stored copy: keep it dirty so autosave stores it.
    dispatch({ type: "replace", variant: selected, dirty: restoredDraft });
    setLoaded(true);
  }, [loaded, masterQ.data, variantsQ.data]);

  const persist = (variant: ResumeVariant, expected: string | null) =>
    serverVersion.current
      ? api.resumeStudioUpdateVariant(
          variant.resume_variant_id,
          {
            title: variant.title,
            target_role: variant.target_role,
            sections: variant.sections,
            validation_warnings: variant.validation_warnings,
          },
          expected ?? undefined,
        )
      : api.resumeStudioSaveVariant(variant);

  const settle = (result: { variant: ResumeVariant }) => {
    serverVersion.current = result.variant.updated_at;
    setSavedAt(result.variant.updated_at);
    setConflict(false);
    dispatch({ type: "saved" });
    // The server now holds this state: a stale browser copy must not win on the next visit.
    safeStorage(() => localStorage.removeItem(draftKey(result.variant.master_resume_id)));
  };

  const autosave = useMutation({
    mutationFn: (variant: ResumeVariant) => persist(variant, serverVersion.current),
    onSuccess: settle,
    onError: (error: Error) => {
      if (error instanceof ApiHttpError && error.status === 409) {
        // Saved in another tab or session since this copy was loaded: ask, never overwrite.
        setConflict(true);
        return;
      }
      toast.warning(`Rascunho salvo no navegador. API: ${error.message}`);
    },
  });

  const keepMine = useMutation({
    mutationFn: () => persist(state.present, null),
    onSuccess: (result) => {
      settle(result);
      toast.success("Sua versão foi salva por cima da outra.");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const loadSaved = useMutation({
    mutationFn: () => api.resumeStudioVariant(state.present.resume_variant_id),
    onSuccess: ({ variant }) => {
      dispatch({ type: "replace", variant });
      settle({ variant });
      toast.info("Versão salva carregada; suas alterações locais foram descartadas.");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  useEffect(() => {
    if (!loaded || !state.dirty || conflict) return;
    window.clearTimeout(autosaveTimer.current);
    autosaveTimer.current = window.setTimeout(() => {
      const draft = { ...state.present, updated_at: new Date().toISOString() };
      safeStorage(() =>
        localStorage.setItem(draftKey(draft.master_resume_id), JSON.stringify(draft)),
      );
      if (navigator.onLine) autosave.mutate(state.present);
    }, 650);
    return () => window.clearTimeout(autosaveTimer.current);
  }, [autosave, conflict, loaded, state.dirty, state.present]);

  const exportMutation = useMutation({
    mutationFn: (format: ResumeExportFormat) =>
      api.resumeStudioExport(state.present.resume_variant_id, format, templateId, pageSize),
    onSuccess: (result) => {
      try {
        downloadResumeExport(result);
        toast.success(
          mode === "demo"
            ? "DEMO: artefato fictício exportado; nenhum dado real foi alterado."
            : `${FORMAT_NAME[result.export.format] ?? result.export.format} exportado com o conteúdo renderizado.`,
        );
      } catch (error) {
        toast.warning(error instanceof Error ? error.message : String(error));
      }
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const validation = useMemo(() => validateVariant(state.present), [state.present]);
  const pages = approximatePageCount(state.present, pageSize);
  const saveState: SaveState = conflict
    ? "conflict"
    : autosave.isPending
      ? "saving"
      : state.dirty
        ? "dirty"
        : "saved";

  return (
    <AppShell
      title="Resume Studio"
      description="Currículo Mestre, variantes rastreáveis, preview ATS-safe e export honesto."
      actions={loaded ? <SaveStatus state={saveState} savedAt={savedAt} /> : null}
    >
      {masterQ.isError && isNotFound(masterQ.error) ? (
        <MasterOnboarding
          onCreated={(resume) => {
            queryClient.setQueryData(["resume-studio-master", mode, baseUrl], { resume });
            void queryClient.invalidateQueries({ queryKey: ["resume-studio-variants"] });
          }}
        />
      ) : masterQ.isLoading || variantsQ.isLoading || templatesQ.isLoading || !loaded ? (
        masterQ.isError ? (
          <ErrorState error={masterQ.error} onRetry={() => masterQ.refetch()} />
        ) : (
          <LoadingState label="Abrindo seu estúdio local…" />
        )
      ) : !masterQ.data?.resume ? (
        <EmptyState
          title="Crie seu Currículo Mestre"
          description="Confirme dados do Perfil ou importe um texto antes de criar variantes."
        />
      ) : (
        <div className="mx-auto max-w-7xl space-y-5" data-testid="resume-studio">
          {search.capture_id && (
            <div className="rounded-xl border border-accent/30 bg-surface-accent px-4 py-3 text-xs">
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

          {conflict && (
            <ConflictNotice
              onLoadSaved={() => loadSaved.mutate()}
              onKeepMine={() => keepMine.mutate()}
              busy={loadSaved.isPending || keepMine.isPending}
            />
          )}

          <StudioHeader
            master={masterQ.data.resume}
            variant={state.present}
            pages={pages}
            pageSize={pageSize}
            warnings={validation.length}
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
            exporting={exportMutation.isPending ? exportMutation.variables : undefined}
          />

          <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(380px,0.85fr)]">
            <div className="min-w-0 space-y-4">
              <ProfileUpdatesPanel
                onApplied={(resume) =>
                  queryClient.setQueryData(["resume-studio-master", mode, baseUrl], { resume })
                }
              />
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

          <details className="group rounded-xl border bg-card shadow-[var(--shadow-soft)]">
            <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-5 py-4 text-sm font-semibold">
              <span className="flex items-center gap-2">
                <FileUp aria-hidden className="h-4 w-4 text-accent-strong" />
                Importar outro currículo para o Mestre
              </span>
              <ChevronDown
                aria-hidden
                className="h-4 w-4 text-muted-foreground transition-transform duration-(--duration-2) group-open:rotate-180"
              />
            </summary>
            <div className="border-t px-5 py-4">
              <ResumeImport
                onImported={(resume) => {
                  queryClient.setQueryData(["resume-studio-master", mode, baseUrl], { resume });
                  dispatch({ type: "replace", variant: variantFromMaster(resume) });
                }}
              />
            </div>
          </details>
          <ProfessionalAssetsPanel />
        </div>
      )}
    </AppShell>
  );
}

const SAVE_STATUS: Record<SaveState, { label: string; icon: typeof History; cls: string }> = {
  saving: { label: "Salvando…", icon: Loader2, cls: "text-muted-foreground" },
  dirty: { label: "Alterações no navegador", icon: History, cls: "text-warning-strong" },
  conflict: { label: "Escolha qual versão manter", icon: TriangleAlert, cls: "text-seal-strong" },
  saved: { label: "Salvo", icon: CheckCircle2, cls: "text-success-strong" },
};

function SaveStatus({ state, savedAt }: { state: SaveState; savedAt: string | null }) {
  const config = SAVE_STATUS[state];
  const Icon = config.icon;
  const time =
    state === "saved" && savedAt
      ? new Date(savedAt).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })
      : "";
  return (
    <span
      role="status"
      aria-live="polite"
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border bg-card px-3 py-1 text-xs font-medium shadow-[var(--shadow-soft)]",
        config.cls,
      )}
    >
      <Icon aria-hidden className={cn("h-3.5 w-3.5", state === "saving" && "animate-spin")} />
      {config.label}
      {time ? <span className="tabular text-muted-foreground"> às {time}</span> : null}
    </span>
  );
}

function ConflictNotice({
  onLoadSaved,
  onKeepMine,
  busy,
}: {
  onLoadSaved: () => void;
  onKeepMine: () => void;
  busy: boolean;
}) {
  return (
    <div
      role="alert"
      className="flex flex-wrap items-start gap-3 rounded-xl border border-seal/40 bg-seal/8 p-4"
      data-testid="variant-conflict"
    >
      <TriangleAlert aria-hidden className="mt-0.5 h-5 w-5 shrink-0 text-seal-strong" />
      <div className="min-w-0 flex-1">
        <p className="text-sm font-semibold">Esta variante foi salva em outra aba ou sessão.</p>
        <p className="mt-1 text-sm text-muted-foreground">
          O salvamento automático parou para não apagar nenhuma das duas versões. Suas alterações
          continuam aqui e no navegador até você escolher.
        </p>
      </div>
      <div className="flex flex-wrap gap-2">
        <Button size="sm" variant="outline" disabled={busy} onClick={onLoadSaved}>
          Carregar a versão salva
        </Button>
        <Button size="sm" disabled={busy} onClick={onKeepMine}>
          Manter a minha
        </Button>
      </div>
    </div>
  );
}

function StudioHeader({
  master,
  variant,
  pages,
  pageSize,
  warnings,
}: {
  master: MasterResume;
  variant: ResumeVariant;
  pages: number;
  pageSize: "A4" | "Letter";
  warnings: number;
}) {
  const facts = [
    { label: "vínculos com o Perfil", value: variant.source_profile_item_ids.length },
    { label: `pág. ${pageSize} (aprox.)`, value: pages },
    { label: warnings === 1 ? "ponto a revisar" : "pontos a revisar", value: warnings },
  ];
  return (
    <section className="grid gap-4 rounded-xl border bg-card p-5 shadow-[var(--shadow-soft)] md:grid-cols-[1fr_auto] md:items-center md:p-6">
      <div className="min-w-0">
        <p className="eyebrow text-accent-strong">Variante ativa</p>
        <h2 className="mt-1.5 truncate text-xl font-semibold tracking-tight">{variant.title}</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Derivada de “{master.title}”
          {variant.target_role ? (
            <>
              {" "}
              · para <span className="text-foreground">{variant.target_role}</span>
            </>
          ) : null}
          . Remover daqui nunca remove do Mestre.
        </p>
      </div>
      <dl className="grid grid-cols-3 gap-2">
        {facts.map((fact) => (
          <div key={fact.label} className="rounded-lg bg-surface-muted px-3 py-2 text-center">
            <dt className="sr-only">{fact.label}</dt>
            <dd
              className={cn(
                "text-metric text-xl",
                fact.label.includes("revisar") && fact.value > 0 && "text-warning-strong",
              )}
            >
              {fact.value}
            </dd>
            <dd aria-hidden className="mt-0.5 text-[11px] leading-tight text-muted-foreground">
              {fact.label}
            </dd>
          </div>
        ))}
      </dl>
    </section>
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
  exporting: ResumeExportFormat | undefined;
}) {
  const exportButton = (format: ResumeExportFormat, label: string, primary = false) => (
    <Button
      size="sm"
      variant={primary ? "default" : "outline"}
      onClick={() => onExport(format)}
      disabled={exporting !== undefined}
    >
      {exporting === format ? (
        <Loader2 aria-hidden className="h-3.5 w-3.5 animate-spin" />
      ) : format === "json_resume" ? (
        <FileJson aria-hidden className="h-3.5 w-3.5" />
      ) : (
        <Download aria-hidden className="h-3.5 w-3.5" />
      )}
      {label}
    </Button>
  );
  return (
    <div className="z-20 flex flex-wrap items-center gap-2 rounded-xl border bg-card/95 p-2 shadow-[var(--shadow-elevated)] backdrop-blur-md md:sticky md:top-[8.5rem]">
      <div
        role="group"
        aria-label="Modo de visualização"
        className="flex rounded-lg bg-muted p-0.5"
      >
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
            aria-pressed={view === id}
            onClick={() => onView(id)}
            className={cn(
              "inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-semibold transition-[background-color,color,box-shadow] duration-(--duration-1)",
              view === id
                ? "bg-card text-foreground shadow-[var(--shadow-soft)]"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            <Icon aria-hidden className="h-3.5 w-3.5" /> {label}
          </button>
        ))}
      </div>
      <div className="flex gap-1">
        <Button
          size="icon"
          variant="ghost"
          onClick={onUndo}
          disabled={!canUndo}
          aria-label="Desfazer"
        >
          <Undo2 aria-hidden className="h-4 w-4" />
        </Button>
        <Button
          size="icon"
          variant="ghost"
          onClick={onRedo}
          disabled={!canRedo}
          aria-label="Refazer"
        >
          <Redo2 aria-hidden className="h-4 w-4" />
        </Button>
      </div>
      <div className="ml-auto flex flex-wrap items-center gap-2">
        <label className="sr-only" htmlFor="template-select">
          Template
        </label>
        <select
          id="template-select"
          value={templateId}
          onChange={(event) => onTemplateId(event.target.value)}
          className="h-8 rounded-lg border bg-card px-2 text-xs"
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
          className="h-8 rounded-lg border bg-card px-2 text-xs"
        >
          <option value="A4">A4</option>
          <option value="Letter">Letter</option>
        </select>
        <span aria-hidden className="mx-1 hidden h-5 w-px bg-border sm:block" />
        {exportButton("pdf", "PDF", true)}
        {exportButton("docx", "DOCX")}
        {exportButton("json_resume", "JSON Resume")}
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
      <div className="grid gap-4 rounded-xl border bg-card p-5 shadow-[var(--shadow-soft)] sm:grid-cols-2">
        <Field label="Nome da variante">
          {(control) => (
            <input
              {...control}
              value={variant.title}
              onChange={(event) =>
                dispatch({ type: "edit-meta", field: "title", value: event.target.value })
              }
              className={controlClass}
            />
          )}
        </Field>
        <Field label="Cargo-alvo" hint="Aparece no topo do currículo exportado.">
          {(control) => (
            <input
              {...control}
              value={variant.target_role}
              onChange={(event) =>
                dispatch({ type: "edit-meta", field: "target_role", value: event.target.value })
              }
              className={controlClass}
            />
          )}
        </Field>
      </div>
      {validation.length > 0 && (
        <div className="rounded-xl border border-warning/40 bg-highlight/40 p-4 text-sm">
          <p className="flex items-center gap-2 font-semibold">
            <TriangleAlert aria-hidden className="h-4 w-4 text-warning-strong" />
            Antes de exportar
          </p>
          <ul className="mt-2 space-y-1 pl-6 text-muted-foreground">
            {validation.map((item) => (
              <li key={item} className="list-disc">
                {item}
              </li>
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

function MoveButtons({
  label,
  first,
  last,
  onMove,
}: {
  label: string;
  first: boolean;
  last: boolean;
  onMove: (direction: -1 | 1) => void;
}) {
  return (
    <span className="flex gap-0.5">
      <Button
        size="icon"
        variant="ghost"
        className="h-7 w-7"
        onClick={() => onMove(-1)}
        disabled={first}
        aria-label={`Mover ${label} para cima`}
      >
        <ArrowUp aria-hidden className="h-3.5 w-3.5" />
      </Button>
      <Button
        size="icon"
        variant="ghost"
        className="h-7 w-7"
        onClick={() => onMove(1)}
        disabled={last}
        aria-label={`Mover ${label} para baixo`}
      >
        <ArrowDown aria-hidden className="h-3.5 w-3.5" />
      </Button>
    </span>
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
  const toggleId = useId();
  return (
    <article
      className={cn(
        "rounded-xl border bg-card shadow-[var(--shadow-soft)] transition-opacity duration-(--duration-2)",
        !section.enabled && "opacity-60",
      )}
    >
      <header className="flex flex-wrap items-center gap-2 border-b bg-surface/60 px-4 py-3">
        <div className="mr-auto min-w-0">
          <h3 className="text-sm font-semibold">{section.title}</h3>
          <p className="text-xs text-muted-foreground">
            {section.entries.length} entrada(s)
            {section.enabled ? "" : " · fora do currículo exportado"}
          </p>
        </div>
        <MoveButtons
          label={section.title}
          first={index === 0}
          last={index === total - 1}
          onMove={(direction) =>
            dispatch({ type: "move-section", sectionId: section.section_id, direction })
          }
        />
        <span className="flex items-center gap-2 text-xs">
          <Switch
            id={toggleId}
            checked={section.enabled}
            onCheckedChange={() =>
              dispatch({ type: "toggle-section", sectionId: section.section_id })
            }
          />
          <label htmlFor={toggleId}>Ativa</label>
        </span>
      </header>
      <div className="space-y-4 p-4">
        <Field label="Texto da seção" optional>
          {(control) => (
            <textarea
              {...control}
              value={section.content}
              onChange={(event) =>
                dispatch({
                  type: "edit-section",
                  sectionId: section.section_id,
                  content: event.target.value,
                })
              }
              className={cn(textareaClass, "min-h-20")}
            />
          )}
        </Field>
        {section.entries.map((entry, entryIndex) => (
          <div key={entry.entry_id} className="rounded-lg border bg-surface p-3">
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <strong className="mr-auto min-w-0 text-sm">
                {entry.title || "Entrada sem título"}
                {entry.subtitle ? (
                  <span className="font-normal text-muted-foreground"> · {entry.subtitle}</span>
                ) : null}
              </strong>
              <span
                className={cn(
                  "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium",
                  entry.confirmed_by_user
                    ? "bg-success/12 text-success-strong"
                    : "bg-highlight text-highlight-foreground",
                )}
              >
                {entry.confirmed_by_user ? (
                  <CheckCircle2 aria-hidden className="h-3 w-3" />
                ) : (
                  <CircleDot aria-hidden className="h-3 w-3" />
                )}
                {entry.confirmed_by_user ? "confirmada" : "revisão pendente"}
              </span>
              <MoveButtons
                label={entry.title}
                first={entryIndex === 0}
                last={entryIndex === section.entries.length - 1}
                onMove={(direction) =>
                  dispatch({
                    type: "move-entry",
                    sectionId: section.section_id,
                    entryId: entry.entry_id,
                    direction,
                  })
                }
              />
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
              className={cn(textareaClass, "min-h-20")}
            />
            <p className="mt-2 flex items-center gap-1.5 text-xs text-muted-foreground">
              <Link2 aria-hidden className="h-3 w-3" />
              {entry.source_profile_item_ids.length
                ? `Vem de ${entry.source_profile_item_ids.length} fato(s) do Perfil`
                : "Sem vínculo com o Perfil"}
              {entry.source_refs.length ? ` · ${entry.source_refs.length} fonte(s)` : ""}
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
    <div className="rounded-xl bg-surface-muted p-3 xl:sticky xl:top-56 md:p-5">
      <div className="mb-3 flex items-center justify-between text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-1.5">
          <MonitorUp aria-hidden className="h-3.5 w-3.5" /> Preview em tempo real
        </span>
        <span className="tabular">
          ~{pages} pág. · {pageSize}
        </span>
      </div>
      <article
        className={cn(
          "resume-print-preview mx-auto overflow-hidden rounded-sm bg-white p-8 text-slate-900 shadow-[var(--shadow-elevated)] ring-1 ring-black/5",
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
                          <p className="text-[10px] text-slate-600">{entry.subtitle}</p>
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
        <article
          key={change.change_id}
          className="overflow-hidden rounded-xl border bg-card shadow-[var(--shadow-soft)]"
        >
          <header className="border-b bg-surface/60 px-4 py-3 text-xs font-semibold">
            {change.section} · {change.change_type}
          </header>
          <div className="grid md:grid-cols-2">
            <div className="bg-destructive/5 p-4 text-xs">
              <strong className="eyebrow text-destructive-strong">Antes</strong>
              <p className="mt-2 leading-5">{change.before || "—"}</p>
            </div>
            <div className="bg-success/8 p-4 text-xs">
              <strong className="eyebrow text-success-strong">Depois</strong>
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
