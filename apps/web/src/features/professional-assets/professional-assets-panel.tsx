import { Archive, Check, ClipboardCopy, Copy, Loader2, Pencil, RotateCcw } from "lucide-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { EmptyState, ErrorState, LoadingState } from "@/components/states";
import { useApi } from "@/lib/api/hooks";
import { useApiMode } from "@/lib/api/mode";
import type {
  ProfessionalAsset,
  ProfessionalAssetsResult,
  ProfessionalAssetStatus,
  ProfessionalAssetType,
} from "@/lib/api/types";
import { toast } from "@/lib/notify";
import { cn } from "@/lib/utils";

const TYPE_LABELS: Record<ProfessionalAssetType, string> = {
  resume_master: "Currículo Mestre",
  resume_variant: "Variante de currículo",
  cover_letter: "Carta de apresentação",
  recruiter_message: "Mensagem para recrutador",
  professional_bio: "Bio profissional",
  about_section: "Seção Sobre",
  portfolio_summary: "Resumo de portfólio",
  project_highlight: "Destaque de projeto",
  application_kit: "Kit de candidatura",
};

const STATUS_LABELS: Record<ProfessionalAssetStatus, string> = {
  draft: "Rascunho",
  review: "Em revisão",
  confirmed: "Confirmado",
  archived: "Arquivado",
  stale: "Desatualizado",
};

export function ProfessionalAssetsPanel() {
  const api = useApi();
  const { mode } = useApiMode();
  const queryClient = useQueryClient();
  const queryKey = ["professional-assets", mode] as const;
  const query = useQuery({ queryKey, queryFn: () => api.professionalAssets() });
  const [typeFilter, setTypeFilter] = useState<ProfessionalAssetType | "all">("all");
  const [statusFilter, setStatusFilter] = useState<ProfessionalAssetStatus | "active">("active");
  const [editing, setEditing] = useState<string | null>(null);
  const [draft, setDraft] = useState({ title: "", content: "" });
  const [busy, setBusy] = useState<string | null>(null);

  const items = useMemo(
    () =>
      (query.data?.items ?? []).filter(
        (asset) =>
          (typeFilter === "all" || asset.asset_type === typeFilter) &&
          (statusFilter === "active" ? asset.status !== "archived" : asset.status === statusFilter),
      ),
    [query.data?.items, statusFilter, typeFilter],
  );

  function cache(asset: ProfessionalAsset, append = false): void {
    queryClient.setQueryData<ProfessionalAssetsResult>(queryKey, (current) => {
      if (!current) return { items: [asset], limit: 50, offset: 0 };
      return {
        ...current,
        items: append
          ? [asset, ...current.items]
          : current.items.map((candidate) =>
              candidate.asset_id === asset.asset_id ? asset : candidate,
            ),
      };
    });
  }

  function notify(message: string): void {
    toast.success(mode === "demo" ? `DEMO: ${message} Nenhum dado real foi alterado.` : message);
  }

  async function save(asset: ProfessionalAsset): Promise<void> {
    setBusy(asset.asset_id);
    try {
      const result = await api.professionalAssetUpdate(asset.asset_id, draft);
      cache(result.asset);
      setEditing(null);
      notify("Ativo atualizado.");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : String(error));
    } finally {
      setBusy(null);
    }
  }

  async function changeStatus(
    asset: ProfessionalAsset,
    status: ProfessionalAssetStatus,
  ): Promise<void> {
    setBusy(asset.asset_id);
    try {
      const result = await api.professionalAssetChangeStatus(asset.asset_id, status);
      cache(result.asset);
      notify(`Status alterado para ${STATUS_LABELS[status].toLowerCase()}.`);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : String(error));
    } finally {
      setBusy(null);
    }
  }

  async function duplicate(asset: ProfessionalAsset): Promise<void> {
    const now = new Date().toISOString();
    const copyAsset: ProfessionalAsset = {
      ...asset,
      asset_id: crypto.randomUUID().replaceAll("-", ""),
      title: `${asset.title} · cópia`,
      status: "draft",
      review_status: "candidate",
      created_at: now,
      updated_at: now,
      stale_at: null,
      stale_reason: "",
    };
    setBusy(asset.asset_id);
    try {
      const result = await api.professionalAssetCreate(copyAsset);
      cache(result.asset, true);
      notify("Cópia independente criada como rascunho.");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : String(error));
    } finally {
      setBusy(null);
    }
  }

  return (
    <section
      className="rounded-2xl border bg-card p-5 shadow-[var(--shadow-soft)]"
      data-testid="professional-assets"
    >
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-accent">
            Professional Assets
          </p>
          <h2 className="mt-1 text-display text-lg">Biblioteca reutilizável</h2>
          <p className="mt-1 text-xs text-muted-foreground">
            Rascunhos e textos confirmados preservam origem, escopo de evidência e estado de
            revisão.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <select
            value={typeFilter}
            onChange={(event) => setTypeFilter(event.target.value as ProfessionalAssetType | "all")}
            className="h-9 rounded-md border bg-background px-2 text-xs"
            aria-label="Filtrar por tipo"
          >
            <option value="all">Todos os tipos</option>
            {Object.entries(TYPE_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
          <select
            value={statusFilter}
            onChange={(event) =>
              setStatusFilter(event.target.value as ProfessionalAssetStatus | "active")
            }
            className="h-9 rounded-md border bg-background px-2 text-xs"
            aria-label="Filtrar por status"
          >
            <option value="active">Ativos</option>
            {Object.entries(STATUS_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {mode === "demo" && (
        <p className="mt-4 rounded-lg border border-warning/30 bg-warning/10 p-3 text-xs">
          <strong>DEMO:</strong> a biblioteca abaixo usa somente conteúdo fictício.
        </p>
      )}

      {query.isLoading ? (
        <LoadingState className="py-8" label="Carregando ativos locais…" />
      ) : query.isError ? (
        <div className="mt-4">
          <ErrorState error={query.error} onRetry={() => query.refetch()} />
        </div>
      ) : items.length === 0 ? (
        <div className="mt-4">
          <EmptyState
            title="Nenhum ativo neste filtro"
            description="Gere um kit no Application Lab ou altere os filtros da biblioteca."
          />
        </div>
      ) : (
        <div className="mt-5 grid gap-3 lg:grid-cols-2">
          {items.map((asset) => {
            const isEditing = editing === asset.asset_id;
            const isBusy = busy === asset.asset_id;
            return (
              <article key={asset.asset_id} className="rounded-xl border p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                      {TYPE_LABELS[asset.asset_type]}
                    </p>
                    <h3 className="mt-1 text-sm font-semibold">{asset.title}</h3>
                  </div>
                  <span
                    className={cn(
                      "rounded-full px-2 py-1 text-[10px] font-bold uppercase",
                      asset.status === "confirmed" && "bg-success/15 text-success",
                      asset.status === "stale" && "bg-warning/15 text-warning-foreground",
                      asset.status === "archived" && "bg-muted text-muted-foreground",
                      (asset.status === "draft" || asset.status === "review") &&
                        "bg-accent/10 text-accent",
                    )}
                  >
                    {STATUS_LABELS[asset.status]}
                  </span>
                </div>

                {isEditing ? (
                  <div className="mt-3 space-y-2">
                    <input
                      value={draft.title}
                      onChange={(event) =>
                        setDraft((current) => ({ ...current, title: event.target.value }))
                      }
                      className="h-9 w-full rounded-md border bg-background px-3 text-sm"
                      aria-label="Título do ativo"
                    />
                    <textarea
                      value={draft.content}
                      onChange={(event) =>
                        setDraft((current) => ({ ...current, content: event.target.value }))
                      }
                      className="min-h-32 w-full rounded-md border bg-background p-3 text-sm leading-6"
                      aria-label="Conteúdo do ativo"
                    />
                  </div>
                ) : (
                  <p className="mt-3 whitespace-pre-wrap text-sm leading-6">{asset.content}</p>
                )}

                <p className="mt-3 text-xs text-muted-foreground">
                  {asset.source_refs.length + asset.evidence_ids.length} referência(s) · escopo{" "}
                  <code>{asset.evidence_scope_id || "não definido"}</code>
                </p>
                {asset.stale_reason && (
                  <p className="mt-2 text-xs text-warning-foreground">{asset.stale_reason}</p>
                )}

                <div className="mt-4 flex flex-wrap gap-2 border-t pt-3">
                  {isEditing ? (
                    <>
                      <button
                        type="button"
                        onClick={() => save(asset)}
                        disabled={isBusy || !draft.title.trim()}
                        className="inline-flex items-center gap-1 rounded-md bg-primary px-2.5 py-1.5 text-xs font-semibold text-primary-foreground disabled:opacity-40"
                      >
                        {isBusy ? (
                          <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        ) : (
                          <Check className="h-3.5 w-3.5" />
                        )}
                        Salvar
                      </button>
                      <button
                        type="button"
                        onClick={() => setEditing(null)}
                        className="rounded-md border px-2.5 py-1.5 text-xs"
                      >
                        Cancelar
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        type="button"
                        onClick={() => {
                          setEditing(asset.asset_id);
                          setDraft({ title: asset.title, content: asset.content });
                        }}
                        disabled={isBusy}
                        className="inline-flex items-center gap-1 rounded-md border px-2.5 py-1.5 text-xs hover:bg-muted disabled:opacity-40"
                      >
                        <Pencil className="h-3.5 w-3.5" /> Editar
                      </button>
                      <button
                        type="button"
                        onClick={() => duplicate(asset)}
                        disabled={isBusy}
                        className="inline-flex items-center gap-1 rounded-md border px-2.5 py-1.5 text-xs hover:bg-muted disabled:opacity-40"
                      >
                        <Copy className="h-3.5 w-3.5" /> Duplicar
                      </button>
                      {asset.status !== "confirmed" && asset.status !== "archived" && (
                        <button
                          type="button"
                          onClick={() => changeStatus(asset, "confirmed")}
                          disabled={isBusy}
                          className="inline-flex items-center gap-1 rounded-md border px-2.5 py-1.5 text-xs hover:bg-muted disabled:opacity-40"
                        >
                          <Check className="h-3.5 w-3.5" /> Confirmar
                        </button>
                      )}
                      {asset.status === "confirmed" && (
                        <button
                          type="button"
                          onClick={() =>
                            navigator.clipboard
                              .writeText(asset.content)
                              .then(() => notify("Texto confirmado copiado."))
                          }
                          className="inline-flex items-center gap-1 rounded-md border px-2.5 py-1.5 text-xs hover:bg-muted"
                        >
                          <ClipboardCopy className="h-3.5 w-3.5" /> Copiar
                        </button>
                      )}
                      {asset.status === "archived" || asset.status === "stale" ? (
                        <button
                          type="button"
                          onClick={() => changeStatus(asset, "review")}
                          disabled={isBusy}
                          className="inline-flex items-center gap-1 rounded-md border px-2.5 py-1.5 text-xs hover:bg-muted disabled:opacity-40"
                        >
                          <RotateCcw className="h-3.5 w-3.5" /> Voltar à revisão
                        </button>
                      ) : (
                        <button
                          type="button"
                          onClick={() => changeStatus(asset, "archived")}
                          disabled={isBusy}
                          className="inline-flex items-center gap-1 rounded-md border px-2.5 py-1.5 text-xs hover:bg-muted disabled:opacity-40"
                        >
                          <Archive className="h-3.5 w-3.5" /> Arquivar
                        </button>
                      )}
                    </>
                  )}
                </div>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
