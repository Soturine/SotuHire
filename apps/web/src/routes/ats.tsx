import { createFileRoute } from "@tanstack/react-router";
import { useMutation } from "@tanstack/react-query";
import {
  AlertTriangle,
  CheckCircle2,
  MinusCircle,
  PlayCircle,
  RotateCcw,
  ScanSearch,
  XCircle,
} from "lucide-react";
import { useState } from "react";
import { AppShell } from "@/components/app-shell";
import { ActionableInsights } from "@/components/actionable-insights";
import { AnalysisStateNote, ProviderBadge } from "@/components/provider-badge";
import { SectionCard } from "@/components/section-card";
import { ScoreRing } from "@/components/score-ring";
import { ErrorState, LoadingState } from "@/components/states";
import { useApi } from "@/lib/api/hooks";
import { SAMPLE_JOB, SAMPLE_RESUME } from "@/mocks/samples";
import { toast } from "sonner";

export const Route = createFileRoute("/ats")({
  head: () => ({ meta: [{ title: "Análise ATS — SotuHire" }] }),
  component: AtsPage,
});

function AtsPage() {
  const api = useApi();
  const [resume, setResume] = useState("");
  const [job, setJob] = useState("");

  const mut = useMutation({
    mutationFn: () => api.atsAnalyze({ resume_text: resume, job_text: job }),
    onError: (e: Error) => toast.error(e.message),
  });

  const r = mut.data;

  const runDemo = () => {
    setResume(SAMPLE_RESUME);
    setJob(SAMPLE_JOB);
    setTimeout(() => mut.mutate(), 50);
  };

  return (
    <AppShell
      title="Análise ATS"
      description="Veja quais keywords ATS estão presentes, ausentes ou sem evidência."
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
            className="h-40 w-full resize-none rounded-lg border border-input bg-background p-3 font-mono text-xs outline-none focus:border-accent/50 focus:ring-2 focus:ring-accent/20"
          />
        </SectionCard>
        <SectionCard
          title="Vaga"
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
            className="h-40 w-full resize-none rounded-lg border border-input bg-background p-3 font-mono text-xs outline-none focus:border-accent/50 focus:ring-2 focus:ring-accent/20"
          />
        </SectionCard>
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
        <p className="text-xs text-muted-foreground">
          A Análise ATS compara seu currículo com as keywords da vaga. Sem invenção: só sinaliza o
          que está ali.
        </p>
        <button
          onClick={() => mut.mutate()}
          disabled={mut.isPending || !resume.trim() || !job.trim()}
          className="inline-flex items-center gap-1.5 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:opacity-90 disabled:opacity-50"
        >
          <ScanSearch className="h-4 w-4" /> {mut.isPending ? "Analisando…" : "Analisar ATS"}
        </button>
      </div>

      <div className="mt-8">
        {mut.isPending ? (
          <LoadingState />
        ) : mut.isError ? (
          <ErrorState error={mut.error} onRetry={() => mut.mutate()} />
        ) : r ? (
          <div className="space-y-6">
            <SectionCard
              title="Pontuação ATS"
              actions={
                r ? (
                  <ProviderBadge
                    provider={r.provider_used}
                    mode={r.analysis_mode}
                    fallback={r.fallback_used}
                  />
                ) : undefined
              }
            >
              <div className="flex flex-col items-center gap-4 sm:flex-row sm:items-center sm:justify-between">
                <ScoreRing
                  value={r.ats_score}
                  label="Pontuação ATS"
                  size={120}
                  tone="accent"
                  sub="ATS"
                />
                <div className="grid flex-1 grid-cols-3 gap-3 text-center">
                  <Stat label="Presentes" value={r.present.length} tone="success" />
                  <Stat
                    label="Adicionáveis"
                    value={r.missing_but_safe_to_add_if_true.length}
                    tone="warning"
                  />
                  <Stat
                    label="Sem evidência"
                    value={r.missing_without_evidence.length}
                    tone="destructive"
                  />
                </div>
              </div>
              <AnalysisStateNote
                provider={r.provider_used}
                mode={r.analysis_mode}
                fallback={r.fallback_used}
                warnings={r.warnings}
              />
            </SectionCard>

            <div className="grid gap-6 lg:grid-cols-3">
              <KeywordBlock
                title="Presentes"
                icon={<CheckCircle2 className="h-4 w-4 text-success" />}
                items={r.present}
                tone="success"
              />
              <KeywordBlock
                title="Adicionáveis (se verdadeiras)"
                icon={<MinusCircle className="h-4 w-4 text-warning" />}
                items={r.missing_but_safe_to_add_if_true}
                tone="warning"
              />
              <KeywordBlock
                title="Sem evidência"
                icon={<XCircle className="h-4 w-4 text-destructive" />}
                items={r.missing_without_evidence}
                tone="destructive"
              />
            </div>

            {r.ai_insights && r.ai_insights.length > 0 && (
              <SectionCard title="Insights da IA">
                <ul className="space-y-2 text-sm">
                  {r.ai_insights.map((item, i) => (
                    <li key={i} className="rounded-md border border-border bg-muted/30 p-3">
                      {item}
                    </li>
                  ))}
                </ul>
              </SectionCard>
            )}

            <ActionableInsights
              title="Assistente de ação ATS"
              why={[
                "A recomendação cruza keywords presentes, adicionáveis com evidência e itens sem evidência.",
                "ATS/Tailor reforçam integridade: não adicione se não for verdade.",
              ]}
              evidence={r.present.slice(0, 8)}
              strengths={r.present.slice(0, 6)}
              gaps={r.missing_but_safe_to_add_if_true}
              improveFirst={r.missing_but_safe_to_add_if_true
                .slice(0, 3)
                .map((item) => `Confirmar evidência real para ${item} antes de editar.`)}
              suggestions={[
                ...r.missing_but_safe_to_add_if_true.map(
                  (item) => `Adicionar ${item} somente se houver evidência real no currículo.`,
                ),
                ...(r.ai_insights ?? []),
              ]}
              risks={r.warnings ?? []}
              nextActions={[
                "Copiar keywords seguras para revisar manualmente.",
                "Enviar itens com evidência para Ajuste de Currículo.",
                "Manter lacunas sem evidência fora da candidatura.",
              ]}
              doNotAdd={r.missing_without_evidence}
              actions={[{ label: "Enviar para ajustes", to: "/tailor", icon: "send" }]}
            />

            {r.warnings && r.warnings.length > 0 && (
              <SectionCard title="Avisos de integridade">
                <ul className="space-y-2 text-sm">
                  {r.warnings.map((w, i) => (
                    <li
                      key={i}
                      className="flex gap-2 rounded-md border border-warning/30 bg-warning/10 p-3"
                    >
                      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-warning" />
                      <span>{w}</span>
                    </li>
                  ))}
                </ul>
              </SectionCard>
            )}
          </div>
        ) : (
          <SectionCard>
            <p className="text-center text-sm text-muted-foreground">
              Cole currículo e vaga e clique em Analisar ATS.
            </p>
          </SectionCard>
        )}
      </div>
    </AppShell>
  );
}

function KeywordBlock({
  title,
  icon,
  items,
  tone,
}: {
  title: string;
  icon: React.ReactNode;
  items: string[];
  tone: "success" | "warning" | "destructive";
}) {
  const bg = {
    success: "bg-success/10 text-success-foreground ring-success/20",
    warning: "bg-warning/10 ring-warning/20",
    destructive: "bg-destructive/10 ring-destructive/20",
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
        <p className="text-sm text-muted-foreground">Nenhum.</p>
      ) : (
        <div className="flex flex-wrap gap-1.5">
          {items.map((k) => (
            <span key={k} className={`rounded-md px-2 py-1 text-xs ring-1 ${bg}`}>
              {k}
            </span>
          ))}
        </div>
      )}
    </SectionCard>
  );
}

function Stat({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: "success" | "warning" | "destructive";
}) {
  const cls = { success: "text-success", warning: "text-warning", destructive: "text-destructive" }[
    tone
  ];
  return (
    <div className="rounded-lg border border-border bg-muted/30 px-3 py-3">
      <div className={`text-display text-2xl tabular-nums ${cls}`}>{value}</div>
      <div className="text-[11px] uppercase tracking-wider text-muted-foreground">{label}</div>
    </div>
  );
}
