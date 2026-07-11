import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  ArrowUpRight,
  Briefcase,
  CheckCircle2,
  Kanban,
  LineChart as LineChartIcon,
  Target,
  TrendingUp,
  UserRound,
  RadioTower,
  ScrollText,
  Inbox,
  Wand2,
  XCircle,
} from "lucide-react";
import { useApi } from "@/lib/api/hooks";
import { AppShell } from "@/components/app-shell";
import { GuidedFlow } from "@/components/guided-flow";
import { StatCard } from "@/components/stat-card";
import { SectionCard } from "@/components/section-card";
import { ScoreRing } from "@/components/score-ring";
import { ErrorState, LoadingState, Skeleton } from "@/components/states";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useApiMode } from "@/lib/api/mode";
import { statusLabel } from "@/lib/labels";

export const Route = createFileRoute("/dashboard")({
  head: () => ({ meta: [{ title: "Dashboard — SotuHire" }] }),
  component: Dashboard,
});

function Dashboard() {
  const api = useApi();
  const { mode } = useApiMode();

  const healthQ = useQuery({ queryKey: ["health", mode], queryFn: () => api.health() });
  const metricsQ = useQuery({ queryKey: ["metrics", mode], queryFn: () => api.trackerMetrics() });
  const jobsQ = useQuery({ queryKey: ["tracker-jobs", mode], queryFn: () => api.trackerJobs() });
  const reqsQ = useQuery({ queryKey: ["reqs", mode], queryFn: () => api.trackerRequirements() });
  const profileQ = useQuery({ queryKey: ["profile", mode], queryFn: () => api.profile() });
  const radarQ = useQuery({ queryKey: ["radar-stats", mode], queryFn: () => api.radarStats() });
  const notificationsQ = useQuery({
    queryKey: ["notifications", mode],
    queryFn: () => api.notifications(),
  });
  const extensionQ = useQuery({
    queryKey: ["extension-captures", mode],
    queryFn: () => api.extensionCaptures(),
  });
  const examsQ = useQuery({
    queryKey: ["public-exams", mode],
    queryFn: () => api.publicExamList(),
  });

  const recentJobs = (jobsQ.data?.jobs ?? []).slice(0, 5);
  const weekly = metricsQ.data?.weekly_applications ?? [];
  const profile = profileQ.data?.profile;
  const profileItems = [...(profile?.items ?? []), ...(profile?.constraints ?? [])];
  const confirmedEvidence = profileItems.filter((item) => item.confirmed_by_user).length;
  const profileSignals = [
    profile?.headline,
    profile?.summary,
    profile?.primary_domains.length,
    profile?.target_roles.length,
    profile?.preferred_locations.length,
    confirmedEvidence,
  ].filter(Boolean).length;
  const profileCompleteness = Math.round((profileSignals / 6) * 100);
  const pendingCaptures = (extensionQ.data?.captures ?? []).filter(
    (capture) => capture.status !== "tracked" && capture.status !== "archived",
  ).length;

  return (
    <AppShell
      title="Dashboard"
      description="Visão geral da sua jornada de candidaturas, scores e gaps."
      actions={
        <Link
          to="/match"
          className="hidden items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:opacity-90 sm:inline-flex"
        >
          Nova análise <ArrowUpRight className="h-3 w-3" />
        </Link>
      }
    >
      <div className="space-y-6">
        {/* API status banner */}
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border bg-card p-4">
          <div className="flex items-center gap-3">
            <div
              className={`grid h-9 w-9 shrink-0 place-items-center rounded-lg ${
                mode === "demo"
                  ? "bg-warning/15 text-warning"
                  : healthQ.isError
                    ? "bg-destructive/15 text-destructive"
                    : "bg-success/15 text-success"
              }`}
            >
              <Activity className="h-4 w-4" />
            </div>
            <div className="min-w-0 text-sm">
              <div className="font-semibold">
                {mode === "demo"
                  ? "Modo Demo ativo"
                  : healthQ.isLoading
                    ? "Verificando API local…"
                    : healthQ.isError
                      ? "API local não detectada"
                      : `API online · v${healthQ.data?.version}`}
              </div>
              <div className="text-xs text-muted-foreground">
                {mode === "demo"
                  ? "Você está navegando com dados fictícios. Troque para API Real em Configurações."
                  : healthQ.isError
                    ? "Rode `python scripts/run_api.py` ou ative o modo Demo."
                    : "Conectado em http://127.0.0.1:8787/api/v1"}
              </div>
            </div>
          </div>
          {mode === "real" && healthQ.data?.capabilities && (
            <div className="flex flex-wrap gap-1.5">
              {healthQ.data.capabilities.slice(0, 4).map((c) => (
                <span
                  key={c}
                  className="rounded-full bg-muted px-2 py-0.5 text-[11px] text-muted-foreground"
                >
                  {c}
                </span>
              ))}
            </div>
          )}
        </div>

        <SectionCard
          title="Fluxo guiado"
          description="Siga o caminho principal: currículo, vaga, compatibilidade, ATS, ajuste, portfólio e tracker."
        >
          <GuidedFlow compact />
        </SectionCard>

        {/* KPIs */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            label="Vagas salvas"
            value={metricsQ.data?.total_saved ?? "—"}
            icon={Briefcase}
            hint="No tracker local"
          />
          <StatCard
            label="Aplicadas"
            value={metricsQ.data?.total_applied ?? "—"}
            icon={CheckCircle2}
            tone="accent"
            hint="Total enviadas"
          />
          <StatCard
            label="Taxa de resposta"
            value={metricsQ.data ? `${Math.round(metricsQ.data.response_rate * 100)}%` : "—"}
            icon={TrendingUp}
            hint={`Entrevistas: ${metricsQ.data ? Math.round(metricsQ.data.interview_rate * 100) : "—"}%`}
          />
          <StatCard
            label="ATS médio"
            value={metricsQ.data?.average_ats ?? "—"}
            icon={Target}
            hint="Últimas análises"
          />
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            label="Perfil completo"
            value={profileQ.isLoading ? "—" : `${profileCompleteness}%`}
            icon={UserRound}
            hint={`${confirmedEvidence} evidência(s) confirmada(s)`}
          />
          <StatCard
            label="Radar"
            value={radarQ.data?.new_results ?? "—"}
            icon={RadioTower}
            tone="accent"
            hint={`${radarQ.data?.unread_alerts ?? 0} alerta(s) não lido(s)`}
          />
          <StatCard
            label="Editais acompanhados"
            value={examsQ.data?.notices.length ?? "—"}
            icon={ScrollText}
            hint="Checklist e plano exigem revisão"
          />
          <StatCard
            label="Itens para revisar"
            value={pendingCaptures + (notificationsQ.data?.unread_count ?? 0)}
            icon={Inbox}
            hint={`${pendingCaptures} captura(s) · ${notificationsQ.data?.unread_count ?? 0} notificação(ões)`}
          />
        </div>

        {/* Charts + scores */}
        <div className="grid gap-6 lg:grid-cols-3">
          <SectionCard
            title="Candidaturas por semana"
            description="Evolução do volume aplicado"
            className="lg:col-span-2"
          >
            {metricsQ.isLoading ? (
              <Skeleton className="h-64 w-full" />
            ) : (
              <div className="h-64 w-full">
                <ResponsiveContainer>
                  <AreaChart data={weekly} margin={{ left: -16, right: 8, top: 8 }}>
                    <defs>
                      <linearGradient id="appsG" x1="0" x2="0" y1="0" y2="1">
                        <stop offset="0%" stopColor="var(--color-accent)" stopOpacity={0.35} />
                        <stop offset="100%" stopColor="var(--color-accent)" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid
                      stroke="var(--color-border)"
                      strokeDasharray="3 3"
                      vertical={false}
                    />
                    <XAxis
                      dataKey="week"
                      tickLine={false}
                      axisLine={false}
                      tick={{ fontSize: 11 }}
                    />
                    <YAxis tickLine={false} axisLine={false} tick={{ fontSize: 11 }} width={32} />
                    <Tooltip
                      contentStyle={{
                        background: "var(--color-card)",
                        border: "1px solid var(--color-border)",
                        borderRadius: 8,
                        fontSize: 12,
                      }}
                    />
                    <Area
                      dataKey="count"
                      stroke="var(--color-accent)"
                      strokeWidth={2}
                      fill="url(#appsG)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            )}
          </SectionCard>

          <SectionCard title="Última análise" description="Pontuação da análise mais recente">
            <div className="flex flex-col items-center gap-4">
              <ScoreRing
                value={78}
                label="Compatibilidade"
                size={128}
                tone="primary"
                sub="COMPAT."
              />
              <div className="grid w-full grid-cols-2 gap-2">
                <MiniScore label="ATS" value={74} />
                <MiniScore label="Aderência" value={81} />
                <MiniScore label="Confiança" value={66} />
                <MiniScore label="Risco" value={18} tone="warning" />
              </div>
              <Link to="/match" className="text-xs font-medium text-accent hover:underline">
                Abrir Análise de Compatibilidade →
              </Link>
            </div>
          </SectionCard>
        </div>

        {/* Recent jobs + intelligence */}
        <div className="grid gap-6 lg:grid-cols-2">
          <SectionCard
            title="Últimas candidaturas"
            description="Vagas mais recentes no tracker"
            actions={
              <Link
                to="/tracker"
                className="text-xs font-medium text-muted-foreground hover:text-foreground"
              >
                Ver tudo
              </Link>
            }
            padded={false}
          >
            {jobsQ.isLoading ? (
              <LoadingState />
            ) : jobsQ.isError ? (
              <ErrorState error={jobsQ.error} onRetry={() => jobsQ.refetch()} />
            ) : (
              <ul className="divide-y divide-border">
                {recentJobs.map((j) => (
                  <li
                    key={j.id}
                    className="flex items-center justify-between gap-3 px-5 py-3 hover:bg-muted/40"
                  >
                    <div className="min-w-0">
                      <div className="truncate text-sm font-medium">{j.title}</div>
                      <div className="truncate text-xs text-muted-foreground">
                        {j.company} · {j.source}
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="hidden rounded-full bg-muted px-2 py-0.5 text-[11px] text-muted-foreground sm:inline">
                        {statusLabel(j.status)}
                      </span>
                      <span className="text-display text-base tabular-nums">
                        {j.match_score ?? "—"}
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </SectionCard>

          <SectionCard
            title="Inteligência de Candidaturas"
            description="Requisitos mais pedidos × evidência sua"
            actions={
              <Link
                to="/intelligence"
                className="text-xs font-medium text-muted-foreground hover:text-foreground"
              >
                Ver tudo
              </Link>
            }
          >
            {reqsQ.isLoading ? (
              <LoadingState />
            ) : (
              <ul className="space-y-3">
                {reqsQ.data?.top_requirements.slice(0, 5).map((r) => (
                  <li key={r.name} className="space-y-1.5">
                    <div className="flex items-center justify-between text-sm">
                      <span className="flex items-center gap-1.5 font-medium">
                        {r.candidate_has_evidence ? (
                          <CheckCircle2 className="h-3.5 w-3.5 text-accent" />
                        ) : (
                          <XCircle className="h-3.5 w-3.5 text-destructive" />
                        )}
                        {r.name}
                      </span>
                      <span className="text-xs tabular-nums text-muted-foreground">
                        {r.count} vagas
                      </span>
                    </div>
                    <div className="h-1.5 overflow-hidden rounded-full bg-muted">
                      <div
                        className={`h-full ${r.candidate_has_evidence ? "bg-accent" : "bg-destructive/70"}`}
                        style={{ width: `${Math.min(100, r.count * 8)}%` }}
                      />
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </SectionCard>
        </div>

        {/* Shortcuts */}
        <SectionCard title="Atalhos">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { to: "/match", icon: Target, label: "Análise de Compatibilidade" },
              { to: "/ats", icon: LineChartIcon, label: "Análise ATS" },
              { to: "/tailor", icon: Wand2, label: "Ajuste de Currículo" },
              { to: "/tracker", icon: Kanban, label: "Candidaturas" },
            ].map((s) => (
              <Link
                key={s.to}
                to={s.to}
                className="group flex items-center justify-between rounded-lg border border-border bg-card px-4 py-3 transition-all hover:border-accent/40 hover:bg-accent/5"
              >
                <div className="flex items-center gap-2.5">
                  <s.icon className="h-4 w-4 text-muted-foreground group-hover:text-accent" />
                  <span className="text-sm font-medium">{s.label}</span>
                </div>
                <ArrowUpRight className="h-3.5 w-3.5 text-muted-foreground group-hover:text-accent" />
              </Link>
            ))}
          </div>
        </SectionCard>
      </div>
    </AppShell>
  );
}

function MiniScore({
  label,
  value,
  tone = "default",
}: {
  label: string;
  value: number;
  tone?: "default" | "warning";
}) {
  return (
    <div className="rounded-lg border border-border bg-muted/30 px-2.5 py-2 text-center">
      <div className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
      <div
        className={`text-display text-lg tabular-nums ${tone === "warning" ? "text-warning" : ""}`}
      >
        {value}
      </div>
    </div>
  );
}
