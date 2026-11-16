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
    accent: "text-accent-strong",
    warning: "text-warning-strong",
    destructive: "text-destructive-strong",
  }[tone];
  const chipCls = {
    default: "bg-surface-accent text-accent-strong",
    accent: "bg-accent/12 text-accent-strong",
    warning: "bg-highlight text-highlight-foreground",
    destructive: "bg-destructive/10 text-destructive-strong",
  }[tone];

  return (
    <div className="group relative overflow-hidden rounded-xl border border-border bg-card p-5 shadow-[var(--shadow-soft)] transition-[box-shadow,border-color] duration-(--duration-2) ease-(--ease-out) hover:border-accent/30 hover:shadow-[var(--shadow-elevated)]">
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-xs font-medium text-muted-foreground">{label}</p>
          <p className={cn("text-metric text-3xl", toneCls)}>{value}</p>
        </div>
        {Icon && (
          <div className={cn("grid h-9 w-9 place-items-center rounded-lg", chipCls)}>
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
