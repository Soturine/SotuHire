import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, CircleCheck, CircleDot, ShieldCheck } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { ErrorState, LoadingState } from "@/components/states";
import { v2Api } from "@/features/career-copilot/api";
import { useApiMode } from "@/lib/api/mode";
import { usePreferences } from "@/lib/preferences";
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

/** Each recommendation type: what to call it and where the person acts on it. */
const ACTIONS: Record<string, { to: string; label: Record<Locale, [string, string]> }> = {
  APPLICATION_FOLLOW_UP_DUE: {
    to: "/tracker",
    label: {
      "pt-BR": ["Retomar candidaturas com prazo vencido", "Abrir Tracker"],
      "en-US": ["Follow up on overdue applications", "Open Tracker"],
    },
  },
  INTERVIEW_PREP_DUE: {
    to: "/interviews",
    label: {
      "pt-BR": ["Preparar a próxima entrevista", "Preparar"],
      "en-US": ["Prepare for the next interview", "Prepare"],
    },
  },
  PROFILE_REVIEW_REQUIRED: {
    to: "/evidence",
    label: {
      "pt-BR": ["Confirmar evidências pendentes", "Revisar evidências"],
      "en-US": ["Confirm pending evidence", "Review evidence"],
    },
  },
  PORTFOLIO_GAP: {
    to: "/portfolio",
    label: {
      "pt-BR": ["Levar projetos confirmados ao portfólio", "Abrir portfólio"],
      "en-US": ["Bring confirmed projects to the portfolio", "Open portfolio"],
    },
  },
  MISSING_CRITICAL_EVIDENCE: {
    to: "/evidence",
    label: {
      "pt-BR": ["Comprovar competências sem evidência", "Ver lacunas"],
      "en-US": ["Back skills that have no evidence", "See gaps"],
    },
  },
  RESUME_STALE: {
    to: "/resume-studio",
    label: {
      "pt-BR": ["Atualizar o Currículo Mestre", "Abrir Resume Studio"],
      "en-US": ["Update the Master Resume", "Open Resume Studio"],
    },
  },
  HIGH_FIT_OPPORTUNITY: {
    to: "/radar",
    label: {
      "pt-BR": ["Avaliar uma oportunidade com boa aderência", "Ver no Radar"],
      "en-US": ["Review a well-matched opportunity", "See in Radar"],
    },
  },
};

function actionCopy(type: string, locale: Locale) {
  const known = ACTIONS[type];
  if (known) return { to: known.to, title: known.label[locale][0], cta: known.label[locale][1] };
  // Unknown types still render, readable, and go to the approval queue as before.
  const readable = type.toLowerCase().replaceAll("_", " ");
  return {
    to: "/approvals",
    title: readable.charAt(0).toUpperCase() + readable.slice(1),
    cta: locale === "pt-BR" ? "Revisar" : "Review",
  };
}

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
  const ledger: { value: number | undefined; label: string; to: string; seal?: boolean }[] = [
    { value: pendingApprovals, label: t.approvals, to: "/approvals", seal: true },
    { value: data.active_applications, label: t.active, to: "/tracker" },
    { value: data.upcoming_interviews, label: t.interview, to: "/interviews" },
    { value: data.evidence_gaps.length, label: t.gapsCount, to: "/evidence" },
  ];
  return (
    <div className="mx-auto max-w-6xl space-y-8">
      <section className="trajectory-surface rounded-lg border px-6 py-7 md:px-9 md:py-9">
        <p className="eyebrow text-accent-strong">{t.eyebrow}</p>
        <div className="mt-3 grid gap-8 lg:grid-cols-[1fr_17rem] lg:items-end">
          <h2 className="text-display max-w-3xl text-[28px] leading-[1.15] md:text-[40px]">
            {data.profile_summary}
          </h2>
          <div>
            <div className="flex items-baseline justify-between gap-3">
              <span className="text-sm font-medium">{t.evidence}</span>
              <span className="text-display tabular text-3xl">{coverage}%</span>
            </div>
            <div
              className="mt-3 h-1.5 overflow-hidden rounded-full bg-muted"
              role="progressbar"
              aria-label={t.evidence}
              aria-valuenow={coverage}
              aria-valuemin={0}
              aria-valuemax={100}
            >
              <div
                className="h-full rounded-full bg-accent transition-[width] duration-(--duration-3) ease-(--ease-out)"
                style={{ width: `${coverage}%` }}
              />
            </div>
            <p className="mt-2 text-xs text-muted-foreground">{t.evidenceHint}</p>
          </div>
        </div>
        <p className="mt-6 text-xs text-muted-foreground">{t.noProvider}</p>
      </section>

      <section aria-label={t.eyebrow}>
        <ul className="grid grid-cols-2 gap-px overflow-hidden rounded-lg border bg-border md:grid-cols-4">
          {ledger.map((row) => (
            <li key={row.to}>
              <Link
                to={row.to}
                className="group flex h-full flex-col gap-1 bg-card px-5 py-4 transition-colors duration-(--duration-1) hover:bg-secondary"
              >
                <span
                  className={cn(
                    "text-display tabular text-3xl",
                    row.seal && (row.value ?? 0) > 0 && "text-seal-strong",
                  )}
                >
                  {row.value ?? "—"}
                </span>
                <span className="flex items-center gap-1 text-sm text-muted-foreground">
                  {row.label}
                  <ArrowRight
                    aria-hidden
                    className="h-3.5 w-3.5 opacity-0 transition-[opacity,transform] duration-(--duration-1) group-hover:translate-x-0.5 group-hover:opacity-100"
                  />
                </span>
              </Link>
            </li>
          ))}
        </ul>
      </section>

      <section className="grid gap-8 lg:grid-cols-[1fr_18rem]">
        <div>
          <div className="flex items-end justify-between gap-4 border-b pb-3">
            <div>
              <h2 className="text-display text-2xl">{t.priorities}</h2>
              <p className="mt-1 text-sm text-muted-foreground">{t.prioritiesHint}</p>
            </div>
            <ShieldCheck aria-hidden className="h-5 w-5 shrink-0 text-accent-strong" />
          </div>
          {data.recommendation_candidates.length ? (
            <ol className="divide-y">
              {data.recommendation_candidates.map((action, index) => {
                const view = actionCopy(action.type, locale);
                return (
                  <li
                    key={action.action_id}
                    className="grid grid-cols-[2rem_1fr] gap-x-4 py-5 sm:grid-cols-[2rem_1fr_auto]"
                  >
                    <span className="text-display tabular pt-0.5 text-xl text-muted-foreground">
                      {String(index + 1).padStart(2, "0")}
                    </span>
                    <div className="min-w-0">
                      <h3 className="flex flex-wrap items-center gap-2 font-semibold">
                        {view.title}
                        <span
                          className={cn(
                            "eyebrow rounded-sm px-1.5 py-0.5",
                            action.urgency === "critical" || action.urgency === "high"
                              ? "bg-seal/12 text-seal-strong"
                              : "bg-muted text-muted-foreground",
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
                      className="col-start-2 mt-3 inline-flex items-center gap-1.5 self-start text-sm font-medium text-accent-strong underline-offset-4 hover:underline sm:col-start-3 sm:mt-0"
                    >
                      {view.cta}
                      <ArrowRight aria-hidden className="h-4 w-4" />
                    </Link>
                  </li>
                );
              })}
            </ol>
          ) : (
            <p className="py-8 text-sm text-muted-foreground">{t.nothingToDo}</p>
          )}
        </div>

        <aside className="space-y-8">
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
    <div>
      <h2 className="eyebrow border-b pb-2 text-muted-foreground">{title}</h2>
      {items.length ? (
        <ul className="mt-3 space-y-2.5">
          {items.slice(0, 5).map((item) => (
            <li key={item} className="flex gap-2 text-sm">
              <Icon
                aria-hidden
                className={cn(
                  "mt-0.5 h-4 w-4 shrink-0",
                  positive ? "text-accent-strong" : "text-warning-strong",
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
