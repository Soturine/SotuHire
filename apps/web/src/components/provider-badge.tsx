import { Cpu, Sparkles, TriangleAlert } from "lucide-react";
import type { AnalysisMode } from "@/lib/api/types";
import { cn } from "@/lib/utils";

export function ProviderBadge({
  provider,
  mode,
  fallback,
  model,
}: {
  provider?: string;
  mode?: AnalysisMode;
  fallback?: boolean;
  model?: string;
}) {
  const effectiveMode = fallback ? "fallback" : (mode ?? (provider === "local" ? "local" : "ai"));
  const cfg = {
    local: {
      icon: Cpu,
      label: "Local",
      cls: "border-border bg-muted/40 text-muted-foreground",
    },
    ai: {
      icon: Sparkles,
      label: providerLabel(provider, model),
      cls: "border-accent/30 bg-accent/10 text-accent",
    },
    fallback: {
      icon: TriangleAlert,
      label: "Fallback local",
      cls: "border-warning/30 bg-warning/10 text-warning",
    },
  }[effectiveMode];
  const Icon = cfg.icon;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium",
        cfg.cls,
      )}
    >
      <Icon className="h-3 w-3" />
      {cfg.label}
    </span>
  );
}

function providerLabel(provider?: string, model?: string): string {
  if (!provider || provider === "local") return "Local";
  if (provider === "gemini") return model ? `Gemini · ${model}` : "Gemini";
  return provider;
}
