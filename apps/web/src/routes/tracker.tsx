import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { GripVertical, Plus, Search, LayoutGrid, Rows3 } from "lucide-react";
import { useMemo, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { EmptyState, ErrorState, LoadingState } from "@/components/states";
import { useApi } from "@/lib/api/hooks";
import type { TrackerJob, TrackerStatus } from "@/lib/api/types";
import { useApiMode } from "@/lib/api/mode";
import { statusLabel } from "@/lib/labels";
import { toast } from "@/lib/notify";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/tracker")({
  head: () => ({ meta: [{ title: "Candidaturas — SotuHire" }] }),
  component: TrackerPage,
});

type ColumnDef = {
  id: TrackerStatus;
  label: string;
  stage: "novas" | "andamento" | "resultado";
  accent: string;
};

const COLUMNS: ColumnDef[] = [
  { id: "found", label: "Encontrada", stage: "novas", accent: "bg-muted-foreground/40" },
  { id: "analyzed", label: "Salva", stage: "novas", accent: "bg-chart-3" },
  { id: "good_fit", label: "Boa para aplicar", stage: "novas", accent: "bg-chart-2" },
  { id: "applied", label: "Aplicada", stage: "andamento", accent: "bg-chart-1" },
  { id: "message_sent", label: "Mensagem enviada", stage: "andamento", accent: "bg-chart-1" },
  { id: "follow_up", label: "Follow-up", stage: "andamento", accent: "bg-warning" },
  { id: "interview", label: "Entrevista", stage: "andamento", accent: "bg-accent" },
  { id: "technical_test", label: "Teste técnico", stage: "andamento", accent: "bg-warning" },
  { id: "offer", label: "Oferta", stage: "resultado", accent: "bg-success" },
  { id: "rejected", label: "Rejeitada", stage: "resultado", accent: "bg-destructive" },
  { id: "archived", label: "Arquivada", stage: "resultado", accent: "bg-muted-foreground/40" },
];

const STAGES: { id: ColumnDef["stage"]; label: string; desc: string }[] = [
  { id: "novas", label: "Novas oportunidades", desc: "Triagem inicial" },
  { id: "andamento", label: "Em andamento", desc: "Após enviar candidatura" },
  { id: "resultado", label: "Resultado", desc: "Oferta, rejeição ou arquivada" },
];

function TrackerPage() {
  const api = useApi();
  const { mode } = useApiMode();
  const qc = useQueryClient();
  const jobsKey = ["tracker-jobs", mode] as const;

  const jobsQ = useQuery({ queryKey: jobsKey, queryFn: () => api.trackerJobs() });
  const [creating, setCreating] = useState(false);
  const [query, setQuery] = useState("");
  const [view, setView] = useState<"board" | "list">("board");
  const [dragOver, setDragOver] = useState<TrackerStatus | null>(null);

  const update = useMutation({
    mutationFn: ({ id, status }: { id: string; status: TrackerStatus }) =>
      api.trackerUpdate(id, { status }),
    onMutate: async ({ id, status }) => {
      await qc.cancelQueries({ queryKey: jobsKey });
      const previous = qc.getQueryData<{ jobs: TrackerJob[] }>(jobsKey);
      qc.setQueryData<{ jobs: TrackerJob[] }>(jobsKey, (current) => ({
        jobs: (current?.jobs ?? []).map((job) =>
          job.id === id
            ? { ...job, status, updated_at: new Date().toISOString().slice(0, 10) }
            : job,
        ),
      }));
      return { previous };
    },
    onSuccess: (data) => {
      qc.setQueryData<{ jobs: TrackerJob[] }>(jobsKey, (current) => ({
        jobs: (current?.jobs ?? []).map((job) => (job.id === data.job.id ? data.job : job)),
      }));
      toast.success(`Candidatura movida para ${statusLabel(data.job.status)}.`);
    },
    onError: (e: Error, _vars, context) => {
      if (context?.previous) qc.setQueryData(jobsKey, context.previous);
      toast.error(`${e.message}. Mudança revertida.`);
    },
  });

  const create = useMutation({
    mutationFn: (input: { title: string; company: string; source?: string; notes?: string }) =>
      api.trackerCreate({ ...input, status: "found" }),
    onSuccess: (data) => {
      qc.setQueryData<{ jobs: TrackerJob[] }>(jobsKey, (current) => ({
        jobs: [data.job, ...(current?.jobs ?? []).filter((job) => job.id !== data.job.id)],
      }));
      toast.success("Candidatura adicionada");
      setCreating(false);
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const filteredJobs = useMemo(() => {
    const q = query.trim().toLowerCase();
    const all = jobsQ.data?.jobs ?? [];
    if (!q) return all;
    return all.filter(
      (j) =>
        j.title.toLowerCase().includes(q) ||
        j.company.toLowerCase().includes(q) ||
        (j.source ?? "").toLowerCase().includes(q),
    );
  }, [jobsQ.data, query]);

  const byColumn = useMemo(() => {
    const m = new Map<TrackerStatus, TrackerJob[]>();
    COLUMNS.forEach((c) => m.set(c.id, []));
    for (const j of filteredJobs) {
      const list = m.get(j.status as TrackerStatus) ?? m.get("found")!;
      list.push(j);
    }
    return m;
  }, [filteredJobs]);

  const totalCount = jobsQ.data?.jobs.length ?? 0;

  function onDrop(e: React.DragEvent, status: TrackerStatus) {
    e.preventDefault();
    setDragOver(null);
    const id = e.dataTransfer.getData("text/plain");
    const current = jobsQ.data?.jobs.find((job) => job.id === id);
    if (id && current && current.status !== status) update.mutate({ id, status });
  }

  return (
    <AppShell
      title="Candidaturas"
      description="Acompanhe cada vaga do primeiro contato até a oferta. Arraste cards entre as etapas."
      actions={
        <>
          <div className="hidden items-center rounded-md border border-input bg-card p-0.5 sm:flex">
            <button
              onClick={() => setView("board")}
              className={cn(
                "inline-flex items-center gap-1 rounded px-2 py-1 text-[11px] font-medium transition-colors",
                view === "board"
                  ? "bg-muted text-foreground"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              <LayoutGrid className="h-3 w-3" /> Quadro
            </button>
            <button
              onClick={() => setView("list")}
              className={cn(
                "inline-flex items-center gap-1 rounded px-2 py-1 text-[11px] font-medium transition-colors",
                view === "list"
                  ? "bg-muted text-foreground"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              <Rows3 className="h-3 w-3" /> Lista
            </button>
          </div>
          <button
            onClick={() => setCreating(true)}
            data-testid="new-application-button"
            className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground shadow-sm transition-all hover:opacity-90 hover:shadow-md"
          >
            <Plus className="h-3.5 w-3.5" /> Nova candidatura
          </button>
        </>
      }
    >
      {jobsQ.isLoading ? (
        <LoadingState />
      ) : jobsQ.isError ? (
        <ErrorState error={jobsQ.error} onRetry={() => jobsQ.refetch()} />
      ) : totalCount === 0 ? (
        <EmptyState
          title="Nenhuma candidatura ainda"
          description="Comece adicionando uma vaga ou rodando uma análise de compatibilidade."
          action={
            <button
              onClick={() => setCreating(true)}
              data-testid="new-application-button"
              className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:opacity-90"
            >
              <Plus className="h-3.5 w-3.5" /> Adicionar candidatura
            </button>
          }
        />
      ) : (
        <div className="space-y-6">
          {/* Toolbar */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative flex-1 min-w-[220px]">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Filtrar por cargo, empresa ou fonte"
                className="h-9 w-full rounded-md border border-input bg-card pl-9 pr-3 text-sm outline-none transition-colors focus:border-accent/50 focus:ring-2 focus:ring-accent/20"
              />
            </div>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <span className="rounded-full bg-muted px-2 py-0.5 tabular-nums">
                {filteredJobs.length}
              </span>
              <span>de {totalCount} candidaturas</span>
            </div>
          </div>

          {view === "list" ? (
            <ListView
              jobs={filteredJobs}
              onChange={(id, status) => update.mutate({ id, status })}
            />
          ) : (
            <div className="space-y-8">
              {STAGES.map((stage) => {
                const cols = COLUMNS.filter((c) => c.stage === stage.id);
                const stageTotal = cols.reduce(
                  (acc, c) => acc + (byColumn.get(c.id)?.length ?? 0),
                  0,
                );
                return (
                  <section key={stage.id}>
                    <div className="mb-3 flex items-baseline justify-between gap-3 border-b border-border pb-2">
                      <div className="min-w-0">
                        <h2 className="text-display text-base sm:text-lg">{stage.label}</h2>
                        <p className="truncate text-xs text-muted-foreground">{stage.desc}</p>
                      </div>
                      <span className="shrink-0 text-xs tabular-nums text-muted-foreground">
                        {stageTotal} {stageTotal === 1 ? "vaga" : "vagas"}
                      </span>
                    </div>
                    <div className="w-full overflow-x-auto pb-2">
                      <div
                        className={cn(
                          "grid min-w-[680px] gap-3 sm:min-w-0",
                          cols.length === 3
                            ? "sm:grid-cols-2 lg:grid-cols-3"
                            : "sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5",
                        )}
                      >
                        {cols.map((c) => {
                          const items = byColumn.get(c.id) ?? [];
                          const isOver = dragOver === c.id;
                          return (
                            <div
                              key={c.id}
                              data-testid={`kanban-column-${c.id}`}
                              onDragOver={(e) => {
                                e.preventDefault();
                                e.dataTransfer.dropEffect = "move";
                                setDragOver(c.id);
                              }}
                              onDragLeave={() => setDragOver((s) => (s === c.id ? null : s))}
                              onDrop={(e) => onDrop(e, c.id)}
                              aria-label={`Coluna ${c.label}`}
                              className={cn(
                                "group flex min-h-40 flex-col rounded-xl border bg-muted/30 p-3 transition-all duration-200",
                                isOver
                                  ? "border-accent/60 bg-accent/5 ring-2 ring-accent/20"
                                  : "border-border hover:border-border/70",
                              )}
                            >
                              <header className="mb-3 flex items-center justify-between gap-2 px-0.5">
                                <div className="flex min-w-0 items-center gap-2">
                                  <span className={cn("h-2 w-2 shrink-0 rounded-full", c.accent)} />
                                  <span className="truncate text-[12px] font-semibold uppercase tracking-wide text-foreground/80">
                                    {c.label}
                                  </span>
                                </div>
                                <span className="shrink-0 rounded-md bg-card px-1.5 py-0.5 text-[10px] font-medium tabular-nums text-muted-foreground">
                                  {items.length}
                                </span>
                              </header>
                              <div className="space-y-2">
                                {items.length === 0 ? (
                                  <div className="rounded-lg border border-dashed border-border/70 bg-background/40 p-4 text-center text-[11px] text-muted-foreground">
                                    Sem candidaturas
                                  </div>
                                ) : (
                                  items.map((j) => (
                                    <JobCard
                                      key={j.id}
                                      job={j}
                                      onChange={(status) => update.mutate({ id: j.id, status })}
                                      updating={update.isPending && update.variables?.id === j.id}
                                    />
                                  ))
                                )}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </section>
                );
              })}
            </div>
          )}
        </div>
      )}

      {creating && (
        <CreateDialog
          onCancel={() => setCreating(false)}
          onSubmit={(v) => create.mutate(v)}
          loading={create.isPending}
        />
      )}
    </AppShell>
  );
}

function JobCard({
  job,
  onChange,
  updating,
}: {
  job: TrackerJob;
  onChange: (status: TrackerStatus) => void;
  updating?: boolean;
}) {
  return (
    <div
      data-testid="kanban-card"
      draggable
      tabIndex={0}
      role="article"
      aria-label={`${job.title} em ${statusLabel(job.status)}`}
      onDragStart={(e) => {
        e.dataTransfer.setData("text/plain", job.id);
        e.dataTransfer.effectAllowed = "move";
      }}
      className="group/card cursor-grab rounded-lg border border-border bg-card p-3 shadow-[var(--shadow-soft)] transition-all duration-150 hover:-translate-y-0.5 hover:border-accent/40 hover:shadow-[var(--shadow-elevated)] active:cursor-grabbing active:scale-[0.99]"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="truncate text-sm font-semibold leading-tight">{job.title}</div>
          <div className="mt-0.5 truncate text-xs text-muted-foreground">{job.company}</div>
        </div>
        <GripVertical className="h-4 w-4 shrink-0 text-muted-foreground/30 opacity-0 transition-opacity group-hover/card:opacity-100" />
      </div>
      <div className="mt-3">
        <label className="sr-only" htmlFor={`status-${job.id}`}>
          Status da candidatura
        </label>
        <select
          id={`status-${job.id}`}
          value={job.status}
          onChange={(e) => onChange(e.target.value as TrackerStatus)}
          disabled={updating}
          data-testid="kanban-card-status-select"
          className="w-full rounded border border-input bg-background px-2 py-1 text-xs outline-none focus:border-accent/50 focus:ring-2 focus:ring-accent/20 disabled:opacity-50"
        >
          {COLUMNS.map((c) => (
            <option key={c.id} value={c.id}>
              {c.label}
            </option>
          ))}
        </select>
      </div>
      <div className="mt-3 flex items-center gap-1.5">
        {job.match_score !== undefined && (
          <span className="inline-flex items-center gap-1 rounded bg-chart-1/15 px-1.5 py-0.5 text-[10px] font-medium text-chart-1 tabular-nums">
            <span className="opacity-70">Comp.</span> {job.match_score}
          </span>
        )}
        {job.ats_score !== undefined && (
          <span className="inline-flex items-center gap-1 rounded bg-accent/15 px-1.5 py-0.5 text-[10px] font-medium text-accent tabular-nums">
            <span className="opacity-70">ATS</span> {job.ats_score}
          </span>
        )}
        {job.source && (
          <span className="ml-auto max-w-[40%] truncate text-[10px] text-muted-foreground">
            {job.source}
          </span>
        )}
      </div>
      <div className="mt-2 grid gap-1 text-[10px] text-muted-foreground">
        <div className="flex items-center justify-between gap-2">
          <span className="truncate">Origem: {job.source ?? "-"}</span>
          <span>{job.updated_at ? `Última análise: ${job.updated_at}` : "Sem análise"}</span>
        </div>
        <div className="flex items-center justify-between gap-2">
          <span>{job.created_at ? `Data: ${job.created_at}` : "Data não informada"}</span>
          <span>Score: {job.match_score ?? "-"}</span>
        </div>
        {job.notes && <p className="line-clamp-2 rounded bg-muted/60 p-1.5">{job.notes}</p>}
      </div>
    </div>
  );
}

function ListView({
  jobs,
  onChange,
}: {
  jobs: TrackerJob[];
  onChange: (id: string, status: TrackerStatus) => void;
}) {
  return (
    <div className="overflow-x-auto rounded-xl border border-border bg-card">
      <table className="w-full min-w-[720px] text-sm">
        <thead className="bg-muted/50 text-left text-[11px] uppercase tracking-wider text-muted-foreground">
          <tr>
            <th className="px-4 py-2.5 font-semibold">Vaga</th>
            <th className="hidden px-4 py-2.5 font-semibold sm:table-cell">Empresa</th>
            <th className="hidden px-4 py-2.5 font-semibold md:table-cell">Fonte</th>
            <th className="px-4 py-2.5 font-semibold">Estágio</th>
            <th className="px-4 py-2.5 text-right font-semibold">Scores</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {jobs.map((j) => (
            <tr key={j.id} className="transition-colors hover:bg-muted/40">
              <td className="px-4 py-2.5">
                <div className="font-medium">{j.title}</div>
                <div className="mt-0.5 text-[11px] text-muted-foreground">
                  {j.updated_at ? `Última análise: ${j.updated_at}` : "Sem análise"} ·{" "}
                  {j.notes || "Sem notas"}
                </div>
              </td>
              <td className="hidden px-4 py-2.5 text-muted-foreground sm:table-cell">
                {j.company}
              </td>
              <td className="hidden px-4 py-2.5 text-xs text-muted-foreground md:table-cell">
                {j.source ?? "—"} {j.created_at ? `· ${j.created_at}` : ""}
              </td>
              <td className="px-4 py-2.5">
                <select
                  value={j.status}
                  onChange={(e) => onChange(j.id, e.target.value as TrackerStatus)}
                  data-testid="application-status-select"
                  className="rounded border border-input bg-background px-2 py-1 text-xs outline-none focus:border-accent/50 focus:ring-2 focus:ring-accent/20"
                >
                  {COLUMNS.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.label}
                    </option>
                  ))}
                </select>
              </td>
              <td className="px-4 py-2.5">
                <div className="flex justify-end gap-1.5 text-[10px]">
                  {j.match_score !== undefined && (
                    <span className="rounded bg-chart-1/15 px-1.5 py-0.5 font-medium text-chart-1 tabular-nums">
                      C {j.match_score}
                    </span>
                  )}
                  {j.ats_score !== undefined && (
                    <span className="rounded bg-accent/15 px-1.5 py-0.5 font-medium text-accent tabular-nums">
                      A {j.ats_score}
                    </span>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function CreateDialog({
  onCancel,
  onSubmit,
  loading,
}: {
  onCancel: () => void;
  onSubmit: (v: { title: string; company: string; source?: string; notes?: string }) => void;
  loading: boolean;
}) {
  const [title, setTitle] = useState("");
  const [company, setCompany] = useState("");
  const [source, setSource] = useState("Manual");
  const [notes, setNotes] = useState("");
  return (
    <div
      data-testid="create-application-dialog"
      className="fixed inset-0 z-50 grid place-items-center bg-foreground/40 p-4 backdrop-blur-sm animate-in fade-in duration-150"
    >
      <div className="w-full max-w-md rounded-xl border border-border bg-card p-5 shadow-[var(--shadow-elevated)] animate-in zoom-in-95 duration-150">
        <h3 className="text-display text-lg">Nova candidatura</h3>
        <p className="mt-1 text-xs text-muted-foreground">Será criada no estágio Encontrada.</p>
        <div className="mt-4 space-y-3">
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Cargo"
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:border-accent/50 focus:ring-2 focus:ring-accent/20"
          />
          <input
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            placeholder="Empresa"
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:border-accent/50 focus:ring-2 focus:ring-accent/20"
          />
          <input
            value={source}
            onChange={(e) => setSource(e.target.value)}
            placeholder="Origem"
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:border-accent/50 focus:ring-2 focus:ring-accent/20"
          />
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Notas"
            className="h-20 w-full resize-none rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:border-accent/50 focus:ring-2 focus:ring-accent/20"
          />
        </div>
        <div className="mt-5 flex justify-end gap-2">
          <button
            onClick={onCancel}
            className="rounded-md border border-input bg-background px-3 py-1.5 text-sm hover:bg-muted"
          >
            Cancelar
          </button>
          <button
            data-testid="create-application-submit"
            onClick={() => onSubmit({ title, company, source, notes })}
            disabled={!title || !company || loading}
            className="rounded-md bg-primary px-3 py-1.5 text-sm text-primary-foreground hover:opacity-90 disabled:opacity-50"
          >
            {loading ? "Criando..." : "Criar"}
          </button>
        </div>
      </div>
    </div>
  );
}
