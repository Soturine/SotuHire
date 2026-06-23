import { createFileRoute, Link } from "@tanstack/react-router";
import {
  ArrowRight,
  ShieldCheck,
  Sparkles,
  Target,
  ScanSearch,
  Github,
  Kanban,
  LineChart,
  Wand2,
  CheckCircle2,
  Lock,
} from "lucide-react";
import { ApiModeBadge } from "@/components/api-mode-badge";
import { GuidedFlow } from "@/components/guided-flow";
import { API_LOCAL_HOST, APP_VERSION } from "@/lib/labels";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "SotuHire — Inteligência de carreira local-first" },
      {
        name: "description",
        content:
          "Analise currículo, vaga, ATS e GitHub com inteligência local-first. Sem enviar seus dados para terceiros.",
      },
    ],
  }),
  component: Landing,
});

const features = [
  {
    icon: Target,
    title: "Análise de Compatibilidade",
    desc: "Pontuação baseada em evidências, com confiança, gaps explicáveis e nada de caixa-preta.",
  },
  {
    icon: ScanSearch,
    title: "Análise ATS",
    desc: "Keywords presentes, ausentes e sem evidência. Sugestões seguras, sem invenção.",
  },
  {
    icon: Wand2,
    title: "Ajuste de Currículo",
    desc: "Bullets ajustados ao alvo, com alerta anti-fabricação e antes/depois transparente.",
  },
  {
    icon: Github,
    title: "Análise de GitHub",
    desc: "Stack detectada, score técnico e evidências reais a partir do seu portfólio.",
  },
  {
    icon: Kanban,
    title: "Candidaturas",
    desc: "Pipeline completo com 11 estágios e métricas de conversão.",
  },
  {
    icon: LineChart,
    title: "Inteligência de Candidaturas",
    desc: "Requisitos pedidos, gaps recorrentes, funil e ranking — para decidir melhor.",
  },
];

function Landing() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-40 border-b border-border/60 bg-background/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3.5">
          <Link to="/" className="flex items-center gap-2">
            <div className="grid h-8 w-8 place-items-center rounded-lg bg-primary text-primary-foreground">
              <Sparkles className="h-4 w-4" />
            </div>
            <span className="text-display text-xl">SotuHire</span>
          </Link>
          <nav className="hidden items-center gap-7 text-sm text-muted-foreground md:flex">
            <a href="#features" className="hover:text-foreground">
              Recursos
            </a>
            <a href="#privacy" className="hover:text-foreground">
              Local-first
            </a>
            <Link to="/dashboard" className="hover:text-foreground">
              Dashboard
            </Link>
          </nav>
          <div className="flex items-center gap-2">
            <ApiModeBadge />
            <Link
              to="/dashboard"
              className="hidden items-center gap-1.5 rounded-md bg-primary px-3.5 py-1.5 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90 sm:inline-flex"
            >
              Entrar no app <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 grid-bg pointer-events-none" />
        <div className="relative mx-auto max-w-7xl px-6 pt-20 pb-24 md:pt-28 md:pb-32">
          <div className="mx-auto max-w-3xl text-center">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-card px-3 py-1 text-xs font-medium text-muted-foreground">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-success" />
              Análise de compatibilidade baseada em evidências
            </span>
            <h1 className="text-display mt-6 text-4xl leading-[1.08] sm:text-5xl md:text-[56px]">
              SotuHire: inteligência de carreira local-first
              <span className="text-muted-foreground"> para decidir melhor onde aplicar.</span>
            </h1>
            <p className="mx-auto mt-5 max-w-2xl text-base text-muted-foreground sm:text-lg">
              Analise currículo, vaga, ATS, GitHub, evidências, gaps e candidaturas com segurança —
              sem inventar experiência e sem expor seus dados.
            </p>
            <div className="mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row">
              <Link
                to="/dashboard"
                className="inline-flex items-center justify-center gap-2 rounded-md bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground shadow-[var(--shadow-elevated)] transition-opacity hover:opacity-90"
              >
                Abrir dashboard <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                to="/match"
                className="inline-flex items-center justify-center gap-2 rounded-md border border-input bg-card px-5 py-2.5 text-sm font-semibold hover:bg-muted"
              >
                Rodar demo
              </Link>
              <Link
                to="/settings"
                className="inline-flex items-center justify-center gap-2 rounded-md border border-input bg-card px-5 py-2.5 text-sm font-semibold hover:bg-muted"
              >
                Configurar API local
              </Link>
            </div>
            <div className="mt-8 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-xs text-muted-foreground">
              {["Local-first", "Sem login", "Sem rastreio", "Código aberto"].map((t) => (
                <span key={t} className="inline-flex items-center gap-1.5">
                  <CheckCircle2 className="h-3.5 w-3.5 text-accent" /> {t}
                </span>
              ))}
            </div>
          </div>

          {/* Hero preview */}
          <div className="relative mx-auto mt-16 max-w-5xl">
            <div className="rounded-2xl border border-border bg-card p-2 shadow-[var(--shadow-elevated)]">
              <div className="rounded-xl bg-gradient-to-br from-muted to-card p-8">
                <div className="grid gap-4 sm:grid-cols-3">
                  {[
                    { label: "Pontuação de compatibilidade", value: 78, tone: "text-chart-1" },
                    { label: "Alinhamento ATS", value: 74, tone: "text-chart-2" },
                    { label: "Aderência à vaga", value: 81, tone: "text-chart-2" },
                  ].map((s) => (
                    <div key={s.label} className="rounded-lg border border-border bg-card p-4">
                      <div className="text-xs text-muted-foreground">{s.label}</div>
                      <div className="text-display mt-1 text-4xl tabular-nums">{s.value}</div>
                      <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-muted">
                        <div
                          className="h-full rounded-full bg-accent"
                          style={{ width: `${s.value}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mt-4 rounded-lg border border-border bg-card p-4 text-xs">
                  <div className="mb-2 font-medium">Recomendação</div>
                  <p className="text-muted-foreground">
                    Aplicar com ajustes seguros: reforce projetos com Docker apenas se houver
                    experiência real; Cloud deve seguir como gap até existir evidência.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-6 py-16">
        <div className="mb-8 flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
          <div>
            <h2 className="text-display text-3xl">
              Fluxo guiado para sair da vaga bruta ao Kanban.
            </h2>
            <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
              O app moderno guia cada etapa sem mover score final ou regra de negócio para o
              frontend.
            </p>
          </div>
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-1.5 text-sm font-medium text-accent hover:underline"
          >
            Abrir fluxo no dashboard <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
        <GuidedFlow />
      </section>

      {/* Features */}
      <section id="features" className="mx-auto max-w-7xl px-6 py-20">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-display text-4xl">Tudo que você precisa para decidir uma vaga.</h2>
          <p className="mt-3 text-muted-foreground">
            Seis módulos integrados, ligados à mesma API local. Sem prometer o que não é
            verificável.
          </p>
        </div>
        <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((f) => (
            <div
              key={f.title}
              className="group rounded-xl border border-border bg-card p-5 shadow-[var(--shadow-soft)] transition-all hover:shadow-[var(--shadow-elevated)]"
            >
              <div className="grid h-10 w-10 place-items-center rounded-lg bg-muted text-muted-foreground transition-colors group-hover:bg-accent/15 group-hover:text-accent">
                <f.icon className="h-5 w-5" />
              </div>
              <h3 className="mt-4 text-base font-semibold">{f.title}</h3>
              <p className="mt-1.5 text-sm text-muted-foreground">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Privacy */}
      <section id="privacy" className="border-y border-border bg-muted/40">
        <div className="mx-auto grid max-w-7xl gap-10 px-6 py-20 md:grid-cols-2 md:items-center">
          <div>
            <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-card px-2.5 py-1 text-xs font-medium">
              <ShieldCheck className="h-3 w-3 text-accent" /> Local-first by design
            </span>
            <h2 className="text-display mt-4 text-4xl">
              Seu currículo não vira{" "}
              <span className="text-muted-foreground">treino de modelo.</span>
            </h2>
            <p className="mt-3 text-muted-foreground">
              A API roda em{" "}
              <code className="rounded bg-card px-1.5 py-0.5 text-xs">127.0.0.1:8787</code>. Nada
              sai da sua máquina sem você pedir. Sem login, sem telemetria, sem segredos no
              frontend.
            </p>
          </div>
          <div className="rounded-xl border border-border bg-card p-6 shadow-[var(--shadow-soft)]">
            <ul className="space-y-3 text-sm">
              {[
                [
                  "Dados no seu disco",
                  "Currículo, vagas e métricas ficam locais. Você decide o que exportar.",
                ],
                ["Sem chaves no cliente", "Tokens de Gemini, GitHub e ATS ficam no backend local."],
                ["Anti-invenção", "Sugestões nunca fabricam experiência, certificação ou cargo."],
                ["Código aberto", "Você pode auditar cada rota antes de confiar."],
              ].map(([t, d]) => (
                <li key={t} className="flex gap-3">
                  <Lock className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
                  <div>
                    <div className="font-medium">{t}</div>
                    <div className="text-xs text-muted-foreground">{d}</div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      <footer className="border-t border-border">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-3 px-6 py-8 text-xs text-muted-foreground sm:flex-row">
          <div className="flex items-center gap-2">
            <Sparkles className="h-3.5 w-3.5" /> SotuHire · v{APP_VERSION} · API local{" "}
            {API_LOCAL_HOST}
          </div>
          <div className="flex gap-4">
            <Link to="/privacy" className="hover:text-foreground">
              Privacidade
            </Link>
            <Link to="/settings" className="hover:text-foreground">
              Configurações
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
