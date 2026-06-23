import { Link } from "@tanstack/react-router";
import { Briefcase, FileText, Github, Kanban, Save, ScanSearch, Target, Wand2 } from "lucide-react";
import type { ComponentType } from "react";
import { cn } from "@/lib/utils";

type FlowStatus = "Pendente" | "Pronto" | "Recomendado" | "Opcional";

type GuidedStep = {
  n: number;
  to: string;
  label: string;
  desc: string;
  status: FlowStatus;
  icon: ComponentType<{ className?: string }>;
};

const steps: GuidedStep[] = [
  {
    n: 1,
    to: "/resume",
    label: "Adicionar curriculo",
    desc: "Extraia o perfil de um texto ficticio ou real local.",
    status: "Pronto",
    icon: FileText,
  },
  {
    n: 2,
    to: "/job",
    label: "Adicionar vaga",
    desc: "Estruture requisitos, senioridade e keywords ATS.",
    status: "Pronto",
    icon: Briefcase,
  },
  {
    n: 3,
    to: "/match",
    label: "Rodar compatibilidade",
    desc: "Compare evidencias, aderencia, confianca e risco.",
    status: "Recomendado",
    icon: Target,
  },
  {
    n: 4,
    to: "/ats",
    label: "Melhorar ATS",
    desc: "Veja keywords presentes, adicionaveis e sem evidencia.",
    status: "Recomendado",
    icon: ScanSearch,
  },
  {
    n: 5,
    to: "/tailor",
    label: "Ajustar curriculo",
    desc: "Gere bullets seguros sem inventar experiencia.",
    status: "Recomendado",
    icon: Wand2,
  },
  {
    n: 6,
    to: "/github",
    label: "Analisar GitHub/portfolio",
    desc: "Use repositorios publicos como evidencia tecnica.",
    status: "Opcional",
    icon: Github,
  },
  {
    n: 7,
    to: "/tracker",
    label: "Salvar candidatura",
    desc: "Registre origem, scores, notas e ultima analise.",
    status: "Pendente",
    icon: Save,
  },
  {
    n: 8,
    to: "/tracker",
    label: "Acompanhar no Kanban",
    desc: "Mova cada vaga entre etapas ate resposta final.",
    status: "Pendente",
    icon: Kanban,
  },
];

export function GuidedFlow({ compact = false }: { compact?: boolean }) {
  return (
    <ol
      data-testid="guided-flow"
      className={cn("grid gap-3", compact ? "sm:grid-cols-2 xl:grid-cols-4" : "lg:grid-cols-4")}
    >
      {steps.map((step) => {
        const Icon = step.icon;
        return (
          <li key={`${step.n}-${step.label}`}>
            <Link
              to={step.to}
              className="group flex h-full min-h-[132px] flex-col rounded-lg border border-border bg-card p-3 transition-all hover:border-accent/40 hover:bg-accent/5 hover:shadow-[var(--shadow-soft)]"
            >
              <div className="flex items-start justify-between gap-3">
                <span className="grid h-8 w-8 shrink-0 place-items-center rounded-md bg-muted text-xs font-bold text-muted-foreground group-hover:bg-accent group-hover:text-accent-foreground">
                  {step.n}
                </span>
                <StatusChip status={step.status} />
              </div>
              <div className="mt-4 flex items-center gap-2">
                <Icon className="h-4 w-4 text-muted-foreground group-hover:text-accent" />
                <span className="text-sm font-semibold">{step.label}</span>
              </div>
              <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">{step.desc}</p>
            </Link>
          </li>
        );
      })}
    </ol>
  );
}

function StatusChip({ status }: { status: FlowStatus }) {
  const cls = {
    Pendente: "bg-muted text-muted-foreground",
    Pronto: "bg-success/15 text-success",
    Recomendado: "bg-accent/15 text-accent",
    Opcional: "bg-warning/15 text-warning",
  }[status];
  return (
    <span className={cn("rounded-full px-2 py-0.5 text-[10px] font-semibold", cls)}>{status}</span>
  );
}
