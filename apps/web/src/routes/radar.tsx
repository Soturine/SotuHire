import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertCircle,
  Bell,
  CheckCircle2,
  Database,
  ExternalLink,
  FileSearch,
  Filter,
  Inbox,
  Loader2,
  Play,
  Plus,
  RadioTower,
  Save,
  Search,
  ShieldCheck,
  Sparkles,
  Target,
  WandSparkles,
  type LucideIcon,
} from "lucide-react";
import type { ReactNode } from "react";
import { useMemo, useState } from "react";
import { toast } from "sonner";
import { AppShell } from "@/components/app-shell";
import { SectionCard } from "@/components/section-card";
import { StatCard } from "@/components/stat-card";
import { EmptyState, ErrorState, LoadingState } from "@/components/states";
import { useApi } from "@/lib/api/hooks";
import { useApiMode } from "@/lib/api/mode";
import type {
  JobWishlist,
  RadarAlert,
  RadarResult,
  RadarSource,
  WishlistDraftResult,
} from "@/lib/api/types";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/radar")({
  head: () => ({
    meta: [
      { title: "Radar de Vagas - SotuHire" },
      {
        name: "description",
        content:
          "Radar local-first para fontes públicas, feeds RSS e alertas de vagas alinhadas à wishlist.",
      },
    ],
  }),
  component: RadarPage,
});

function RadarPage() {
  const api = useApi();
  const { mode, baseUrl } = useApiMode();
  const qc = useQueryClient();
  const [lastRunResults, setLastRunResults] = useState<RadarResult[]>([]);
  const [lastRunAlerts, setLastRunAlerts] = useState<RadarAlert[]>([]);
  const [wishlistName, setWishlistName] = useState("Busca profissional revisada");
  const [targetTitles, setTargetTitles] = useState(
    "Estágio em Engenharia, Analista Júnior, Assistente Técnico",
  );
  const [targetDomains, setTargetDomains] = useState("Engenharia, Operações, Dados");
  const [targetSeniority, setTargetSeniority] = useState("estágio, júnior");
  const [requiredSkills, setRequiredSkills] = useState("Excel, relatórios técnicos, qualidade");
  const [desiredSkills, setDesiredSkills] = useState("Python, Power BI, comunicação");
  const [excludedTerms, setExcludedTerms] = useState("PJ");
  const [locations, setLocations] = useState("Remoto, Brasil");
  const [minScore, setMinScore] = useState(70);
  const [minAtsScore, setMinAtsScore] = useState(60);
  const [wishlistNotes, setWishlistNotes] = useState(
    "Revise esta wishlist antes de rodar o Radar.",
  );
  const [aiWishlistText, setAiWishlistText] = useState(
    "Sou estudante de engenharia e quero estágio ou vaga júnior em operações, qualidade ou dados. Tenho Excel, relatórios técnicos e interesse em Power BI. Prefiro remoto ou híbrido e não quero PJ.",
  );
  const [useProfileContext, setUseProfileContext] = useState(true);
  const [useAiForRadar, setUseAiForRadar] = useState(false);
  const [draft, setDraft] = useState<WishlistDraftResult | null>(null);
  const [sourceName, setSourceName] = useState("Feed publico ficticio");
  const [sourceUrl, setSourceUrl] = useState("https://example.com/jobs.xml");
  const [sourceFilter, setSourceFilter] = useState("all");

  const wishlistsQ = useQuery({
    queryKey: ["radar-wishlists", mode, baseUrl],
    queryFn: () => api.radarWishlists(),
    retry: false,
  });
  const sourcesQ = useQuery({
    queryKey: ["radar-sources", mode, baseUrl],
    queryFn: () => api.radarSources(),
    retry: false,
  });
  const resultsQ = useQuery({
    queryKey: ["radar-results", mode, baseUrl],
    queryFn: () => api.radarResults(),
    retry: false,
  });
  const alertsQ = useQuery({
    queryKey: ["radar-alerts", mode, baseUrl],
    queryFn: () => api.radarAlerts(),
    retry: false,
  });
  const statsQ = useQuery({
    queryKey: ["radar-stats", mode, baseUrl],
    queryFn: () => api.radarStats(),
    retry: false,
  });
  const runsQ = useQuery({
    queryKey: ["radar-runs", mode, baseUrl],
    queryFn: () => api.radarRuns(),
    retry: false,
  });

  const activeWishlist = wishlistsQ.data?.wishlists.find((item) => item.is_active);
  const activeSources = sourcesQ.data?.sources.filter((item) => item.is_active) ?? [];
  const shownResults = (
    lastRunResults.length ? lastRunResults : (resultsQ.data?.results ?? [])
  ).filter((result) => sourceFilter === "all" || result.source_type === sourceFilter);
  const shownAlerts = lastRunAlerts.length ? lastRunAlerts : (alertsQ.data?.alerts ?? []);

  const invalidateRadar = () => {
    qc.invalidateQueries({ queryKey: ["radar-wishlists"] });
    qc.invalidateQueries({ queryKey: ["radar-sources"] });
    qc.invalidateQueries({ queryKey: ["radar-results"] });
    qc.invalidateQueries({ queryKey: ["radar-alerts"] });
    qc.invalidateQueries({ queryKey: ["radar-stats"] });
    qc.invalidateQueries({ queryKey: ["radar-runs"] });
  };

  function applyDraftToForm(data: WishlistDraftResult) {
    const wishlist = data.wishlist;
    setWishlistName(wishlist.name);
    setTargetTitles(wishlist.target_titles.join(", "));
    setTargetDomains(wishlist.target_domains.join(", "));
    setTargetSeniority(wishlist.target_seniority.join(", "));
    setRequiredSkills(wishlist.required_skills.join(", "));
    setDesiredSkills(wishlist.desired_skills.join(", "));
    setExcludedTerms(wishlist.excluded_terms.join(", "));
    setLocations(wishlist.locations.join(", "));
    setMinScore(wishlist.min_match_score);
    setMinAtsScore(wishlist.min_ats_score);
    setWishlistNotes(wishlist.notes || "Rascunho revisado manualmente antes de salvar.");
  }

  const createWishlist = useMutation({
    mutationFn: () =>
      api.radarCreateWishlist({
        name: wishlistName,
        target_titles: splitList(targetTitles),
        target_domains: splitList(targetDomains),
        target_seniority: splitList(targetSeniority),
        required_skills: splitList(requiredSkills),
        desired_skills: splitList(desiredSkills),
        excluded_terms: splitList(excludedTerms),
        locations: splitList(locations),
        remote_preferences: splitList(locations).some((item) => /remoto/i.test(item))
          ? ["remoto"]
          : [],
        min_match_score: minScore,
        min_ats_score: minAtsScore,
        notify_on_new_matches: true,
        notes: wishlistNotes,
        is_active: true,
      }),
    onSuccess: (data) => {
      toast.success(data.message || "Wishlist criada.");
      invalidateRadar();
    },
    onError: (error) =>
      toast.error(error instanceof Error ? error.message : "Falha ao criar wishlist."),
  });

  const draftWishlist = useMutation({
    mutationFn: () =>
      api.radarDraftWishlist({
        free_text: aiWishlistText,
        use_profile_context: useProfileContext,
        language: "pt-BR",
      }),
    onSuccess: (data) => {
      setDraft(data);
      applyDraftToForm(data);
      toast.success("Rascunho de wishlist gerado. Revise antes de salvar.");
    },
    onError: (error) =>
      toast.error(error instanceof Error ? error.message : "Falha ao gerar rascunho."),
  });

  const createSource = useMutation({
    mutationFn: () =>
      api.radarCreateSource({
        name: sourceName,
        source_type: "public_feed",
        url: sourceUrl,
        status: "available",
        max_results: 20,
        timeout_seconds: 6,
        rate_limit_seconds: 1,
        is_active: true,
      }),
    onSuccess: (data) => {
      toast.success(data.message || "Fonte criada.");
      invalidateRadar();
    },
    onError: (error) =>
      toast.error(error instanceof Error ? error.message : "Falha ao criar fonte."),
  });

  const runRadar = useMutation({
    mutationFn: () =>
      api.radarRun({
        wishlist_id: activeWishlist?.id,
        source_ids: activeSources.map((item) => item.id),
        keywords: activeWishlist ? [] : splitList(targetTitles),
        use_ai: useAiForRadar,
      }),
    onSuccess: (data) => {
      setLastRunResults(data.results);
      setLastRunAlerts(data.alerts);
      toast.success(data.message || "Radar concluido.");
      invalidateRadar();
    },
    onError: (error) =>
      toast.error(error instanceof Error ? error.message : "Falha ao rodar radar."),
  });
  const canRunRadar = activeSources.length > 0 && !runRadar.isPending;

  const saveInbox = useMutation({
    mutationFn: (id: string) => api.radarSaveInbox(id),
    onSuccess: (data) => {
      toast.success(data.message || "Salvo na Caixa de Entrada.");
      invalidateRadar();
    },
    onError: (error) =>
      toast.error(error instanceof Error ? error.message : "Nao foi possivel salvar."),
  });

  const saveTracker = useMutation({
    mutationFn: (id: string) => api.radarSaveTracker(id),
    onSuccess: (data) => {
      toast.success(data.message || "Salvo em Candidaturas.");
      invalidateRadar();
    },
    onError: (error) =>
      toast.error(error instanceof Error ? error.message : "Nao foi possivel salvar no tracker."),
  });

  const patchResult = useMutation({
    mutationFn: ({ id, status }: { id: string; status: RadarResult["radar_status"] }) =>
      api.radarPatchResult(id, { status }),
    onSuccess: (data) => {
      toast.success(data.message || "Resultado atualizado.");
      invalidateRadar();
    },
    onError: (error) =>
      toast.error(error instanceof Error ? error.message : "Falha ao atualizar resultado."),
  });

  const markAlertRead = useMutation({
    mutationFn: (id: string) => api.radarPatchAlert(id, { status: "read" }),
    onSuccess: (data) => {
      toast.success(data.message || "Alerta marcado como lido.");
      invalidateRadar();
    },
    onError: (error) =>
      toast.error(error instanceof Error ? error.message : "Falha ao atualizar alerta."),
  });

  const hasRealEmpty =
    mode === "real" &&
    !wishlistsQ.isLoading &&
    !sourcesQ.isLoading &&
    !resultsQ.isLoading &&
    (wishlistsQ.data?.wishlists.length ?? 0) === 0 &&
    (sourcesQ.data?.sources.length ?? 0) === 0 &&
    (resultsQ.data?.results.length ?? 0) === 0;

  return (
    <AppShell
      title="Radar de Vagas"
      description="Monitore fontes públicas e feeds permitidos, compare com sua wishlist e revise tudo manualmente."
      actions={
        <button
          onClick={() => runRadar.mutate()}
          disabled={!canRunRadar}
          data-testid="radar-run-now"
          title={activeSources.length ? "Rodar fontes ativas" : "Adicione uma fonte ativa antes"}
          className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:opacity-90 disabled:opacity-60"
        >
          {runRadar.isPending ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <Play className="h-3.5 w-3.5" />
          )}
          Rodar radar agora
        </button>
      }
    >
      <div className="space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border bg-card p-4">
          <div className="flex items-start gap-3">
            <div className="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-accent/15 text-accent">
              <RadioTower className="h-5 w-5" />
            </div>
            <div>
              <div className="font-semibold">Radar local-first com revisão manual</div>
              <p className="mt-1 max-w-3xl text-xs leading-relaxed text-muted-foreground">
                O Radar consulta somente fontes configuradas por você, como RSS público ou páginas
                públicas simples. APIs oficiais ficam preparadas por adapter e nada vai para
                Candidaturas sem sua ação.
              </p>
            </div>
          </div>
          {mode === "demo" && (
            <span
              data-testid="radar-demo-badge"
              className="rounded-full bg-warning/15 px-3 py-1 text-[11px] font-semibold text-warning"
            >
              Dados de demonstração
            </span>
          )}
        </div>

        {hasRealEmpty && (
          <div
            data-testid="radar-real-empty"
            className="rounded-xl border border-dashed border-border bg-muted/30 p-5 text-sm text-muted-foreground"
          >
            API Real sem Radar configurado. Crie uma wishlist, adicione uma fonte RSS pública e rode
            a busca manualmente.
          </div>
        )}

        {!sourcesQ.isLoading && activeSources.length === 0 && (
          <div className="rounded-xl border border-warning/30 bg-warning/5 p-4 text-sm text-muted-foreground">
            Adicione uma fonte ativa antes de rodar o Radar. Fontes RSS públicas e páginas públicas
            simples sempre ficam sob revisão manual.
          </div>
        )}

        <section
          id="radar-summary"
          data-testid="radar-summary"
          className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"
        >
          <StatCard
            label="Fontes ativas"
            value={statsQ.data?.active_sources ?? 0}
            icon={RadioTower}
          />
          <StatCard
            label="Resultados"
            value={statsQ.data?.total_results ?? 0}
            icon={FileSearch}
            tone="accent"
          />
          <StatCard
            label="Alertas novos"
            value={
              statsQ.data?.unread_alerts ?? shownAlerts.filter((a) => a.status === "unread").length
            }
            icon={Bell}
            tone="warning"
          />
          <StatCard label="Duplicatas" value={statsQ.data?.duplicates ?? 0} icon={Filter} />
        </section>

        <SectionCard
          id="radar-ai-wishlist"
          title={
            <span className="flex items-center gap-2">
              <WandSparkles className="h-4 w-4 text-accent" />
              Criar wishlist com IA
            </span>
          }
          description="Transforme um pedido em texto livre em um rascunho editável. Nada é salvo automaticamente."
        >
          <div className="grid gap-4 lg:grid-cols-[1fr_0.9fr]">
            <div className="space-y-3">
              <label className="text-xs font-medium">
                O que você está procurando?
                <textarea
                  value={aiWishlistText}
                  onChange={(event) => setAiWishlistText(event.target.value)}
                  data-testid="radar-wishlist-ai-text"
                  className="mt-1 min-h-28 w-full rounded-md border border-input bg-card px-3 py-2 text-sm outline-none focus:border-accent/50 focus:ring-2 focus:ring-accent/20"
                />
              </label>
              <label className="flex items-start gap-2 rounded-lg border border-border bg-muted/30 p-3 text-xs text-muted-foreground">
                <input
                  type="checkbox"
                  checked={useProfileContext}
                  onChange={(event) => setUseProfileContext(event.target.checked)}
                  data-testid="radar-wishlist-profile-context"
                  className="mt-0.5"
                />
                Usar contexto local do perfil quando existir. O contexto continua local e serve só
                para sugerir campos editáveis.
              </label>
              <div className="flex flex-wrap items-center gap-2">
                <button
                  onClick={() => draftWishlist.mutate()}
                  disabled={draftWishlist.isPending || !aiWishlistText.trim()}
                  data-testid="radar-generate-wishlist-draft"
                  className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-2 text-xs font-medium text-primary-foreground hover:opacity-90 disabled:opacity-60"
                >
                  {draftWishlist.isPending ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Sparkles className="h-3.5 w-3.5" />
                  )}
                  Gerar sugestão
                </button>
                {draft && (
                  <Badge
                    tone={
                      draft.analysis_mode === "ai"
                        ? "success"
                        : draft.analysis_mode === "fallback"
                          ? "warning"
                          : "muted"
                    }
                  >
                    <span data-testid="radar-draft-mode-badge">
                      {draft.analysis_mode === "ai"
                        ? "IA"
                        : draft.analysis_mode === "fallback"
                          ? "Fallback local"
                          : "Local"}
                    </span>
                  </Badge>
                )}
              </div>
            </div>

            <div className="space-y-3">
              {draft ? (
                <>
                  <div className="rounded-lg border border-border bg-muted/30 p-3">
                    <div className="flex items-center justify-between gap-2">
                      <div>
                        <div className="text-sm font-semibold">{draft.wishlist.name}</div>
                        <div className="text-xs text-muted-foreground">
                          Confiança {Math.round(draft.confidence * 100)}% · revisão humana
                          obrigatória
                        </div>
                      </div>
                      <button
                        onClick={() => applyDraftToForm(draft)}
                        data-testid="radar-apply-wishlist-draft"
                        className="rounded-md border border-input bg-card px-2.5 py-1.5 text-xs font-medium hover:bg-muted"
                      >
                        Preencher formulário
                      </button>
                    </div>
                    <div className="mt-3 space-y-2">
                      <MiniList title="Suposições" items={draft.assumptions} />
                      <MiniList
                        title="Perguntas para confirmar"
                        items={draft.questions_to_confirm}
                      />
                      <MiniList title="Avisos" items={draft.warnings} />
                    </div>
                  </div>
                </>
              ) : (
                <div className="rounded-lg border border-dashed border-border bg-muted/30 p-4 text-sm text-muted-foreground">
                  Descreva cargos, áreas, habilidades, locais e termos que quer evitar. O SotuHire
                  gera um rascunho e você decide o que salvar.
                </div>
              )}
            </div>
          </div>
        </SectionCard>

        <div className="grid gap-6 xl:grid-cols-3">
          <SectionCard
            id="radar-wishlist"
            title={
              <span className="flex items-center gap-2">
                <Target className="h-4 w-4 text-accent" />
                Wishlist
              </span>
            }
            description="Defina o pedido de vaga que deve gerar alerta."
            className="xl:col-span-2"
          >
            {wishlistsQ.isError ? (
              <ErrorState error={wishlistsQ.error} onRetry={() => wishlistsQ.refetch()} />
            ) : (
              <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
                <div className="space-y-3">
                  <TextField label="Nome" value={wishlistName} onChange={setWishlistName} />
                  <TextField
                    label="Cargos aceitos"
                    value={targetTitles}
                    onChange={setTargetTitles}
                  />
                  <div className="grid gap-3 sm:grid-cols-2">
                    <TextField
                      label="Domínios/áreas"
                      value={targetDomains}
                      onChange={setTargetDomains}
                    />
                    <TextField
                      label="Senioridade"
                      value={targetSeniority}
                      onChange={setTargetSeniority}
                    />
                  </div>
                  <TextField
                    label="Skills obrigatórias"
                    value={requiredSkills}
                    onChange={setRequiredSkills}
                  />
                  <TextField
                    label="Skills desejáveis"
                    value={desiredSkills}
                    onChange={setDesiredSkills}
                  />
                  <TextField
                    label="Termos a evitar"
                    value={excludedTerms}
                    onChange={setExcludedTerms}
                  />
                  <div className="grid gap-3 sm:grid-cols-[1fr_120px_120px]">
                    <TextField
                      label="Locais/modelos aceitos"
                      value={locations}
                      onChange={setLocations}
                    />
                    <label className="text-xs font-medium">
                      Score mínimo
                      <input
                        value={minScore}
                        onChange={(event) => setMinScore(Number(event.target.value) || 0)}
                        type="number"
                        min={0}
                        max={100}
                        className="mt-1 h-9 w-full rounded-md border border-input bg-card px-3 text-sm outline-none focus:border-accent/50 focus:ring-2 focus:ring-accent/20"
                      />
                    </label>
                    <label className="text-xs font-medium">
                      ATS mínimo
                      <input
                        value={minAtsScore}
                        onChange={(event) => setMinAtsScore(Number(event.target.value) || 0)}
                        type="number"
                        min={0}
                        max={100}
                        className="mt-1 h-9 w-full rounded-md border border-input bg-card px-3 text-sm outline-none focus:border-accent/50 focus:ring-2 focus:ring-accent/20"
                      />
                    </label>
                  </div>
                  <TextField label="Notas" value={wishlistNotes} onChange={setWishlistNotes} />
                  <button
                    onClick={() => createWishlist.mutate()}
                    disabled={createWishlist.isPending}
                    data-testid="radar-create-wishlist"
                    className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-2 text-xs font-medium text-primary-foreground hover:opacity-90 disabled:opacity-60"
                  >
                    <Plus className="h-3.5 w-3.5" /> Salvar wishlist
                  </button>
                </div>
                <div className="rounded-lg border border-border bg-muted/30 p-3">
                  <h3 className="text-sm font-semibold">Wishlist ativa</h3>
                  {wishlistsQ.isLoading ? (
                    <LoadingState />
                  ) : activeWishlist ? (
                    <WishlistCard wishlist={activeWishlist} />
                  ) : (
                    <p className="mt-2 text-sm text-muted-foreground">
                      Nenhuma wishlist ativa. O Radar pode rodar com palavras-chave rápidas, mas os
                      alertas ficam melhores com uma wishlist salva.
                    </p>
                  )}
                </div>
              </div>
            )}
          </SectionCard>

          <SectionCard
            id="radar-alerts"
            title={
              <span className="flex items-center gap-2">
                <Bell className="h-4 w-4 text-accent" />
                Alertas
              </span>
            }
            description="Avisos locais gerados por score e erros de fonte."
          >
            <div className="space-y-3" data-testid="radar-alerts-panel">
              {alertsQ.isLoading && !shownAlerts.length ? (
                <LoadingState />
              ) : shownAlerts.length ? (
                shownAlerts.map((alert) => (
                  <div key={alert.id} className="rounded-lg border border-border bg-muted/30 p-3">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="text-sm font-semibold">{alert.title}</div>
                        <p className="mt-1 text-xs text-muted-foreground">{alert.message}</p>
                      </div>
                      <ScoreBadge value={alert.score} />
                    </div>
                    <button
                      onClick={() => markAlertRead.mutate(alert.id)}
                      data-testid="radar-mark-alert-read"
                      className="mt-3 inline-flex items-center gap-1 rounded-md border border-input bg-card px-2.5 py-1.5 text-[11px] font-medium hover:bg-muted"
                    >
                      <CheckCircle2 className="h-3 w-3" /> Marcar como lido
                    </button>
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">
                  Nenhum alerta ainda. Rode o Radar depois de configurar wishlist e fonte.
                </p>
              )}
            </div>
          </SectionCard>
        </div>

        <SectionCard
          id="radar-sources"
          title={
            <span className="flex items-center gap-2">
              <RadioTower className="h-4 w-4 text-accent" />
              Fontes do Radar
            </span>
          }
          description="Adicione feeds públicos ou registre APIs oficiais planejadas. Nada roda em massa nem tenta login."
        >
          <div className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
            <div className="space-y-3">
              <TextField label="Nome da fonte RSS" value={sourceName} onChange={setSourceName} />
              <TextField label="URL do feed público" value={sourceUrl} onChange={setSourceUrl} />
              <button
                onClick={() => createSource.mutate()}
                disabled={createSource.isPending}
                data-testid="radar-create-source"
                className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-2 text-xs font-medium text-primary-foreground hover:opacity-90 disabled:opacity-60"
              >
                <Plus className="h-3.5 w-3.5" /> Adicionar RSS
              </button>
              <div className="rounded-lg border border-warning/30 bg-warning/5 p-3 text-xs text-muted-foreground">
                APIs oficiais aparecem como estrutura planejada: exigem contrato documentado e chave
                armazenada somente no backend local quando aplicável.
              </div>
            </div>
            <div className="grid gap-3 md:grid-cols-2" data-testid="radar-sources-panel">
              {(sourcesQ.data?.sources ?? []).map((source) => (
                <SourceBox key={source.id} source={source} />
              ))}
              {!sourcesQ.isLoading && !(sourcesQ.data?.sources.length ?? 0) && (
                <div className="rounded-lg border border-dashed border-border p-4 text-sm text-muted-foreground">
                  Nenhuma fonte cadastrada. Adicione um RSS público para começar.
                </div>
              )}
            </div>
          </div>
        </SectionCard>

        <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
          <SectionCard
            id="radar-results"
            title={
              <span className="flex items-center gap-2">
                <Search className="h-4 w-4 text-accent" />
                Resultados do Radar
              </span>
            }
            description="Revise evidências, lacunas e origem antes de salvar."
            actions={
              <select
                value={sourceFilter}
                onChange={(event) => setSourceFilter(event.target.value)}
                data-testid="radar-source-filter"
                className="h-8 rounded-md border border-input bg-card px-2 text-xs outline-none"
              >
                <option value="all">Todas as fontes</option>
                <option value="public_feed">RSS</option>
                <option value="official_api">API oficial</option>
                <option value="manual_public_page">Página pública</option>
              </select>
            }
          >
            {resultsQ.isLoading && !shownResults.length ? (
              <LoadingState />
            ) : resultsQ.isError ? (
              <ErrorState error={resultsQ.error} onRetry={() => resultsQ.refetch()} />
            ) : shownResults.length ? (
              <div className="space-y-3" data-testid="radar-results-panel">
                {shownResults.map((result) => (
                  <ResultCard
                    key={result.id}
                    result={result}
                    onSaveInbox={() => saveInbox.mutate(result.id)}
                    onSaveTracker={() => saveTracker.mutate(result.id)}
                    onIgnore={() => patchResult.mutate({ id: result.id, status: "ignored" })}
                  />
                ))}
              </div>
            ) : (
              <EmptyState
                title="Nenhum resultado do Radar"
                description="Cadastre fontes públicas, crie uma wishlist e rode o Radar manualmente."
              />
            )}
          </SectionCard>

          <SectionCard
            id="radar-runs"
            title="Rodadas"
            description="Histórico local das execuções manuais."
          >
            <div className="space-y-3">
              {(runsQ.data?.runs ?? []).slice(0, 5).map((run) => (
                <div
                  key={run.id}
                  className="rounded-lg border border-border bg-muted/30 p-3 text-sm"
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className="font-medium">Rodada {run.id.slice(0, 8)}</span>
                    <span className="text-xs text-muted-foreground">{run.total_found} vagas</span>
                  </div>
                  <div className="mt-2 grid grid-cols-3 gap-2 text-[11px] text-muted-foreground">
                    <span>{run.total_sources} fontes</span>
                    <span>{run.total_alerted} alertas</span>
                    <span>{run.total_errors} erros</span>
                  </div>
                </div>
              ))}
              {!runsQ.isLoading && !(runsQ.data?.runs.length ?? 0) && (
                <p className="text-sm text-muted-foreground">Nenhuma rodada registrada.</p>
              )}
              <div className="rounded-lg border border-border bg-muted/30 p-3 text-xs text-muted-foreground">
                Limites padrão: até 10 fontes por rodada, 50 resultados por fonte, timeout curto e
                revisão manual antes de salvar.
              </div>
            </div>
          </SectionCard>
        </div>

        <SectionCard
          id="radar-settings"
          title={
            <span className="flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-accent" />
              Segurança e próximos passos
            </span>
          }
        >
          <label className="mb-4 flex items-start gap-2 rounded-lg border border-border bg-muted/30 p-3 text-xs text-muted-foreground">
            <input
              type="checkbox"
              checked={useAiForRadar}
              onChange={(event) => setUseAiForRadar(event.target.checked)}
              className="mt-0.5"
            />
            Usar IA explicativa no Radar quando estiver configurada. Se falhar, o SotuHire mantém
            análise local e mostra fallback.
          </label>
          <div className="grid gap-3 md:grid-cols-3">
            <InfoBox
              icon={Database}
              title="Caixa de Entrada"
              text="Resultados salvos preservam origem Radar, fonte original e score local."
              to="/sources"
            />
            <InfoBox
              icon={Inbox}
              title="Candidaturas"
              text="Tracker recebe fonte, score e referência à wishlist quando você decide salvar."
              to="/tracker"
            />
            <InfoBox
              icon={AlertCircle}
              title="Limites"
              text="Sem SERP scraping, sem login automático, sem auto-apply e sem captura de sessão."
              to="/privacy"
            />
          </div>
        </SectionCard>
      </div>
    </AppShell>
  );
}

function WishlistCard({ wishlist }: { wishlist: JobWishlist }) {
  return (
    <div className="mt-3 space-y-3 text-xs">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="font-semibold">{wishlist.name}</div>
          <div className="text-muted-foreground">Score mínimo {wishlist.min_match_score}%</div>
        </div>
        <span className="rounded-full bg-success/15 px-2 py-0.5 font-medium text-success">
          Ativa
        </span>
      </div>
      <ChipList items={wishlist.target_titles} />
      <div className="grid gap-2 sm:grid-cols-2">
        <div>
          <div className="mb-1 font-medium">Áreas</div>
          <ChipList items={wishlist.target_domains} />
        </div>
        <div>
          <div className="mb-1 font-medium">Momento</div>
          <ChipList items={wishlist.target_seniority} />
        </div>
      </div>
      <div>
        <div className="mb-1 font-medium">Obrigatórias</div>
        <ChipList items={wishlist.required_skills} />
      </div>
      <div>
        <div className="mb-1 font-medium">Desejáveis</div>
        <ChipList items={wishlist.desired_skills} />
      </div>
      {wishlist.notes && (
        <p className="rounded-md bg-muted p-2 text-muted-foreground">{wishlist.notes}</p>
      )}
    </div>
  );
}

function SourceBox({ source }: { source: RadarSource }) {
  return (
    <div className="rounded-lg border border-border bg-muted/30 p-3 text-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="truncate font-semibold">{source.name}</div>
          <div className="mt-1 truncate text-xs text-muted-foreground">
            {source.url || "Sem URL"}
          </div>
        </div>
        <StatusBadge status={source.status} />
      </div>
      <div className="mt-3 flex flex-wrap gap-1.5">
        <Badge>{sourceLabel(source.source_type)}</Badge>
        <Badge>{source.is_active ? "Ativa" : "Desativada"}</Badge>
        {source.last_error && <Badge tone="error">Erro</Badge>}
      </div>
      {source.notes && <p className="mt-3 text-xs text-muted-foreground">{source.notes}</p>}
      {source.last_error && (
        <p className="mt-2 rounded-md bg-destructive/10 p-2 text-xs text-destructive">
          {source.last_error}
        </p>
      )}
    </div>
  );
}

function ResultCard({
  result,
  onSaveInbox,
  onSaveTracker,
  onIgnore,
}: {
  result: RadarResult;
  onSaveInbox: () => void;
  onSaveTracker: () => void;
  onIgnore: () => void;
}) {
  return (
    <article
      data-testid="radar-result-card"
      className="rounded-xl border border-border bg-muted/20 p-4"
    >
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-base font-semibold">{result.title}</h3>
            <Badge>{sourceLabel(result.source_type)}</Badge>
            <Badge tone={result.analysis_mode === "ai" ? "success" : "muted"}>
              {result.analysis_mode === "ai"
                ? "IA"
                : result.analysis_mode === "fallback"
                  ? "Fallback local"
                  : "Local"}
            </Badge>
            {result.radar_status === "duplicate" && <Badge tone="warning">Duplicata</Badge>}
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            {result.company || "Empresa não informada"} · {result.location || "Local não informado"}{" "}
            · Fonte: {result.source_name || "Radar"}
          </p>
        </div>
        <ScoreBadge value={result.radar_score} label="Radar" />
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-3">
        <MiniList title="Por que alertou" items={result.reasons} />
        <MiniList title="Evidências usadas" items={result.evidence} />
        <MiniList title="Lacunas" items={result.gaps} empty="Sem lacunas claras." />
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        <button
          onClick={onSaveInbox}
          data-testid="radar-save-inbox"
          className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:opacity-90"
        >
          <Save className="h-3.5 w-3.5" /> Salvar na Caixa de Entrada
        </button>
        <button
          onClick={onSaveTracker}
          data-testid="radar-save-tracker"
          className="inline-flex items-center gap-1.5 rounded-md border border-input bg-card px-3 py-1.5 text-xs font-medium hover:bg-muted"
        >
          <Inbox className="h-3.5 w-3.5" /> Salvar em Candidaturas
        </button>
        <button
          onClick={onIgnore}
          data-testid="radar-ignore-result"
          className="rounded-md border border-input bg-card px-3 py-1.5 text-xs font-medium hover:bg-muted"
        >
          Ignorar
        </button>
        {result.url && (
          <a
            href={result.url}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 text-xs font-medium text-accent hover:underline"
          >
            Ver fonte <ExternalLink className="h-3 w-3" />
          </a>
        )}
      </div>
    </article>
  );
}

function MiniList({
  title,
  items,
  empty = "Sem dados.",
}: {
  title: string;
  items: string[];
  empty?: string;
}) {
  return (
    <div className="rounded-lg border border-border bg-card p-3">
      <div className="mb-2 text-xs font-semibold">{title}</div>
      <ul className="space-y-1 text-xs text-muted-foreground">
        {(items.length ? items : [empty]).slice(0, 4).map((item) => (
          <li key={item} className="leading-relaxed">
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

function TextField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="text-xs font-medium">
      {label}
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="mt-1 h-9 w-full rounded-md border border-input bg-card px-3 text-sm outline-none focus:border-accent/50 focus:ring-2 focus:ring-accent/20"
      />
    </label>
  );
}

function ChipList({ items }: { items: string[] }) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {items.slice(0, 8).map((item) => (
        <Badge key={item}>{item}</Badge>
      ))}
      {!items.length && <span className="text-xs text-muted-foreground">Não definido</span>}
    </div>
  );
}

function Badge({
  children,
  tone = "muted",
}: {
  children: ReactNode;
  tone?: "muted" | "success" | "warning" | "error";
}) {
  return (
    <span
      className={cn(
        "rounded-full px-2 py-0.5 text-[11px] font-medium",
        tone === "success" && "bg-success/15 text-success",
        tone === "warning" && "bg-warning/15 text-warning",
        tone === "error" && "bg-destructive/15 text-destructive",
        tone === "muted" && "bg-muted text-muted-foreground",
      )}
    >
      {children}
    </span>
  );
}

function ScoreBadge({ value, label = "Score" }: { value: number; label?: string }) {
  return (
    <div className="grid h-16 w-16 shrink-0 place-items-center rounded-xl border border-border bg-card text-center">
      <div>
        <div className="text-lg font-semibold tabular-nums">{value}</div>
        <div className="text-[10px] uppercase tracking-wide text-muted-foreground">{label}</div>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: RadarSource["status"] }) {
  const tone = status === "available" ? "success" : status === "error" ? "error" : "warning";
  return <Badge tone={tone}>{sourceStatusLabel(status)}</Badge>;
}

function InfoBox({
  icon: Icon,
  title,
  text,
  to,
}: {
  icon: LucideIcon;
  title: string;
  text: string;
  to: string;
}) {
  return (
    <a
      href={to}
      className="rounded-lg border border-border bg-muted/30 p-4 transition-colors hover:bg-muted"
    >
      <Icon className="h-4 w-4 text-accent" />
      <div className="mt-2 text-sm font-semibold">{title}</div>
      <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{text}</p>
    </a>
  );
}

function splitList(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function sourceLabel(sourceType: RadarSource["source_type"]): string {
  const labels: Record<RadarSource["source_type"], string> = {
    public_feed: "RSS público",
    official_api: "API oficial",
    manual_public_page: "Página pública",
    manual_url: "Link manual",
    recurring_csv_json: "CSV/JSON recorrente",
  };
  return labels[sourceType];
}

function sourceStatusLabel(status: RadarSource["status"]): string {
  const labels: Record<RadarSource["status"], string> = {
    available: "Disponível",
    experimental: "Experimental",
    requires_official_api: "Requer API oficial",
    requires_user_key: "Requer chave",
    planned: "Planejado",
    disabled: "Desativado",
    error: "Erro",
  };
  return labels[status];
}
