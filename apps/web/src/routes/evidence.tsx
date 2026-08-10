import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, GitMerge, Inbox, Search, X } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { v2Api, type EvidenceNode } from "@/features/career-copilot/api";
import { useApiMode } from "@/lib/api/mode";
import { usePreferences } from "@/lib/preferences";

export const Route = createFileRoute("/evidence")({ component: EvidenceInbox });

function EvidenceInbox() {
  const { mode, baseUrl } = useApiMode();
  const { locale } = usePreferences();
  const queryClient = useQueryClient();
  const evidence = useQuery({
    queryKey: ["v2", "evidence", mode, baseUrl],
    queryFn: () => v2Api(mode, baseUrl).evidence(),
  });
  const review = useMutation({
    mutationFn: ({ id, status }: { id: string; status: EvidenceNode["review_status"] }) =>
      v2Api(mode, baseUrl).reviewEvidence(id, status),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["v2", "evidence", mode, baseUrl] }),
  });
  const pt = locale === "pt-BR";
  const groups = ["candidate", "confirmed", "stale", "rejected"] as const;
  return (
    <AppShell
      title={pt ? "Caixa de evidências" : "Evidence inbox"}
      description={
        pt
          ? "Confirme fatos, rejeite inferências e preserve a origem."
          : "Confirm facts, reject inferences, and preserve provenance."
      }
    >
      <div className="mx-auto max-w-7xl space-y-6">
        <div className="rounded-2xl border bg-card p-5">
          <div className="flex items-center gap-3">
            <Search className="h-5 w-5 text-accent" />
            <div>
              <h2 className="font-semibold">
                {pt ? "Por que isto está aqui?" : "Why is this here?"}
              </h2>
              <p className="text-sm text-muted-foreground">
                {pt
                  ? "Cada item mostra fonte, confiança separada e estado de revisão. Nenhuma extração entra como fato."
                  : "Every item shows source, separate confidence, and review status. Extraction never becomes fact automatically."}
              </p>
            </div>
          </div>
        </div>
        <div className="grid gap-5 xl:grid-cols-4">
          {groups.map((group) => (
            <section
              key={group}
              className="min-w-0 rounded-2xl border bg-muted/30 p-3"
              aria-labelledby={`evidence-${group}`}
            >
              <div className="mb-3 flex items-center justify-between px-1">
                <h2 id={`evidence-${group}`} className="font-semibold capitalize">
                  {group}
                </h2>
                <span className="rounded-full bg-background px-2 py-0.5 text-xs">
                  {evidence.data?.filter((item) => item.review_status === group).length ?? 0}
                </span>
              </div>
              <div className="space-y-3">
                {evidence.data
                  ?.filter((item) => item.review_status === group)
                  .map((item) => (
                    <article
                      key={item.node_id}
                      className="rounded-xl border bg-card p-4 shadow-[var(--shadow-soft)]"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <Inbox className="mt-0.5 h-4 w-4 text-accent" />
                        <span className="text-[11px] uppercase text-muted-foreground">
                          {item.node_type}
                        </span>
                      </div>
                      <h3 className="mt-3 font-semibold">{item.title}</h3>
                      <p className="mt-1 line-clamp-3 text-xs text-muted-foreground">
                        {item.summary || (pt ? "Sem resumo confirmado." : "No confirmed summary.")}
                      </p>
                      <div className="mt-3 text-[11px] text-muted-foreground">
                        {Math.round(item.confidence * 100)}% rule confidence · {item.source_refs[0]}
                      </div>
                      {group === "candidate" && (
                        <div className="mt-4 grid grid-cols-2 gap-2">
                          <Button
                            size="sm"
                            onClick={() => review.mutate({ id: item.node_id, status: "confirmed" })}
                          >
                            <Check />
                            {pt ? "Confirmar" : "Confirm"}
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => review.mutate({ id: item.node_id, status: "rejected" })}
                          >
                            <X />
                            {pt ? "Rejeitar" : "Reject"}
                          </Button>
                        </div>
                      )}
                      {group === "confirmed" && (
                        <Button className="mt-4 w-full" size="sm" variant="ghost" disabled>
                          <GitMerge />
                          {pt ? "Relações explicáveis" : "Explainable links"}
                        </Button>
                      )}
                    </article>
                  ))}
              </div>
            </section>
          ))}
        </div>
      </div>
    </AppShell>
  );
}
