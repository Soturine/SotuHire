import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

export function StatCard({
  label,
  value,
  hint,
  icon: Icon,
  tone = "default",
  trend,
}: {
  label: string;
  value: ReactNode;
  hint?: ReactNode;
  icon?: LucideIcon;
  tone?: "default" | "accent" | "warning" | "destructive";
  trend?: ReactNode;
}) {
  const toneCls = {
    default: "text-foreground",
    accent: "text-accent",
    warning: "text-warning",
    destructive: "text-destructive",
  }[tone];

  return (
    <div className="group relative overflow-hidden rounded-xl border border-border bg-card p-5 shadow-[var(--shadow-soft)] transition-all hover:shadow-[var(--shadow-elevated)]">
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            {label}
          </p>
          <p className={cn("text-display text-3xl tabular-nums leading-none", toneCls)}>{value}</p>
        </div>
        {Icon && (
          <div className="grid h-9 w-9 place-items-center rounded-lg bg-muted text-muted-foreground transition-colors group-hover:bg-accent/15 group-hover:text-accent">
            <Icon className="h-4 w-4" />
          </div>
        )}
      </div>
      {(hint || trend) && (
        <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
          <span>{hint}</span>
          <span>{trend}</span>
        </div>
      )}
    </div>
  );
}
