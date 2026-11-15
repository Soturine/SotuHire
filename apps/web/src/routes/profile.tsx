import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  CheckCircle2,
  CircleDot,
  FileSearch,
  GraduationCap,
  Loader2,
  Pencil,
  Plus,
  RefreshCw,
  Save,
  Sparkle,
  Trash2,
  Undo2,
  UserRound,
} from "lucide-react";
import { useEffect, useMemo, useState, type ReactNode } from "react";

import { AppShell } from "@/components/app-shell";
import { Field, controlClass, textareaClass } from "@/components/field";
import { ProviderBadge } from "@/components/provider-badge";
import { ScoreRing } from "@/components/score-ring";
import { EmptyState, ErrorState, LoadingState } from "@/components/states";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useApi } from "@/lib/api/hooks";
import { useApiMode } from "@/lib/api/mode";
import type {
  LattesImportResult,
  ProfileImportResult,
  ProfileItem,
  UniversalCareerProfile,
} from "@/lib/api/types";
import { toast } from "@/lib/notify";
import { profileSourceLabel, profileTypeLabel } from "@/lib/profile-labels";
import { cn } from "@/lib/utils";

type ProfileTab = "facts" | "identity" | "import";

export const Route = createFileRoute("/profile")({
  validateSearch: (search: Record<string, unknown>): { tab?: ProfileTab } => ({
    tab:
      search.tab === "identity" || search.tab === "import" || search.tab === "facts"
        ? search.tab
        : undefined,
  }),
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

const typeLabel = profileTypeLabel;

const MANUAL_TYPES = [
  "experience",
  "education",
  "project",
  "certification",
  "skill",
  "language",
  "publication",
  "award",
  "volunteer",
  "course",
  "license",
];

const sourceLabel = profileSourceLabel;

function ProfilePage() {
  const api = useApi();
  const qc = useQueryClient();
  const navigate = useNavigate({ from: "/profile" });
  const { tab: tabParam } = Route.useSearch();
  const tab: ProfileTab = tabParam ?? "facts";
  const setTab = (next: string) =>
    void navigate({ search: { tab: next as ProfileTab }, replace: true });
  const { mode, baseUrl } = useApiMode();
  const profileQ = useQuery({ queryKey: ["profile", mode, baseUrl], queryFn: () => api.profile() });
  const profile = profileQ.data?.profile;
  const [adding, setAdding] = useState(false);

  const invalidate = () => {
    // Confirmed profile facts feed the Master Resume; its pending-updates list must refresh too.
    void qc.invalidateQueries({ queryKey: ["resume-studio-profile-updates"] });
    return qc.invalidateQueries({ queryKey: ["profile"] });
  };

  const items = useMemo(
    () => [...(profile?.items ?? []), ...(profile?.constraints ?? [])],
    [profile],
  );
  const summary = profileSummary(profile);

  return (
    <AppShell
      title="Perfil"
      description="Perfil Profissional Universal local-first e baseado em evidências."
    >
      {profileQ.isError ? (
        <ErrorState error={profileQ.error} onRetry={() => profileQ.refetch()} />
      ) : profileQ.isLoading || !profile ? (
        <LoadingState label="Abrindo seu perfil…" />
      ) : (
        <div className="mx-auto max-w-6xl space-y-6">
          <ProfileHero
            profile={profile}
            summary={summary}
            onAdd={() => setAdding(true)}
            onImport={() => setTab("import")}
          />

          <Tabs value={tab} onValueChange={setTab} className="gap-5">
            <TabsList className="grid h-auto w-full grid-cols-3 gap-1 rounded-xl bg-surface-muted p-1 sm:inline-flex sm:w-auto">
              <TabsTrigger value="facts" className="rounded-lg px-3.5 py-2">
                <span className="sm:hidden">Fatos</span>
                <span className="hidden sm:inline">Fatos e evidências</span>
                <span className="tabular ml-1.5 rounded-full bg-muted px-1.5 text-[11px] text-muted-foreground">
                  {items.length}
                </span>
              </TabsTrigger>
              <TabsTrigger value="identity" className="rounded-lg px-3.5 py-2">
                <span className="sm:hidden">Identidade</span>
                <span className="hidden sm:inline">Identidade e objetivos</span>
              </TabsTrigger>
              <TabsTrigger value="import" className="rounded-lg px-3.5 py-2">
                Importar
              </TabsTrigger>
            </TabsList>

            <TabsContent value="facts" className="animate-page-in">
              <FactsPanel
                items={items}
                demo={mode === "demo"}
                onAdd={() => setAdding(true)}
                onImport={() => setTab("import")}
                invalidate={invalidate}
              />
            </TabsContent>
            <TabsContent value="identity" className="animate-page-in">
              <IdentityPanel profile={profile} invalidate={invalidate} />
            </TabsContent>
            <TabsContent value="import" className="animate-page-in">
              <ImportPanel invalidate={invalidate} onReviewed={() => setTab("facts")} />
            </TabsContent>
          </Tabs>

          <AddFactDialog open={adding} onOpenChange={setAdding} invalidate={invalidate} />
        </div>
      )}
    </AppShell>
  );
}

function ProfileHero({
  profile,
  summary,
  onAdd,
  onImport,
}: {
  profile: UniversalCareerProfile;
  summary: ReturnType<typeof profileSummary>;
  onAdd: () => void;
  onImport: () => void;
}) {
  const confirmedShare = summary.items ? (summary.confirmed / summary.items) * 100 : 0;
  const domains = [...profile.primary_domains, ...profile.secondary_domains].slice(0, 5);
  return (
    <section className="trajectory-surface rounded-2xl px-6 py-7 md:px-9 md:py-8">
      <div className="grid gap-7 md:grid-cols-[1fr_auto] md:items-center">
        <div className="min-w-0">
          <p className="eyebrow inline-flex items-center gap-2 text-hero-accent">
            <UserRound aria-hidden className="h-3.5 w-3.5" />
            Perfil Profissional Universal
          </p>
          <h2 className="text-display mt-3 text-[28px] leading-tight md:text-[38px]">
            {profile.display_name || "Seu perfil profissional"}
          </h2>
          <p className="mt-2 max-w-2xl text-sm text-hero-muted md:text-base">
            {profile.headline ||
              "Comece pelos fatos: o que você fez, estudou e comprovou. A IA sugere; você revisa."}
          </p>
          {domains.length ? (
            <ul className="mt-4 flex flex-wrap gap-1.5" aria-label="Áreas">
              {domains.map((domain) => (
                <li
                  key={domain}
                  className="rounded-full border border-hero-foreground/15 bg-hero-foreground/10 px-2.5 py-0.5 text-xs"
                >
                  {domain}
                </li>
              ))}
            </ul>
          ) : null}
          <div className="mt-6 flex flex-wrap gap-2">
            <Button
              onClick={onAdd}
              className="bg-hero-foreground text-sidebar shadow-[var(--shadow-soft)] hover:bg-hero-foreground/90"
            >
              <Plus aria-hidden className="h-4 w-4" /> Adicionar fato
            </Button>
            <Button
              variant="outline"
              onClick={onImport}
              className="border-hero-foreground/25 bg-transparent text-hero-foreground hover:bg-hero-foreground/10 hover:text-hero-foreground"
            >
              <FileSearch aria-hidden className="h-4 w-4" /> Importar texto ou Lattes
            </Button>
          </div>
        </div>
        <div className="flex items-center gap-5 md:flex-col md:gap-3 md:text-center">
          <ScoreRing
            value={confirmedShare}
            size={120}
            tone="hero"
            suffix="%"
            sub="confirmados"
            ariaLabel="Fatos confirmados por você"
          />
          <dl className="grid grid-cols-3 gap-x-4 gap-y-1 text-center md:gap-x-5">
            {(
              [
                ["fatos", summary.items],
                ["fontes", summary.sources],
                ["áreas", summary.domains],
              ] as const
            ).map(([label, value]) => (
              <div key={label}>
                <dd className="text-metric text-xl">{value}</dd>
                <dt className="text-[11px] text-hero-muted">{label}</dt>
              </div>
            ))}
          </dl>
        </div>
      </div>
    </section>
  );
}

function FactsPanel({
  items,
  demo,
  onAdd,
  onImport,
  invalidate,
}: {
  items: ProfileItem[];
  demo: boolean;
  onAdd: () => void;
  onImport: () => void;
  invalidate: () => Promise<void>;
}) {
  const api = useApi();
  const [typeFilter, setTypeFilter] = useState("all");
  const [pendingOnly, setPendingOnly] = useState(false);

  const deleteItem = useMutation({
    mutationFn: (itemId: string) => api.profileDeleteItem(itemId),
    onSuccess: () => {
      toast.success("Item removido.");
      void invalidate();
    },
    onError: (error) => toast.error(error instanceof Error ? error.message : "Falha ao remover."),
  });
  const updateItem = useMutation({
    mutationFn: ({ itemId, patch }: { itemId: string; patch: Partial<ProfileItem> }) =>
      api.profilePatchItem(itemId, patch),
    onSuccess: (_data, { patch }) => {
      toast.success(Object.keys(patch).length ? "Item atualizado." : "Item confirmado.");
      void invalidate();
    },
    onError: (error) => toast.error(error instanceof Error ? error.message : "Falha ao editar."),
  });
  const dedupe = useMutation({
    mutationFn: () => api.profileDeduplicate(),
    onSuccess: (data) => toast.success(data.message || "Deduplicação concluída."),
    onError: (error) =>
      toast.error(error instanceof Error ? error.message : "Falha ao deduplicar."),
  });

  const counts = new Map<string, number>();
  for (const item of items) counts.set(item.type, (counts.get(item.type) ?? 0) + 1);
  const types = [...counts.keys()].sort((a, b) => typeLabel(a).localeCompare(typeLabel(b)));
  const pending = items.filter((item) => !item.confirmed_by_user).length;
  const visible = items.filter(
    (item) =>
      (typeFilter === "all" || item.type === typeFilter) &&
      (!pendingOnly || !item.confirmed_by_user),
  );

  if (!items.length) {
    return (
      <div className="rounded-xl border border-dashed bg-card p-8 text-center shadow-[var(--shadow-soft)]">
        <p className="text-lg font-semibold">
          {demo ? "Perfil demo vazio" : "Seu perfil ainda não tem fatos"}
        </p>
        <p className="mx-auto mt-2 max-w-lg text-sm text-muted-foreground">
          Cada fato (uma experiência, um curso, um certificado) guarda de onde veio e se você o
          confirmou. Currículos, Radar e análises usam só o que estiver aqui.
        </p>
        <div className="mt-5 flex flex-wrap justify-center gap-2">
          <Button onClick={onAdd}>
            <Plus aria-hidden className="h-4 w-4" /> Adicionar o primeiro fato
          </Button>
          <Button variant="outline" onClick={onImport}>
            <FileSearch aria-hidden className="h-4 w-4" /> Importar de um texto
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {pending > 0 && (
        <div className="flex flex-wrap items-center gap-3 rounded-xl border border-warning/40 bg-highlight/50 px-4 py-3 text-sm">
          <CircleDot aria-hidden className="h-4 w-4 shrink-0 text-warning-strong" />
          <p className="min-w-0 flex-1">
            <strong className="font-semibold">{pending} fato(s) aguardam sua confirmação.</strong>{" "}
            <span className="text-muted-foreground">
              Fatos não confirmados não entram no Currículo Mestre.
            </span>
          </p>
          <Button size="sm" variant="outline" onClick={() => setPendingOnly((value) => !value)}>
            {pendingOnly ? "Ver todos" : "Revisar agora"}
          </Button>
        </div>
      )}

      <div className="flex flex-wrap items-center gap-2">
        <div
          role="group"
          aria-label="Filtrar fatos por tipo"
          className="flex flex-wrap gap-1.5"
          data-testid="profile-type-filter"
        >
          {["all", ...types].map((type) => (
            <button
              key={type}
              type="button"
              aria-pressed={typeFilter === type}
              onClick={() => setTypeFilter(type)}
              className={cn(
                "rounded-full border px-3 py-1 text-xs font-medium transition-colors duration-(--duration-1)",
                typeFilter === type
                  ? "border-primary bg-primary text-primary-foreground"
                  : "bg-card text-muted-foreground hover:border-foreground/30 hover:text-foreground",
              )}
            >
              {type === "all" ? "Todos" : typeLabel(type)}
              <span className="tabular ml-1 opacity-70">
                {type === "all" ? items.length : counts.get(type)}
              </span>
            </button>
          ))}
        </div>
        <div className="ml-auto flex gap-2">
          <Button
            size="sm"
            variant="ghost"
            onClick={() => dedupe.mutate()}
            disabled={dedupe.isPending}
          >
            <RefreshCw
              aria-hidden
              className={cn("h-3.5 w-3.5", dedupe.isPending && "animate-spin")}
            />
            Procurar duplicados
          </Button>
          <Button size="sm" onClick={onAdd}>
            <Plus aria-hidden className="h-3.5 w-3.5" /> Adicionar fato
          </Button>
        </div>
      </div>

      <ul className="grid gap-3" data-testid="profile-items">
        {visible.map((item) => (
          <li key={item.item_id}>
            <FactCard
              item={item}
              onConfirm={() => updateItem.mutate({ itemId: item.item_id, patch: {} })}
              onEdit={(patch) => updateItem.mutate({ itemId: item.item_id, patch })}
              onDelete={() => deleteItem.mutate(item.item_id)}
            />
          </li>
        ))}
      </ul>
      {!visible.length && (
        <EmptyState
          title="Nenhum fato neste filtro"
          description="Troque o tipo ou mostre também os confirmados."
        />
      )}
    </div>
  );
}

function FactCard({
  item,
  onConfirm,
  onEdit,
  onDelete,
}: {
  item: ProfileItem;
  onConfirm: () => void;
  onEdit: (patch: Partial<ProfileItem>) => void;
  onDelete: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(() => editDraft(item));
  useEffect(() => setDraft(editDraft(item)), [item]);
  const place = item.organization || item.institution;
  const period = [item.start_date, item.end_date].filter(Boolean).join(" – ");
  const text = item.description || item.evidence;
  return (
    <article
      className={cn(
        "group rounded-xl border bg-card p-4 shadow-[var(--shadow-soft)] transition-[border-color,box-shadow] duration-(--duration-2) hover:shadow-[var(--shadow-elevated)] md:p-5",
        !item.confirmed_by_user && "border-l-4 border-l-warning",
      )}
    >
      <div className="flex flex-col gap-3 md:flex-row md:items-start">
        <div className="min-w-0 flex-1">
          <p className="eyebrow text-muted-foreground">{typeLabel(item.type)}</p>
          <h3 className="mt-1 font-semibold leading-snug">
            <span className={cn(!item.confirmed_by_user && "mark-pending")}>{item.title}</span>
          </h3>
          {(place || period) && (
            <p className="mt-0.5 text-sm text-muted-foreground">
              {[place, period].filter(Boolean).join(" · ")}
            </p>
          )}
          {text && <p className="mt-2 text-sm leading-relaxed">{text}</p>}
          <div className="mt-3 flex flex-wrap items-center gap-1.5 text-xs">
            <Chip tone={item.confirmed_by_user ? "success" : "warning"}>
              {item.confirmed_by_user ? (
                <CheckCircle2 aria-hidden className="h-3 w-3" />
              ) : (
                <CircleDot aria-hidden className="h-3 w-3" />
              )}
              {item.confirmed_by_user ? "Confirmado" : "Revisar"}
            </Chip>
            <Chip>Origem: {sourceLabel(item.source)}</Chip>
            <Chip>{confidenceLabel(item.confidence)}</Chip>
            {(item.domain || item.area) && <Chip>{item.domain || item.area}</Chip>}
          </div>
        </div>
        <div className="flex shrink-0 flex-wrap gap-1.5">
          {!item.confirmed_by_user && (
            <Button size="sm" onClick={onConfirm}>
              <CheckCircle2 aria-hidden className="h-3.5 w-3.5" /> Confirmar
            </Button>
          )}
          <Button
            size="sm"
            variant="outline"
            aria-expanded={editing}
            onClick={() => setEditing((value) => !value)}
          >
            <Pencil aria-hidden className="h-3.5 w-3.5" /> Editar
          </Button>
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button
                size="sm"
                variant="ghost"
                className="text-destructive-strong hover:bg-destructive/10 hover:text-destructive-strong"
              >
                <Trash2 aria-hidden className="h-3.5 w-3.5" /> Remover
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Remover “{item.title}” do Perfil?</AlertDialogTitle>
                <AlertDialogDescription>
                  O fato sai do Perfil e deixa de aparecer em novas análises. Currículos já montados
                  mantêm o texto que já têm.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Manter</AlertDialogCancel>
                <AlertDialogAction
                  onClick={onDelete}
                  className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                >
                  Remover
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </div>
      {editing && (
        <form
          className="mt-4 grid gap-4 rounded-lg border bg-surface p-4 md:grid-cols-2"
          onSubmit={(event) => {
            event.preventDefault();
            onEdit({
              title: draft.title,
              organization: draft.organization,
              domain: draft.domain,
              area: draft.domain,
              evidence: draft.evidence,
              description: draft.evidence,
            });
            setEditing(false);
          }}
        >
          <Field label="Título" error={!draft.title.trim() ? "O fato precisa de um título." : null}>
            {(control) => (
              <input
                {...control}
                value={draft.title}
                onChange={(event) => setDraft({ ...draft, title: event.target.value })}
                className={controlClass}
              />
            )}
          </Field>
          <Field label="Organização ou instituição" optional>
            {(control) => (
              <input
                {...control}
                value={draft.organization}
                onChange={(event) => setDraft({ ...draft, organization: event.target.value })}
                className={controlClass}
              />
            )}
          </Field>
          <Field label="Área" optional>
            {(control) => (
              <input
                {...control}
                value={draft.domain}
                onChange={(event) => setDraft({ ...draft, domain: event.target.value })}
                className={controlClass}
              />
            )}
          </Field>
          <Field
            label="Evidência ou descrição"
            hint="O que comprova este fato. Salvar uma edição o marca como confirmado."
            className="md:col-span-2"
          >
            {(control) => (
              <textarea
                {...control}
                value={draft.evidence}
                onChange={(event) => setDraft({ ...draft, evidence: event.target.value })}
                className={textareaClass}
              />
            )}
          </Field>
          <div className="flex gap-2 md:col-span-2">
            <Button type="submit" size="sm" disabled={!draft.title.trim()}>
              <Save aria-hidden className="h-3.5 w-3.5" /> Salvar edição
            </Button>
            <Button
              type="button"
              size="sm"
              variant="ghost"
              onClick={() => {
                setDraft(editDraft(item));
                setEditing(false);
              }}
            >
              Cancelar
            </Button>
          </div>
        </form>
      )}
    </article>
  );
}

function editDraft(item: ProfileItem) {
  return {
    title: item.title,
    organization: item.organization || item.institution || "",
    domain: item.domain || item.area || "",
    evidence: item.evidence || item.description || "",
  };
}

function AddFactDialog({
  open,
  onOpenChange,
  invalidate,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  invalidate: () => Promise<void>;
}) {
  const api = useApi();
  const [form, setForm] = useState(() => itemFormDefaults());
  const [touched, setTouched] = useState(false);
  const addItem = useMutation({
    mutationFn: (item: Partial<ProfileItem>) => api.profileAddItem(item),
    onSuccess: () => {
      toast.success("Item adicionado ao perfil.");
      setForm(itemFormDefaults());
      setTouched(false);
      onOpenChange(false);
      void invalidate();
    },
    onError: (error) =>
      toast.error(error instanceof Error ? error.message : "Falha ao adicionar item."),
  });
  const titleError = touched && !form.title.trim() ? "Dê um título ao fato." : null;
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Adicionar um fato ao Perfil</DialogTitle>
          <DialogDescription>
            Fatos que você informa entram confirmados. Escreva como diria numa entrevista.
          </DialogDescription>
        </DialogHeader>
        <form
          className="grid gap-4"
          onSubmit={(event) => {
            event.preventDefault();
            setTouched(true);
            if (!form.title.trim()) return;
            addItem.mutate({
              ...form,
              area: form.domain,
              description: form.evidence,
              source: "manual",
            });
          }}
        >
          <Field label="Tipo">
            {(control) => (
              <select
                {...control}
                value={form.type}
                onChange={(event) => setForm({ ...form, type: event.target.value })}
                className={controlClass}
              >
                {MANUAL_TYPES.map((type) => (
                  <option key={type} value={type}>
                    {typeLabel(type)}
                  </option>
                ))}
              </select>
            )}
          </Field>
          <Field label="Título" error={titleError}>
            {(control) => (
              <input
                {...control}
                value={form.title}
                onChange={(event) => setForm({ ...form, title: event.target.value })}
                onBlur={() => setTouched(true)}
                placeholder="Ex.: NR10, Estágio em obra, Mestrado em Geofísica"
                data-testid="profile-item-title"
                className={controlClass}
                autoFocus
              />
            )}
          </Field>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Organização ou instituição" optional>
              {(control) => (
                <input
                  {...control}
                  value={form.organization}
                  onChange={(event) => setForm({ ...form, organization: event.target.value })}
                  className={controlClass}
                />
              )}
            </Field>
            <Field label="Área" optional>
              {(control) => (
                <input
                  {...control}
                  value={form.domain}
                  onChange={(event) => setForm({ ...form, domain: event.target.value })}
                  placeholder="Engenharia, Saúde, Direito…"
                  className={controlClass}
                />
              )}
            </Field>
          </div>
          <Field label="Evidência" hint="O que comprova: certificado, resultado, link, número.">
            {(control) => (
              <textarea
                {...control}
                value={form.evidence}
                onChange={(event) => setForm({ ...form, evidence: event.target.value })}
                data-testid="profile-item-evidence"
                className={textareaClass}
              />
            )}
          </Field>
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={addItem.isPending} data-testid="profile-add-item">
              {addItem.isPending ? (
                <Loader2 aria-hidden className="h-4 w-4 animate-spin" />
              ) : (
                <Plus aria-hidden className="h-4 w-4" />
              )}
              Adicionar item
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

const IDENTITY_FIELDS: {
  key: keyof ReturnType<typeof profileFormDefaults>;
  label: string;
  hint?: string;
  placeholder?: string;
}[] = [
  { key: "primary_domains", label: "Áreas principais", placeholder: "Engenharia, Saúde, Direito" },
  { key: "secondary_domains", label: "Áreas secundárias" },
  { key: "target_roles", label: "Cargos ou objetivos" },
  { key: "career_moments", label: "Momento de carreira", placeholder: "estágio, transição…" },
  { key: "target_seniority", label: "Senioridade alvo" },
  { key: "preferred_locations", label: "Localizações preferidas" },
  { key: "preferred_work_models", label: "Modalidade", placeholder: "remoto, híbrido, presencial" },
  { key: "preferred_contract_types", label: "Contrato", placeholder: "estágio, CLT, PJ, bolsa" },
];

function IdentityPanel({
  profile,
  invalidate,
}: {
  profile: UniversalCareerProfile;
  invalidate: () => Promise<void>;
}) {
  const api = useApi();
  const saved = useMemo(() => profileToForm(profile), [profile]);
  const [form, setForm] = useState(saved);
  useEffect(() => setForm(saved), [saved]);
  const dirty = (Object.keys(saved) as (keyof typeof saved)[]).some(
    (key) => form[key] !== saved[key],
  );
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
      void invalidate();
    },
    onError: (error) => toast.error(error instanceof Error ? error.message : "Falha ao salvar."),
  });
  const set = (key: keyof typeof form) => (value: string) => setForm({ ...form, [key]: value });

  return (
    <form
      className="space-y-5"
      onSubmit={(event) => {
        event.preventDefault();
        saveProfile.mutate();
      }}
    >
      <PanelCard title="Quem você é" description="Aparece no topo dos currículos e das análises.">
        <div className="grid gap-4 md:grid-cols-2">
          <Field label="Nome">
            {(control) => (
              <input
                {...control}
                value={form.display_name}
                onChange={(event) => set("display_name")(event.target.value)}
                data-testid="profile-name"
                autoComplete="name"
                className={controlClass}
              />
            )}
          </Field>
          <Field label="Headline" hint="Uma linha: quem você é profissionalmente.">
            {(control) => (
              <input
                {...control}
                value={form.headline}
                onChange={(event) => set("headline")(event.target.value)}
                className={controlClass}
              />
            )}
          </Field>
          <Field
            label="Resumo"
            optional
            hint={`${form.summary.length} caracteres. Três a cinco frases costumam bastar.`}
            className="md:col-span-2"
          >
            {(control) => (
              <textarea
                {...control}
                value={form.summary}
                onChange={(event) => set("summary")(event.target.value)}
                className={textareaClass}
              />
            )}
          </Field>
        </div>
      </PanelCard>
      <PanelCard
        title="O que você busca"
        description="Radar, Match e Ajuste usam estas preferências. Separe vários valores por vírgula."
      >
        <div className="grid gap-4 md:grid-cols-2">
          {IDENTITY_FIELDS.map((field) => (
            <Field key={field.key} label={field.label} optional>
              {(control) => (
                <>
                  <input
                    {...control}
                    value={form[field.key]}
                    onChange={(event) => set(field.key)(event.target.value)}
                    placeholder={field.placeholder}
                    className={controlClass}
                  />
                  <TokenPreview value={form[field.key]} />
                </>
              )}
            </Field>
          ))}
        </div>
      </PanelCard>
      <div
        className={cn(
          "sticky bottom-20 z-10 flex flex-wrap items-center gap-3 rounded-xl border bg-card/95 px-4 py-3 shadow-[var(--shadow-elevated)] backdrop-blur-md transition-[border-color] duration-(--duration-2) lg:bottom-4",
          dirty && "border-warning/50",
        )}
      >
        <p role="status" className="min-w-0 flex-1 text-sm">
          {saveProfile.isPending
            ? "Salvando…"
            : dirty
              ? "Alterações ainda não salvas."
              : "Tudo salvo."}
        </p>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          disabled={!dirty || saveProfile.isPending}
          onClick={() => setForm(saved)}
        >
          <Undo2 aria-hidden className="h-3.5 w-3.5" /> Descartar
        </Button>
        <Button
          type="submit"
          size="sm"
          disabled={!dirty || saveProfile.isPending}
          data-testid="profile-save"
        >
          {saveProfile.isPending ? (
            <Loader2 aria-hidden className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <Save aria-hidden className="h-3.5 w-3.5" />
          )}
          Salvar
        </Button>
      </div>
    </form>
  );
}

function TokenPreview({ value }: { value: string }) {
  const tokens = splitList(value);
  if (tokens.length < 2) return null;
  return (
    <ul className="mt-1.5 flex flex-wrap gap-1" aria-hidden>
      {tokens.map((token) => (
        <li key={token} className="rounded-full bg-surface-accent px-2 py-0.5 text-[11px]">
          {token}
        </li>
      ))}
    </ul>
  );
}

function ImportPanel({
  invalidate,
  onReviewed,
}: {
  invalidate: () => Promise<void>;
  onReviewed: () => void;
}) {
  const api = useApi();
  const [sourceType, setSourceType] = useState("manual_notes");
  const [importText, setImportText] = useState("");
  const [useAi, setUseAi] = useState(true);
  const [draft, setDraft] = useState<ProfileImportResult | null>(null);
  const [added, setAdded] = useState<Set<string>>(new Set());
  const [lattesText, setLattesText] = useState("");
  const [lattesId, setLattesId] = useState("");
  const [lattesUrl, setLattesUrl] = useState("");
  const [orcid, setOrcid] = useState("");
  const [useLattesAi, setUseLattesAi] = useState(false);
  const [lattesDraft, setLattesDraft] = useState<LattesImportResult | null>(null);
  const [lattesSelectedIds, setLattesSelectedIds] = useState<Set<string>>(new Set());
  const [lattesFilter, setLattesFilter] = useState("all");

  const importProfile = useMutation({
    mutationFn: () =>
      api.profileImportText({ text: importText, source_type: sourceType, use_ai: useAi }),
    onSuccess: (data) => {
      setDraft(data);
      setAdded(new Set());
      toast.success("Itens extraídos para revisão.");
    },
    onError: (error) => toast.error(error instanceof Error ? error.message : "Falha ao extrair."),
  });
  const addItem = useMutation({
    mutationFn: (item: ProfileItem) => api.profileAddItem(item),
    onSuccess: (_data, item) => {
      toast.success("Item adicionado ao perfil.");
      setAdded((current) => new Set(current).add(item.item_id));
      void invalidate();
    },
    onError: (error) =>
      toast.error(error instanceof Error ? error.message : "Falha ao adicionar item."),
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
      void invalidate();
    },
    onError: (error) =>
      toast.error(error instanceof Error ? error.message : "Falha ao confirmar itens."),
  });

  const lattesItems = lattesDraft?.items ?? [];
  const lattesTypes = ["all", ...Array.from(new Set(lattesItems.map((item) => item.type))).sort()];
  const visibleLattesItems =
    lattesFilter === "all" ? lattesItems : lattesItems.filter((item) => item.type === lattesFilter);

  return (
    <div className="space-y-5">
      <p className="flex items-start gap-2 rounded-xl border bg-surface-accent px-4 py-3 text-sm">
        <Sparkle aria-hidden className="mt-0.5 h-4 w-4 shrink-0 text-accent-strong" />
        Nada importado entra no Perfil sem a sua revisão: cada item extraído aparece abaixo para
        você adicionar ou ignorar.
      </p>
      <div className="grid gap-5 xl:grid-cols-2">
        <PanelCard
          title="Texto livre"
          description="Currículo, portfólio, certificado ou notas. Cole um trecho; você revisa o que sair."
        >
          <div className="space-y-4">
            <Field label="Texto para extração">
              {(control) => (
                <textarea
                  {...control}
                  value={importText}
                  onChange={(event) => setImportText(event.target.value)}
                  placeholder="Cole um trecho fictício de currículo, Lattes, portfólio ou certificado."
                  data-testid="profile-import-textarea"
                  className={cn(textareaClass, "min-h-44")}
                />
              )}
            </Field>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Tipo de fonte">
                {(control) => (
                  <select
                    {...control}
                    value={sourceType}
                    onChange={(event) => setSourceType(event.target.value)}
                    className={controlClass}
                  >
                    {sourceTypes.map(([value, label]) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </select>
                )}
              </Field>
              <label className="flex items-center gap-2 self-end rounded-lg border bg-surface px-3 py-2 text-sm">
                <input
                  type="checkbox"
                  checked={useAi}
                  onChange={(event) => setUseAi(event.target.checked)}
                />
                Usar IA se configurada
              </label>
            </div>
            <Button
              onClick={() => importProfile.mutate()}
              disabled={!importText.trim() || importProfile.isPending}
              data-testid="profile-import-text"
            >
              {importProfile.isPending ? (
                <Loader2 aria-hidden className="h-4 w-4 animate-spin" />
              ) : (
                <FileSearch aria-hidden className="h-4 w-4" />
              )}
              Extrair itens
            </Button>
          </div>
        </PanelCard>

        <PanelCard
          title="Acadêmico / Lattes"
          description="Texto colado do Currículo Lattes ou da trajetória acadêmica."
          actions={
            <ProviderBadge
              provider={lattesDraft?.provider_used || "local"}
              mode={lattesDraft?.analysis_mode || "local"}
              fallback={lattesDraft?.analysis_mode === "fallback"}
            />
          }
        >
          <div className="space-y-4" data-testid="profile-lattes-section">
            <p
              className="flex items-start gap-2 rounded-lg border border-warning/40 bg-highlight/50 px-3 py-2 text-xs"
              data-testid="profile-lattes-review-warning"
            >
              <GraduationCap aria-hidden className="mt-0.5 h-4 w-4 shrink-0 text-warning-strong" />
              Nada é salvo sem revisão. O SotuHire não acessa sua conta Lattes, não faz login e não
              usa scraping autenticado.
            </p>
            <Field label="Texto do Currículo Lattes ou acadêmico">
              {(control) => (
                <textarea
                  {...control}
                  value={lattesText}
                  onChange={(event) => setLattesText(event.target.value)}
                  placeholder="Formação, projetos, publicações, extensão, docência, prêmios, eventos ou produção técnica/artística."
                  data-testid="profile-lattes-textarea"
                  className={cn(textareaClass, "min-h-44")}
                />
              )}
            </Field>
            <details className="rounded-lg border bg-surface px-3 py-2 text-sm">
              <summary className="cursor-pointer font-medium">Identificadores (opcional)</summary>
              <div className="mt-3 grid gap-3 sm:grid-cols-3">
                <Field label="Lattes ID" optional>
                  {(control) => (
                    <input
                      {...control}
                      value={lattesId}
                      onChange={(event) => setLattesId(event.target.value)}
                      className={controlClass}
                    />
                  )}
                </Field>
                <Field label="URL do Lattes" optional>
                  {(control) => (
                    <input
                      {...control}
                      value={lattesUrl}
                      onChange={(event) => setLattesUrl(event.target.value)}
                      placeholder="https://lattes.cnpq.br/..."
                      className={controlClass}
                    />
                  )}
                </Field>
                <Field label="ORCID" optional>
                  {(control) => (
                    <input
                      {...control}
                      value={orcid}
                      onChange={(event) => setOrcid(event.target.value)}
                      className={controlClass}
                    />
                  )}
                </Field>
              </div>
            </details>
            <div className="flex flex-wrap items-center gap-3">
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={useLattesAi}
                  onChange={(event) => setUseLattesAi(event.target.checked)}
                />
                Usar IA/Gemini se configurada
              </label>
              <Button
                className="ml-auto"
                onClick={() => importLattes.mutate()}
                disabled={!lattesText.trim() || importLattes.isPending}
                data-testid="profile-lattes-extract"
              >
                {importLattes.isPending ? (
                  <Loader2 aria-hidden className="h-4 w-4 animate-spin" />
                ) : (
                  <FileSearch aria-hidden className="h-4 w-4" />
                )}
                Extrair do Lattes
              </Button>
            </div>
          </div>
        </PanelCard>
      </div>

      {draft && (
        <PanelCard
          title="Itens extraídos para revisão"
          description="Itens de IA ou da extração local começam como não confirmados. Adicione só o que for verdadeiro."
          actions={
            <ProviderBadge
              provider={draft.provider_used || "local"}
              mode={draft.analysis_mode || "local"}
              fallback={draft.analysis_mode === "fallback"}
            />
          }
        >
          <div className="space-y-3" data-testid="profile-draft-items">
            {draft.warnings.map((warning) => (
              <p
                key={warning}
                className="rounded-lg border border-warning/40 bg-highlight/50 px-3 py-2 text-xs"
              >
                {warning}
              </p>
            ))}
            {draft.items.map((item) => (
              <DraftRow key={item.item_id} item={item}>
                {added.has(item.item_id) ? (
                  <span className="inline-flex items-center gap-1 text-xs font-medium text-success-strong">
                    <CheckCircle2 aria-hidden className="h-3.5 w-3.5" /> No Perfil
                  </span>
                ) : (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => addItem.mutate(item)}
                    disabled={addItem.isPending}
                  >
                    <Plus aria-hidden className="h-3.5 w-3.5" /> Adicionar ao perfil
                  </Button>
                )}
              </DraftRow>
            ))}
            {added.size > 0 && (
              <Button size="sm" variant="ghost" onClick={onReviewed}>
                Ver os fatos do Perfil
              </Button>
            )}
          </div>
        </PanelCard>
      )}

      {lattesDraft && (
        <PanelCard
          title="Candidatos do Lattes"
          description={`${lattesDraft.items.length} candidato(s), confiança ${confidenceLabel(lattesDraft.confidence).toLowerCase()}.`}
          actions={
            <div className="flex flex-wrap items-center gap-2">
              <select
                aria-label="Filtrar candidatos do Lattes por tipo"
                value={lattesFilter}
                onChange={(event) => setLattesFilter(event.target.value)}
                className="h-8 rounded-lg border bg-card px-2 text-xs"
              >
                {lattesTypes.map((type) => (
                  <option key={type} value={type}>
                    {type === "all" ? "Todos os tipos" : typeLabel(type)}
                  </option>
                ))}
              </select>
              <Button
                size="sm"
                onClick={() => confirmLattes.mutate()}
                disabled={!lattesSelectedIds.size || confirmLattes.isPending}
                data-testid="profile-lattes-add-selected"
              >
                <CheckCircle2 aria-hidden className="h-3.5 w-3.5" />
                Adicionar {lattesSelectedIds.size} ao Perfil
              </Button>
            </div>
          }
        >
          <div className="space-y-3" data-testid="profile-lattes-candidates">
            {[...lattesDraft.warnings, ...lattesDraft.assumptions].map((warning) => (
              <p
                key={warning}
                className="rounded-lg border border-warning/40 bg-highlight/50 px-3 py-2 text-xs"
              >
                {warning}
              </p>
            ))}
            {visibleLattesItems.map((item) => (
              <label key={item.item_id} className="block cursor-pointer">
                <DraftRow
                  item={item}
                  leading={
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
                  }
                />
              </label>
            ))}
            {!visibleLattesItems.length && (
              <EmptyState
                title="Nenhum candidato neste filtro"
                description="Troque o tipo do filtro para ver outros itens extraídos."
              />
            )}
          </div>
        </PanelCard>
      )}
    </div>
  );
}

function DraftRow({
  item,
  leading,
  children,
}: {
  item: ProfileItem;
  leading?: ReactNode;
  children?: ReactNode;
}) {
  return (
    <div className="flex gap-3 rounded-lg border border-l-4 border-l-warning bg-surface p-3.5">
      {leading}
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-1.5">
          <h3 className="mr-1 font-semibold">{item.title}</h3>
          <Chip>{typeLabel(item.type)}</Chip>
          <Chip>{confidenceLabel(item.confidence)}</Chip>
          <Chip tone="warning">Revisar</Chip>
        </div>
        <p className="mt-1.5 text-sm text-muted-foreground">
          {item.description || item.evidence || "Sem descrição."}
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          {item.domain || item.area || "Área não informada"} · Origem: {sourceLabel(item.source)}
        </p>
      </div>
      {children ? <div className="shrink-0 self-center">{children}</div> : null}
    </div>
  );
}

function PanelCard({
  title,
  description,
  actions,
  children,
}: {
  title: string;
  description?: string;
  actions?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="rounded-xl border bg-card shadow-[var(--shadow-soft)]">
      <header className="flex flex-wrap items-start justify-between gap-3 border-b bg-surface/60 px-5 py-4">
        <div className="min-w-0">
          <h2 className="font-semibold tracking-tight">{title}</h2>
          {description && <p className="mt-0.5 text-sm text-muted-foreground">{description}</p>}
        </div>
        {actions}
      </header>
      <div className="p-5">{children}</div>
    </section>
  );
}

function Chip({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: "neutral" | "success" | "warning";
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium",
        tone === "success"
          ? "bg-success/12 text-success-strong"
          : tone === "warning"
            ? "bg-highlight text-highlight-foreground"
            : "bg-muted text-muted-foreground",
      )}
    >
      {children}
    </span>
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
  return { type: "project", title: "", organization: "", domain: "", evidence: "" };
}

function profileToForm(profile: UniversalCareerProfile): ReturnType<typeof profileFormDefaults> {
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
