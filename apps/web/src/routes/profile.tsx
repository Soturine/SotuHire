import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  CheckCircle2,
  FileSearch,
  GraduationCap,
  Loader2,
  Pencil,
  Plus,
  RefreshCw,
  Save,
  Trash2,
  UserRound,
} from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";
import { toast } from "@/lib/notify";
import { AppShell } from "@/components/app-shell";
import { SectionCard } from "@/components/section-card";
import { EmptyState } from "@/components/states";
import { ProviderBadge } from "@/components/provider-badge";
import { useApi } from "@/lib/api/hooks";
import { useApiMode } from "@/lib/api/mode";
import type {
  LattesImportResult,
  ProfileImportResult,
  ProfileItem,
  UniversalCareerProfile,
} from "@/lib/api/types";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/profile")({
  head: () => ({
    meta: [
      { title: "Perfil Profissional - SotuHire" },
      {
        name: "description",
        content: "Perfil Profissional Universal local-first, baseado em evidências e multiárea.",
      },
    ],
  }),
  component: ProfilePage,
});

const sourceTypes = [
  ["resume", "Currículo"],
  ["curriculum_lattes", "Currículo Lattes"],
  ["portfolio", "Portfólio"],
  ["certificate", "Certificado"],
  ["manual_notes", "Notas manuais"],
  ["other", "Outro"],
] as const;

function ProfilePage() {
  const api = useApi();
  const qc = useQueryClient();
  const { mode } = useApiMode();
  const profileQ = useQuery({ queryKey: ["profile", mode], queryFn: () => api.profile() });
  const profile = profileQ.data?.profile;

  const [form, setForm] = useState(() => profileFormDefaults());
  const [manualItem, setManualItem] = useState(() => itemFormDefaults());
  const [sourceType, setSourceType] = useState("manual_notes");
  const [importText, setImportText] = useState("");
  const [useAi, setUseAi] = useState(true);
  const [typeFilter, setTypeFilter] = useState("all");
  const [draft, setDraft] = useState<ProfileImportResult | null>(null);
  const [lattesText, setLattesText] = useState("");
  const [lattesId, setLattesId] = useState("");
  const [lattesUrl, setLattesUrl] = useState("");
  const [orcid, setOrcid] = useState("");
  const [useLattesAi, setUseLattesAi] = useState(false);
  const [lattesDraft, setLattesDraft] = useState<LattesImportResult | null>(null);
  const [lattesSelectedIds, setLattesSelectedIds] = useState<Set<string>>(new Set());
  const [lattesFilter, setLattesFilter] = useState("all");

  useEffect(() => {
    if (!profile) return;
    setForm(profileToForm(profile));
  }, [profile]);

  const invalidate = () => qc.invalidateQueries({ queryKey: ["profile"] });

  const saveProfile = useMutation({
    mutationFn: () =>
      api.profileSave({
        display_name: form.display_name,
        headline: form.headline,
        summary: form.summary,
        primary_domains: splitList(form.primary_domains),
        secondary_domains: splitList(form.secondary_domains),
        career_moments: splitList(form.career_moments),
        target_roles: splitList(form.target_roles),
        target_seniority: splitList(form.target_seniority),
        preferred_locations: splitList(form.preferred_locations),
        preferred_work_models: splitList(form.preferred_work_models),
        preferred_contract_types: splitList(form.preferred_contract_types),
      }),
    onSuccess: () => {
      toast.success("Perfil atualizado.");
      invalidate();
    },
    onError: (error) => toast.error(error instanceof Error ? error.message : "Falha ao salvar."),
  });

  const addItem = useMutation({
    mutationFn: (item: Partial<ProfileItem>) => api.profileAddItem(item),
    onSuccess: () => {
      toast.success("Item adicionado ao perfil.");
      setManualItem(itemFormDefaults());
      invalidate();
    },
    onError: (error) =>
      toast.error(error instanceof Error ? error.message : "Falha ao adicionar item."),
  });

  const deleteItem = useMutation({
    mutationFn: (itemId: string) => api.profileDeleteItem(itemId),
    onSuccess: () => {
      toast.success("Item removido.");
      invalidate();
    },
    onError: (error) => toast.error(error instanceof Error ? error.message : "Falha ao remover."),
  });

  const updateItem = useMutation({
    mutationFn: ({ itemId, patch }: { itemId: string; patch: Partial<ProfileItem> }) =>
      api.profilePatchItem(itemId, patch),
    onSuccess: () => {
      toast.success("Item atualizado.");
      invalidate();
    },
    onError: (error) => toast.error(error instanceof Error ? error.message : "Falha ao editar."),
  });

  const importProfile = useMutation({
    mutationFn: () =>
      api.profileImportText({ text: importText, source_type: sourceType, use_ai: useAi }),
    onSuccess: (data) => {
      setDraft(data);
      toast.success("Itens extraídos para revisão.");
    },
    onError: (error) => toast.error(error instanceof Error ? error.message : "Falha ao extrair."),
  });

  const importLattes = useMutation({
    mutationFn: () =>
      api.profileImportLattes({
        text: lattesText,
        source_url: lattesUrl,
        lattes_id: lattesId,
        orcid,
        use_ai: useLattesAi,
      }),
    onSuccess: (data) => {
      setLattesDraft(data);
      setLattesSelectedIds(new Set(data.items.map((item) => item.item_id)));
      toast.success("Evidências acadêmicas extraídas para revisão.");
    },
    onError: (error) =>
      toast.error(error instanceof Error ? error.message : "Falha ao extrair Lattes."),
  });

  const confirmLattes = useMutation({
    mutationFn: () => {
      const selected = (lattesDraft?.items ?? []).filter((item) =>
        lattesSelectedIds.has(item.item_id),
      );
      return api.profileConfirmLattes(selected);
    },
    onSuccess: (data) => {
      toast.success(data.message || "Itens acadêmicos adicionados ao Perfil.");
      setLattesSelectedIds(new Set());
      invalidate();
    },
    onError: (error) =>
      toast.error(error instanceof Error ? error.message : "Falha ao confirmar itens."),
  });

  const dedupe = useMutation({
    mutationFn: () => api.profileDeduplicate(),
    onSuccess: (data) => toast.success(data.message || "Deduplicação concluída."),
    onError: (error) =>
      toast.error(error instanceof Error ? error.message : "Falha ao deduplicar."),
  });

  const items = [...(profile?.items ?? []), ...(profile?.constraints ?? [])];
  const visibleItems =
    typeFilter === "all" ? items : items.filter((item) => item.type === typeFilter);
  const itemTypes = ["all", ...Array.from(new Set(items.map((item) => item.type))).sort()];
  const lattesItems = lattesDraft?.items ?? [];
  const lattesTypes = ["all", ...Array.from(new Set(lattesItems.map((item) => item.type))).sort()];
  const visibleLattesItems =
    lattesFilter === "all" ? lattesItems : lattesItems.filter((item) => item.type === lattesFilter);
  const summary = profileSummary(profile);

  return (
    <AppShell
      title="Perfil"
      description="Perfil Profissional Universal local-first e baseado em evidências."
      actions={
        <ProviderBadge
          provider={draft?.provider_used || "local"}
          mode={draft?.analysis_mode || "local"}
          fallback={draft?.analysis_mode === "fallback"}
        />
      }
    >
      <div className="mx-auto flex max-w-7xl flex-col gap-5">
        <section className="rounded-xl border border-border bg-card p-4">
          <div className="flex items-center gap-2 text-sm font-medium text-accent">
            <UserRound className="h-4 w-4" />
            Perfil Profissional Universal
          </div>
          <p className="mt-2 max-w-3xl text-sm text-muted-foreground">
            Contexto local-first e baseado em evidências para Radar, Wishlist, Match, ATS, Ajuste,
            Kanban, Fontes e Captura. A IA sugere; você revisa antes de salvar.
          </p>
        </section>

        <section className="grid gap-3 md:grid-cols-4">
          <Metric label="Itens" value={summary.items} />
          <Metric label="Confirmados" value={summary.confirmed} />
          <Metric label="Fontes" value={summary.sources} />
          <Metric label="Áreas" value={summary.domains} />
        </section>

        <section className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_420px]">
          <SectionCard
            title="Dados básicos"
            description="Campos editáveis do perfil ativo local."
            actions={
              <button
                type="button"
                onClick={() => saveProfile.mutate()}
                disabled={saveProfile.isPending}
                className="inline-flex items-center gap-2 rounded-md bg-primary px-3 py-2 text-xs font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
                data-testid="profile-save"
              >
                {saveProfile.isPending ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Save className="h-3.5 w-3.5" />
                )}
                Salvar
              </button>
            }
          >
            {profileQ.isLoading ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                Carregando perfil...
              </div>
            ) : (
              <div className="grid gap-4 md:grid-cols-2">
                <TextField
                  label="Nome"
                  value={form.display_name}
                  onChange={(value) => setForm({ ...form, display_name: value })}
                  testId="profile-name"
                />
                <TextField
                  label="Headline"
                  value={form.headline}
                  onChange={(value) => setForm({ ...form, headline: value })}
                />
                <TextArea
                  label="Resumo"
                  value={form.summary}
                  onChange={(value) => setForm({ ...form, summary: value })}
                  className="md:col-span-2"
                />
                <TextField
                  label="Áreas principais"
                  value={form.primary_domains}
                  onChange={(value) => setForm({ ...form, primary_domains: value })}
                  placeholder="Engenharia, Saúde, Direito"
                />
                <TextField
                  label="Áreas secundárias"
                  value={form.secondary_domains}
                  onChange={(value) => setForm({ ...form, secondary_domains: value })}
                />
                <TextField
                  label="Objetivos/cargos alvo"
                  value={form.target_roles}
                  onChange={(value) => setForm({ ...form, target_roles: value })}
                />
                <TextField
                  label="Momento de carreira"
                  value={form.career_moments}
                  onChange={(value) => setForm({ ...form, career_moments: value })}
                />
                <TextField
                  label="Senioridade alvo"
                  value={form.target_seniority}
                  onChange={(value) => setForm({ ...form, target_seniority: value })}
                />
                <TextField
                  label="Localizações preferidas"
                  value={form.preferred_locations}
                  onChange={(value) => setForm({ ...form, preferred_locations: value })}
                />
                <TextField
                  label="Modalidade"
                  value={form.preferred_work_models}
                  onChange={(value) => setForm({ ...form, preferred_work_models: value })}
                  placeholder="remoto, híbrido, presencial"
                />
                <TextField
                  label="Contrato"
                  value={form.preferred_contract_types}
                  onChange={(value) => setForm({ ...form, preferred_contract_types: value })}
                  placeholder="estágio, CLT, PJ, bolsa"
                />
              </div>
            )}
          </SectionCard>

          <SectionCard
            title="Adicionar item manual"
            description="Itens manuais entram confirmados."
          >
            <div className="space-y-3">
              <TextField
                label="Tipo"
                value={manualItem.type}
                onChange={(value) => setManualItem({ ...manualItem, type: value })}
                placeholder="education, certification, project"
              />
              <TextField
                label="Título"
                value={manualItem.title}
                onChange={(value) => setManualItem({ ...manualItem, title: value })}
                testId="profile-item-title"
              />
              <TextField
                label="Área/domínio"
                value={manualItem.domain}
                onChange={(value) => setManualItem({ ...manualItem, domain: value, area: value })}
              />
              <TextArea
                label="Evidência"
                value={manualItem.evidence}
                onChange={(value) =>
                  setManualItem({ ...manualItem, evidence: value, description: value })
                }
                testId="profile-item-evidence"
              />
              <button
                type="button"
                onClick={() => addItem.mutate({ ...manualItem, source: "manual" })}
                disabled={!manualItem.title.trim() || addItem.isPending}
                className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-primary px-3 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
                data-testid="profile-add-item"
              >
                <Plus className="h-4 w-4" />
                Adicionar item
              </button>
            </div>
          </SectionCard>
        </section>

        <SectionCard
          title="Importar texto"
          description="Cole currículo, Lattes, portfólio, certificado ou notas. Nada é salvo sem revisão."
        >
          <div className="grid gap-4 lg:grid-cols-[260px_minmax(0,1fr)]">
            <div className="space-y-3">
              <label className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Tipo de fonte
              </label>
              <select
                value={sourceType}
                onChange={(event) => setSourceType(event.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                {sourceTypes.map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
              <label className="flex items-center gap-2 rounded-md border border-border px-3 py-2 text-sm">
                <input
                  type="checkbox"
                  checked={useAi}
                  onChange={(event) => setUseAi(event.target.checked)}
                />
                Usar IA se configurada
              </label>
              <button
                type="button"
                onClick={() => importProfile.mutate()}
                disabled={!importText.trim() || importProfile.isPending}
                className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-primary px-3 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
                data-testid="profile-import-text"
              >
                {importProfile.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <FileSearch className="h-4 w-4" />
                )}
                Extrair itens
              </button>
            </div>
            <TextArea
              label="Texto para extração"
              value={importText}
              onChange={setImportText}
              className="min-h-52"
              testId="profile-import-textarea"
              placeholder="Cole um trecho fictício de currículo, Lattes, portfólio ou certificado."
            />
          </div>
        </SectionCard>

        {draft && (
          <SectionCard
            title="Itens extraídos para revisão"
            description="Itens de IA/fallback começam como não confirmados. Adicione apenas o que for verdadeiro."
            actions={
              <span className="rounded-full border border-accent/30 bg-accent/10 px-2.5 py-1 text-xs font-medium text-accent">
                {draft.analysis_mode === "ai"
                  ? "IA"
                  : draft.analysis_mode === "fallback"
                    ? "Fallback local"
                    : "Local"}
              </span>
            }
          >
            <div className="space-y-3" data-testid="profile-draft-items">
              {draft.warnings.map((warning) => (
                <p
                  key={warning}
                  className="rounded-md border border-warning/30 bg-warning/10 px-3 py-2 text-xs text-warning-foreground"
                >
                  {warning}
                </p>
              ))}
              {draft.items.map((item) => (
                <ProfileItemRow
                  key={item.item_id}
                  item={item}
                  actionLabel="Adicionar ao perfil"
                  onAction={() => addItem.mutate(item)}
                />
              ))}
            </div>
          </SectionCard>
        )}

        <SectionCard
          title="Acadêmico / Lattes"
          description="Importe texto colado do Currículo Lattes ou trajetória acadêmica. Nada é salvo sem revisão."
          actions={
            <ProviderBadge
              provider={lattesDraft?.provider_used || "local"}
              mode={lattesDraft?.analysis_mode || "local"}
              fallback={lattesDraft?.analysis_mode === "fallback"}
            />
          }
        >
          <div className="space-y-4" data-testid="profile-lattes-section">
            <div
              className="flex items-start gap-2 rounded-md border border-warning/30 bg-warning/10 px-3 py-2 text-xs text-warning-foreground"
              data-testid="profile-lattes-review-warning"
            >
              <GraduationCap className="mt-0.5 h-4 w-4 shrink-0" />
              <div>
                Nada é salvo sem revisão. O SotuHire não acessa sua conta Lattes, não faz login e
                não usa scraping autenticado.
              </div>
            </div>

            <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
              <TextArea
                label="Texto do Currículo Lattes ou acadêmico"
                value={lattesText}
                onChange={setLattesText}
                className="min-h-64"
                testId="profile-lattes-textarea"
                placeholder="Cole aqui formação, projetos, publicações, extensão, docência, prêmios, eventos ou produção técnica/artística."
              />
              <div className="space-y-3">
                <TextField
                  label="Lattes ID"
                  value={lattesId}
                  onChange={setLattesId}
                  placeholder="opcional"
                />
                <TextField
                  label="URL do Lattes"
                  value={lattesUrl}
                  onChange={setLattesUrl}
                  placeholder="https://lattes.cnpq.br/..."
                />
                <TextField label="ORCID" value={orcid} onChange={setOrcid} placeholder="opcional" />
                <label className="flex items-center gap-2 rounded-md border border-border px-3 py-2 text-sm">
                  <input
                    type="checkbox"
                    checked={useLattesAi}
                    onChange={(event) => setUseLattesAi(event.target.checked)}
                  />
                  Usar IA/Gemini se configurada
                </label>
                <button
                  type="button"
                  onClick={() => importLattes.mutate()}
                  disabled={!lattesText.trim() || importLattes.isPending}
                  className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-primary px-3 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
                  data-testid="profile-lattes-extract"
                >
                  {importLattes.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <FileSearch className="h-4 w-4" />
                  )}
                  Extrair do Lattes
                </button>
              </div>
            </div>

            {lattesDraft && (
              <div className="space-y-3" data-testid="profile-lattes-candidates">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="text-sm text-muted-foreground">
                    {lattesDraft.items.length} candidato(s), confiança{" "}
                    {confidenceLabel(lattesDraft.confidence)}.
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <select
                      value={lattesFilter}
                      onChange={(event) => setLattesFilter(event.target.value)}
                      className="rounded-md border border-input bg-background px-2.5 py-2 text-xs font-semibold"
                    >
                      {lattesTypes.map((type) => (
                        <option key={type} value={type}>
                          {type === "all" ? "Todos os tipos" : type}
                        </option>
                      ))}
                    </select>
                    <button
                      type="button"
                      onClick={() => confirmLattes.mutate()}
                      disabled={!lattesSelectedIds.size || confirmLattes.isPending}
                      className="inline-flex items-center gap-2 rounded-md bg-primary px-3 py-2 text-xs font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
                      data-testid="profile-lattes-add-selected"
                    >
                      <CheckCircle2 className="h-3.5 w-3.5" />
                      Adicionar selecionados ao Perfil
                    </button>
                  </div>
                </div>

                {[...lattesDraft.warnings, ...lattesDraft.assumptions].map((warning) => (
                  <p
                    key={warning}
                    className="rounded-md border border-warning/30 bg-warning/10 px-3 py-2 text-xs text-warning-foreground"
                  >
                    {warning}
                  </p>
                ))}

                <div className="grid gap-3">
                  {visibleLattesItems.map((item) => (
                    <label
                      key={item.item_id}
                      className="grid gap-3 rounded-lg border border-border bg-background p-4 md:grid-cols-[auto_minmax(0,1fr)]"
                    >
                      <input
                        type="checkbox"
                        className="mt-1"
                        checked={lattesSelectedIds.has(item.item_id)}
                        onChange={(event) =>
                          setLattesSelectedIds((current) => {
                            const next = new Set(current);
                            if (event.target.checked) next.add(item.item_id);
                            else next.delete(item.item_id);
                            return next;
                          })
                        }
                      />
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <h3 className="font-semibold">{item.title}</h3>
                          <Badge>{item.type}</Badge>
                          <Badge>{item.source}</Badge>
                          <Badge
                            tone={
                              item.confidence === "high"
                                ? "success"
                                : item.confidence === "low"
                                  ? "warning"
                                  : "neutral"
                            }
                          >
                            {confidenceLabel(item.confidence)}
                          </Badge>
                          <Badge tone="warning">Revisar</Badge>
                        </div>
                        <p className="mt-2 text-sm text-muted-foreground">
                          {item.description || item.evidence || "Sem descrição."}
                        </p>
                        <p className="mt-2 text-xs text-muted-foreground">
                          {item.domain || item.area || "Acadêmico"} · Evidência:{" "}
                          {item.evidence || "a confirmar"}
                        </p>
                      </div>
                    </label>
                  ))}
                  {!visibleLattesItems.length && (
                    <EmptyState
                      title="Nenhum candidato neste filtro"
                      description="Troque o tipo do filtro para ver outros itens extraídos."
                    />
                  )}
                </div>
              </div>
            )}
          </div>
        </SectionCard>

        <SectionCard
          title="Itens do perfil"
          description="Cada item preserva origem, evidência, confiança e revisão."
          actions={
            <div className="flex flex-wrap items-center justify-end gap-2">
              <select
                value={typeFilter}
                onChange={(event) => setTypeFilter(event.target.value)}
                data-testid="profile-type-filter"
                className="rounded-md border border-input bg-background px-2.5 py-2 text-xs font-semibold"
              >
                {itemTypes.map((type) => (
                  <option key={type} value={type}>
                    {type === "all" ? "Todos os tipos" : type}
                  </option>
                ))}
              </select>
              <button
                type="button"
                onClick={() => dedupe.mutate()}
                className="inline-flex items-center gap-2 rounded-md border border-input px-3 py-2 text-xs font-semibold hover:bg-muted"
              >
                <RefreshCw className="h-3.5 w-3.5" />
                Deduplicar
              </button>
            </div>
          }
        >
          {items.length ? (
            <div className="grid gap-3" data-testid="profile-items">
              {visibleItems.map((item) => (
                <ProfileItemRow
                  key={item.item_id}
                  item={item}
                  actionLabel="Remover"
                  danger
                  onEdit={(patch) => updateItem.mutate({ itemId: item.item_id, patch })}
                  onAction={() => deleteItem.mutate(item.item_id)}
                />
              ))}
              {!visibleItems.length && (
                <EmptyState
                  title="Nenhum item neste filtro"
                  description="Troque o tipo do filtro para ver outros itens do perfil."
                />
              )}
            </div>
          ) : (
            <EmptyState
              title={mode === "demo" ? "Perfil demo vazio" : "Perfil vazio"}
              description="Adicione um item manual ou importe texto para começar a montar seu contexto profissional."
            />
          )}
        </SectionCard>
      </div>
    </AppShell>
  );
}

function ProfileItemRow({
  item,
  actionLabel,
  onAction,
  danger,
  onEdit,
}: {
  item: ProfileItem;
  actionLabel: string;
  onAction: () => void;
  danger?: boolean;
  onEdit?: (patch: Partial<ProfileItem>) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(item.title);
  const [editDomain, setEditDomain] = useState(item.domain || item.area || "");
  const [editEvidence, setEditEvidence] = useState(item.evidence || item.description || "");

  useEffect(() => {
    setEditTitle(item.title);
    setEditDomain(item.domain || item.area || "");
    setEditEvidence(item.evidence || item.description || "");
  }, [item]);

  return (
    <article className="rounded-lg border border-border bg-background p-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-semibold">{item.title}</h3>
            <Badge>{item.type}</Badge>
            <Badge>{item.source || "manual"}</Badge>
            <Badge
              tone={
                item.confidence === "high"
                  ? "success"
                  : item.confidence === "low"
                    ? "warning"
                    : "neutral"
              }
            >
              {confidenceLabel(item.confidence)}
            </Badge>
            <Badge tone={item.confirmed_by_user ? "success" : "warning"}>
              {item.confirmed_by_user ? "Confirmado" : "Revisar"}
            </Badge>
          </div>
          <p className="mt-2 text-sm text-muted-foreground">
            {item.description || item.evidence || "Sem descrição."}
          </p>
          <p className="mt-2 text-xs text-muted-foreground">
            {item.domain || item.area || "Área não informada"} · Evidência:{" "}
            {item.evidence || "a confirmar"}
          </p>
          {editing && (
            <div className="mt-3 grid gap-3 rounded-md border border-border bg-muted/30 p-3 md:grid-cols-2">
              <TextField label="Título" value={editTitle} onChange={setEditTitle} />
              <TextField label="Área/domínio" value={editDomain} onChange={setEditDomain} />
              <TextArea
                label="Evidência"
                value={editEvidence}
                onChange={setEditEvidence}
                className="md:col-span-2"
              />
              <button
                type="button"
                onClick={() => {
                  onEdit?.({
                    title: editTitle,
                    domain: editDomain,
                    area: editDomain,
                    evidence: editEvidence,
                    description: editEvidence,
                  });
                  setEditing(false);
                }}
                className="inline-flex items-center justify-center gap-2 rounded-md bg-primary px-3 py-2 text-xs font-semibold text-primary-foreground hover:bg-primary/90"
              >
                <Save className="h-3.5 w-3.5" />
                Salvar edição
              </button>
            </div>
          )}
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          {onEdit && (
            <button
              type="button"
              onClick={() => setEditing((current) => !current)}
              className="inline-flex items-center justify-center gap-2 rounded-md border border-input px-3 py-2 text-xs font-semibold hover:bg-muted"
            >
              <Pencil className="h-3.5 w-3.5" />
              Editar
            </button>
          )}
          <button
            type="button"
            onClick={onAction}
            className={cn(
              "inline-flex items-center justify-center gap-2 rounded-md border px-3 py-2 text-xs font-semibold",
              danger
                ? "border-destructive/40 text-destructive hover:bg-destructive/10"
                : "border-success/40 text-success-foreground hover:bg-success/10",
            )}
          >
            {danger ? <Trash2 className="h-3.5 w-3.5" /> : <CheckCircle2 className="h-3.5 w-3.5" />}
            {actionLabel}
          </button>
        </div>
      </div>
    </article>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-border bg-card px-4 py-3">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="mt-1 text-2xl font-semibold">{value}</div>
    </div>
  );
}

function Badge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: "neutral" | "success" | "warning";
}) {
  const cls =
    tone === "success"
      ? "border-success/30 bg-success/10 text-success-foreground"
      : tone === "warning"
        ? "border-warning/30 bg-warning/10 text-warning-foreground"
        : "border-border bg-muted text-muted-foreground";
  return (
    <span className={cn("rounded-full border px-2 py-0.5 text-[11px] font-medium", cls)}>
      {children}
    </span>
  );
}

function TextField({
  label,
  value,
  onChange,
  placeholder,
  testId,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  testId?: string;
}) {
  return (
    <label className="block">
      <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
        {label}
      </span>
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        data-testid={testId}
        className="mt-1.5 w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:border-accent/50 focus:ring-2 focus:ring-accent/20"
      />
    </label>
  );
}

function TextArea({
  label,
  value,
  onChange,
  placeholder,
  className,
  testId,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
  testId?: string;
}) {
  return (
    <label className={cn("block", className)}>
      <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
        {label}
      </span>
      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        data-testid={testId}
        className="mt-1.5 min-h-28 w-full resize-y rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:border-accent/50 focus:ring-2 focus:ring-accent/20"
      />
    </label>
  );
}

function profileFormDefaults() {
  return {
    display_name: "",
    headline: "",
    summary: "",
    primary_domains: "",
    secondary_domains: "",
    career_moments: "",
    target_roles: "",
    target_seniority: "",
    preferred_locations: "",
    preferred_work_models: "",
    preferred_contract_types: "",
  };
}

function itemFormDefaults() {
  return {
    type: "project",
    title: "",
    domain: "",
    area: "",
    evidence: "",
    description: "",
  };
}

function profileToForm(profile: UniversalCareerProfile) {
  return {
    display_name: profile.display_name || "",
    headline: profile.headline || "",
    summary: profile.summary || "",
    primary_domains: profile.primary_domains.join(", "),
    secondary_domains: profile.secondary_domains.join(", "),
    career_moments: profile.career_moments.join(", "),
    target_roles: profile.target_roles.join(", "),
    target_seniority: profile.target_seniority.join(", "),
    preferred_locations: profile.preferred_locations.join(", "),
    preferred_work_models: profile.preferred_work_models.join(", "),
    preferred_contract_types: profile.preferred_contract_types.join(", "),
  };
}

function profileSummary(profile?: UniversalCareerProfile) {
  const items = [...(profile?.items ?? []), ...(profile?.constraints ?? [])];
  return {
    items: items.length,
    confirmed: items.filter((item) => item.confirmed_by_user).length,
    sources: new Set(items.map((item) => item.source)).size,
    domains: new Set(
      [
        ...items.map((item) => item.domain || item.area),
        ...(profile?.primary_domains ?? []),
      ].filter(Boolean),
    ).size,
  };
}

function splitList(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function confidenceLabel(value: ProfileItem["confidence"]): string {
  if (value === "high") return "Alta confiança";
  if (value === "low") return "Baixa confiança";
  return "Média confiança";
}
