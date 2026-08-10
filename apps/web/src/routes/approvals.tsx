import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, FileDiff, RotateCcw, ShieldCheck, X } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { v2Api } from "@/features/career-copilot/api";
import { useApiMode } from "@/lib/api/mode";
import { usePreferences } from "@/lib/preferences";

export const Route = createFileRoute("/approvals")({ component: ApprovalQueue });

function ApprovalQueue() {
  const { mode, baseUrl } = useApiMode();
  const { locale } = usePreferences();
  const pt = locale === "pt-BR";
  const client = useQueryClient();
  const approvals = useQuery({
    queryKey: ["v2", "approvals", mode, baseUrl],
    queryFn: () => v2Api(mode, baseUrl).approvals(),
  });
  const transition = useMutation({
    mutationFn: ({
      id,
      action,
    }: {
      id: string;
      action: "approve" | "reject" | "execute" | "undo";
    }) => v2Api(mode, baseUrl).transition(id, action),
    onSuccess: () => client.invalidateQueries({ queryKey: ["v2", "approvals", mode, baseUrl] }),
  });
  return (
    <AppShell
      title={pt ? "Aguardando sua aprovação" : "Waiting for your approval"}
      description={
        pt
          ? "Prévia, evidências, impacto e undo antes de qualquer escrita local."
          : "Preview, evidence, impact, and undo before any local write."
      }
    >
      <div className="mx-auto max-w-5xl space-y-5">
        <div className="flex items-center gap-3 rounded-2xl border border-accent/20 bg-accent/5 p-4">
          <ShieldCheck className="h-6 w-6 text-accent" />
          <p className="text-sm">
            {pt
              ? "Não existe Aprovar tudo. Cada alteração importante precisa da sua decisão individual."
              : "There is no Approve all. Every important change requires an individual decision."}
          </p>
        </div>
        {approvals.data?.map((item) => (
          <article
            key={item.proposal_id}
            className="rounded-2xl border bg-card p-5 shadow-[var(--shadow-soft)] md:p-6"
          >
            <div className="flex flex-col gap-5 md:flex-row md:items-start">
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="rounded-full border px-2 py-1 text-xs font-medium">
                    {item.action_type}
                  </span>
                  <span className="rounded-full bg-warning/15 px-2 py-1 text-xs">
                    {item.risk} risk
                  </span>
                  <span className="rounded-full bg-muted px-2 py-1 text-xs">{item.status}</span>
                </div>
                <h2 className="mt-4 text-xl font-semibold">{item.title}</h2>
                <p className="mt-2 text-sm text-muted-foreground">{item.reason}</p>
                <div className="mt-5 grid gap-3 sm:grid-cols-2">
                  <Diff label={pt ? "Antes" : "Before"} value={item.before_snapshot} />
                  <Diff
                    label={pt ? "Depois da aprovação" : "After approval"}
                    value={item.after_preview}
                  />
                </div>
                <div className="mt-4 flex flex-wrap gap-4 text-xs text-muted-foreground">
                  <span>
                    <FileDiff className="mr-1 inline h-3.5 w-3.5" />
                    {item.affected_entities.length}{" "}
                    {pt ? "entidade(s) afetada(s)" : "affected entity(s)"}
                  </span>
                  <span>
                    {item.evidence_refs.length} {pt ? "evidência(s)" : "evidence reference(s)"}
                  </span>
                  {item.reversible && (
                    <span>
                      <RotateCcw className="mr-1 inline h-3.5 w-3.5" />
                      {item.undo_strategy}
                    </span>
                  )}
                </div>
              </div>
              <div className="flex shrink-0 flex-wrap gap-2 md:w-44 md:flex-col">
                {item.status === "proposed" && (
                  <>
                    <Button
                      onClick={() => transition.mutate({ id: item.proposal_id, action: "approve" })}
                    >
                      <Check />
                      {pt ? "Aprovar" : "Approve"}
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => transition.mutate({ id: item.proposal_id, action: "reject" })}
                    >
                      <X />
                      {pt ? "Rejeitar" : "Reject"}
                    </Button>
                  </>
                )}
                {item.status === "approved" && (
                  <Button
                    onClick={() => transition.mutate({ id: item.proposal_id, action: "execute" })}
                  >
                    {pt ? "Executar localmente" : "Execute locally"}
                  </Button>
                )}
                {item.status === "executed" && item.reversible && (
                  <Button
                    variant="outline"
                    onClick={() => transition.mutate({ id: item.proposal_id, action: "undo" })}
                  >
                    <RotateCcw />
                    Undo
                  </Button>
                )}
              </div>
            </div>
          </article>
        ))}
      </div>
    </AppShell>
  );
}

function Diff({ label, value }: { label: string; value: Record<string, unknown> }) {
  return (
    <div className="rounded-xl border bg-muted/30 p-3">
      <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {label}
      </div>
      <pre className="overflow-auto whitespace-pre-wrap text-xs">
        {JSON.stringify(value, null, 2)}
      </pre>
    </div>
  );
}
