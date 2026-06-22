import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { AppShell } from "@/components/app-shell";
import { SectionCard } from "@/components/section-card";
import { StatCard } from "@/components/stat-card";
import { ErrorState, LoadingState } from "@/components/states";
import { useApi } from "@/lib/api/hooks";
import { useApiMode } from "@/lib/api/mode";
import { TrendingUp, Target, ScanSearch, BadgeCheck } from "lucide-react";

export const Route = createFileRoute("/intelligence")({
  head: () => ({ meta: [{ title: "Inteligência de Candidaturas — SotuHire" }] }),
  component: IntelPage,
});

const CHART_COLORS = [
  "var(--color-chart-1)",
  "var(--color-chart-2)",
  "var(--color-chart-3)",
  "var(--color-chart-4)",
  "var(--color-chart-5)",
];

function IntelPage() {
  const api = useApi();
  const { mode } = useApiMode();
  const metricsQ = useQuery({ queryKey: ["metrics", mode], queryFn: () => api.trackerMetrics() });
  const funnelQ = useQuery({ queryKey: ["funnel", mode], queryFn: () => api.trackerFunnel() });
  const reqsQ = useQuery({ queryKey: ["reqs", mode], queryFn: () => api.trackerRequirements() });
  const srcQ = useQuery({ queryKey: ["sources", mode], queryFn: () => api.trackerSources() });

  const loading = metricsQ.isLoading || funnelQ.isLoading || reqsQ.isLoading || srcQ.isLoading;
  const err = metricsQ.error || funnelQ.error || reqsQ.error || srcQ.error;

  if (loading)
    return (
      <AppShell title="Inteligência de Candidaturas">
        <LoadingState label="Carregando inteligência…" />
      </AppShell>
    );
  if (err)
    return (
      <AppShell title="Inteligência de Candidaturas">
        <ErrorState error={err} />
      </AppShell>
    );

  const metrics = metricsQ.data!;
  const funnel = funnelQ.data!;
  const reqs = reqsQ.data!;
  const sources = srcQ.data!;

  const statusData = Object.entries(metrics.by_status).map(([name, value]) => ({ name, value }));
  const matchAvgData = Object.entries(metrics.average_match_by_status).map(([name, value]) => ({
    name,
    value,
  }));

  return (
    <AppShell
      title="Inteligência de Candidaturas"
      description="Aprenda com o seu próprio pipeline. Tudo calculado localmente, sobre seus dados."
    >
      <div className="space-y-6">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            label="Compatibilidade média (aplicadas)"
            value={metrics.average_match_by_status.applied ?? "—"}
            icon={Target}
            tone="accent"
          />
          <StatCard label="ATS médio" value={metrics.average_ats ?? "—"} icon={ScanSearch} />
          <StatCard
            label="Taxa de resposta"
            value={`${Math.round(metrics.response_rate * 100)}%`}
            icon={TrendingUp}
          />
          <StatCard
            label="Taxa de oferta"
            value={`${Math.round(metrics.offer_rate * 100)}%`}
            icon={BadgeCheck}
            tone="accent"
          />
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <SectionCard title="Requisitos mais pedidos" description="Top requisitos × evidência sua">
            <div className="h-72">
              <ResponsiveContainer>
                <BarChart
                  data={reqs.top_requirements}
                  layout="vertical"
                  margin={{ left: 8, right: 16 }}
                >
                  <CartesianGrid
                    stroke="var(--color-border)"
                    strokeDasharray="3 3"
                    horizontal={false}
                  />
                  <XAxis type="number" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis
                    dataKey="name"
                    type="category"
                    width={90}
                    tick={{ fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip
                    contentStyle={{
                      background: "var(--color-card)",
                      border: "1px solid var(--color-border)",
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                  />
                  <Bar dataKey="count" radius={[0, 6, 6, 0]}>
                    {reqs.top_requirements.map((r, i) => (
                      <Cell
                        key={i}
                        fill={
                          r.candidate_has_evidence
                            ? "var(--color-accent)"
                            : "var(--color-destructive)"
                        }
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-3 flex gap-4 text-xs text-muted-foreground">
              <Legend2 color="var(--color-accent)" label="Com evidência sua" />
              <Legend2 color="var(--color-destructive)" label="Sem evidência" />
            </div>
          </SectionCard>

          <SectionCard title="Funil de candidaturas">
            <div className="space-y-3">
              {funnel.stages.map((s, i) => {
                const max = funnel.stages[0]!.count;
                const pct = (s.count / max) * 100;
                return (
                  <div key={s.status}>
                    <div className="mb-1 flex justify-between text-xs">
                      <span className="font-medium">{s.label}</span>
                      <span className="tabular-nums text-muted-foreground">{s.count}</span>
                    </div>
                    <div className="h-7 overflow-hidden rounded-md bg-muted">
                      <div
                        className="flex h-full items-center justify-end pr-2 text-[11px] font-medium text-primary-foreground transition-all"
                        style={{
                          width: `${pct}%`,
                          background: `linear-gradient(90deg, ${CHART_COLORS[i % CHART_COLORS.length]}, color-mix(in oklab, ${CHART_COLORS[i % CHART_COLORS.length]} 70%, white))`,
                        }}
                      >
                        {pct > 15 ? `${Math.round(pct)}%` : ""}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </SectionCard>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          <SectionCard title="Status do Kanban" className="lg:col-span-1">
            <div className="h-64">
              <ResponsiveContainer>
                <PieChart>
                  <Pie
                    data={statusData}
                    dataKey="value"
                    nameKey="name"
                    innerRadius={45}
                    outerRadius={75}
                    paddingAngle={2}
                  >
                    {statusData.map((_, i) => (
                      <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      background: "var(--color-card)",
                      border: "1px solid var(--color-border)",
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </SectionCard>

          <SectionCard title="Compatibilidade média por status" className="lg:col-span-2">
            <div className="h-64">
              <ResponsiveContainer>
                <BarChart data={matchAvgData} margin={{ left: -16, right: 8 }}>
                  <CartesianGrid
                    stroke="var(--color-border)"
                    strokeDasharray="3 3"
                    vertical={false}
                  />
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11 }} axisLine={false} tickLine={false} width={32} />
                  <Tooltip
                    contentStyle={{
                      background: "var(--color-card)",
                      border: "1px solid var(--color-border)",
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                  />
                  <Bar dataKey="value" fill="var(--color-chart-2)" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </SectionCard>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <SectionCard title="Evolução das candidaturas" description="Aplicações por semana">
            <div className="h-64">
              <ResponsiveContainer>
                <LineChart
                  data={metrics.weekly_applications ?? []}
                  margin={{ left: -16, right: 8 }}
                >
                  <CartesianGrid
                    stroke="var(--color-border)"
                    strokeDasharray="3 3"
                    vertical={false}
                  />
                  <XAxis dataKey="week" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11 }} axisLine={false} tickLine={false} width={32} />
                  <Tooltip
                    contentStyle={{
                      background: "var(--color-card)",
                      border: "1px solid var(--color-border)",
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="count"
                    stroke="var(--color-chart-1)"
                    strokeWidth={2.5}
                    dot={{ r: 3 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </SectionCard>

          <SectionCard title="Fontes com mais vagas">
            <div className="space-y-3">
              {sources.sources.map((s) => (
                <div key={s.name} className="rounded-lg border border-border bg-muted/30 p-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium">{s.name}</span>
                    <span className="text-xs tabular-nums text-muted-foreground">
                      compat. média {s.average_match}
                    </span>
                  </div>
                  <div className="mt-2 grid grid-cols-3 gap-2 text-center text-xs">
                    <Mini label="Salvas" value={s.saved} />
                    <Mini label="Aplicadas" value={s.applied} />
                    <Mini label="Entrevistas" value={s.interviews} />
                  </div>
                  <div className="mt-2 flex flex-wrap gap-1">
                    {s.top_requirements.map((r) => (
                      <span key={r} className="rounded bg-card px-1.5 py-0.5 text-[10px]">
                        {r}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </SectionCard>
        </div>

        <SectionCard
          title="Gaps críticos recorrentes"
          description="Aparecem com mais frequência sem evidência"
        >
          {reqs.critical_gaps && reqs.critical_gaps.length > 0 ? (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {reqs.critical_gaps.map((g) => (
                <div
                  key={g.name}
                  className="rounded-lg border border-destructive/30 bg-destructive/5 p-4"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{g.name}</span>
                    <span className="rounded-full bg-destructive/20 px-2 py-0.5 text-[10px] uppercase tracking-wider text-destructive">
                      {g.severity}
                    </span>
                  </div>
                  <div className="mt-1 text-xs text-muted-foreground">{g.count} vagas</div>
                  <p className="mt-2 text-xs">{g.safe_action}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">Sem gaps críticos detectados.</p>
          )}
        </SectionCard>
      </div>
    </AppShell>
  );
}

function Mini({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded bg-card px-2 py-1.5">
      <div className="text-display tabular-nums">{value}</div>
      <div className="text-[10px] text-muted-foreground">{label}</div>
    </div>
  );
}

function Legend2({ color, label }: { color: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className="h-2 w-2 rounded-sm" style={{ background: color }} />
      {label}
    </span>
  );
}
