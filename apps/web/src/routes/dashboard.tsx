import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowRight,
  ArrowUpRight,
  CalendarClock,
  CircleCheck,
  CircleDot,
  Send,
  ShieldCheck,
  Sparkle,
  Stamp,
  type LucideIcon,
} from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { ScoreRing } from "@/components/score-ring";
import { ErrorState, LoadingState } from "@/components/states";
import { v2Api } from "@/features/career-copilot/api";
import { useApiMode } from "@/lib/api/mode";
import { usePreferences } from "@/lib/preferences";
import { actionCopy } from "@/lib/recommendations";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/dashboard")({ component: CareerCockpit });

type Locale = "pt-BR" | "en-US";

const copy = {
  "pt-BR": {
    title: "Cockpit de carreira",
    description: "O que mudou, o que precisa de atenção e por quê.",
    eyebrow: "Seu estado profissional agora",
    loading: "Lendo seu estado profissional…",
    approvals: "aguardando sua aprovação",
    evidence: "Cobertura de evidências",
    evidenceHint: "parte dos fatos do Perfil com evidência confirmada",
    active: "candidaturas ativas",
    interview: "entrevistas nos próximos 7 dias",
    gapsCount: "lacunas para revisar",
    priorities: "Próximos passos",
    prioritiesHint: "Ordenados por urgência. Nada é executado sem você.",
    nothingToDo: "Nada pede sua atenção agora.",
    why: "Por que agora",
    impact: "Impacto",
    effort: "Esforço",
    strengths: "Forças comprovadas",
    gaps: "Lacunas para revisar",
    none: "Nenhuma ainda.",
    noProvider:
      "Calculado a partir dos seus dados; a confiança de provider de IA não entra na conta.",
    urgency: { low: "baixa", medium: "média", high: "alta", critical: "crítica" },
  },
  "en-US": {
    title: "Career cockpit",
    description: "What changed, what needs attention, and why.",
    eyebrow: "Your career state now",
    loading: "Reading your career state…",
    approvals: "waiting for your approval",
    evidence: "Evidence coverage",
    evidenceHint: "share of Profile facts with confirmed evidence",
    active: "active applications",
    interview: "interviews in the next 7 days",
    gapsCount: "gaps to review",
    priorities: "Next steps",
    prioritiesHint: "Ordered by urgency. Nothing runs without you.",
    nothingToDo: "Nothing needs your attention right now.",
    why: "Why now",
    impact: "Impact",
    effort: "Effort",
    strengths: "Confirmed strengths",
    gaps: "Gaps to review",
    none: "None yet.",
    noProvider: "Computed from your data; AI provider confidence is not part of it.",
    urgency: { low: "low", medium: "medium", high: "high", critical: "critical" },
  },
} satisfies Record<Locale, unknown>;

function CareerCockpit() {
  const { mode, baseUrl } = useApiMode();
  const { locale } = usePreferences();
  const t = copy[locale];
  const state = useQuery({
    queryKey: ["v2", "career-state", mode, baseUrl],
    queryFn: () => v2Api(mode, baseUrl).careerState(),
  });
  const approvals = useQuery({
    queryKey: ["v2", "approvals", mode, baseUrl],
    queryFn: () => v2Api(mode, baseUrl).approvals(),
  });

  return (
    <AppShell title={t.title} description={t.description}>
      {state.isError ? (
        // Before: zeros rendered as if they were the person's data while the API was down.
        <ErrorState error={state.error} onRetry={() => state.refetch()} />
      ) : state.isLoading || !state.data ? (
        <LoadingState label={t.loading} />
      ) : (
        <Cockpit
          t={t}
          locale={locale}
          data={state.data}
          pendingApprovals={approvals.data?.filter((item) => item.status === "proposed").length}
        />
      )}
    </AppShell>
  );
}

type CareerState = Awaited<ReturnType<ReturnType<typeof v2Api>["careerState"]>>;

function Cockpit({
  t,
  locale,
  data,
  pendingApprovals,
}: {
  t: (typeof copy)[Locale];
  locale: Locale;
  data: CareerState;
  pendingApprovals: number | undefined;
}) {
  const coverage = Math.round(data.confidence.data_coverage * 100);
  const ledger: {
    value: number | undefined;
    label: string;
    to: string;
    icon: LucideIcon;
    tone: string;
    urgent?: boolean;
  }[] = [
    {
      value: pendingApprovals,
      label: t.approvals,
      to: "/approvals",
      icon: Stamp,
      tone: "bg-seal/12 text-seal-strong",
      urgent: (pendingApprovals ?? 0) > 0,
    },
    {
      value: data.active_applications,
      label: t.active,
      to: "/tracker",
      icon: Send,
      tone: "bg-accent/12 text-accent-strong",
    },
    {
      value: data.upcoming_interviews,
      label: t.interview,
      to: "/interviews",
      icon: CalendarClock,
      tone: "bg-chart-5/15 text-foreground",
    },
    {
      value: data.evidence_gaps.length,
      label: t.gapsCount,
      to: "/evidence",
      icon: CircleDot,
      tone: "bg-highlight text-highlight-foreground",
    },
  ];
  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <section className="trajectory-surface rounded-2xl px-6 py-7 md:px-10 md:py-10">
        <div className="grid gap-8 md:grid-cols-[1fr_auto] md:items-center">
          <div className="min-w-0">
            <p className="eyebrow inline-flex items-center gap-2 text-hero-accent">
              <Sparkle aria-hidden className="h-3.5 w-3.5" />
              {t.eyebrow}
            </p>
            <h2 className="text-display mt-4 max-w-3xl text-[30px] leading-[1.12] md:text-[44px]">
              {data.profile_summary}
            </h2>
            <p className="mt-5 max-w-xl text-sm text-hero-muted">{t.noProvider}</p>
          </div>
          <div className="flex items-center gap-5 md:flex-col md:gap-3 md:text-center">
            <ScoreRing value={coverage} size={136} tone="hero" suffix="%" ariaLabel={t.evidence} />
            <div className="md:max-w-[11rem]">
              <p className="text-sm font-semibold">{t.evidence}</p>
              <p className="mt-1 text-xs text-hero-muted">{t.evidenceHint}</p>
            </div>
          </div>
        </div>
      </section>

      <section aria-label={t.eyebrow}>
        <ul className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {ledger.map((row) => {
            const Icon = row.icon;
            return (
              <li key={row.to}>
                <Link
                  to={row.to}
                  className="group flex h-full flex-col gap-3 rounded-xl border bg-card p-4 shadow-[var(--shadow-soft)] transition-[box-shadow,transform,border-color] duration-(--duration-2) ease-(--ease-out) hover:-translate-y-0.5 hover:border-accent/40 hover:shadow-[var(--shadow-elevated)] md:p-5"
                >
                  <span className="flex items-center justify-between">
                    <span className={cn("grid h-9 w-9 place-items-center rounded-lg", row.tone)}>
                      <Icon aria-hidden className="h-4 w-4" />
                    </span>
                    <ArrowUpRight
                      aria-hidden
                      className="h-4 w-4 text-muted-foreground opacity-0 transition-opacity duration-(--duration-1) group-hover:opacity-100"
                    />
                  </span>
                  <span
                    className={cn(
                      "text-metric text-3xl md:text-4xl",
                      row.urgent && "text-seal-strong",
                    )}
                  >
                    {row.value ?? "—"}
                  </span>
                  <span className="text-sm leading-snug text-muted-foreground">{row.label}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </section>

      <section className="grid gap-6 lg:grid-cols-[1fr_19rem]">
        <div className="rounded-xl border bg-card shadow-[var(--shadow-soft)]">
          <div className="flex items-start justify-between gap-4 border-b px-5 py-4 md:px-6">
            <div>
              <h2 className="text-lg font-semibold tracking-tight">{t.priorities}</h2>
              <p className="mt-0.5 text-sm text-muted-foreground">{t.prioritiesHint}</p>
            </div>
            <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-accent/12 text-accent-strong">
              <ShieldCheck aria-hidden className="h-4 w-4" />
            </span>
          </div>
          {data.recommendation_candidates.length ? (
            <ol className="divide-y">
              {data.recommendation_candidates.map((action, index) => {
                const view = actionCopy(action.type, locale);
                const hot = action.urgency === "critical" || action.urgency === "high";
                return (
                  <li
                    key={action.action_id}
                    className="grid grid-cols-[2.25rem_1fr] gap-x-4 px-5 py-5 transition-colors duration-(--duration-1) hover:bg-surface-muted/60 sm:grid-cols-[2.25rem_1fr_auto] md:px-6"
                  >
                    <span
                      className={cn(
                        "text-metric grid h-9 w-9 place-items-center rounded-full text-sm",
                        index === 0
                          ? "bg-brand-gradient text-white shadow-[var(--shadow-soft)]"
                          : "bg-muted text-muted-foreground",
                      )}
                    >
                      {String(index + 1).padStart(2, "0")}
                    </span>
                    <div className="min-w-0">
                      <h3 className="flex flex-wrap items-center gap-2 font-semibold">
                        {view.title}
                        <span
                          className={cn(
                            "eyebrow rounded-full px-2 py-0.5",
                            hot ? "bg-seal/12 text-seal-strong" : "bg-muted text-muted-foreground",
                          )}
                        >
                          {t.urgency[action.urgency]}
                        </span>
                      </h3>
                      <p className="mt-1.5 text-sm">
                        <span className="text-muted-foreground">{t.why}: </span>
                        {action.reason}
                      </p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {t.impact}: {action.impact} · {t.effort}:{" "}
                        <span className="tabular">{action.estimated_effort}</span>
                      </p>
                    </div>
                    <Link
                      to={view.to}
                      className={cn(
                        "col-start-2 mt-3 inline-flex items-center gap-1.5 self-start justify-self-start rounded-lg px-3 py-1.5 text-sm font-medium transition-[background-color,box-shadow] duration-(--duration-1) sm:col-start-3 sm:mt-0",
                        index === 0
                          ? "bg-primary text-primary-foreground shadow-[var(--shadow-soft)] hover:bg-primary/90"
                          : "border bg-card text-foreground hover:bg-secondary",
                      )}
                    >
                      {view.cta}
                      <ArrowRight aria-hidden className="h-4 w-4" />
                    </Link>
                  </li>
                );
              })}
            </ol>
          ) : (
            <p className="px-6 py-8 text-sm text-muted-foreground">{t.nothingToDo}</p>
          )}
        </div>

        <aside className="space-y-4">
          <FactList title={t.strengths} items={data.confirmed_strengths} none={t.none} positive />
          <FactList title={t.gaps} items={data.evidence_gaps} none={t.none} />
        </aside>
      </section>
    </div>
  );
}

function FactList({
  title,
  items,
  none,
  positive = false,
}: {
  title: string;
  items: string[];
  none: string;
  positive?: boolean;
}) {
  const Icon = positive ? CircleCheck : CircleDot;
  return (
    <div
      className={cn(
        "rounded-xl border p-5 shadow-[var(--shadow-soft)]",
        positive ? "insight-surface" : "bg-card",
      )}
    >
      <h2
        className={cn(
          "eyebrow flex items-center gap-2",
          positive ? "text-accent-strong" : "text-warning-strong",
        )}
      >
        <Icon aria-hidden className="h-3.5 w-3.5" />
        {title}
      </h2>
      {items.length ? (
        <ul className="mt-3.5 space-y-2.5">
          {items.slice(0, 5).map((item) => (
            <li key={item} className="flex gap-2.5 text-sm">
              <span
                aria-hidden
                className={cn(
                  "mt-[7px] h-1.5 w-1.5 shrink-0 rounded-full",
                  positive ? "bg-accent" : "bg-warning",
                )}
              />
              <span className={cn(!positive && "mark-pending")}>{item}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-3 text-sm text-muted-foreground">{none}</p>
      )}
    </div>
  );
}
