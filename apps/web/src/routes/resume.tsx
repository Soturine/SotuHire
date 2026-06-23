import { createFileRoute } from "@tanstack/react-router";
import { useMutation } from "@tanstack/react-query";
import { FileText, Sparkles, Upload } from "lucide-react";
import { useState } from "react";
import { AppShell } from "@/components/app-shell";
import { ProviderBadge } from "@/components/provider-badge";
import { SectionCard } from "@/components/section-card";
import { EmptyState, ErrorState, LoadingState } from "@/components/states";
import { useApi } from "@/lib/api/hooks";
import { toast } from "sonner";
import type { ResumeProfile } from "@/lib/api/types";

export const Route = createFileRoute("/resume")({
  head: () => ({ meta: [{ title: "Currículo — SotuHire" }] }),
  component: ResumePage,
});

const sample = `Pessoa Fictícia — Desenvolvedora Backend Python
Remoto · Brasil

Resumo
Perfil fictício com experiência em APIs, testes e integrações.

Competências
Python, FastAPI, SQL, Pytest, APIs REST, Git

Experiência
Desenvolvedor Backend — Empresa Exemplo Alpha (2022-2026)
- Construiu APIs internas com Python e testes automatizados.
- Participou de revisões de código e monitoramento de erros.
`;

function ResumePage() {
  const api = useApi();
  const [text, setText] = useState("");

  const mut = useMutation({
    mutationFn: (resume_text: string) => api.resumeExtract(resume_text),
    onError: (e: Error) => toast.error(e.message),
    onSuccess: () => toast.success("Currículo extraído"),
  });

  const profile = mut.data?.profile;

  return (
    <AppShell
      title="Currículo"
      description="Cole ou edite o texto do seu currículo. A extração roda local — nada sai da sua máquina."
      actions={
        <>
          <button
            onClick={() => {
              setText(sample);
              setTimeout(() => mut.mutate(sample), 50);
            }}
            className="inline-flex items-center gap-1.5 rounded-md border border-input bg-card px-3 py-1.5 text-xs font-medium hover:bg-muted"
          >
            Rodar demo
          </button>
          <button
            onClick={() => {
              setText("");
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
          title="Texto do currículo"
          description="Suporta texto colado. Arquivos PDF/DOCX em breve."
          actions={
            <button
              onClick={() => setText(sample)}
              className="rounded-md border border-input bg-background px-2.5 py-1 text-xs font-medium hover:bg-muted"
            >
              Usar exemplo
            </button>
          }
        >
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Cole seu currículo aqui…"
            className="h-80 w-full resize-none rounded-lg border border-input bg-background p-3 font-mono text-xs leading-relaxed outline-none transition-colors focus:border-accent/50 focus:ring-2 focus:ring-accent/20"
          />
          <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
            <span>{text.length} caracteres</span>
            <button
              onClick={() => mut.mutate(text)}
              disabled={!text.trim() || mut.isPending}
              className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3.5 py-1.5 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-50"
            >
              <Sparkles className="h-3.5 w-3.5" />
              {mut.isPending ? "Extraindo…" : "Extrair perfil"}
            </button>
          </div>
        </SectionCard>

        <SectionCard
          className="lg:col-span-2"
          title="Perfil extraído"
          description={
            mut.data
              ? `Confiança ${Math.round((mut.data.confidence ?? 0) * 100)}%`
              : "Resultado aparece aqui"
          }
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
            <LoadingState label="Analisando currículo…" />
          ) : mut.isError ? (
            <ErrorState error={mut.error} onRetry={() => mut.mutate(text)} />
          ) : !profile ? (
            <EmptyState
              icon={<FileText className="h-5 w-5" />}
              title="Sem perfil ainda"
              description="Cole um currículo e clique em Extrair perfil. Em modo Demo usamos dados fictícios."
              action={
                <button
                  onClick={() => setText(sample)}
                  className="inline-flex items-center gap-1.5 rounded-md border border-input bg-background px-3 py-1.5 text-xs font-medium hover:bg-muted"
                >
                  <Upload className="h-3.5 w-3.5" /> Carregar exemplo
                </button>
              }
            />
          ) : (
            <ProfileView profile={profile} />
          )}
        </SectionCard>
      </div>
    </AppShell>
  );
}

function ProfileView({ profile }: { profile: ResumeProfile }) {
  return (
    <div className="space-y-5 text-sm">
      <div>
        <div className="text-display text-xl">{profile.name}</div>
        <div className="text-xs text-muted-foreground">
          {profile.headline} · {profile.location}
        </div>
      </div>
      {profile.summary && <p className="text-muted-foreground">{profile.summary}</p>}
      <div>
        <div className="mb-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
          Competências
        </div>
        <div className="flex flex-wrap gap-1.5">
          {profile.skills.map((s) => (
            <span key={s} className="rounded-md bg-muted px-2 py-0.5 text-xs">
              {s}
            </span>
          ))}
        </div>
      </div>
      {profile.experience && profile.experience.length > 0 && (
        <div>
          <div className="mb-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Experiência
          </div>
          <ul className="space-y-3">
            {profile.experience.map((e, i) => (
              <li key={i} className="rounded-lg border border-border bg-muted/30 p-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium">{e.role}</span>
                  <span className="text-xs text-muted-foreground">{e.period}</span>
                </div>
                <div className="text-xs text-muted-foreground">{e.company}</div>
                {e.highlights && (
                  <ul className="mt-2 space-y-1 text-xs text-muted-foreground">
                    {e.highlights.map((h, j) => (
                      <li key={j}>• {h}</li>
                    ))}
                  </ul>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
