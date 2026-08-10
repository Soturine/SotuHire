import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowRight,
  CalendarClock,
  CheckCircle2,
  Compass,
  Inbox,
  Layers3,
  ShieldCheck,
  Target,
} from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { v2Api } from "@/features/career-copilot/api";
import { useApiMode } from "@/lib/api/mode";
import { usePreferences } from "@/lib/preferences";

export const Route = createFileRoute("/dashboard")({ component: CareerCockpit });

const copy = {
  "pt-BR": {
    title: "Cockpit de carreira",
    description: "O que mudou, o que precisa de atenção e por quê.",
    eyebrow: "Seu estado profissional agora",
    approvals: "Aguardando sua aprovação",
    evidence: "Cobertura de evidências",
    active: "Candidaturas ativas",
    interview: "Próxima entrevista",
    priorities: "Próximas melhores ações",
    why: "Por que agora",
    impact: "Impacto esperado",
    effort: "Esforço",
    open: "Revisar",
    strengths: "Forças comprovadas",
    gaps: "Lacunas para revisar",
    noProvider: "Confiança do provider não entra no cálculo determinístico.",
  },
  "en-US": {
    title: "Career cockpit",
    description: "What changed, what needs attention, and why.",
    eyebrow: "Your career state now",
    approvals: "Waiting for your approval",
    evidence: "Evidence coverage",
    active: "Active applications",
    interview: "Next interview",
    priorities: "Next best actions",
    why: "Why now",
    impact: "Expected impact",
    effort: "Effort",
    open: "Review",
    strengths: "Confirmed strengths",
    gaps: "Gaps to review",
    noProvider: "Provider confidence is not part of deterministic scoring.",
  },
};

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
      <div className="career-map mx-auto max-w-7xl space-y-6">
        <section className="trajectory-surface overflow-hidden rounded-3xl border p-6 md:p-8">
          <div className="grid gap-8 lg:grid-cols-[1.3fr_0.7fr] lg:items-end">
            <div>
              <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-accent">
                <Compass className="h-4 w-4" /> {t.eyebrow}
              </p>
              <h2 className="mt-4 max-w-3xl text-3xl font-semibold tracking-tight md:text-5xl">
                {state.data?.profile_summary ?? "Carregando estado da carreira…"}
              </h2>
              <p className="mt-4 max-w-2xl text-sm text-muted-foreground">{t.noProvider}</p>
            </div>
            <div className="rounded-2xl border border-accent/20 bg-background/70 p-5 backdrop-blur">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">{t.evidence}</span>
                <span className="text-2xl font-semibold tabular-nums">
                  {Math.round((state.data?.confidence.data_coverage ?? 0) * 100)}%
                </span>
              </div>
              <div className="mt-4 h-2 rounded-full bg-muted">
                <div
                  className="h-full rounded-full bg-accent"
                  style={{
                    width: `${Math.round((state.data?.confidence.data_coverage ?? 0) * 100)}%`,
                  }}
                />
              </div>
            </div>
          </div>
        </section>

        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Career signals">
          <Signal
            icon={Inbox}
            label={t.approvals}
            value={approvals.data?.filter((item) => item.status === "proposed").length ?? 0}
            to="/approvals"
          />
          <Signal
            icon={Target}
            label={t.active}
            value={state.data?.active_applications ?? 0}
            to="/tracker"
          />
          <Signal
            icon={CalendarClock}
            label={t.interview}
            value={state.data?.upcoming_interviews ?? 0}
            to="/interviews"
          />
          <Signal
            icon={Layers3}
            label={t.gaps}
            value={state.data?.evidence_gaps.length ?? 0}
            to="/evidence"
          />
        </section>

        <section className="grid gap-6 lg:grid-cols-[1.45fr_0.55fr]">
          <div className="rounded-2xl border bg-card p-5 shadow-[var(--shadow-soft)] md:p-6">
            <div className="mb-5 flex items-center justify-between">
              <h2 className="text-xl font-semibold">{t.priorities}</h2>
              <ShieldCheck className="h-5 w-5 text-accent" aria-label="Human approval required" />
            </div>
            <ol className="space-y-3">
              {state.data?.recommendation_candidates.map((action, index) => (
                <li
                  key={action.action_id}
                  className="group rounded-xl border bg-background p-4 transition-colors hover:border-accent/40"
                >
                  <div className="flex gap-4">
                    <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-primary text-xs font-semibold text-primary-foreground">
                      {index + 1}
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="font-semibold">{action.type.replaceAll("_", " ")}</h3>
                        <span className="rounded-full bg-warning/15 px-2 py-0.5 text-[11px] font-medium">
                          {action.urgency}
                        </span>
                      </div>
                      <p className="mt-2 text-sm">
                        <span className="font-medium">{t.why}:</span> {action.reason}
                      </p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        <span className="font-medium text-foreground">{t.impact}:</span>{" "}
                        {action.impact} · {t.effort}: {action.estimated_effort}
                      </p>
                    </div>
                    <Button asChild variant="outline" size="sm">
                      <Link to="/approvals">
                        {t.open}
                        <ArrowRight />
                      </Link>
                    </Button>
                  </div>
                </li>
              ))}
            </ol>
          </div>

          <div className="space-y-6">
            <ListPanel title={t.strengths} items={state.data?.confirmed_strengths ?? []} positive />
            <ListPanel title={t.gaps} items={state.data?.evidence_gaps ?? []} />
          </div>
        </section>
      </div>
    </AppShell>
  );
}

function Signal({
  icon: Icon,
  label,
  value,
  to,
}: {
  icon: typeof Target;
  label: string;
  value: number;
  to: "/approvals" | "/tracker" | "/interviews" | "/evidence";
}) {
  return (
    <Link
      to={to}
      className="group rounded-2xl border bg-card p-5 shadow-[var(--shadow-soft)] transition-transform hover:-translate-y-0.5"
    >
      <div className="flex items-center justify-between">
        <Icon className="h-5 w-5 text-accent" />
        <ArrowRight className="h-4 w-4 text-muted-foreground transition-transform group-hover:translate-x-1" />
      </div>
      <div className="mt-5 text-3xl font-semibold tabular-nums">{value}</div>
      <div className="mt-1 text-sm text-muted-foreground">{label}</div>
    </Link>
  );
}

function ListPanel({
  title,
  items,
  positive = false,
}: {
  title: string;
  items: string[];
  positive?: boolean;
}) {
  return (
    <div className="rounded-2xl border bg-card p-5">
      <h2 className="font-semibold">{title}</h2>
      <ul className="mt-4 space-y-3">
        {items.slice(0, 5).map((item) => (
          <li key={item} className="flex gap-2 text-sm">
            <CheckCircle2
              className={`mt-0.5 h-4 w-4 shrink-0 ${positive ? "text-accent" : "text-warning"}`}
            />
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
