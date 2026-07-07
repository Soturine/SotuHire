import { createFileRoute } from "@tanstack/react-router";
import {
  Activity,
  Beaker,
  Brain,
  ExternalLink,
  Eye,
  EyeOff,
  Loader2,
  Radio,
  RefreshCw,
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
import type { AiProvider, AiSettings, AiSettingsPreset, AiSettingsStatus } from "@/lib/api/types";
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

        <AiProvidersCardV194 />

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

const AI_PRESETS: Array<{
  id: AiSettingsPreset;
  label: string;
  description: string;
}> = [
  {
    id: "local_safe",
    label: "Local seguro",
    description: "Sem provider externo e sem memória enviada.",
  },
  {
    id: "basic",
    label: "IA básica",
    description: "Perfil, Lattes, vaga, edital, match, ATS e tailor.",
  },
  {
    id: "complete",
    label: "IA completa",
    description: "Inclui Radar, extensão e GitHub; memória continua desligada.",
  },
  {
    id: "custom",
    label: "Personalizado",
    description: "Mostra permissões avançadas agrupadas.",
  },
];

type AiToggleState = {
  enabled: boolean;
  profile: boolean;
  lattes: boolean;
  resume: boolean;
  job: boolean;
  publicExams: boolean;
  match: boolean;
  ats: boolean;
  tailor: boolean;
  github: boolean;
  sourceImport: boolean;
  extension: boolean;
  radar: boolean;
  notifications: boolean;
  memory: boolean;
};

function AiProvidersCardV194() {
  const { mode, baseUrl } = useApiMode();
  const api = useApi();
  const queryClient = useQueryClient();
  const aiQueryKey = ["ai-settings", mode, baseUrl];
  const [provider, setProvider] = useState<AiProvider>("local");
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState("local");
  const [customModel, setCustomModel] = useState("");
  const [preset, setPreset] = useState<AiSettingsPreset>("local_safe");
  const [showKey, setShowKey] = useState(false);
  const [status, setStatus] = useState<AiUiStatus>("idle");
  const [toggles, setToggles] = useState<AiToggleState>(localAiToggles());

  const settingsQ = useQuery({
    queryKey: aiQueryKey,
    queryFn: () => api.aiSettings(),
    retry: false,
  });
  const providersQ = useQuery({
    queryKey: ["ai-providers", mode, baseUrl],
    queryFn: () => api.aiProviders(),
    retry: false,
  });
  const modelsQ = useQuery({
    queryKey: ["ai-models", mode, baseUrl, provider],
    queryFn: () => api.aiModels(provider),
    retry: false,
  });

  useEffect(() => {
    if (!settingsQ.data) return;
    const data = settingsQ.data;
    setProvider(data.provider);
    setModel(data.model || defaultModel(data.provider));
    setCustomModel("");
    setPreset(data.preset || "custom");
    setStatus(statusFromSettings(data));
    setToggles({
      enabled: data.use_ai,
      profile: data.allow_profile,
      lattes: data.allow_lattes,
      resume: data.allow_resume,
      job: data.allow_job,
      publicExams: data.allow_public_exams,
      match: data.allow_match,
      ats: data.allow_ats,
      tailor: data.allow_tailor,
      github: data.allow_github,
      sourceImport: data.allow_source_import,
      extension: data.allow_extension,
      radar: data.allow_radar,
      notifications: data.allow_notifications,
      memory: data.allow_memory_context,
    });
  }, [settingsQ.data]);

  const providerAllowsKey = provider === "gemini" || provider === "openai";
  const selectedProviderInfo = providersQ.data?.providers.find((item) => item.id === provider);
  const modelOptions = modelsQ.data?.models ?? [];
  const selectedModel = provider === "local" ? "local" : customModel.trim() || model;

  const saveMutation = useMutation({
    mutationFn: () =>
      api.aiSettingsSave({
        provider,
        model: selectedModel,
        api_key: providerAllowsKey && apiKey.trim() ? apiKey.trim() : undefined,
        preset,
        use_ai: toggles.enabled,
        allow_profile: toggles.profile,
        allow_lattes: toggles.lattes,
        allow_resume: toggles.resume,
        allow_job: toggles.job,
        allow_public_exams: toggles.publicExams,
        allow_match: toggles.match,
        allow_ats: toggles.ats,
        allow_tailor: toggles.tailor,
        allow_github: toggles.github,
        allow_source_import: toggles.sourceImport,
        allow_extension: toggles.extension,
        allow_radar: toggles.radar,
        allow_notifications: toggles.notifications,
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
        model: selectedModel,
        api_key: providerAllowsKey && apiKey.trim() ? apiKey.trim() : undefined,
      }),
    onMutate: () => setStatus("testing"),
    onSuccess: (data) => {
      setStatus(statusFromTest(data.status, data.success));
      if (data.success) {
        toast.success(data.message || "Provider configurado.");
      } else {
        toast.warning(data.message || "Provider indisponível.");
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

  const refreshModels = useMutation({
    mutationFn: () =>
      provider === "gemini" || provider === "openai"
        ? api.aiModelsRefresh(provider)
        : api.aiModels(provider),
    onSuccess: (data) => {
      queryClient.setQueryData(["ai-models", mode, baseUrl, provider], data);
      toast.success("Catálogo de modelos atualizado ou fallback mantido.");
    },
    onError: (error) =>
      toast.error(error instanceof Error ? error.message : "Não foi possível atualizar modelos."),
  });

  function applyPreset(nextPreset: AiSettingsPreset) {
    setPreset(nextPreset);
    if (nextPreset === "local_safe") {
      setProvider("local");
      setModel("local");
      setCustomModel("");
      setToggles(localAiToggles());
      return;
    }
    if (provider === "local") {
      setProvider("gemini");
      setModel("gemini-2.5-flash");
    }
    if (nextPreset === "basic") setToggles(basicAiToggles());
    if (nextPreset === "complete") setToggles(completeAiToggles());
  }

  const busy =
    saveMutation.isPending ||
    testMutation.isPending ||
    deleteMutation.isPending ||
    refreshModels.isPending;

  return (
    <SectionCard
      className="lg:col-span-2"
      title={
        <span className="flex items-center gap-2">
          <Brain className="h-4 w-4 text-accent" /> IA e Providers
        </span>
      }
      description="Escolha um preset simples. A API key vai apenas para o backend local e nunca é salva no frontend."
    >
      <div className="grid gap-5 lg:grid-cols-2">
        <div className="space-y-4">
          <div>
            <label className="block text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
              Preset
            </label>
            <div className="mt-1.5 grid grid-cols-2 gap-2">
              {AI_PRESETS.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => applyPreset(item.id)}
                  data-testid={`ai-preset-${item.id}`}
                  className={`rounded-md border px-3 py-2 text-left text-xs transition-colors ${
                    preset === item.id
                      ? "border-accent/50 bg-accent/10 text-foreground"
                      : "border-input bg-background hover:bg-muted"
                  }`}
                >
                  <span className="block font-semibold">{item.label}</span>
                  <span className="mt-0.5 block text-[11px] text-muted-foreground">
                    {item.description}
                  </span>
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
              Provider
            </label>
            <div className="mt-1.5 grid grid-cols-3 gap-2">
              {(["local", "gemini", "openai"] as AiProvider[]).map((item) => (
                <button
                  key={item}
                  type="button"
                  onClick={() => {
                    setProvider(item);
                    setModel(defaultModel(item));
                    setCustomModel("");
                    if (item === "local") {
                      setPreset("local_safe");
                      setToggles(localAiToggles());
                    } else if (preset === "local_safe") {
                      setPreset("basic");
                      setToggles(basicAiToggles());
                    }
                  }}
                  data-testid={`ai-provider-${item}`}
                  className={`rounded-md border px-3 py-2 text-xs font-medium transition-colors ${
                    provider === item
                      ? "border-accent/50 bg-accent/10 text-foreground"
                      : "border-input bg-background hover:bg-muted"
                  }`}
                >
                  {providerLabel(item)}
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
                  data-testid="ai-api-key-input"
                  placeholder={
                    providerAllowsKey
                      ? `Cole a chave ${providerLabel(provider)} para salvar no backend`
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
              Após salvar, a chave nunca é exibida novamente. Use variáveis de ambiente para testes
              reais locais.
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              <ProviderKeyLink provider="gemini" />
              <ProviderKeyLink provider="openai" />
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
              Modelo
            </label>
            <div className="mt-1.5 flex gap-2">
              <select
                value={model}
                onChange={(event) => {
                  setModel(event.target.value);
                  setCustomModel("");
                }}
                disabled={provider === "local"}
                data-testid="ai-model-select"
                className="min-w-0 flex-1 rounded-md border border-input bg-background px-3 py-2 font-mono text-xs outline-none focus:border-accent/50 focus:ring-2 focus:ring-accent/20 disabled:opacity-50"
              >
                {(modelOptions.length
                  ? modelOptions
                  : [{ id: defaultModel(provider), label: defaultModel(provider) }]
                ).map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.label || item.id}
                  </option>
                ))}
              </select>
              <button
                type="button"
                onClick={() => refreshModels.mutate()}
                disabled={busy || provider === "local"}
                data-testid="ai-refresh-models"
                className="inline-flex items-center gap-1.5 rounded-md border border-input bg-background px-3 py-2 text-xs font-medium hover:bg-muted disabled:opacity-50"
              >
                <RefreshCw
                  className={`h-3.5 w-3.5 ${refreshModels.isPending ? "animate-spin" : ""}`}
                />
                Atualizar modelos
              </button>
            </div>
            <details className="mt-2 rounded-md border border-border bg-muted/30 p-2 text-xs">
              <summary className="cursor-pointer font-medium">Modelo customizado avançado</summary>
              <input
                value={customModel}
                onChange={(event) => setCustomModel(event.target.value)}
                disabled={provider === "local"}
                data-testid="ai-custom-model"
                placeholder="Ex.: modelo customizado do provider"
                className="mt-2 w-full rounded-md border border-input bg-background px-3 py-2 font-mono text-xs outline-none focus:border-accent/50 focus:ring-2 focus:ring-accent/20 disabled:opacity-50"
              />
            </details>
            <p className="mt-1.5 text-[11px] text-muted-foreground">
              Atual: {selectedModel}. Fonte do catálogo: {modelsQ.data?.source || "builtin"}.
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => testMutation.mutate()}
              disabled={busy}
              className="inline-flex items-center gap-1.5 rounded-md border border-input bg-background px-3 py-1.5 text-xs font-medium hover:bg-muted disabled:opacity-50"
            >
              {testMutation.isPending && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
              Testar conexão
            </button>
            <button
              type="button"
              onClick={() => saveMutation.mutate()}
              disabled={busy}
              className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
            >
              {saveMutation.isPending && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
              Salvar no backend local
            </button>
            <button
              type="button"
              onClick={() => deleteMutation.mutate()}
              disabled={busy}
              className="inline-flex items-center gap-1.5 rounded-md border border-destructive/30 bg-destructive/5 px-3 py-1.5 text-xs font-medium text-destructive hover:bg-destructive/10"
            >
              <Trash2 className="h-3.5 w-3.5" /> Remover chave
            </button>
            <StatusPill status={status} />
          </div>
          <p className="rounded-md border border-border bg-muted/30 p-2 text-[11px] text-muted-foreground">
            Provider atual: {providerLabel(provider)} · Modelo: {selectedModel} · IA{" "}
            {toggles.enabled ? "ligada" : "desligada"} · Chave{" "}
            {settingsQ.data?.configured ? "salva no backend local" : "não configurada"}.
            {selectedProviderInfo?.status ? ` Status: ${selectedProviderInfo.status}.` : ""}
          </p>
          <p className="rounded-md border border-border bg-muted/30 p-2 text-[11px] text-muted-foreground">
            {aiStatusMessage(status, provider)}
          </p>
          {[...(settingsQ.data?.warnings ?? []), ...(modelsQ.data?.warnings ?? [])].map(
            (warning) => (
              <p key={warning} className="rounded-md bg-warning/10 p-2 text-[11px] text-warning">
                {warning}
              </p>
            ),
          )}
        </div>

        <div className="space-y-3">
          <Toggle
            label="Usar IA nos fluxos permitidos"
            checked={toggles.enabled}
            onChange={(value) => {
              setPreset("custom");
              setToggles({ ...toggles, enabled: value });
            }}
          />
          <div className="rounded-lg border border-border bg-muted/30 p-3 text-xs">
            <div className="font-semibold text-foreground">Fluxos usando IA</div>
            <p className="mt-1 text-muted-foreground">{enabledFlowSummary(toggles)}</p>
          </div>
          <details
            className="rounded-lg border border-border bg-card p-3 text-xs"
            open={preset === "custom"}
          >
            <summary className="cursor-pointer font-semibold text-foreground">
              Avançado: permissões por grupo
            </summary>
            <div className="mt-3 space-y-3">
              <ToggleGroup title="Documentos e Perfil">
                <Toggle
                  label="Currículo"
                  checked={toggles.resume}
                  onChange={(value) => setToggles({ ...toggles, resume: value })}
                  disabled={!toggles.enabled}
                />
                <Toggle
                  label="Lattes"
                  checked={toggles.lattes}
                  onChange={(value) => setToggles({ ...toggles, lattes: value })}
                  disabled={!toggles.enabled}
                />
                <Toggle
                  label="Perfil Universal"
                  checked={toggles.profile}
                  onChange={(value) => setToggles({ ...toggles, profile: value })}
                  disabled={!toggles.enabled}
                />
              </ToggleGroup>
              <ToggleGroup title="Oportunidades">
                <Toggle
                  label="Vagas"
                  checked={toggles.job}
                  onChange={(value) => setToggles({ ...toggles, job: value })}
                  disabled={!toggles.enabled}
                />
                <Toggle
                  label="Editais / Concursos"
                  checked={toggles.publicExams}
                  onChange={(value) => setToggles({ ...toggles, publicExams: value })}
                  disabled={!toggles.enabled}
                />
                <Toggle
                  label="Fontes / Extensão"
                  checked={toggles.sourceImport && toggles.extension}
                  onChange={(value) =>
                    setToggles({ ...toggles, sourceImport: value, extension: value })
                  }
                  disabled={!toggles.enabled}
                />
              </ToggleGroup>
              <ToggleGroup title="Análises">
                <Toggle
                  label="Match"
                  checked={toggles.match}
                  onChange={(value) => setToggles({ ...toggles, match: value })}
                  disabled={!toggles.enabled}
                />
                <Toggle
                  label="ATS"
                  checked={toggles.ats}
                  onChange={(value) => setToggles({ ...toggles, ats: value })}
                  disabled={!toggles.enabled}
                />
                <Toggle
                  label="Tailor"
                  checked={toggles.tailor}
                  onChange={(value) => setToggles({ ...toggles, tailor: value })}
                  disabled={!toggles.enabled}
                />
                <Toggle
                  label="GitHub / Portfólio"
                  checked={toggles.github}
                  onChange={(value) => setToggles({ ...toggles, github: value })}
                  disabled={!toggles.enabled}
                />
              </ToggleGroup>
              <ToggleGroup title="Radar e Memória">
                <Toggle
                  label="Radar / Wishlist"
                  checked={toggles.radar}
                  onChange={(value) => setToggles({ ...toggles, radar: value })}
                  disabled={!toggles.enabled}
                />
                <Toggle
                  label="Notificações"
                  checked={toggles.notifications}
                  onChange={(value) => setToggles({ ...toggles, notifications: value })}
                  disabled={!toggles.enabled}
                />
                <Toggle
                  label="Contexto da memória local"
                  hint="Desligado por padrão"
                  checked={toggles.memory}
                  onChange={(value) => setToggles({ ...toggles, memory: value })}
                  disabled={!toggles.enabled}
                />
              </ToggleGroup>
            </div>
          </details>
          <div className="mt-2 flex items-start gap-2 rounded-lg border border-warning/30 bg-warning/5 p-3 text-xs">
            <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-warning" />
            <p className="text-muted-foreground">
              A chave de IA nunca é salva no frontend, localStorage ou sessionStorage. O backend
              local executa Gemini/OpenAI e usa fallback local quando necessário.
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
              <li>GET /api/v1/settings/ai/providers</li>
              <li>GET /api/v1/settings/ai/models</li>
              <li>POST /api/v1/settings/ai/models/refresh</li>
            </ul>
          </details>
        </div>
      </div>
    </SectionCard>
  );
}

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
    resume: true,
    job: true,
    match: true,
    ats: true,
    tailor: true,
    github: true,
    sourceImport: true,
    radar: true,
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
      resume: data.allow_resume,
      job: data.allow_job,
      match: data.allow_match,
      ats: data.allow_ats,
      tailor: data.allow_tailor,
      github: data.allow_github,
      sourceImport: data.allow_source_import,
      radar: data.allow_radar,
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
        allow_resume: toggles.resume,
        allow_job: toggles.job,
        allow_match: toggles.match,
        allow_ats: toggles.ats,
        allow_tailor: toggles.tailor,
        allow_github: toggles.github,
        allow_source_import: toggles.sourceImport,
        allow_radar: toggles.radar,
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

  const providerAllowsKey = provider === "gemini" || provider === "openai";
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
              {(["local", "gemini", "openai"] as AiProvider[]).map((p) => (
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
                  data-testid="ai-api-key-input"
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
          <p className="rounded-md border border-border bg-muted/30 p-2 text-[11px] text-muted-foreground">
            {aiStatusMessage(status, provider)}
          </p>
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
            label="Permitir IA em Currículo"
            checked={toggles.resume}
            onChange={(v) => setToggles({ ...toggles, resume: v })}
            disabled={!toggles.enabled}
          />
          <Toggle
            label="Permitir IA em Vaga"
            checked={toggles.job}
            onChange={(v) => setToggles({ ...toggles, job: v })}
            disabled={!toggles.enabled}
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
            label="Permitir IA na Caixa de Entrada e importações"
            checked={toggles.sourceImport}
            onChange={(v) => setToggles({ ...toggles, sourceImport: v })}
            disabled={!toggles.enabled}
          />
          <Toggle
            label="Permitir IA no Radar e Wishlist"
            checked={toggles.radar}
            onChange={(v) => setToggles({ ...toggles, radar: v })}
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

function ToggleGroup({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="space-y-2 rounded-lg border border-border bg-muted/20 p-2">
      <div className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
        {title}
      </div>
      {children}
    </div>
  );
}

function ProviderKeyLink({ provider }: { provider: "gemini" | "openai" }) {
  const href =
    provider === "gemini"
      ? "https://aistudio.google.com/app/apikey"
      : "https://platform.openai.com/api-keys";
  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      data-testid={`ai-key-link-${provider}`}
      className="inline-flex items-center gap-1.5 rounded-md border border-input bg-background px-2.5 py-1 text-[11px] font-medium hover:bg-muted"
    >
      <ExternalLink className="h-3 w-3" />
      Obter chave {provider === "gemini" ? "Gemini" : "OpenAI"}
    </a>
  );
}

function localAiToggles(): AiToggleState {
  return {
    enabled: false,
    profile: false,
    lattes: false,
    resume: false,
    job: false,
    publicExams: false,
    match: false,
    ats: false,
    tailor: false,
    github: false,
    sourceImport: false,
    extension: false,
    radar: false,
    notifications: false,
    memory: false,
  };
}

function basicAiToggles(): AiToggleState {
  return {
    ...localAiToggles(),
    enabled: true,
    profile: true,
    lattes: true,
    resume: true,
    job: true,
    publicExams: true,
    match: true,
    ats: true,
    tailor: true,
  };
}

function completeAiToggles(): AiToggleState {
  return {
    ...basicAiToggles(),
    github: true,
    sourceImport: true,
    extension: true,
    radar: true,
    notifications: true,
    memory: false,
  };
}

function enabledFlowSummary(toggles: AiToggleState): string {
  if (!toggles.enabled) return "IA desligada. Todos os fluxos usam fallback local.";
  const flows = [
    toggles.resume && "Currículo",
    toggles.lattes && "Lattes",
    toggles.profile && "Perfil Universal",
    toggles.job && "Vagas",
    toggles.publicExams && "Editais/Concursos",
    toggles.match && "Match",
    toggles.ats && "ATS",
    toggles.tailor && "Tailor",
    toggles.github && "GitHub/Portfólio",
    toggles.sourceImport && "Fontes",
    toggles.extension && "Extensão",
    toggles.radar && "Radar/Wishlist",
    toggles.notifications && "Notificações",
  ].filter(Boolean);
  return flows.length ? flows.join(", ") : "IA ligada, mas nenhum fluxo avançado está permitido.";
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
  if (provider === "openai" || provider === "openai_future") return "OpenAI";
  if (provider === "gemini") return "Gemini";
  return "Local";
}

function defaultModel(provider: AiProvider): string {
  if (provider === "local") return "local";
  if (provider === "gemini") return "gemini-2.5-flash";
  return "gpt-5-mini";
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

function aiStatusMessage(status: AiUiStatus, provider: AiProvider): string {
  if (status === "testing") return "Analisando com IA: teste em andamento com timeout curto.";
  if (provider === "local") return "Provider local: regras internas, sem chave externa.";
  if (status === "configured")
    return "Provider configurado: a chave fica somente no backend local.";
  if (status === "planned")
    return "Provider legado detectado; use Gemini ou OpenAI no backend local.";
  if (status === "error") {
    return "Limite, timeout, chave invalida ou erro do provider: use fallback local e revise a configuracao.";
  }
  return "Provider nao configurado. Configure uma chave em Configuracoes -> IA e Providers.";
}

function Item({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-border bg-muted/30 px-3 py-2">
      <span className="text-xs text-muted-foreground">{k}</span>
      <span className="font-mono text-xs">{v}</span>
    </div>
  );
}
