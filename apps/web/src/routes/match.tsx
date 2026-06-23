import { createFileRoute } from "@tanstack/react-router";
import { useMutation } from "@tanstack/react-query";
import {
  AlertTriangle,
  CheckCircle2,
  MinusCircle,
  PlayCircle,
  RotateCcw,
  Sparkles,
  ShieldAlert,
  XCircle,
} from "lucide-react";
import { useState } from "react";
import { AppShell } from "@/components/app-shell";
import { ProviderBadge } from "@/components/provider-badge";
import { SectionCard } from "@/components/section-card";
import { ScoreRing } from "@/components/score-ring";
import { ErrorState, LoadingState } from "@/components/states";
import { useApi } from "@/lib/api/hooks";
import type { MatchAnalysis, MatchAnalyzeResult, MatchRequirement } from "@/lib/api/types";
import { SAMPLE_JOB, SAMPLE_RESUME } from "@/mocks/samples";
import { toast } from "sonner";

export const Route = createFileRoute("/match")({
  head: () => ({ meta: [{ title: "Análise de Compatibilidade — SotuHire" }] }),
  component: MatchPage,
});

function MatchPage() {
  const api = useApi();
  const [resume, setResume] = useState("");
  const [job, setJob] = useState("");

  const mut = useMutation({
    mutationFn: () => api.matchAnalyze({ resume_text: resume, job_text: job }),
    onError: (e: Error) => toast.error(e.message),
  });

  const a = mut.data?.analysis;

  const runDemo = () => {
    setResume(SAMPLE_RESUME);
    setJob(SAMPLE_JOB);
    setTimeout(() => mut.mutate(), 50);
  };

  return (
    <AppShell
      title="Análise de Compatibilidade"
      description="Compare currículo e vaga com base em requisitos, evidências, ATS, aderência e riscos."
      actions={
        <>
          <button
            onClick={runDemo}
            className="inline-flex items-center gap-1.5 rounded-md border border-input bg-card px-3 py-1.5 text-xs font-medium hover:bg-muted"
          >
            <PlayCircle className="h-3.5 w-3.5" /> Rodar demo
          </button>
          <button
            onClick={() => {
              setResume("");
              setJob("");
              mut.reset();
            }}
            className="inline-flex items-center gap-1.5 rounded-md border border-input bg-card px-3 py-1.5 text-xs font-medium hover:bg-muted"
          >
            <RotateCcw className="h-3.5 w-3.5" /> Limpar
          </button>
        </>
      }
    >
      <div className="grid gap-6 lg:grid-cols-2">
        <SectionCard
          title="Currículo"
          description="Texto bruto para análise"
          actions={
            <button
              onClick={() => setResume(SAMPLE_RESUME)}
              className="rounded-md border border-input bg-background px-2.5 py-1 text-[11px] font-medium hover:bg-muted"
            >
              Usar exemplo
            </button>
          }
        >
          <textarea
            value={resume}
            onChange={(e) => setResume(e.target.value)}
            placeholder="Cole seu currículo…"
            className="h-44 w-full resize-none rounded-lg border border-input bg-background p-3 font-mono text-xs outline-none focus:border-accent/50 focus:ring-2 focus:ring-accent/20"
          />
        </SectionCard>
        <SectionCard
          title="Vaga"
          description="Descrição completa"
          actions={
            <button
              onClick={() => setJob(SAMPLE_JOB)}
              className="rounded-md border border-input bg-background px-2.5 py-1 text-[11px] font-medium hover:bg-muted"
            >
              Usar exemplo
            </button>
          }
        >
          <textarea
            value={job}
            onChange={(e) => setJob(e.target.value)}
            placeholder="Cole a descrição da vaga…"
            className="h-44 w-full resize-none rounded-lg border border-input bg-background p-3 font-mono text-xs outline-none focus:border-accent/50 focus:ring-2 focus:ring-accent/20"
          />
        </SectionCard>
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
        <p className="text-xs text-muted-foreground">
          Dica: clique em <strong>Rodar demo</strong> para ver o resultado completo sem digitar
          nada.
        </p>
        <button
          onClick={() => mut.mutate()}
          disabled={mut.isPending || !resume.trim() || !job.trim()}
          className="inline-flex items-center gap-1.5 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:opacity-90 disabled:opacity-50"
        >
          <Sparkles className="h-4 w-4" />
          {mut.isPending ? "Analisando…" : "Analisar compatibilidade"}
        </button>
      </div>

      <div className="mt-8">
        {mut.isPending ? (
          <LoadingState label="Calculando pontuação de compatibilidade…" />
        ) : mut.isError ? (
          <ErrorState error={mut.error} onRetry={() => mut.mutate()} />
        ) : a ? (
          <MatchResult a={a} meta={mut.data} />
        ) : (
          <SectionCard>
            <div className="grid gap-4 sm:grid-cols-3">
              {[
                { t: "Pontuação de compatibilidade", d: "Score 0–100 com confiança e evidência." },
                { t: "Alinhamento ATS", d: "Keywords presentes, ausentes e adicionáveis." },
                { t: "Gaps explícitos", d: "Onde aplicar com cuidado ou priorizar estudo." },
              ].map((p) => (
                <div key={p.t} className="rounded-lg border border-border bg-muted/30 p-4">
                  <div className="text-sm font-semibold">{p.t}</div>
                  <p className="mt-1 text-xs text-muted-foreground">{p.d}</p>
                </div>
              ))}
            </div>
            <p className="mt-4 text-center text-sm text-muted-foreground">
              Preencha currículo e vaga ou rode uma demo para ver a análise completa.
            </p>
          </SectionCard>
        )}
      </div>
    </AppShell>
  );
}

function MatchResult({ a, meta }: { a: MatchAnalysis; meta?: MatchAnalyzeResult }) {
  return (
    <div className="space-y-6">
      {/* Score grid */}
      <SectionCard
        title="Pontuações"
        description="Visão consolidada da análise"
        actions={
          meta ? (
            <ProviderBadge
              provider={meta.provider_used}
              mode={meta.analysis_mode}
              fallback={meta.fallback_used}
              model={meta.model}
            />
          ) : undefined
        }
      >
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
          <ScoreRing
            value={a.match_score}
            label="Pontuação de compatibilidade"
            tone="primary"
            sub="COMPAT."
          />
          <ScoreRing
            value={Math.round(a.confidence_score * 100)}
            label="Confiança"
            tone="accent"
            sub="CONF."
          />
          <ScoreRing value={a.ats_score} label="Alinhamento ATS" tone="accent" sub="ATS" />
          <ScoreRing
            value={a.opportunity_fit_score}
            label="Aderência à vaga"
            tone="accent"
            sub="ADER."
          />
          <ScoreRing value={a.risk_score} label="Risco" tone="warning" sub="RISCO" />
        </div>
        {a.recommendation && (
          <div className="mt-5 flex items-start gap-3 rounded-lg border border-accent/30 bg-accent/10 p-4">
            <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
            <div className="text-sm">
              <div className="font-medium">Recomendação: {translate(a.recommendation)}</div>
              <div className="text-xs text-muted-foreground">
                Decisão baseada em evidências do currículo + vaga. Aplicar com calma e ajustes
                seguros.
              </div>
            </div>
          </div>
        )}
      </SectionCard>

      <div className="grid gap-6 lg:grid-cols-3">
        <RequirementsList
          title="Requisitos atendidos"
          icon={<CheckCircle2 className="h-4 w-4 text-success" />}
          items={a.matched_requirements}
          tone="success"
          showEvidence
        />
        <RequirementsList
          title="Requisitos parciais"
          icon={<MinusCircle className="h-4 w-4 text-warning" />}
          items={a.partial_requirements}
          tone="warning"
        />
        <RequirementsList
          title="Requisitos ausentes"
          icon={<XCircle className="h-4 w-4 text-destructive" />}
          items={a.missing_requirements}
          tone="destructive"
        />
      </div>

      {a.critical_gaps.length > 0 && (
        <SectionCard title="Gaps críticos">
          <ul className="space-y-2">
            {a.critical_gaps.map((g) => (
              <li
                key={g.name}
                className="flex items-start gap-2 rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm"
              >
                <AlertTriangle className="mt-0.5 h-4 w-4 text-destructive" />
                <div>
                  <div className="font-medium">{g.name}</div>
                  {g.reason && <div className="text-xs text-muted-foreground">{g.reason}</div>}
                </div>
              </li>
            ))}
          </ul>
        </SectionCard>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <SectionCard title="Ações seguras" description="Sem inventar experiência ou credencial">
          <ul className="space-y-2 text-sm">
            {a.safe_actions.map((s, i) => (
              <li key={i} className="flex gap-2 rounded-md border border-border bg-muted/40 p-3">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
                <span>{s}</span>
              </li>
            ))}
          </ul>
        </SectionCard>

        <SectionCard title="Competências transferíveis">
          {a.transferable_skills && a.transferable_skills.length > 0 ? (
            <ul className="space-y-2 text-sm">
              {a.transferable_skills.map((s, i) => (
                <li
                  key={i}
                  className="rounded-md border border-border bg-muted/40 p-3 text-muted-foreground"
                >
                  {s}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">
              Nenhuma competência transferível identificada.
            </p>
          )}
        </SectionCard>
      </div>
    </div>
  );
}

function RequirementsList({
  title,
  icon,
  items,
  tone,
  showEvidence,
}: {
  title: string;
  icon: React.ReactNode;
  items: MatchRequirement[];
  tone: "success" | "warning" | "destructive";
  showEvidence?: boolean;
}) {
  const border = {
    success: "border-success/30",
    warning: "border-warning/30",
    destructive: "border-destructive/30",
  }[tone];
  return (
    <SectionCard
      title={
        <span className="flex items-center gap-2">
          {icon} {title}{" "}
          <span className="text-xs font-normal text-muted-foreground">({items.length})</span>
        </span>
      }
    >
      {items.length === 0 ? (
        <p className="text-sm text-muted-foreground">Nada por aqui.</p>
      ) : (
        <ul className="space-y-2">
          {items.map((r) => (
            <li key={r.name} className={`rounded-lg border ${border} bg-card p-3 text-sm`}>
              <div className="flex items-center justify-between">
                <span className="font-medium">{r.name}</span>
                {r.category && (
                  <span className="text-[10px] uppercase tracking-wider text-muted-foreground">
                    {r.category.replace("_", " ")}
                  </span>
                )}
              </div>
              {r.reason && <p className="mt-1 text-xs text-muted-foreground">{r.reason}</p>}
              {showEvidence && r.evidence && (
                <ul className="mt-2 space-y-1 text-xs text-muted-foreground">
                  {r.evidence.map((e, i) => (
                    <li key={i}>· {e}</li>
                  ))}
                </ul>
              )}
            </li>
          ))}
        </ul>
      )}
    </SectionCard>
  );
}

function translate(r: string) {
  const map: Record<string, string> = {
    apply: "Aplicar",
    apply_with_adjustments: "Aplicar com ajustes",
    needs_more_evidence: "Precisa mais evidência",
    do_not_apply: "Não aplicar",
  };
  return map[r] ?? r;
}
