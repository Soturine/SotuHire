import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Check,
  CircleAlert,
  FileDiff,
  Loader2,
  Play,
  RotateCcw,
  ShieldCheck,
  X,
} from "lucide-react";
import { useState } from "react";

import { AppShell } from "@/components/app-shell";
import { EmptyState, ErrorState, LoadingState } from "@/components/states";
import { Button } from "@/components/ui/button";
import { v2Api, type ApprovalAction, type ProposedAction } from "@/features/career-copilot/api";
import { useApiMode } from "@/lib/api/mode";
import { toast } from "@/lib/notify";
import { usePreferences } from "@/lib/preferences";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/approvals")({ component: ApprovalQueue });

type Locale = "pt-BR" | "en-US";
type Filter = "pending" | "approved" | "done";

const COPY = {
  "pt-BR": {
    title: "Aguardando sua aprovação",
    description: "Prévia, evidências, impacto e como desfazer, antes de qualquer escrita local.",
    rule: "Não existe Aprovar tudo. Cada alteração importante precisa da sua decisão individual.",
    filters: { pending: "Para decidir", approved: "Aprovadas", done: "Encerradas" },
    empty: {
      pending: ["Nada esperando você", "Quando o Copilot propuser uma escrita, ela aparece aqui."],
      approved: [
        "Nenhuma aprovada aguardando execução",
        "Aprovar não executa: você executa depois.",
      ],
      done: ["Nada encerrado ainda", "Executadas, rejeitadas e desfeitas ficam aqui."],
    },
    before: "Hoje",
    after: "Depois de executar",
    changed: "muda",
    affected: "entidade(s) afetada(s)",
    evidence: "evidência(s)",
    undo: "Como desfazer",
    noUndo: "Não reversível",
    approve: "Aprovar",
    reject: "Rejeitar",
    execute: "Executar localmente",
    revert: "Desfazer",
    done: {
      approve: "Aprovada. Nada foi executado ainda.",
      reject: "Rejeitada. Nada foi alterado.",
      execute: "Executada localmente.",
      undo: "Desfeita.",
    },
    failed: "A ação não foi feita",
    risk: { low: "risco baixo", medium: "risco médio", high: "risco alto" } as Record<
      string,
      string
    >,
    status: {
      proposed: "proposta",
      reviewing: "em revisão",
      approved: "aprovada",
      rejected: "rejeitada",
      executed: "executada",
      failed: "falhou",
      undone: "desfeita",
      expired: "expirada",
      stale: "desatualizada",
    } as Record<string, string>,
    empty_value: "—",
  },
  "en-US": {
    title: "Waiting for your approval",
    description: "Preview, evidence, impact and how to undo, before any local write.",
    rule: "There is no Approve all. Every important change requires an individual decision.",
    filters: { pending: "To decide", approved: "Approved", done: "Closed" },
    empty: {
      pending: ["Nothing is waiting for you", "When the Copilot proposes a write, it shows here."],
      approved: ["No approved item waiting to run", "Approving does not run: you run it after."],
      done: ["Nothing closed yet", "Executed, rejected and undone items stay here."],
    },
    before: "Today",
    after: "After running",
    changed: "changes",
    affected: "affected entity(s)",
    evidence: "evidence reference(s)",
    undo: "How to undo",
    noUndo: "Not reversible",
    approve: "Approve",
    reject: "Reject",
    execute: "Run locally",
    revert: "Undo",
    done: {
      approve: "Approved. Nothing has run yet.",
      reject: "Rejected. Nothing changed.",
      execute: "Ran locally.",
      undo: "Undone.",
    },
    failed: "The action was not done",
    risk: { low: "low risk", medium: "medium risk", high: "high risk" } as Record<string, string>,
    status: {
      proposed: "proposed",
      reviewing: "reviewing",
      approved: "approved",
      rejected: "rejected",
      executed: "executed",
      failed: "failed",
      undone: "undone",
      expired: "expired",
      stale: "stale",
    } as Record<string, string>,
    empty_value: "—",
  },
} satisfies Record<Locale, unknown>;

const FILTER_STATUSES: Record<Filter, string[]> = {
  pending: ["proposed", "reviewing"],
  approved: ["approved"],
  done: ["executed", "rejected", "undone", "failed", "expired", "stale"],
};

function ApprovalQueue() {
  const { mode, baseUrl } = useApiMode();
  const { locale } = usePreferences();
  const t = COPY[locale];
  const client = useQueryClient();
  const [filter, setFilter] = useState<Filter>("pending");
  const key = ["v2", "approvals", mode, baseUrl];
  const approvals = useQuery({ queryKey: key, queryFn: () => v2Api(mode, baseUrl).approvals() });
  const transition = useMutation({
    mutationFn: ({ id, action }: { id: string; action: ApprovalAction }) =>
      v2Api(mode, baseUrl).transition(id, action),
    onSuccess: (_data, { action }) => {
      toast.success(t.done[action]);
      return client.invalidateQueries({ queryKey: key });
    },
    // Before: a failed approve/execute said nothing and the card stayed as it was.
    onError: (error: Error) => toast.error(`${t.failed}: ${error.message}`),
  });

  const items = approvals.data ?? [];
  const count = (f: Filter) =>
    items.filter((item) => FILTER_STATUSES[f].includes(item.status)).length;
  const visible = items.filter((item) => FILTER_STATUSES[filter].includes(item.status));

  return (
    <AppShell title={t.title} description={t.description}>
      <div className="mx-auto max-w-5xl space-y-5">
        <p className="flex items-start gap-3 rounded-xl border bg-surface-accent px-4 py-3 text-sm">
          <ShieldCheck aria-hidden className="mt-0.5 h-5 w-5 shrink-0 text-accent-strong" />
          {t.rule}
        </p>

        {approvals.isError ? (
          <ErrorState error={approvals.error} onRetry={() => approvals.refetch()} />
        ) : approvals.isLoading ? (
          <LoadingState />
        ) : (
          <>
            <div role="group" aria-label={t.title} className="flex flex-wrap gap-1.5">
              {(Object.keys(FILTER_STATUSES) as Filter[]).map((f) => (
                <button
                  key={f}
                  type="button"
                  aria-pressed={filter === f}
                  onClick={() => setFilter(f)}
                  className={cn(
                    "rounded-full border px-3 py-1 text-sm font-medium transition-colors duration-(--duration-1)",
                    filter === f
                      ? "border-primary bg-primary text-primary-foreground"
                      : "bg-card text-muted-foreground hover:border-foreground/30 hover:text-foreground",
                  )}
                >
                  {t.filters[f]}
                  <span className="tabular ml-1.5 opacity-70">{count(f)}</span>
                </button>
              ))}
            </div>

            {visible.length ? (
              <ul className="space-y-4">
                {visible.map((item) => (
                  <li key={item.proposal_id}>
                    <ProposalCard
                      item={item}
                      t={t}
                      pending={
                        transition.isPending && transition.variables?.id === item.proposal_id
                          ? transition.variables.action
                          : undefined
                      }
                      busy={transition.isPending}
                      onAction={(action) => transition.mutate({ id: item.proposal_id, action })}
                    />
                  </li>
                ))}
              </ul>
            ) : (
              <EmptyState title={t.empty[filter][0]} description={t.empty[filter][1]} />
            )}
          </>
        )}
      </div>
    </AppShell>
  );
}

function ProposalCard({
  item,
  t,
  pending,
  busy,
  onAction,
}: {
  item: ProposedAction;
  t: (typeof COPY)[Locale];
  pending: ApprovalAction | undefined;
  busy: boolean;
  onAction: (action: ApprovalAction) => void;
}) {
  const risk = item.risk?.toLowerCase();
  const icon = (action: ApprovalAction, Icon: typeof Check) =>
    pending === action ? <Loader2 className="animate-spin" /> : <Icon />;
  return (
    <article
      aria-labelledby={`proposal-${item.proposal_id}`}
      className={cn(
        "rounded-xl border bg-card p-5 shadow-[var(--shadow-soft)] md:p-6",
        FILTER_STATUSES.pending.includes(item.status) && "border-l-4 border-l-seal",
      )}
    >
      <div className="flex flex-col gap-5 md:flex-row md:items-start">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-1.5 text-xs">
            <span
              className={cn(
                "rounded-full px-2 py-0.5 font-medium",
                risk === "high"
                  ? "bg-destructive/12 text-destructive-strong"
                  : risk === "medium"
                    ? "bg-highlight text-highlight-foreground"
                    : "bg-success/12 text-success-strong",
              )}
            >
              {t.risk[risk] ?? item.risk}
            </span>
            <span className="rounded-full bg-muted px-2 py-0.5 text-muted-foreground">
              {t.status[item.status] ?? item.status}
            </span>
            <span className="font-mono text-[11px] text-muted-foreground">{item.action_type}</span>
          </div>
          <h2 id={`proposal-${item.proposal_id}`} className="mt-3 text-lg font-semibold">
            {item.title}
          </h2>
          <p className="mt-1.5 text-sm text-muted-foreground">{item.reason}</p>
          <ChangePreview before={item.before_snapshot} after={item.after_preview} t={t} />
          <div className="mt-4 flex flex-wrap gap-x-5 gap-y-1 text-xs text-muted-foreground">
            <span className="inline-flex items-center gap-1">
              <FileDiff aria-hidden className="h-3.5 w-3.5" />
              {item.affected_entities.length} {t.affected}
            </span>
            <span>
              {item.evidence_refs.length} {t.evidence}
            </span>
            <span className="inline-flex items-center gap-1">
              <RotateCcw aria-hidden className="h-3.5 w-3.5" />
              {item.reversible ? `${t.undo}: ${item.undo_strategy}` : t.noUndo}
            </span>
          </div>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2 md:w-48 md:flex-col">
          {FILTER_STATUSES.pending.includes(item.status) && (
            <>
              <Button disabled={busy} onClick={() => onAction("approve")}>
                {icon("approve", Check)}
                {t.approve}
              </Button>
              <Button variant="outline" disabled={busy} onClick={() => onAction("reject")}>
                {icon("reject", X)}
                {t.reject}
              </Button>
            </>
          )}
          {item.status === "approved" && (
            <Button disabled={busy} onClick={() => onAction("execute")}>
              {icon("execute", Play)}
              {t.execute}
            </Button>
          )}
          {item.status === "executed" && item.reversible && (
            <Button variant="outline" disabled={busy} onClick={() => onAction("undo")}>
              {icon("undo", RotateCcw)}
              {t.revert}
            </Button>
          )}
          {item.status === "failed" && (
            <p className="inline-flex items-center gap-1.5 text-sm text-destructive-strong">
              <CircleAlert aria-hidden className="h-4 w-4" />
              {t.status.failed}
            </p>
          )}
        </div>
      </div>
    </article>
  );
}

/** Field by field, the changed ones marked; raw JSON only for nested values. */
function ChangePreview({
  before,
  after,
  t,
}: {
  before: Record<string, unknown>;
  after: Record<string, unknown>;
  t: (typeof COPY)[Locale];
}) {
  const keys = [...new Set([...Object.keys(before ?? {}), ...Object.keys(after ?? {})])];
  if (!keys.length) return null;
  const show = (value: unknown) =>
    value === undefined || value === null || value === ""
      ? t.empty_value
      : typeof value === "object"
        ? JSON.stringify(value)
        : String(value);
  return (
    <div className="mt-4 overflow-hidden rounded-lg border">
      <table className="w-full table-fixed text-left text-xs">
        <thead className="bg-surface-muted text-muted-foreground">
          <tr>
            <th scope="col" className="w-1/4 px-3 py-2 font-medium">
              <span className="sr-only">Campo</span>
            </th>
            <th scope="col" className="px-3 py-2 font-medium">
              {t.before}
            </th>
            <th scope="col" className="px-3 py-2 font-medium">
              {t.after}
            </th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {keys.map((key) => {
            const changed = show(before?.[key]) !== show(after?.[key]);
            return (
              <tr key={key} className={cn(changed && "bg-surface-accent/60")}>
                <th scope="row" className="px-3 py-2 align-top font-mono font-normal">
                  {key}
                  {changed ? (
                    <span className="ml-1.5 rounded bg-accent/15 px-1 font-sans text-[10px] text-accent-strong">
                      {t.changed}
                    </span>
                  ) : null}
                </th>
                <td className="break-words px-3 py-2 align-top text-muted-foreground">
                  {show(before?.[key])}
                </td>
                <td className="break-words px-3 py-2 align-top">{show(after?.[key])}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
