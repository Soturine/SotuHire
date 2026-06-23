import { createFileRoute } from "@tanstack/react-router";
import {
  Activity,
  Beaker,
  Brain,
  Eye,
  EyeOff,
  Loader2,
  Radio,
  ShieldAlert,
  Trash2,
  WifiOff,
} from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";
import { AppShell } from "@/components/app-shell";
import { SectionCard } from "@/components/section-card";
import { useApiStatus } from "@/components/api-mode-badge";
import { useApi } from "@/lib/api/hooks";
import { DEFAULT_API_URL, useApiMode } from "@/lib/api/mode";
import { APP_VERSION } from "@/lib/labels";
import type { AiProvider, AiSettings, AiSettingsStatus } from "@/lib/api/types";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

export const Route = createFileRoute("/settings")({
  head: () => ({ meta: [{ title: "Configurações — SotuHire" }] }),
  component: SettingsPage,
});

function SettingsPage() {
  const { mode, setMode, baseUrl, setBaseUrl } = useApiMode();
  const api = useApi();
  const healthQ = useQuery({
    queryKey: ["health-settings", mode, baseUrl],
    queryFn: () => api.health(),
    retry: false,
  });
  const status = useApiStatus();

  return (
    <AppShell
      title="Configurações"
      description="Modo da API, providers de IA e verificações do ambiente local."
    >
      <div className="grid gap-6 lg:grid-cols-2">
        <SectionCard
          title="Modo de operação"
          description="Demo usa dados fictícios. Real consome sua API local."
        >
          <div className="grid grid-cols-2 gap-3">
            <ModeCard
              active={mode === "demo"}
              onClick={() => setMode("demo")}
              icon={<Beaker className="h-4 w-4" />}
              title="Demo"
              desc="Dados fictícios, ideal para explorar a UI."
              tone="warning"
            />
            <ModeCard
              active={mode === "real"}
              onClick={() => setMode("real")}
              icon={<Radio className="h-4 w-4" />}
              title="API Real"
              desc="Consome 127.0.0.1:8787 (FastAPI local)."
              tone="success"
            />
          </div>

          <div className="mt-5">
            <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Base URL da API
            </label>
            <div className="mt-1.5 flex gap-2">
              <input
                value={baseUrl}
                onChange={(e) => setBaseUrl(e.target.value)}
                className="flex-1 rounded-md border border-input bg-background px-3 py-2 font-mono text-sm outline-none focus:border-accent/50 focus:ring-2 focus:ring-accent/20"
              />
              <button
                onClick={() => {
                  setBaseUrl(DEFAULT_API_URL);
                  toast.success("Restaurado para o padrão");
                }}
                className="rounded-md border border-input bg-background px-3 py-2 text-xs font-medium hover:bg-muted"
              >
                Padrão
              </button>
            </div>
            <p className="mt-2 text-xs text-muted-foreground">
              Padrão: <code className="rounded bg-muted px-1 py-0.5">{DEFAULT_API_URL}</code>
            </p>
          </div>
        </SectionCard>

        <SectionCard title="Status da API">
          <ApiStatusPanel
            status={status.status}
            message={status.message}
            onRefetch={() => healthQ.refetch()}
            refreshing={healthQ.isFetching}
            capabilities={healthQ.data?.capabilities}
          />
        </SectionCard>

        <AiProvidersCard />

        <SectionCard title="Sobre">
          <div className="grid gap-3 text-sm">
            <Item k="Versão" v={`v${APP_VERSION}`} />
            <Item k="Local-first" v="Sim" />
            <Item k="Segredos no cliente" v="Nenhum" />
            <Item k="Contrato da API" v="v1" />
          </div>
        </SectionCard>
      </div>
    </AppShell>
  );
}

function ApiStatusPanel({
  status,
  message,
  onRefetch,
  refreshing,
  capabilities,
}: {
  status: ReturnType<typeof useApiStatus>["status"];
  message: string;
  onRefetch: () => void;
  refreshing: boolean;
  capabilities?: string[];
}) {
  const cfg = {
    demo: {
      Icon: Beaker,
      cls: "border-warning/30 bg-warning/10 text-warning",
      title: "Modo Demo ativo",
    },
    checking: {
      Icon: Loader2,
      cls: "border-border bg-muted/40 text-muted-foreground",
      title: "Verificando…",
    },
    online: { Icon: Activity, cls: "border-success/30 bg-success/5 text-success", title: "Online" },
    offline: {
      Icon: WifiOff,
      cls: "border-destructive/30 bg-destructive/5 text-destructive",
      title: "Offline",
    },
    error: {
      Icon: ShieldAlert,
      cls: "border-destructive/30 bg-destructive/5 text-destructive",
      title: "Erro de CORS/API",
    },
  }[status];
  const { Icon } = cfg;
  return (
    <>
      <div className={`flex items-start gap-3 rounded-lg border p-3 ${cfg.cls}`}>
        <Icon className={`h-5 w-5 shrink-0 ${status === "checking" ? "animate-spin" : ""}`} />
        <div className="flex-1 text-sm">
          <div className="font-semibold text-foreground">{cfg.title}</div>
          <div className="mt-0.5 text-xs text-muted-foreground">{message}</div>
        </div>
        <button
          onClick={onRefetch}
          disabled={refreshing}
          className="rounded-md border border-input bg-background px-2.5 py-1 text-xs font-medium text-foreground hover:bg-muted disabled:opacity-50"
        >
          {refreshing ? "…" : "Re-verificar"}
        </button>
      </div>
      {capabilities && capabilities.length > 0 && (
        <div className="mt-4">
          <div className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
            Capacidades
          </div>
          <div className="flex flex-wrap gap-1.5">
            {capabilities.map((c) => (
              <span key={c} className="rounded-md bg-muted px-2 py-0.5 font-mono text-[11px]">
                {c}
              </span>
            ))}
          </div>
        </div>
      )}
      {status === "offline" && (
        <p className="mt-3 rounded-md bg-muted/50 p-3 text-xs text-muted-foreground">
          Dica: rode <code className="rounded bg-card px-1 py-0.5">python scripts/run_api.py</code>{" "}
          ou use o modo Demo enquanto a API local não estiver disponível.
        </p>
      )}
    </>
  );
}

// ---------------- AI Providers ----------------

type AiUiStatus = "idle" | "testing" | "ready" | "configured" | "planned" | "error";

function AiProvidersCard() {
  const { mode, baseUrl } = useApiMode();
  const api = useApi();
  const queryClient = useQueryClient();
  const aiQueryKey = ["ai-settings", mode, baseUrl];
  const [provider, setProvider] = useState<AiProvider>("local");
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState("gemini-2.5-flash");
  const [showKey, setShowKey] = useState(false);
  const [status, setStatus] = useState<AiUiStatus>("idle");
  const [toggles, setToggles] = useState({
    enabled: false,
    match: true,
    ats: true,
    tailor: true,
    github: true,
    memory: false,
  });

  const settingsQ = useQuery({
    queryKey: aiQueryKey,
    queryFn: () => api.aiSettings(),
    retry: false,
  });

  useEffect(() => {
    if (!settingsQ.data) return;
    const data = settingsQ.data;
    setProvider(data.provider);
    setModel(data.model || defaultModel(data.provider));
    setStatus(statusFromSettings(data));
    setToggles({
      enabled: data.use_ai,
      match: data.allow_match,
      ats: data.allow_ats,
      tailor: data.allow_tailor,
      github: data.allow_github,
      memory: data.allow_memory_context,
    });
  }, [settingsQ.data]);

  const saveMutation = useMutation({
    mutationFn: () =>
      api.aiSettingsSave({
        provider,
        model: provider === "local" ? "local" : model,
        api_key: provider === "gemini" && apiKey.trim() ? apiKey.trim() : undefined,
        use_ai: toggles.enabled,
        allow_match: toggles.match,
        allow_ats: toggles.ats,
        allow_tailor: toggles.tailor,
        allow_github: toggles.github,
        allow_memory_context: toggles.memory,
      }),
    onSuccess: (data) => {
      setApiKey("");
      setStatus(statusFromSettings(data));
      queryClient.setQueryData(aiQueryKey, data);
      toast.success("Configuração salva no backend local.");
    },
    onError: (error) => {
      setStatus("error");
      toast.error(
        error instanceof Error ? error.message : "Não foi possível salvar a configuração.",
      );
    },
  });

  const testMutation = useMutation({
    mutationFn: () =>
      api.aiSettingsTest({
        provider,
        model: provider === "local" ? "local" : model,
        api_key: provider === "gemini" && apiKey.trim() ? apiKey.trim() : undefined,
      }),
    onMutate: () => {
      setStatus("testing");
    },
    onSuccess: (data) => {
      setStatus(statusFromTest(data.status, data.success));
      if (data.success) {
        toast.success(data.message || "Provider configurado com sucesso.");
      } else {
        toast.warning(data.message || "Não foi possível testar o provider.");
      }
    },
    onError: (error) => {
      setStatus("error");
      toast.error(error instanceof Error ? error.message : "Não foi possível testar o provider.");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => api.aiSettingsDelete(),
    onSuccess: (data) => {
      setApiKey("");
      setStatus(statusFromSettings(data));
      queryClient.setQueryData(aiQueryKey, data);
      toast.success("Chave removida do backend local.");
    },
    onError: (error) => {
      setStatus("error");
      toast.error(error instanceof Error ? error.message : "Não foi possível remover a chave.");
    },
  });

  const providerAllowsKey = provider === "gemini";
  const busy = saveMutation.isPending || testMutation.isPending || deleteMutation.isPending;

  return (
    <SectionCard
      className="lg:col-span-2"
      title={
        <span className="flex items-center gap-2">
          <Brain className="h-4 w-4 text-accent" /> IA e Providers
        </span>
      }
      description="Configure visualmente. A API key vai apenas para o backend local — nunca é salva no frontend."
    >
      <div className="grid gap-5 lg:grid-cols-2">
        <div className="space-y-4">
          <div>
            <label className="block text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
              Provider
            </label>
            <div className="mt-1.5 grid grid-cols-3 gap-2">
              {(["local", "gemini", "openai_future"] as AiProvider[]).map((p) => (
                <button
                  key={p}
                  onClick={() => {
                    setProvider(p);
                    setModel(defaultModel(p));
                  }}
                  className={`rounded-md border px-3 py-2 text-xs font-medium capitalize transition-colors ${
                    provider === p
                      ? "border-accent/50 bg-accent/10 text-foreground"
                      : "border-input bg-background hover:bg-muted"
                  }`}
                >
                  {providerLabel(p)}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
              Chave de IA
            </label>
            <div className="mt-1.5 flex gap-2">
              <div className="relative flex-1">
                <input
                  type={showKey ? "text" : "password"}
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder={
                    providerAllowsKey
                      ? "Cole a chave Gemini para salvar no backend"
                      : "Não necessário"
                  }
                  disabled={!providerAllowsKey}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 pr-9 font-mono text-xs outline-none focus:border-accent/50 focus:ring-2 focus:ring-accent/20 disabled:opacity-50"
                />
                <button
                  type="button"
                  onClick={() => setShowKey((v) => !v)}
                  className="absolute right-1.5 top-1/2 -translate-y-1/2 rounded p-1 text-muted-foreground hover:bg-muted"
                  aria-label="Alternar visualização"
                >
                  {showKey ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                </button>
              </div>
            </div>
            <p className="mt-1.5 text-[11px] text-muted-foreground">
              Após salvar, a chave nunca é exibida novamente — apenas o status.
            </p>
          </div>

          <div>
            <label className="block text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
              Modelo
            </label>
            <input
              value={model}
              onChange={(e) => setModel(e.target.value)}
              disabled={provider === "local"}
              className="mt-1.5 w-full rounded-md border border-input bg-background px-3 py-2 font-mono text-xs outline-none focus:border-accent/50 focus:ring-2 focus:ring-accent/20 disabled:opacity-50"
            />
          </div>

          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => testMutation.mutate()}
              disabled={busy}
              className="inline-flex items-center gap-1.5 rounded-md border border-input bg-background px-3 py-1.5 text-xs font-medium hover:bg-muted disabled:opacity-50"
            >
              {testMutation.isPending && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
              Testar conexão
            </button>
            <button
              onClick={() => saveMutation.mutate()}
              disabled={busy}
              className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
            >
              {saveMutation.isPending && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
              Salvar no backend local
            </button>
            <button
              onClick={() => deleteMutation.mutate()}
              disabled={busy}
              className="inline-flex items-center gap-1.5 rounded-md border border-destructive/30 bg-destructive/5 px-3 py-1.5 text-xs font-medium text-destructive hover:bg-destructive/10"
            >
              <Trash2 className="h-3.5 w-3.5" /> Remover chave
            </button>
            <StatusPill status={status} />
          </div>
          {settingsQ.data?.updated_at && (
            <p className="text-[11px] text-muted-foreground">
              Atualizado em {new Date(settingsQ.data.updated_at).toLocaleString("pt-BR")}.
            </p>
          )}
          {settingsQ.isError && (
            <p className="rounded-md bg-muted/50 p-2 text-[11px] text-muted-foreground">
              API offline ou sem resposta. A tela continua funcionando em modo Demo/mock.
            </p>
          )}
          {settingsQ.data?.warnings?.map((warning) => (
            <p key={warning} className="rounded-md bg-warning/10 p-2 text-[11px] text-warning">
              {warning}
            </p>
          ))}
        </div>

        <div className="space-y-3">
          <Toggle
            label="Usar IA nas análises"
            checked={toggles.enabled}
            onChange={(v) => setToggles({ ...toggles, enabled: v })}
          />
          <Toggle
            label="Permitir IA na Análise de Compatibilidade"
            checked={toggles.match}
            onChange={(v) => setToggles({ ...toggles, match: v })}
            disabled={!toggles.enabled}
          />
          <Toggle
            label="Permitir IA na Análise ATS"
            checked={toggles.ats}
            onChange={(v) => setToggles({ ...toggles, ats: v })}
            disabled={!toggles.enabled}
          />
          <Toggle
            label="Permitir IA no Ajuste de Currículo"
            checked={toggles.tailor}
            onChange={(v) => setToggles({ ...toggles, tailor: v })}
            disabled={!toggles.enabled}
          />
          <Toggle
            label="Permitir IA na Análise de GitHub"
            checked={toggles.github}
            onChange={(v) => setToggles({ ...toggles, github: v })}
            disabled={!toggles.enabled}
          />
          <Toggle
            label="Enviar contexto relevante da memória local"
            hint="Desligado por padrão"
            checked={toggles.memory}
            onChange={(v) => setToggles({ ...toggles, memory: v })}
            disabled={!toggles.enabled}
          />

          <div className="mt-2 flex items-start gap-2 rounded-lg border border-warning/30 bg-warning/5 p-3 text-xs">
            <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-warning" />
            <p className="text-muted-foreground">
              A chave de IA nunca é salva no frontend. Ela deve ser enviada somente para a API local
              do SotuHire. O GitHub Pages não processa IA e não deve receber segredos.
            </p>
          </div>

          <details className="rounded-lg border border-border bg-muted/30 p-3 text-xs text-muted-foreground">
            <summary className="cursor-pointer font-medium text-foreground">
              Endpoints ativos no backend local
            </summary>
            <ul className="mt-2 space-y-0.5 font-mono">
              <li>GET /api/v1/settings/ai</li>
              <li>POST /api/v1/settings/ai</li>
              <li>POST /api/v1/settings/ai/test</li>
              <li>DELETE /api/v1/settings/ai</li>
              <li>GET /api/v1/settings/ai/status</li>
            </ul>
          </details>
        </div>
      </div>
    </SectionCard>
  );
}

function StatusPill({ status }: { status: AiUiStatus }) {
  const cfg = {
    idle: { cls: "bg-muted text-muted-foreground", label: "Não configurado" },
    testing: { cls: "bg-muted text-muted-foreground", label: "Testando…" },
    ready: { cls: "bg-success/15 text-success", label: "Pronto local" },
    configured: { cls: "bg-success/15 text-success", label: "Configurado" },
    planned: { cls: "bg-warning/15 text-warning", label: "Planejado" },
    error: { cls: "bg-destructive/15 text-destructive", label: "Erro" },
  }[status];
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-1 text-[11px] font-medium ${cfg.cls}`}
    >
      {cfg.label}
    </span>
  );
}

function Toggle({
  label,
  hint,
  checked,
  onChange,
  disabled,
}: {
  label: string;
  hint?: string;
  checked: boolean;
  onChange: (v: boolean) => void;
  disabled?: boolean;
}) {
  return (
    <label
      className={`flex items-center justify-between gap-3 rounded-lg border border-border bg-card px-3 py-2.5 ${disabled ? "opacity-50" : ""}`}
    >
      <div className="min-w-0">
        <div className="text-sm font-medium">{label}</div>
        {hint && <div className="text-[11px] text-muted-foreground">{hint}</div>}
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => onChange(!checked)}
        className={`relative h-5 w-9 shrink-0 rounded-full transition-colors ${checked ? "bg-accent" : "bg-muted"}`}
      >
        <span
          className={`absolute top-0.5 h-4 w-4 rounded-full bg-card shadow transition-all ${checked ? "left-[18px]" : "left-0.5"}`}
        />
      </button>
    </label>
  );
}

function ModeCard({
  active,
  onClick,
  icon,
  title,
  desc,
  tone,
}: {
  active: boolean;
  onClick: () => void;
  icon: ReactNode;
  title: string;
  desc: string;
  tone: "warning" | "success";
}) {
  const ring = tone === "warning" ? "ring-warning/40 bg-warning/5" : "ring-success/40 bg-success/5";
  return (
    <button
      onClick={onClick}
      className={`group rounded-xl border border-border p-4 text-left transition-all hover:shadow-[var(--shadow-soft)] ${
        active ? `ring-2 ${ring}` : ""
      }`}
    >
      <div className="flex items-center gap-2">
        <div
          className={`grid h-7 w-7 place-items-center rounded-md ${tone === "warning" ? "bg-warning/20 text-warning" : "bg-success/20 text-success"}`}
        >
          {icon}
        </div>
        <span className="font-semibold">{title}</span>
        {active && (
          <span className="ml-auto text-[10px] font-semibold uppercase tracking-wider text-accent">
            Ativo
          </span>
        )}
      </div>
      <p className="mt-2 text-xs text-muted-foreground">{desc}</p>
    </button>
  );
}

function providerLabel(provider: AiProvider): string {
  if (provider === "openai_future") return "OpenAI (futuro)";
  if (provider === "gemini") return "Gemini";
  return "Local";
}

function defaultModel(provider: AiProvider): string {
  if (provider === "local") return "local";
  if (provider === "gemini") return "gemini-2.5-flash";
  return "planned";
}

function statusFromSettings(settings: AiSettings): AiUiStatus {
  if (settings.status === "planned") return "planned";
  if (settings.status === "error") return "error";
  if (settings.status === "ready") return "ready";
  return settings.configured ? "configured" : "idle";
}

function statusFromTest(status: AiSettingsStatus, success: boolean): AiUiStatus {
  if (status === "planned") return "planned";
  if (status === "ready") return "ready";
  if (success) return "configured";
  return "error";
}

function Item({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-border bg-muted/30 px-3 py-2">
      <span className="text-xs text-muted-foreground">{k}</span>
      <span className="font-mono text-xs">{v}</span>
    </div>
  );
}
