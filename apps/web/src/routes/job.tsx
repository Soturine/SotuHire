import { createFileRoute } from "@tanstack/react-router";
import { useMutation } from "@tanstack/react-query";
import { Briefcase, Sparkles } from "lucide-react";
import { useState } from "react";
import { AppShell } from "@/components/app-shell";
import { ProviderBadge } from "@/components/provider-badge";
import { SectionCard } from "@/components/section-card";
import { EmptyState, ErrorState, LoadingState } from "@/components/states";
import { useApi } from "@/lib/api/hooks";
import { toast } from "sonner";

export const Route = createFileRoute("/job")({
  head: () => ({ meta: [{ title: "Vaga — SotuHire" }] }),
  component: JobPage,
});

const sample = `Cargo: Desenvolvedor Backend Python
Empresa: Fictícia Delta
Modalidade: Remoto · Pleno

Responsabilidades
- Desenvolver e manter APIs REST
- Escrever testes automatizados
- Apoiar observabilidade e monitoramento

Requisitos
Python, FastAPI, SQL, Pytest, APIs REST

Diferenciais
Docker, Cloud (AWS/GCP), CI/CD
`;

function JobPage() {
  const api = useApi();
  const [text, setText] = useState("");
  const [url, setUrl] = useState("");

  const mut = useMutation({
    mutationFn: () => api.jobExtract(text, url || undefined),
    onError: (e: Error) => toast.error(e.message),
    onSuccess: () => toast.success("Vaga extraída"),
  });

  const job = mut.data?.job;

  return (
    <AppShell
      title="Vaga"
      description="Cole a descrição da vaga para extrair requisitos, keywords ATS e contexto."
      actions={
        <>
          <button
            onClick={() => {
              setText(sample);
              setUrl("https://example.invalid/jobs/backend");
              setTimeout(() => mut.mutate(), 50);
            }}
            className="inline-flex items-center gap-1.5 rounded-md border border-input bg-card px-3 py-1.5 text-xs font-medium hover:bg-muted"
          >
            Rodar demo
          </button>
          <button
            onClick={() => {
              setText("");
              setUrl("");
              mut.reset();
            }}
            className="inline-flex items-center gap-1.5 rounded-md border border-input bg-card px-3 py-1.5 text-xs font-medium hover:bg-muted"
          >
            Limpar
          </button>
        </>
      }
    >
      <div className="grid gap-6 lg:grid-cols-5">
        <SectionCard
          className="lg:col-span-3"
          title="Descrição da vaga"
          actions={
            <button
              onClick={() => {
                setText(sample);
                setUrl("https://example.invalid/jobs/backend");
              }}
              className="rounded-md border border-input bg-background px-2.5 py-1 text-xs font-medium hover:bg-muted"
            >
              Usar exemplo
            </button>
          }
        >
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://… (opcional)"
            className="mb-3 w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm outline-none focus:border-accent/50 focus:ring-2 focus:ring-accent/20"
          />
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Cole a descrição da vaga…"
            className="h-72 w-full resize-none rounded-lg border border-input bg-background p-3 font-mono text-xs leading-relaxed outline-none focus:border-accent/50 focus:ring-2 focus:ring-accent/20"
          />
          <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
            <span>{text.length} caracteres</span>
            <button
              onClick={() => mut.mutate()}
              disabled={!text.trim() || mut.isPending}
              className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3.5 py-1.5 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
            >
              <Sparkles className="h-3.5 w-3.5" />
              {mut.isPending ? "Extraindo…" : "Extrair vaga"}
            </button>
          </div>
        </SectionCard>

        <SectionCard
          className="lg:col-span-2"
          title="Vaga estruturada"
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
          {mut.isPending ? (
            <LoadingState />
          ) : mut.isError ? (
            <ErrorState error={mut.error} onRetry={() => mut.mutate()} />
          ) : !job ? (
            <EmptyState
              icon={<Briefcase className="h-5 w-5" />}
              title="Sem vaga ainda"
              description="Cole uma descrição e clique em Extrair vaga."
            />
          ) : (
            <div className="space-y-4 text-sm">
              <div>
                <div className="text-display text-xl">{job.title}</div>
                <div className="text-xs text-muted-foreground">
                  {job.company} · {job.modality} · {job.seniority}
                </div>
              </div>
              <SkillBlock title="Obrigatórios" items={job.required_skills} tone="primary" />
              <SkillBlock
                title="Diferenciais"
                items={job.preferred_skills ?? job.desired_skills ?? []}
                tone="muted"
              />
              {job.responsibilities && (
                <div>
                  <div className="mb-1.5 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    Responsabilidades
                  </div>
                  <ul className="space-y-1 text-xs text-muted-foreground">
                    {job.responsibilities.map((r, i) => (
                      <li key={i}>• {r}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </SectionCard>
      </div>
    </AppShell>
  );
}

function SkillBlock({
  title,
  items,
  tone,
}: {
  title: string;
  items: string[];
  tone: "primary" | "muted";
}) {
  if (!items.length) return null;
  return (
    <div>
      <div className="mb-1.5 text-xs font-medium uppercase tracking-wider text-muted-foreground">
        {title}
      </div>
      <div className="flex flex-wrap gap-1.5">
        {items.map((s) => (
          <span
            key={s}
            className={`rounded-md px-2 py-0.5 text-xs ${
              tone === "primary"
                ? "bg-accent/15 text-accent-foreground ring-1 ring-accent/25"
                : "bg-muted text-muted-foreground"
            }`}
          >
            {s}
          </span>
        ))}
      </div>
    </div>
  );
}
