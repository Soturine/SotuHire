import { ArrowRight, CheckCircle2, Clipboard, Lightbulb, Save, ShieldAlert } from "lucide-react";
import { Link } from "@tanstack/react-router";
import { toast } from "sonner";
import { SectionCard } from "@/components/section-card";
import { cn } from "@/lib/utils";

type InsightAction = {
  label: string;
  to?: string;
  onClick?: () => void;
  icon?: "send" | "save";
};

export function ActionableInsights({
  title = "Assistente de acao",
  strengths,
  gaps,
  suggestions,
  risks,
  nextActions,
  doNotAdd,
  actions = [],
}: {
  title?: string;
  strengths?: string[];
  gaps?: string[];
  suggestions?: string[];
  risks?: string[];
  nextActions?: string[];
  doNotAdd?: string[];
  actions?: InsightAction[];
}) {
  const groups = [
    { title: "Pontos fortes", items: strengths ?? [], tone: "success" as const },
    { title: "Lacunas", items: gaps ?? [], tone: "warning" as const },
    { title: "Sugestoes praticas", items: suggestions ?? [], tone: "accent" as const },
    { title: "Riscos", items: risks ?? [], tone: "destructive" as const },
    { title: "Proximas acoes", items: nextActions ?? [], tone: "default" as const },
    {
      title: "Nao adicionar se nao for verdade",
      items: doNotAdd ?? [],
      tone: "integrity" as const,
    },
  ].filter((group) => group.items.length > 0);

  if (!groups.length) return null;

  const copyText = groups
    .map((group) => `${group.title}\n${group.items.map((item) => `- ${item}`).join("\n")}`)
    .join("\n\n");

  async function copy() {
    try {
      await navigator.clipboard.writeText(copyText);
      toast.success("Sugestoes copiadas.");
    } catch {
      toast.error("Nao foi possivel copiar automaticamente.");
    }
  }

  return (
    <SectionCard
      title={title}
      description="Organizado para agir sem fabricar experiencia, certificacao, metrica ou habilidade."
      actions={
        <button
          type="button"
          onClick={copy}
          className="inline-flex items-center gap-1.5 rounded-md border border-input bg-background px-2.5 py-1 text-[11px] font-medium hover:bg-muted"
        >
          <Clipboard className="h-3.5 w-3.5" />
          Copiar plano de acao
        </button>
      }
    >
      <div className="grid gap-3 lg:grid-cols-2">
        {groups.map((group) => (
          <InsightGroup
            key={group.title}
            title={group.title}
            items={group.items}
            tone={group.tone}
          />
        ))}
      </div>
      {actions.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2">
          {actions.map((action) =>
            action.to ? (
              <Link
                key={action.label}
                to={action.to}
                className="inline-flex items-center gap-1.5 rounded-md border border-input bg-background px-3 py-1.5 text-xs font-medium hover:bg-muted"
              >
                {action.icon === "save" ? (
                  <Save className="h-3.5 w-3.5" />
                ) : (
                  <ArrowRight className="h-3.5 w-3.5" />
                )}
                {action.label}
              </Link>
            ) : (
              <button
                key={action.label}
                type="button"
                onClick={action.onClick}
                className="inline-flex items-center gap-1.5 rounded-md border border-input bg-background px-3 py-1.5 text-xs font-medium hover:bg-muted"
              >
                {action.icon === "save" ? (
                  <Save className="h-3.5 w-3.5" />
                ) : (
                  <ArrowRight className="h-3.5 w-3.5" />
                )}
                {action.label}
              </button>
            ),
          )}
        </div>
      )}
    </SectionCard>
  );
}

function InsightGroup({
  title,
  items,
  tone,
}: {
  title: string;
  items: string[];
  tone: "success" | "warning" | "accent" | "destructive" | "default" | "integrity";
}) {
  const cfg = {
    success: {
      icon: CheckCircle2,
      cls: "border-success/30 bg-success/5",
      iconCls: "text-success",
    },
    warning: { icon: Lightbulb, cls: "border-warning/30 bg-warning/5", iconCls: "text-warning" },
    accent: { icon: Lightbulb, cls: "border-accent/30 bg-accent/5", iconCls: "text-accent" },
    destructive: {
      icon: ShieldAlert,
      cls: "border-destructive/30 bg-destructive/5",
      iconCls: "text-destructive",
    },
    default: {
      icon: ArrowRight,
      cls: "border-border bg-muted/30",
      iconCls: "text-muted-foreground",
    },
    integrity: {
      icon: ShieldAlert,
      cls: "border-warning/30 bg-warning/5",
      iconCls: "text-warning",
    },
  }[tone];
  const Icon = cfg.icon;
  return (
    <div className={cn("rounded-lg border p-3", cfg.cls)}>
      <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider">
        <Icon className={cn("h-3.5 w-3.5", cfg.iconCls)} />
        {title}
      </div>
      <ul className="space-y-1.5 text-sm">
        {items.map((item, index) => (
          <li key={`${title}-${index}`} className="leading-relaxed text-muted-foreground">
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
