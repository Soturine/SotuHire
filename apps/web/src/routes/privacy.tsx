import { createFileRoute } from "@tanstack/react-router";
import { Database, Eye, Globe, Lock, Server, ShieldCheck } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { SectionCard } from "@/components/section-card";

export const Route = createFileRoute("/privacy")({
  head: () => ({ meta: [{ title: "Privacidade — SotuHire" }] }),
  component: PrivacyPage,
});

function PrivacyPage() {
  return (
    <AppShell
      title="Privacidade"
      description="SotuHire é local-first. Esta página explica o que sai (ou não) da sua máquina."
    >
      <div className="grid gap-6 lg:grid-cols-3">
        <SectionCard className="lg:col-span-2" title="Princípios">
          <ul className="space-y-3 text-sm">
            {[
              {
                icon: Server,
                t: "API roda local",
                d: "FastAPI em 127.0.0.1:8787. Não há servidor remoto obrigatório.",
              },
              {
                icon: Database,
                t: "Dados ficam no disco",
                d: "Currículo, vagas e métricas do tracker são persistidos localmente.",
              },
              {
                icon: Lock,
                t: "Sem chaves no cliente",
                d: "Tokens (Gemini, GitHub) ficam no backend. O frontend nunca conhece segredos.",
              },
              {
                icon: Eye,
                t: "Sem rastreio",
                d: "Não enviamos eventos para terceiros. Não há login nem cookies de identidade.",
              },
              {
                icon: ShieldCheck,
                t: "Anti-invenção",
                d: "Sugestões nunca fabricam experiência, certificação ou cargo.",
              },
              {
                icon: Globe,
                t: "Saídas externas são opcionais",
                d: "Análise do GitHub usa a API pública somente quando você pede.",
              },
            ].map((i) => (
              <li key={i.t} className="flex gap-3 rounded-lg border border-border bg-muted/30 p-3">
                <div className="grid h-9 w-9 shrink-0 place-items-center rounded-md bg-card text-accent">
                  <i.icon className="h-4 w-4" />
                </div>
                <div>
                  <div className="font-medium">{i.t}</div>
                  <div className="text-xs text-muted-foreground">{i.d}</div>
                </div>
              </li>
            ))}
          </ul>
        </SectionCard>

        <SectionCard title="O que sai da máquina?">
          <ul className="space-y-2 text-sm">
            <li className="rounded-lg border border-success/30 bg-success/5 p-3">
              <div className="font-medium">Padrão</div>
              <div className="text-xs text-muted-foreground">
                Nada. Toda análise roda em localhost.
              </div>
            </li>
            <li className="rounded-lg border border-warning/30 bg-warning/5 p-3">
              <div className="font-medium">Sob demanda</div>
              <div className="text-xs text-muted-foreground">
                Apenas chamadas explícitas ao GitHub público ou ao provedor IA configurado pelo
                backend.
              </div>
            </li>
            <li className="rounded-lg border border-destructive/30 bg-destructive/5 p-3">
              <div className="font-medium">Nunca</div>
              <div className="text-xs text-muted-foreground">
                Telemetria, analytics ou compartilhamento com terceiros.
              </div>
            </li>
          </ul>
        </SectionCard>
      </div>
    </AppShell>
  );
}
