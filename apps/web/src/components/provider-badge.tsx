import { Cpu, Sparkles, TriangleAlert, WifiOff } from "lucide-react";
import type { AnalysisMode } from "@/lib/api/types";
import { cn } from "@/lib/utils";

type ProviderState = "disabled" | "unconfigured";
type EffectiveMode = AnalysisMode | ProviderState;

export function ProviderBadge({
  provider,
  mode,
  fallback,
  model,
  state,
}: {
  provider?: string;
  mode?: AnalysisMode;
  fallback?: boolean;
  model?: string;
  state?: ProviderState;
}) {
  const effectiveMode: EffectiveMode =
    state ?? (fallback ? "fallback" : (mode ?? (provider === "local" ? "local" : "ai")));
  const cfg = {
    local: {
      icon: Cpu,
      label: "Análise local",
      cls: "border-border bg-muted/40 text-muted-foreground",
    },
    ai: {
      icon: Sparkles,
      label: "Análise com IA",
      cls: "border-accent/30 bg-accent/10 text-accent",
      title: providerLabel(provider, model),
    },
    fallback: {
      icon: TriangleAlert,
      label: "Fallback local",
      cls: "border-warning/30 bg-warning/10 text-warning",
    },
    disabled: {
      icon: WifiOff,
      label: "IA desativada",
      cls: "border-border bg-muted/40 text-muted-foreground",
    },
    unconfigured: {
      icon: TriangleAlert,
      label: "Provider não configurado",
      cls: "border-warning/30 bg-warning/10 text-warning",
    },
  }[effectiveMode];
  const Icon = cfg.icon;

  return (
    <span
      title={cfg.title}
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

export function AnalysisStateNote({
  provider,
  mode,
  fallback,
  model,
  warnings,
}: {
  provider?: string;
  mode?: AnalysisMode;
  fallback?: boolean;
  model?: string;
  warnings?: string[];
}) {
  const warningText = (warnings ?? []).join(" ").toLowerCase();
  const state =
    warningText.includes("sem chave") || warningText.includes("not_configured")
      ? "unconfigured"
      : warningText.includes("ia desativada")
        ? "disabled"
        : undefined;
  const effectiveMode = fallback ? "fallback" : (mode ?? (provider === "local" ? "local" : "ai"));
  const text =
    state === "unconfigured"
      ? "Provider não configurado: o SotuHire manteve a análise local até uma chave existir no backend."
      : state === "disabled"
        ? "IA desativada: esta tela usa apenas regras internas locais."
        : effectiveMode === "fallback"
          ? "Fallback: a IA falhou ou está indisponível, então o SotuHire usou análise local."
          : effectiveMode === "ai"
            ? "IA: análise enriquecida com provider configurado; score final e regras continuam no backend/core."
            : "Local: análise feita por regras internas.";

  return (
    <div className="mt-4 flex flex-wrap items-center gap-2 rounded-lg border border-border bg-muted/30 p-3 text-xs text-muted-foreground">
      <ProviderBadge
        provider={provider}
        mode={mode}
        fallback={fallback}
        model={model}
        state={state}
      />
      <span>{text}</span>
    </div>
  );
}

function providerLabel(provider?: string, model?: string): string {
  if (!provider || provider === "local") return "Provider local";
  if (provider === "gemini") return model ? `Gemini - ${model}` : "Gemini";
  return provider;
}
