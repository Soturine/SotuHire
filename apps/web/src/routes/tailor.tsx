import { createFileRoute } from "@tanstack/react-router";
import { useMutation } from "@tanstack/react-query";
import { AlertTriangle, PlayCircle, RotateCcw, ShieldAlert, Sparkles, Wand2 } from "lucide-react";
import { useState } from "react";
import { AppShell } from "@/components/app-shell";
import { ActionableInsights } from "@/components/actionable-insights";
import { AnalysisStateNote, ProviderBadge } from "@/components/provider-badge";
import { SectionCard } from "@/components/section-card";
import { ErrorState, LoadingState } from "@/components/states";
import { useApi } from "@/lib/api/hooks";
import { SAMPLE_EVIDENCE, SAMPLE_JOB } from "@/mocks/samples";
import { toast } from "sonner";

export const Route = createFileRoute("/tailor")({
  head: () => ({ meta: [{ title: "Ajuste de Currículo — SotuHire" }] }),
  component: TailorPage,
});

function TailorPage() {
  const api = useApi();
  const [role, setRole] = useState("Backend Python");
  const [company, setCompany] = useState("Empresa Fictícia");
  const [jobText, setJobText] = useState("");
  const [evidence, setEvidence] = useState("");

  const mut = useMutation({
    mutationFn: () =>
      api.resumeTailor({
        target_role: role,
        target_company: company,
        job_text: jobText,
        evidence_text: evidence,
      }),
    onError: (e: Error) => toast.error(e.message),
  });

  const t = mut.data?.tailor;

  const runDemo = () => {
    setRole("Backend Python");
    setCompany("Fictícia Delta");
    setJobText(SAMPLE_JOB);
    setEvidence(SAMPLE_EVIDENCE);
    setTimeout(() => mut.mutate(), 50);
  };

  return (
    <AppShell
      title="Ajuste de Currículo"
      description="Sugestões seguras para ajustar seu currículo ao alvo — sem inventar nada."
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
              setJobText("");
              setEvidence("");
              mut.reset();
            }}
            className="inline-flex items-center gap-1.5 rounded-md border border-input bg-card px-3 py-1.5 text-xs font-medium hover:bg-muted"
          >
            <RotateCcw className="h-3.5 w-3.5" /> Limpar
          </button>
        </>
      }
    >
      <SectionCard>
        <div className="mb-4 flex items-start gap-3 rounded-lg border border-warning/30 bg-warning/10 p-3 text-sm">
          <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-warning" />
          <div>
            <div className="font-medium">Anti-invenção</div>
            <div className="text-xs text-muted-foreground">
              Todas as sugestões partem da sua evidência. Bullets condicionais aparecem com aviso
              explícito.
            </div>
          </div>
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="Cargo alvo">
            <input value={role} onChange={(e) => setRole(e.target.value)} className="ti" />
          </Field>
          <Field label="Empresa alvo">
            <input value={company} onChange={(e) => setCompany(e.target.value)} className="ti" />
          </Field>
        </div>
        <Field label="Descrição da vaga" className="mt-3">
          <textarea
            value={jobText}
            onChange={(e) => setJobText(e.target.value)}
            className="ti h-28 resize-none font-mono text-xs"
            placeholder="Cole a vaga…"
          />
        </Field>
        <Field label="Evidências (projetos, experiências, links)" className="mt-3">
          <textarea
            value={evidence}
            onChange={(e) => setEvidence(e.target.value)}
            className="ti h-24 resize-none font-mono text-xs"
            placeholder="Liste evidências reais que possam virar bullets…"
          />
        </Field>
        <div className="mt-4 flex justify-end">
          <button
            onClick={() => mut.mutate()}
            disabled={mut.isPending}
            className="inline-flex items-center gap-1.5 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
          >
            <Wand2 className="h-4 w-4" /> {mut.isPending ? "Gerando…" : "Gerar sugestões"}
          </button>
        </div>
      </SectionCard>

      <div className="mt-8">
        {mut.isPending ? (
          <LoadingState label="Gerando bullets seguros…" />
        ) : mut.isError ? (
          <ErrorState error={mut.error} onRetry={() => mut.mutate()} />
        ) : t ? (
          <div className="space-y-6">
            <SectionCard
              title={
                <span className="flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-accent" /> Bullets seguros
                </span>
              }
              description="Baseados na sua evidência. Pode usar à vontade."
              actions={
                mut.data ? (
                  <ProviderBadge
                    provider={mut.data.provider_used}
                    mode={mut.data.analysis_mode}
                    fallback={mut.data.fallback_used}
                  />
                ) : undefined
              }
            >
              <ul className="space-y-2">
                {t.suggested_bullets.map((b, i) => (
                  <li key={i} className="rounded-lg border border-border bg-muted/30 p-3 text-sm">
                    {b}
                  </li>
                ))}
              </ul>
              <AnalysisStateNote
                provider={mut.data?.provider_used}
                mode={mut.data?.analysis_mode}
                fallback={mut.data?.fallback_used}
                model={mut.data?.model_used || mut.data?.model}
                warnings={t.warnings}
                trace={mut.data}
              />
            </SectionCard>

            <div className="grid gap-6 lg:grid-cols-2">
              <SectionCard title="Keywords seguras" description="Confirmadas pela evidência">
                <div className="flex flex-wrap gap-1.5">
                  {t.safe_keywords.map((k) => (
                    <span
                      key={k}
                      className="rounded-md bg-success/15 px-2 py-0.5 text-xs ring-1 ring-success/25"
                    >
                      {k}
                    </span>
                  ))}
                </div>
              </SectionCard>

              <SectionCard title="Sugestões condicionais" description="Use SOMENTE se for verdade">
                {t.conditional_suggestions.length === 0 ? (
                  <p className="text-sm text-muted-foreground">Nenhuma sugestão condicional.</p>
                ) : (
                  <ul className="space-y-2">
                    {t.conditional_suggestions.map((c, i) => (
                      <li
                        key={i}
                        className="rounded-lg border border-warning/30 bg-warning/5 p-3 text-sm"
                      >
                        <div className="text-xs font-medium uppercase tracking-wider text-warning">
                          se: {c.keyword}
                        </div>
                        <p className="mt-1">{c.text}</p>
                      </li>
                    ))}
                  </ul>
                )}
              </SectionCard>
            </div>

            {mut.data?.ai_suggestions && mut.data.ai_suggestions.length > 0 && (
              <SectionCard title="Sugestões adicionais da IA">
                <ul className="space-y-2 text-sm">
                  {mut.data.ai_suggestions.map((item, i) => (
                    <li key={i} className="rounded-md border border-border bg-muted/30 p-3">
                      {item}
                    </li>
                  ))}
                </ul>
              </SectionCard>
            )}

            <ActionableInsights
              title="Assistente de ação para ajuste"
              why={[
                "As sugestões partem da vaga alvo e das evidências informadas pelo usuário.",
                "Bullets condicionais continuam marcados para evitar experiência inventada.",
              ]}
              evidence={t.evidence_used}
              strengths={t.safe_keywords}
              gaps={t.conditional_suggestions.map((item) => item.keyword)}
              improveFirst={[
                "Revisar primeiro os bullets seguros que já têm evidência.",
                "Separar sugestões condicionais e usar somente quando forem verdadeiras.",
              ]}
              suggestions={[...t.suggested_bullets, ...(mut.data?.ai_suggestions ?? [])]}
              risks={t.warnings}
              nextActions={[
                "Revisar cada bullet antes de usar em candidatura real.",
                "Copiar apenas sugestões que representem experiência real.",
                "Salvar a versão final na candidatura correspondente.",
              ]}
              doNotAdd={t.conditional_suggestions.map((item) => item.text)}
              actions={[{ label: "Salvar em candidatura", to: "/tracker", icon: "save" }]}
            />

            {t.warnings.length > 0 && (
              <SectionCard title="Avisos">
                <ul className="space-y-2 text-sm">
                  {t.warnings.map((w, i) => (
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
        ) : null}
      </div>

      <style>{`.ti{display:block;width:100%;border-radius:.5rem;border:1px solid var(--color-input);background:var(--color-background);padding:.5rem .75rem;font-size:.875rem;outline:none}.ti:focus{border-color:color-mix(in oklab,var(--color-accent) 50%,transparent);box-shadow:0 0 0 2px color-mix(in oklab,var(--color-accent) 20%,transparent)}`}</style>
    </AppShell>
  );
}

function Field({
  label,
  children,
  className,
}: {
  label: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <label className={`block ${className ?? ""}`}>
      <span className="mb-1 block text-xs font-medium text-muted-foreground">{label}</span>
      {children}
    </label>
  );
}
