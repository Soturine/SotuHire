import { Cpu, KeyRound, Loader2, Sparkles, TriangleAlert, WifiOff } from "lucide-react";
import type { AiUiState, AnalysisMeta, AnalysisMode } from "@/lib/api/types";
import { cn } from "@/lib/utils";

type EffectiveMode = AnalysisMode | AiUiState;

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
  state?: AiUiState;
}) {
  const effectiveMode: EffectiveMode =
    state ?? (fallback ? "fallback" : (mode ?? (provider === "local" ? "local" : "ai")));
  const cfg = {
    local: {
      icon: Cpu,
      label: "Analise local",
      cls: "border-border bg-muted/40 text-muted-foreground",
    },
    provider_local: {
      icon: Cpu,
      label: "Provider local",
      cls: "border-border bg-muted/40 text-muted-foreground",
    },
    ai: {
      icon: Sparkles,
      label: "Analise com IA",
      cls: "border-accent/30 bg-accent/10 text-accent",
      title: providerLabel(provider, model),
    },
    configured: {
      icon: KeyRound,
      label: "Provider configurado",
      cls: "border-success/30 bg-success/10 text-success",
      title: providerLabel(provider, model),
    },
    analyzing: {
      icon: Loader2,
      label: "Analisando com IA",
      cls: "border-accent/30 bg-accent/10 text-accent",
      title: providerLabel(provider, model),
      spin: true,
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
      label: "Provider nao configurado",
      cls: "border-warning/30 bg-warning/10 text-warning",
    },
    provider_error: {
      icon: TriangleAlert,
      label: "Limite/erro do provider",
      cls: "border-destructive/30 bg-destructive/10 text-destructive",
    },
    provider_timeout: {
      icon: TriangleAlert,
      label: "Timeout do provider",
      cls: "border-warning/30 bg-warning/10 text-warning",
    },
    invalid_key: {
      icon: KeyRound,
      label: "Chave invalida",
      cls: "border-destructive/30 bg-destructive/10 text-destructive",
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
      <Icon className={cn("h-3 w-3", "spin" in cfg && cfg.spin ? "animate-spin" : "")} />
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
  trace,
}: {
  provider?: string;
  mode?: AnalysisMode;
  fallback?: boolean;
  model?: string;
  warnings?: string[];
  trace?: AnalysisMeta;
}) {
  const warningText = (warnings ?? []).join(" ").toLowerCase();
  const state =
    warningText.includes("timeout") || warningText.includes("demor")
      ? "provider_timeout"
      : warningText.includes("invalid") ||
          warningText.includes("invalida") ||
          warningText.includes("invalido")
        ? "invalid_key"
        : warningText.includes("limit") ||
            warningText.includes("quota") ||
            warningText.includes("erro do provider")
          ? "provider_error"
          : warningText.includes("sem chave") || warningText.includes("not_configured")
            ? "unconfigured"
            : warningText.includes("ia desativada")
              ? "disabled"
              : undefined;
  const effectiveMode = fallback ? "fallback" : (mode ?? (provider === "local" ? "local" : "ai"));
  const text =
    state === "provider_timeout"
      ? "A IA demorou para responder. O SotuHire usou a analise local."
      : state === "provider_error"
        ? "O provider retornou limite ou erro. O fluxo continua com fallback local."
        : state === "invalid_key"
          ? "Chave invalida: confira Configuracoes -> IA e Providers. Nenhuma chave e exibida no frontend."
          : state === "unconfigured"
            ? "Provider nao configurado: configure uma chave em Configuracoes -> IA e Providers ou continue com analise local."
            : state === "disabled"
              ? "IA desativada: esta tela usa apenas regras internas locais."
              : effectiveMode === "fallback"
                ? "Fallback: a IA falhou ou esta indisponivel, entao o SotuHire usou analise local."
                : effectiveMode === "ai"
                  ? "IA: analise enriquecida com provider configurado. Revise as sugestoes antes de aplicar."
                  : "Local: analise feita por regras internas.";

  return (
    <div className="mt-4 rounded-lg border border-border bg-muted/30 p-3 text-xs text-muted-foreground">
      <div className="flex flex-wrap items-center gap-2">
        <ProviderBadge
          provider={provider}
          mode={mode}
          fallback={fallback}
          model={model}
          state={state}
        />
        <span>{text}</span>
      </div>
      {trace?.prompt_id && (
        <details className="mt-3 border-t border-border pt-2">
          <summary className="cursor-pointer font-medium text-foreground">Rastreabilidade</summary>
          <dl className="mt-2 grid gap-x-4 gap-y-1 sm:grid-cols-2">
            <div>
              <dt className="inline font-medium">Provider: </dt>
              <dd className="inline">
                {trace.provider_requested || trace.requested_provider || "local"} →{" "}
                {trace.provider_used || "local"}
              </dd>
            </div>
            <div>
              <dt className="inline font-medium">Modelo: </dt>
              <dd className="inline">
                {trace.model_requested || "local"} → {trace.model_used || trace.model || "local"}
              </dd>
            </div>
            <div>
              <dt className="inline font-medium">Prompt: </dt>
              <dd className="inline font-mono">
                {trace.prompt_id}@{trace.prompt_version || "?"}
              </dd>
            </div>
            <div>
              <dt className="inline font-medium">Revisão: </dt>
              <dd className="inline">
                {trace.needs_user_review === false ? "opcional" : "necessária"}
              </dd>
            </div>
          </dl>
          {trace.fallback_reason && (
            <p className="mt-2 text-warning">Fallback: {trace.fallback_reason}</p>
          )}
          {trace.evidence_used && trace.evidence_used.length > 0 && (
            <div className="mt-2">
              <span className="font-medium text-foreground">Contexto usado: </span>
              {trace.evidence_used
                .slice(0, 5)
                .map((item) => `${item.title} (${item.confidence || "medium"})`)
                .join(" · ")}
            </div>
          )}
        </details>
      )}
    </div>
  );
}

function providerLabel(provider?: string, model?: string): string {
  if (!provider || provider === "local") return "Provider local";
  if (provider === "gemini") return model ? `Gemini - ${model}` : "Gemini";
  return provider;
}
