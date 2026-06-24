import { createFileRoute } from "@tanstack/react-router";
import { useMutation } from "@tanstack/react-query";
import { AlertTriangle, CheckCircle2, Github, Lightbulb, PlayCircle } from "lucide-react";
import { useState } from "react";
import { AppShell } from "@/components/app-shell";
import { ActionableInsights } from "@/components/actionable-insights";
import { AnalysisStateNote, ProviderBadge } from "@/components/provider-badge";
import { SectionCard } from "@/components/section-card";
import { ScoreRing } from "@/components/score-ring";
import { ErrorState, LoadingState } from "@/components/states";
import { useApi } from "@/lib/api/hooks";
import { toast } from "sonner";

export const Route = createFileRoute("/github")({
  head: () => ({ meta: [{ title: "Análise de GitHub — SotuHire" }] }),
  component: GhPage,
});

function GhPage() {
  const api = useApi();
  const [url, setUrl] = useState("https://github.com/example/fictitious-api-lab");
  const [role, setRole] = useState("Backend Python");

  const mut = useMutation({
    mutationFn: () => api.githubAnalyze({ repo_url: url, target_role: role }),
    onError: (e: Error) => toast.error(e.message),
  });

  const r = mut.data?.report;

  const runDemo = () => {
    setUrl("https://github.com/example/fictitious-api-lab");
    setRole("Backend Python");
    setTimeout(() => mut.mutate(), 50);
  };

  return (
    <AppShell
      title="Análise de GitHub"
      description="Use seu repositório público como evidência técnica."
      actions={
        <button
          onClick={runDemo}
          className="inline-flex items-center gap-1.5 rounded-md border border-input bg-card px-3 py-1.5 text-xs font-medium hover:bg-muted"
        >
          <PlayCircle className="h-3.5 w-3.5" /> Rodar demo
        </button>
      }
    >
      <SectionCard>
        <div className="grid gap-3 sm:grid-cols-[2fr_1fr_auto]">
          <input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://github.com/usuario/repo"
            className="rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:border-accent/50 focus:ring-2 focus:ring-accent/20"
          />
          <input
            value={role}
            onChange={(e) => setRole(e.target.value)}
            placeholder="Cargo alvo"
            className="rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:border-accent/50 focus:ring-2 focus:ring-accent/20"
          />
          <button
            onClick={() => mut.mutate()}
            disabled={mut.isPending || !url}
            className="inline-flex items-center justify-center gap-1.5 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
          >
            <Github className="h-4 w-4" /> {mut.isPending ? "Analisando…" : "Analisar"}
          </button>
        </div>
      </SectionCard>

      <div className="mt-8">
        {mut.isPending ? (
          <LoadingState />
        ) : mut.isError ? (
          <ErrorState error={mut.error} onRetry={() => mut.mutate()} />
        ) : r ? (
          <div className="space-y-6">
            <SectionCard
              title={
                <span className="font-mono text-sm">
                  {r.repo.owner}/<span className="text-foreground">{r.repo.name}</span>
                </span>
              }
              description={r.repo.url}
              actions={
                <div className="flex items-center gap-2">
                  <ProviderBadge
                    provider={mut.data?.provider_used}
                    mode={mut.data?.analysis_mode}
                    fallback={mut.data?.fallback_used}
                  />
                  <a
                    href={r.repo.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-xs font-medium text-accent hover:underline"
                  >
                    Abrir no GitHub →
                  </a>
                </div>
              }
            >
              <div className="grid gap-6 sm:grid-cols-[auto_1fr] sm:items-center">
                <div className="flex gap-6">
                  <ScoreRing
                    value={r.quality_score}
                    label="Qualidade"
                    size={104}
                    tone="primary"
                    sub="QUAL."
                  />
                  <ScoreRing
                    value={r.evidence_score}
                    label="Evidência"
                    size={104}
                    tone="accent"
                    sub="EVID."
                  />
                </div>
                <div>
                  <div className="mb-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    Stack detectada
                  </div>
                  <div className="space-y-2">
                    {r.languages.map((l) => (
                      <div key={l.name}>
                        <div className="flex justify-between text-xs">
                          <span className="font-medium">{l.name}</span>
                          <span className="tabular-nums text-muted-foreground">{l.percent}%</span>
                        </div>
                        <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-muted">
                          <div className="h-full bg-accent" style={{ width: `${l.percent}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              <AnalysisStateNote
                provider={mut.data?.provider_used}
                mode={mut.data?.analysis_mode}
                fallback={mut.data?.fallback_used}
              />
            </SectionCard>

            <div className="grid gap-6 lg:grid-cols-2">
              <SectionCard title="Evidências técnicas (positivas)">
                <ul className="space-y-2 text-sm">
                  {r.positive_signals.map((s, i) => (
                    <li
                      key={i}
                      className="flex gap-2 rounded-md border border-success/30 bg-success/5 p-3"
                    >
                      <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-success" />
                      {s}
                    </li>
                  ))}
                </ul>
              </SectionCard>
              <SectionCard title="Riscos / Inconsistências">
                {r.risks.length === 0 ? (
                  <p className="text-sm text-muted-foreground">Nenhum risco detectado.</p>
                ) : (
                  <ul className="space-y-2 text-sm">
                    {r.risks.map((s, i) => (
                      <li
                        key={i}
                        className="flex gap-2 rounded-md border border-warning/30 bg-warning/5 p-3"
                      >
                        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-warning" />
                        {s}
                      </li>
                    ))}
                  </ul>
                )}
              </SectionCard>
            </div>

            <SectionCard
              title={
                <span className="flex items-center gap-2">
                  <Lightbulb className="h-4 w-4 text-accent" /> Recomendações para portfólio
                </span>
              }
            >
              <ul className="space-y-2 text-sm">
                {r.portfolio_suggestions.map((s, i) => (
                  <li key={i} className="rounded-md border border-border bg-muted/30 p-3">
                    {s}
                  </li>
                ))}
              </ul>
            </SectionCard>

            <ActionableInsights
              title="Assistente de ação para GitHub"
              why={[
                "A recomendação usa sinais técnicos visíveis no repositório e riscos de inconsistência com o currículo.",
                "Use o repositório como evidência apenas quando ele sustentar requisito real da vaga.",
              ]}
              evidence={r.positive_signals}
              strengths={r.positive_signals}
              gaps={r.portfolio_suggestions}
              improveFirst={r.portfolio_suggestions.slice(0, 3)}
              suggestions={r.portfolio_suggestions}
              risks={r.risks}
              nextActions={[
                "Atualizar README com contexto verificável do projeto.",
                "Usar evidências do repositório apenas quando conectarem com a vaga.",
                "Salvar candidatura se o portfólio reforçar os requisitos principais.",
              ]}
              doNotAdd={r.risks}
              actions={[{ label: "Salvar em candidatura", to: "/tracker", icon: "save" }]}
            />
          </div>
        ) : null}
      </div>
    </AppShell>
  );
}
