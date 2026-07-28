import { createFileRoute, Link } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  BriefcaseBusiness,
  Check,
  CheckCircle2,
  ClipboardCheck,
  FileDiff,
  FileText,
  FlaskConical,
  Loader2,
  RotateCcw,
  Save,
  ShieldCheck,
  Sparkles,
  X,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { EmptyState, ErrorState, LoadingState } from "@/components/states";
import { Progress } from "@/components/ui/progress";
import { useApi } from "@/lib/api/hooks";
import { useApiMode } from "@/lib/api/mode";
import type {
  ApplicationLabDetail,
  ApplicationSuggestion,
  SuggestionStatus,
} from "@/lib/api/types";
import { toast } from "@/lib/notify";
import { cn } from "@/lib/utils";

type LabSearch = {
  capture_id?: string;
  job_snapshot_id?: string;
  novo?: boolean;
};

export const Route = createFileRoute("/application-lab")({
  validateSearch: (search: Record<string, unknown>): LabSearch => ({
    capture_id: typeof search.capture_id === "string" ? search.capture_id : undefined,
    job_snapshot_id:
      typeof search.job_snapshot_id === "string" ? search.job_snapshot_id : undefined,
    novo: search.novo === true || search.novo === "1" || search.novo === 1,
  }),
  head: () => ({ meta: [{ title: "Preparar candidatura — SotuHire" }] }),
  component: ApplicationLabPage,
});

const STEPS = [
  "Objetivo",
  "Perfil e evidências",
  "Currículo Mestre",
  "Vaga",
  "Análise",
  "Melhorias",
  "Variante",
  "Kit de candidatura",
  "Plano de ação",
  "Salvar no Tracker",
];

const REAL_PROGRESS = [
  "Extraindo currículo",
  "Carregando evidências",
  "Estruturando vaga",
  "Comparando requisitos",
  "Validando afirmações",
  "Gerando sugestões",
  "Criando variante",
  "Salvando snapshots",
];

function ApplicationLabPage() {
  const api = useApi();
  const { mode } = useApiMode();
  const search = Route.useSearch();
  const qc = useQueryClient();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const hydratedSessionId = useRef<string | null>(null);
  const [viewStep, setViewStep] = useState(1);
  const [jobSnapshotId, setJobSnapshotId] = useState(
    search.job_snapshot_id ?? (mode === "demo" ? "job-snapshot-demo" : ""),
  );
  const [objective, setObjective] = useState("Preparar uma candidatura revisada e rastreável");
  const [privacyAcknowledged, setPrivacyAcknowledged] = useState(false);
  const [editingSuggestion, setEditingSuggestion] = useState<string | null>(null);
  const [editedValue, setEditedValue] = useState("");
  const [offline, setOffline] = useState(
    typeof navigator !== "undefined" ? !navigator.onLine : false,
  );

  const sessionsQ = useQuery({
    queryKey: ["application-lab-sessions", mode],
    queryFn: () => api.applicationLabSessions(),
  });
  const masterQ = useQuery({
    queryKey: ["resume-studio-master", mode],
    queryFn: () => api.resumeStudioMaster(),
    retry: false,
  });
  const detailQ = useQuery({
    queryKey: ["application-lab-session", mode, sessionId],
    queryFn: () => api.applicationLabSession(sessionId!),
    enabled: Boolean(sessionId),
  });

  useEffect(() => {
    if (!sessionId && !search.novo && sessionsQ.data?.items[0]) {
      setSessionId(sessionsQ.data.items[0].session_id);
    }
  }, [search.novo, sessionId, sessionsQ.data]);

  useEffect(() => {
    const session = detailQ.data?.session;
    if (session && hydratedSessionId.current !== session.session_id) {
      hydratedSessionId.current = session.session_id;
      setViewStep(session.current_step);
    }
  }, [detailQ.data?.session]);

  useEffect(() => {
    const online = () => setOffline(false);
    const offlineHandler = () => setOffline(true);
    window.addEventListener("online", online);
    window.addEventListener("offline", offlineHandler);
    return () => {
      window.removeEventListener("online", online);
      window.removeEventListener("offline", offlineHandler);
    };
  }, []);

  const detailKey = ["application-lab-session", mode, sessionId] as const;
  const setDetail = (detail: ApplicationLabDetail) => qc.setQueryData(detailKey, detail);

  const create = useMutation({
    mutationFn: () =>
      api.applicationLabCreate({
        master_resume_id: masterQ.data?.resume.master_resume_id,
        job_snapshot_id: jobSnapshotId,
        selected_context_refs: masterQ.data?.resume.source_refs ?? [],
      }),
    onSuccess: (detail) => {
      setSessionId(detail.session.session_id);
      setViewStep(1);
      qc.setQueryData(["application-lab-session", mode, detail.session.session_id], detail);
      toast.success("Sessão criada. Você pode sair e continuar depois.");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const update = useMutation({
    mutationFn: (patch: Parameters<typeof api.applicationLabUpdate>[1]) =>
      api.applicationLabUpdate(sessionId!, patch),
    onSuccess: setDetail,
    onError: (error: Error) => toast.error(error.message),
  });

  const analyze = useMutation({
    mutationFn: () => api.applicationLabAnalyze(sessionId!),
    onSuccess: (result) => {
      setDetail(result);
      setViewStep(5);
      toast.success("Relatório de prontidão concluído.");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const review = useMutation({
    mutationFn: ({
      item,
      action,
      value,
    }: {
      item: ApplicationSuggestion;
      action: "accept" | "edit" | "reject" | "undo";
      value?: string;
    }) => api.applicationLabReviewSuggestion(sessionId!, item.suggestion_id, action, value ?? ""),
    onSuccess: (suggestion) => {
      const current = qc.getQueryData<ApplicationLabDetail>(detailKey);
      if (current) {
        setDetail({
          ...current,
          suggestions: current.suggestions.map((item) =>
            item.suggestion_id === suggestion.suggestion_id ? suggestion : item,
          ),
        });
      }
      setEditingSuggestion(null);
      setEditedValue("");
      toast.success("Decisão registrada. O currículo ainda não foi alterado.");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const variant = useMutation({
    mutationFn: () => api.applicationLabCreateVariant(sessionId!),
    onSuccess: (createdVariant) => {
      const current = qc.getQueryData<ApplicationLabDetail>(detailKey);
      if (current) setDetail({ ...current, variant: createdVariant });
      setViewStep(7);
      toast.success("Variante criada sem alterar o Currículo Mestre.");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const kit = useMutation({
    mutationFn: () => api.applicationLabCreateKit(sessionId!),
    onSuccess: (result) => {
      const current = qc.getQueryData<ApplicationLabDetail>(detailKey);
      if (current) setDetail({ ...current, kit: result.kit });
      setViewStep(8);
      toast.success("Kit criado como rascunho revisável.");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const plan = useMutation({
    mutationFn: () => api.applicationLabCreatePlan(sessionId!, 7),
    onSuccess: (createdPlan) => {
      const current = qc.getQueryData<ApplicationLabDetail>(detailKey);
      if (current) setDetail({ ...current, action_plan: createdPlan });
      setViewStep(9);
      toast.success("Plano de 7 dias criado.");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const tracker = useMutation({
    mutationFn: () =>
      api.applicationLabSaveTracker(sessionId!, {
        privacy_acknowledged: privacyAcknowledged,
        source_capture_id: search.capture_id,
      }),
    onSuccess: (result) => {
      const current = qc.getQueryData<ApplicationLabDetail>(detailKey);
      if (current) setDetail({ ...current, session: result.session });
      toast.success("Candidatura salva no Tracker com snapshots vinculados.");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const cancel = useMutation({
    mutationFn: () => api.applicationLabCancel(sessionId!),
    onSuccess: (result) => {
      setDetail(result);
      toast.message("Sessão cancelada; nenhum documento foi enviado.");
    },
  });

  const detail = detailQ.data;
  const operationPending =
    analyze.isPending || variant.isPending || kit.isPending || plan.isPending || tracker.isPending;

  return (
    <AppShell
      title="Preparar candidatura"
      description="Uma jornada guiada, local-first e sempre sob sua aprovação."
      actions={
        sessionId ? (
          <button
            type="button"
            onClick={() => cancel.mutate()}
            disabled={cancel.isPending || detail?.session.status === "cancelled"}
            className="rounded-md border border-input bg-card px-3 py-1.5 text-xs font-medium hover:bg-muted disabled:opacity-50"
          >
            Cancelar sessão
          </button>
        ) : undefined
      }
    >
      {offline && (
        <div
          role="status"
          className="mb-4 flex items-center gap-2 rounded-lg border border-warning/30 bg-warning/10 px-4 py-3 text-sm"
        >
          <AlertTriangle className="h-4 w-4" /> Você está offline. Edições locais são preservadas;
          sincronize quando a API voltar.
        </div>
      )}
      {sessionsQ.isLoading || masterQ.isLoading ? (
        <LoadingState label="Carregando laboratório local…" />
      ) : sessionsQ.isError ? (
        <ErrorState error={sessionsQ.error} onRetry={() => sessionsQ.refetch()} />
      ) : !sessionId ? (
        <LabStart
          captureId={search.capture_id}
          masterTitle={masterQ.data?.resume.title}
          jobSnapshotId={jobSnapshotId}
          onJobSnapshotId={setJobSnapshotId}
          objective={objective}
          onObjective={setObjective}
          onStart={() => create.mutate()}
          pending={create.isPending}
          hasMaster={Boolean(masterQ.data?.resume)}
        />
      ) : detailQ.isLoading ? (
        <LoadingState label="Retomando sua sessão…" />
      ) : detailQ.isError || !detail ? (
        <ErrorState error={detailQ.error} onRetry={() => detailQ.refetch()} />
      ) : (
        <div className="grid gap-6 xl:grid-cols-[270px_minmax(0,1fr)]">
          <LabStepper
            current={viewStep}
            persisted={detail.session.current_step}
            invalidated={detail.session.invalidated_steps}
            onSelect={setViewStep}
          />
          <section className="min-w-0 space-y-5" aria-live="polite">
            <SessionStatus detail={detail} />
            {analyze.isPending ? (
              <AnalysisProgress />
            ) : (
              <StepPanel
                step={viewStep}
                detail={detail}
                objective={objective}
                onObjective={setObjective}
                jobSnapshotId={jobSnapshotId}
                onJobSnapshotId={setJobSnapshotId}
                masterTitle={masterQ.data?.resume.title ?? ""}
                editingSuggestion={editingSuggestion}
                editedValue={editedValue}
                onEditSuggestion={(item) => {
                  setEditingSuggestion(item.suggestion_id);
                  setEditedValue(item.edited_value || item.after);
                }}
                onEditedValue={setEditedValue}
                onReview={(item, action) =>
                  review.mutate({ item, action, value: action === "edit" ? editedValue : "" })
                }
                onAnalyze={() => analyze.mutate()}
                onVariant={() => variant.mutate()}
                onKit={() => kit.mutate()}
                onPlan={() => plan.mutate()}
                onTracker={() => tracker.mutate()}
                privacyAcknowledged={privacyAcknowledged}
                onPrivacyAcknowledged={setPrivacyAcknowledged}
                pending={operationPending || review.isPending}
              />
            )}
            <div className="flex flex-wrap items-center justify-between gap-3 border-t pt-4">
              <button
                type="button"
                onClick={() => setViewStep((step) => Math.max(1, step - 1))}
                disabled={viewStep === 1 || operationPending}
                className="inline-flex items-center gap-2 rounded-md border border-input px-3 py-2 text-sm font-medium hover:bg-muted disabled:opacity-40"
              >
                <ArrowLeft className="h-4 w-4" /> Voltar
              </button>
              <p className="text-xs text-muted-foreground">
                Salvo localmente · etapa {detail.session.current_step} de 10
              </p>
              <button
                type="button"
                onClick={() => {
                  const next = Math.min(10, viewStep + 1);
                  setViewStep(next);
                  if (viewStep === 4 && jobSnapshotId !== detail.session.job_snapshot_id) {
                    update.mutate({ job_snapshot_id: jobSnapshotId, current_step: next });
                  } else if (next > detail.session.current_step) {
                    update.mutate({ current_step: next });
                  }
                }}
                disabled={viewStep === 10 || operationPending}
                className="inline-flex items-center gap-2 rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-40"
              >
                Continuar <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </section>
        </div>
      )}
    </AppShell>
  );
}

function LabStart({
  captureId,
  masterTitle,
  jobSnapshotId,
  onJobSnapshotId,
  objective,
  onObjective,
  onStart,
  pending,
  hasMaster,
}: {
  captureId?: string;
  masterTitle?: string;
  jobSnapshotId: string;
  onJobSnapshotId: (value: string) => void;
  objective: string;
  onObjective: (value: string) => void;
  onStart: () => void;
  pending: boolean;
  hasMaster: boolean;
}) {
  return (
    <div className="mx-auto max-w-5xl space-y-6" data-testid="application-lab-start">
      <div className="overflow-hidden rounded-3xl border bg-[image:var(--gradient-ink)] px-6 py-10 text-primary-foreground shadow-[var(--shadow-elevated)] sm:px-10">
        <div className="grid gap-8 md:grid-cols-[1fr_280px] md:items-center">
          <div>
            <span className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-3 py-1 text-xs">
              <FlaskConical className="h-3.5 w-3.5 text-accent" /> Application Lab
            </span>
            <h2 className="mt-5 text-display text-3xl leading-tight sm:text-4xl">
              Da vaga ao Tracker, com cada mudança sob seu controle.
            </h2>
            <p className="mt-4 max-w-2xl text-sm leading-6 text-white/70">
              Revise evidências, entenda bloqueadores, aprove sugestões individualmente e preserve
              snapshots do que realmente foi usado.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            {["10 etapas reais", "3 perspectivas", "0 auto-apply", "Local-first"].map((item) => (
              <div key={item} className="rounded-xl border border-white/10 bg-white/5 p-3">
                <CheckCircle2 className="mb-2 h-4 w-4 text-accent" /> {item}
              </div>
            ))}
          </div>
        </div>
      </div>

      {captureId && (
        <div className="rounded-xl border border-accent/25 bg-accent/5 px-4 py-3 text-sm">
          <strong>Vaga recebida da extensão.</strong> Somente o identificador de captura foi
          compartilhado: <code className="text-xs">{captureId}</code>.
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-3">
        <StartCard
          icon={<Sparkles className="h-5 w-5" />}
          label="Objetivo"
          ready={Boolean(objective.trim())}
        >
          <label className="text-xs font-medium" htmlFor="lab-objective">
            O que você quer preparar?
          </label>
          <textarea
            id="lab-objective"
            value={objective}
            onChange={(event) => onObjective(event.target.value)}
            className="mt-2 min-h-24 w-full rounded-md border bg-background p-2 text-sm"
          />
        </StartCard>
        <StartCard
          icon={<FileText className="h-5 w-5" />}
          label="Currículo Mestre"
          ready={hasMaster}
        >
          <p className="text-sm font-medium">{masterTitle ?? "Nenhum currículo mestre"}</p>
          <p className="mt-2 text-xs text-muted-foreground">
            O mestre nunca é alterado por uma sugestão do Lab.
          </p>
          <Link to="/resume-studio" className="mt-3 inline-block text-xs font-semibold underline">
            Abrir Resume Studio
          </Link>
        </StartCard>
        <StartCard
          icon={<BriefcaseBusiness className="h-5 w-5" />}
          label="Vaga"
          ready={Boolean(jobSnapshotId)}
        >
          <label className="text-xs font-medium" htmlFor="job-snapshot-id">
            Snapshot da vaga
          </label>
          <input
            id="job-snapshot-id"
            value={jobSnapshotId}
            onChange={(event) => onJobSnapshotId(event.target.value)}
            placeholder="job_snapshot_id"
            className="mt-2 h-9 w-full rounded-md border bg-background px-3 text-sm"
          />
          <p className="mt-2 text-xs text-muted-foreground">A vaga original permanece imutável.</p>
        </StartCard>
      </div>

      <button
        type="button"
        onClick={onStart}
        disabled={pending || !hasMaster || !jobSnapshotId || !objective.trim()}
        className="mx-auto flex items-center gap-2 rounded-lg bg-primary px-5 py-3 text-sm font-semibold text-primary-foreground shadow-sm hover:opacity-90 disabled:opacity-40"
      >
        {pending ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <FlaskConical className="h-4 w-4" />
        )}
        Iniciar preparação
      </button>
    </div>
  );
}

function StartCard({
  icon,
  label,
  ready,
  children,
}: {
  icon: React.ReactNode;
  label: string;
  ready: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-2xl border bg-card p-5 shadow-[var(--shadow-soft)]">
      <div className="mb-4 flex items-center justify-between">
        <div className="grid h-9 w-9 place-items-center rounded-lg bg-muted text-primary">
          {icon}
        </div>
        <span
          className={cn(
            "rounded-full px-2 py-1 text-[10px] font-semibold uppercase tracking-wide",
            ready ? "bg-success/15 text-success" : "bg-warning/15 text-warning-foreground",
          )}
        >
          {ready ? "Pronto" : "Pendente"}
        </span>
      </div>
      <h3 className="mb-3 font-semibold">{label}</h3>
      {children}
    </div>
  );
}

function LabStepper({
  current,
  persisted,
  invalidated,
  onSelect,
}: {
  current: number;
  persisted: number;
  invalidated: number[];
  onSelect: (step: number) => void;
}) {
  return (
    <aside className="h-fit rounded-2xl border bg-card p-4 shadow-[var(--shadow-soft)] xl:sticky xl:top-24">
      <div className="mb-4 flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Progresso
        </span>
        <span className="text-xs tabular-nums">{persisted}/10</span>
      </div>
      <Progress value={persisted * 10} aria-label={`${persisted} de 10 etapas`} />
      <ol className="mt-5 grid gap-1 sm:grid-cols-2 xl:grid-cols-1">
        {STEPS.map((label, index) => {
          const step = index + 1;
          const active = step === current;
          const complete = step < persisted && !invalidated.includes(step);
          const stale = invalidated.includes(step);
          return (
            <li key={label}>
              <button
                type="button"
                onClick={() => onSelect(step)}
                aria-current={active ? "step" : undefined}
                className={cn(
                  "flex w-full items-center gap-3 rounded-lg px-2.5 py-2 text-left text-xs transition-colors",
                  active ? "bg-primary text-primary-foreground" : "hover:bg-muted",
                )}
              >
                <span
                  className={cn(
                    "grid h-6 w-6 shrink-0 place-items-center rounded-full border text-[10px] font-bold",
                    active && "border-white/30 bg-white/10",
                    complete && !active && "border-success/30 bg-success/15 text-success",
                    stale && !active && "border-warning/30 bg-warning/15 text-warning-foreground",
                  )}
                >
                  {complete ? <Check className="h-3 w-3" /> : stale ? "!" : step}
                </span>
                <span className="truncate">{label}</span>
              </button>
            </li>
          );
        })}
      </ol>
    </aside>
  );
}

function SessionStatus({ detail }: { detail: ApplicationLabDetail }) {
  const { session, report } = detail;
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border bg-card px-4 py-3 text-xs">
      <div className="flex items-center gap-2">
        <Save className="h-4 w-4 text-accent" />
        <span>
          Sessão <code>{session.session_id.slice(0, 8)}</code> · {session.status}
        </span>
      </div>
      <div className="flex flex-wrap gap-2">
        <span className="rounded-full bg-success/10 px-2 py-1 text-success">local-first</span>
        <span className="rounded-full bg-muted px-2 py-1">
          {report?.provider_metadata.provider_used === "local" ? "análise local" : "provider"}
        </span>
        {session.invalidated_steps.length > 0 && (
          <span className="rounded-full bg-warning/15 px-2 py-1 text-warning-foreground">
            recalcular {session.invalidated_steps.join(", ")}
          </span>
        )}
      </div>
    </div>
  );
}

function AnalysisProgress() {
  const [active, setActive] = useState(0);
  useEffect(() => {
    const timer = window.setInterval(
      () => setActive((value) => Math.min(REAL_PROGRESS.length - 1, value + 1)),
      350,
    );
    return () => window.clearInterval(timer);
  }, []);
  return (
    <div className="rounded-2xl border bg-card p-6 shadow-[var(--shadow-soft)]" aria-live="polite">
      <div className="flex items-center gap-3">
        <Loader2 className="h-5 w-5 animate-spin text-accent" />
        <div>
          <h2 className="font-semibold">Análise consolidada em andamento</h2>
          <p className="text-xs text-muted-foreground">{REAL_PROGRESS[active]}</p>
        </div>
      </div>
      <Progress className="mt-5" value={((active + 1) / REAL_PROGRESS.length) * 100} />
      <ol className="mt-5 grid gap-2 sm:grid-cols-2">
        {REAL_PROGRESS.map((step, index) => (
          <li
            key={step}
            className={cn(
              "flex items-center gap-2 rounded-lg border px-3 py-2 text-xs",
              index <= active ? "border-accent/30 bg-accent/5" : "text-muted-foreground",
            )}
          >
            {index < active ? <Check className="h-3.5 w-3.5 text-success" /> : <span>○</span>}
            {step}
          </li>
        ))}
      </ol>
    </div>
  );
}

function StepPanel({
  step,
  detail,
  objective,
  onObjective,
  jobSnapshotId,
  onJobSnapshotId,
  masterTitle,
  editingSuggestion,
  editedValue,
  onEditSuggestion,
  onEditedValue,
  onReview,
  onAnalyze,
  onVariant,
  onKit,
  onPlan,
  onTracker,
  privacyAcknowledged,
  onPrivacyAcknowledged,
  pending,
}: {
  step: number;
  detail: ApplicationLabDetail;
  objective: string;
  onObjective: (value: string) => void;
  jobSnapshotId: string;
  onJobSnapshotId: (value: string) => void;
  masterTitle: string;
  editingSuggestion: string | null;
  editedValue: string;
  onEditSuggestion: (item: ApplicationSuggestion) => void;
  onEditedValue: (value: string) => void;
  onReview: (item: ApplicationSuggestion, action: "accept" | "edit" | "reject" | "undo") => void;
  onAnalyze: () => void;
  onVariant: () => void;
  onKit: () => void;
  onPlan: () => void;
  onTracker: () => void;
  privacyAcknowledged: boolean;
  onPrivacyAcknowledged: (value: boolean) => void;
  pending: boolean;
}) {
  const report = detail.report;
  if (step === 1)
    return (
      <Panel title="Qual é o objetivo desta candidatura?" eyebrow="Etapa 1">
        <label htmlFor="objective-edit" className="text-sm font-medium">
          Objetivo revisável
        </label>
        <textarea
          id="objective-edit"
          value={objective}
          onChange={(event) => onObjective(event.target.value)}
          className="mt-2 min-h-32 w-full rounded-lg border bg-background p-3 text-sm"
        />
        <p className="mt-2 text-xs text-muted-foreground">
          Isto orienta a preparação; não é enviado a nenhuma empresa.
        </p>
      </Panel>
    );
  if (step === 2)
    return (
      <Panel title="Perfil e evidências selecionadas" eyebrow="Etapa 2">
        <div className="grid gap-3 sm:grid-cols-2">
          {detail.session.selected_context_refs.map((ref) => (
            <div key={ref} className="rounded-lg border bg-muted/30 p-3 text-xs">
              <ShieldCheck className="mb-2 h-4 w-4 text-success" />
              <code className="break-all">{ref}</code>
              <p className="mt-2 text-muted-foreground">Confirmada e incluída nesta sessão.</p>
            </div>
          ))}
        </div>
        {detail.session.selected_context_refs.length === 0 && (
          <EmptyState
            title="Nenhuma evidência selecionada"
            description="A análise continuará em modo parcial e mostrará essa limitação."
          />
        )}
      </Panel>
    );
  if (step === 3)
    return (
      <Panel title="Currículo Mestre" eyebrow="Etapa 3">
        <div className="flex items-start justify-between gap-4 rounded-xl border p-4">
          <div>
            <h3 className="font-semibold">{masterTitle || detail.session.master_resume_id}</h3>
            <p className="mt-1 text-xs text-muted-foreground">
              Fonte imutável das variantes; sugestões nunca alteram este documento sozinhas.
            </p>
          </div>
          <Link
            to="/resume-studio"
            className="shrink-0 rounded-md border px-3 py-2 text-xs font-semibold hover:bg-muted"
          >
            Editar mestre
          </Link>
        </div>
      </Panel>
    );
  if (step === 4)
    return (
      <Panel title="Vaga e snapshot" eyebrow="Etapa 4">
        <label htmlFor="job-snapshot-edit" className="text-sm font-medium">
          Identificador imutável da vaga
        </label>
        <input
          id="job-snapshot-edit"
          value={jobSnapshotId}
          onChange={(event) => onJobSnapshotId(event.target.value)}
          className="mt-2 h-10 w-full rounded-md border bg-background px-3 text-sm"
        />
        <p className="mt-3 rounded-lg bg-muted p-3 text-xs text-muted-foreground">
          Trocar a vaga invalida apenas as etapas 5–10. Sugestões já aceitas ficam registradas.
        </p>
      </Panel>
    );
  if (step === 5)
    return (
      <Panel title="Relatório de prontidão" eyebrow="Etapa 5">
        {!report ? (
          <div className="py-8 text-center">
            <ClipboardCheck className="mx-auto h-8 w-8 text-accent" />
            <h3 className="mt-3 font-semibold">Pronto para uma análise consolidada</h3>
            <p className="mx-auto mt-2 max-w-lg text-xs text-muted-foreground">
              O score é determinístico. A explicação separa cobertura, evidência insuficiente e
              itens não aplicáveis — nunca “probabilidade de entrevista”.
            </p>
            <PrimaryAction onClick={onAnalyze} pending={pending} label="Analisar candidatura" />
          </div>
        ) : (
          <ReadinessReport detail={detail} onAnalyze={onAnalyze} pending={pending} />
        )}
      </Panel>
    );
  if (step === 6)
    return (
      <Panel title="Sugestões revisáveis" eyebrow="Etapa 6">
        <p className="mb-4 text-xs text-muted-foreground">
          Aceite, edite ou rejeite individualmente. Nenhuma decisão altera o currículo até você
          criar a variante.
        </p>
        <div className="space-y-3">
          {detail.suggestions.map((item) => (
            <SuggestionCard
              key={item.suggestion_id}
              item={item}
              editing={editingSuggestion === item.suggestion_id}
              editedValue={editedValue}
              onEditedValue={onEditedValue}
              onEdit={() => onEditSuggestion(item)}
              onReview={(action) => onReview(item, action)}
              pending={pending}
            />
          ))}
        </div>
        {detail.suggestions.length === 0 && (
          <EmptyState
            title="Sem sugestões ainda"
            description="Execute ou repita a análise depois de escolher currículo e vaga."
          />
        )}
      </Panel>
    );
  if (step === 7)
    return (
      <Panel title="Variante e diff" eyebrow="Etapa 7">
        {!detail.variant ? (
          <div className="py-8 text-center">
            <FileDiff className="mx-auto h-8 w-8 text-accent" />
            <p className="mt-3 text-sm">Crie uma cópia apenas com sugestões aprovadas.</p>
            <PrimaryAction onClick={onVariant} pending={pending} label="Criar variante" />
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h3 className="font-semibold">{detail.variant.title}</h3>
              <Link to="/resume-studio" className="text-xs font-semibold underline">
                Abrir no Resume Studio
              </Link>
            </div>
            {detail.variant.change_set.map((change) => (
              <div key={change.change_id} className="overflow-hidden rounded-xl border">
                <div className="border-b bg-muted/40 px-4 py-2 text-xs font-semibold">
                  {change.section} · {change.change_type}
                </div>
                <div className="grid md:grid-cols-2">
                  <DiffBlock label="Antes" value={change.before} tone="before" />
                  <DiffBlock label="Depois" value={change.after} tone="after" />
                </div>
                <div className="border-t px-4 py-3 text-xs text-muted-foreground">
                  <strong>Motivo:</strong> {change.reason} · <strong>Evidências:</strong>{" "}
                  {change.source_refs.length}
                </div>
              </div>
            ))}
          </div>
        )}
      </Panel>
    );
  if (step === 8)
    return (
      <Panel title="Kit de candidatura" eyebrow="Etapa 8">
        {!detail.kit ? (
          <div className="py-8 text-center">
            <Sparkles className="mx-auto h-8 w-8 text-accent" />
            <p className="mt-3 text-sm">Gere rascunhos factuais para revisar e copiar.</p>
            <PrimaryAction onClick={onKit} pending={pending} label="Criar kit" />
          </div>
        ) : (
          <div className="grid gap-3 md:grid-cols-2">
            {detail.kit.items.map((item) => (
              <article key={item.item_id} className="rounded-xl border bg-background p-4">
                <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                  {item.type.replaceAll("_", " ")}
                </p>
                <p className="mt-3 text-sm leading-6">{item.content}</p>
                <p className="mt-3 text-xs text-muted-foreground">
                  {item.evidence_used.length} evidência(s) · revisão pendente
                </p>
              </article>
            ))}
          </div>
        )}
      </Panel>
    );
  if (step === 9)
    return (
      <Panel title="Plano de ação" eyebrow="Etapa 9">
        {!detail.action_plan ? (
          <div className="py-8 text-center">
            <ClipboardCheck className="mx-auto h-8 w-8 text-accent" />
            <p className="mt-3 text-sm">Transforme bloqueadores reais em tarefas de 7 dias.</p>
            <PrimaryAction onClick={onPlan} pending={pending} label="Criar plano de 7 dias" />
          </div>
        ) : (
          <ol className="space-y-3">
            {detail.action_plan.items.map((item, index) => (
              <li key={item.action_item_id} className="flex gap-3 rounded-xl border p-4">
                <span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-primary text-xs text-primary-foreground">
                  {index + 1}
                </span>
                <div>
                  <h3 className="text-sm font-semibold">{item.title}</h3>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {item.estimated_effort} · prioridade {item.priority}
                  </p>
                </div>
              </li>
            ))}
          </ol>
        )}
      </Panel>
    );
  return (
    <Panel title="Salvar no Tracker" eyebrow="Etapa 10">
      {detail.session.status === "completed" ? (
        <div className="py-8 text-center">
          <CheckCircle2 className="mx-auto h-10 w-10 text-success" />
          <h3 className="mt-3 text-lg font-semibold">Candidatura salva</h3>
          <p className="mt-2 text-xs text-muted-foreground">
            Tracker <code>{detail.session.tracker_application_id}</code> com vaga, currículo,
            relatório e kit vinculados por snapshots.
          </p>
          <Link
            to="/tracker"
            className="mt-5 inline-flex rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground"
          >
            Abrir Tracker
          </Link>
        </div>
      ) : (
        <div className="space-y-5">
          <div className="rounded-xl border bg-muted/30 p-4 text-sm">
            <h3 className="font-semibold">O que será salvo</h3>
            <ul className="mt-3 grid gap-2 text-xs text-muted-foreground sm:grid-cols-2">
              <li>✓ Snapshot da vaga</li>
              <li>✓ Currículo/variante usados</li>
              <li>✓ Relatório determinístico</li>
              <li>✓ Kit e plano vinculados</li>
            </ul>
          </div>
          <label className="flex cursor-pointer items-start gap-3 rounded-xl border p-4 text-sm">
            <input
              type="checkbox"
              checked={privacyAcknowledged}
              onChange={(event) => onPrivacyAcknowledged(event.target.checked)}
              className="mt-0.5 h-4 w-4"
            />
            <span>
              <strong>Confirmo o aviso de privacidade.</strong>
              <span className="mt-1 block text-xs text-muted-foreground">
                Nenhuma candidatura será enviada automaticamente.
              </span>
            </span>
          </label>
          <PrimaryAction
            onClick={onTracker}
            pending={pending}
            disabled={!privacyAcknowledged}
            label="Salvar no Tracker"
          />
        </div>
      )}
    </Panel>
  );
}

function Panel({
  title,
  eyebrow,
  children,
}: {
  title: string;
  eyebrow: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-2xl border bg-card p-5 shadow-[var(--shadow-soft)] sm:p-6">
      <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-accent">{eyebrow}</p>
      <h2 className="mt-1 mb-5 text-display text-xl">{title}</h2>
      {children}
    </div>
  );
}

function ReadinessReport({
  detail,
  onAnalyze,
  pending,
}: {
  detail: ApplicationLabDetail;
  onAnalyze: () => void;
  pending: boolean;
}) {
  const report = detail.report!;
  const dimensions = Object.values(report.source_dimensions);
  return (
    <div className="space-y-6" data-testid="readiness-report">
      <div className="grid gap-4 lg:grid-cols-[180px_1fr]">
        <div className="grid place-items-center rounded-2xl bg-[image:var(--gradient-ink)] p-5 text-primary-foreground">
          <span className="text-display text-5xl tabular-nums">{report.readiness_score}</span>
          <span className="mt-1 text-xs text-white/65">readiness / 100</span>
        </div>
        <div className="rounded-xl border p-4">
          <h3 className="text-sm font-semibold">Cobertura, não promessa</h3>
          <p className="mt-2 text-xs leading-5 text-muted-foreground">{report.score_explanation}</p>
          <p className="mt-2 text-xs font-semibold text-warning-foreground">
            Readiness não é probabilidade de entrevista.
          </p>
          <div className="mt-4 grid grid-cols-2 gap-3">
            <Metric label="Evidências" value={`${Math.round(report.evidence_coverage * 100)}%`} />
            <Metric
              label="Requisitos"
              value={`${Math.round(report.requirement_coverage * 100)}%`}
            />
          </div>
        </div>
      </div>
      <div className="grid gap-2 sm:grid-cols-2">
        {dimensions.map((dimension) => (
          <div key={dimension.dimension} className="flex items-start gap-3 rounded-lg border p-3">
            <StatusMark status={dimension.status} />
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <h4 className="text-xs font-semibold">{dimension.label}</h4>
                <span className="text-[10px] text-muted-foreground">
                  {dimension.status === "not_applicable"
                    ? "N/A"
                    : `${Math.round((dimension.coverage ?? 0) * 100)}%`}
                </span>
              </div>
              <p className="mt-1 text-[11px] leading-4 text-muted-foreground">
                {dimension.explanation}
              </p>
            </div>
          </div>
        ))}
      </div>
      <div>
        <h3 className="mb-3 text-sm font-semibold">Uma análise consolidada em três perspectivas</h3>
        <div className="grid gap-3 md:grid-cols-3">
          {Object.values(report.perspectives).map((perspective) => (
            <article key={perspective.perspective_id} className="rounded-xl border p-4">
              <h4 className="text-sm font-semibold">{perspective.label}</h4>
              <p className="mt-2 text-xs leading-5 text-muted-foreground">{perspective.summary}</p>
              <ul className="mt-3 space-y-2 text-xs">
                {perspective.findings.map((finding) => (
                  <li key={finding} className="flex gap-2">
                    <span className="text-accent">•</span> {finding}
                  </li>
                ))}
              </ul>
            </article>
          ))}
        </div>
      </div>
      {report.top_blockers.length > 0 && (
        <div className="rounded-xl border border-warning/30 bg-warning/5 p-4">
          <h3 className="text-sm font-semibold">Bloqueadores prioritários</h3>
          <ul className="mt-2 space-y-1 text-xs text-muted-foreground">
            {report.top_blockers.map((item) => (
              <li key={item}>• {item}</li>
            ))}
          </ul>
        </div>
      )}
      <button
        type="button"
        onClick={onAnalyze}
        disabled={pending}
        className="inline-flex items-center gap-2 text-xs font-semibold underline disabled:opacity-50"
      >
        <RotateCcw className="h-3.5 w-3.5" /> Reexecutar somente a análise
      </button>
    </div>
  );
}

function SuggestionCard({
  item,
  editing,
  editedValue,
  onEditedValue,
  onEdit,
  onReview,
  pending,
}: {
  item: ApplicationSuggestion;
  editing: boolean;
  editedValue: string;
  onEditedValue: (value: string) => void;
  onEdit: () => void;
  onReview: (action: "accept" | "edit" | "reject" | "undo") => void;
  pending: boolean;
}) {
  return (
    <article className="rounded-xl border bg-background p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
            {item.section} · {item.suggestion_type}
          </p>
          <p className="mt-2 text-xs text-muted-foreground">{item.reason}</p>
        </div>
        <StatusPill status={item.status} />
      </div>
      {(item.before || item.after) && (
        <div className="mt-4 grid gap-2 md:grid-cols-2">
          <DiffBlock label="Antes" value={item.before || "—"} tone="before" />
          <DiffBlock label="Depois" value={item.after || "—"} tone="after" />
        </div>
      )}
      {editing && (
        <div className="mt-4">
          <label htmlFor={`edit-${item.suggestion_id}`} className="text-xs font-semibold">
            Sua versão
          </label>
          <textarea
            id={`edit-${item.suggestion_id}`}
            value={editedValue}
            onChange={(event) => onEditedValue(event.target.value)}
            className="mt-2 min-h-24 w-full rounded-md border p-3 text-sm"
          />
        </div>
      )}
      <div className="mt-4 flex flex-wrap items-center gap-2">
        {item.status === "pending" ? (
          <>
            <button
              type="button"
              onClick={() => onReview("accept")}
              disabled={pending || (!item.evidence_used.length && Boolean(item.after))}
              className="rounded-md bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground disabled:opacity-40"
            >
              Aceitar
            </button>
            <button
              type="button"
              onClick={editing ? () => onReview("edit") : onEdit}
              disabled={pending || !item.after}
              className="rounded-md border px-3 py-1.5 text-xs font-semibold disabled:opacity-40"
            >
              {editing ? "Salvar edição" : "Editar"}
            </button>
            <button
              type="button"
              onClick={() => onReview("reject")}
              disabled={pending}
              className="rounded-md border px-3 py-1.5 text-xs font-semibold text-destructive"
            >
              Rejeitar
            </button>
          </>
        ) : (
          <button
            type="button"
            onClick={() => onReview("undo")}
            disabled={pending}
            className="inline-flex items-center gap-1 rounded-md border px-3 py-1.5 text-xs font-semibold"
          >
            <RotateCcw className="h-3 w-3" /> Desfazer decisão
          </button>
        )}
        <span className="ml-auto text-[11px] text-muted-foreground">
          {item.evidence_used.length > 0
            ? `${item.evidence_used.length} evidência(s)`
            : "Sem evidência — não pode virar fato"}
        </span>
      </div>
      {item.warnings.map((warning) => (
        <p key={warning} className="mt-3 flex items-center gap-2 text-xs text-warning-foreground">
          <AlertTriangle className="h-3.5 w-3.5" /> {warning}
        </p>
      ))}
    </article>
  );
}

function DiffBlock({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone: "before" | "after";
}) {
  return (
    <div
      className={cn(
        "p-3 text-xs leading-5",
        tone === "before" ? "bg-destructive/5" : "bg-success/5",
      )}
    >
      <p className="mb-1 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
        {label}
      </p>
      {value}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-muted p-3">
      <p className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</p>
      <p className="mt-1 text-display text-xl">{value}</p>
    </div>
  );
}

function StatusMark({ status }: { status: string }) {
  return (
    <span
      className={cn(
        "mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full text-[10px]",
        status === "met" && "bg-success/15 text-success",
        status === "partial" && "bg-warning/15 text-warning-foreground",
        status === "missing" && "bg-destructive/10 text-destructive",
        status === "not_applicable" && "bg-muted text-muted-foreground",
      )}
    >
      {status === "met" ? (
        <Check className="h-3 w-3" />
      ) : status === "missing" ? (
        <X className="h-3 w-3" />
      ) : (
        "•"
      )}
    </span>
  );
}

function StatusPill({ status }: { status: SuggestionStatus }) {
  const labels: Record<SuggestionStatus, string> = {
    pending: "Pendente",
    accepted: "Aceita",
    edited: "Editada",
    rejected: "Rejeitada",
  };
  return (
    <span
      className={cn(
        "rounded-full px-2 py-1 text-[10px] font-semibold",
        status === "pending" && "bg-muted",
        (status === "accepted" || status === "edited") && "bg-success/15 text-success",
        status === "rejected" && "bg-destructive/10 text-destructive",
      )}
    >
      {labels[status]}
    </span>
  );
}

function PrimaryAction({
  onClick,
  pending,
  label,
  disabled = false,
}: {
  onClick: () => void;
  pending: boolean;
  label: string;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={pending || disabled}
      className="mx-auto mt-5 inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground hover:opacity-90 disabled:opacity-40"
    >
      {pending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
      {label}
    </button>
  );
}
