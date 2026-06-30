import { createFileRoute, Link } from "@tanstack/react-router";
import {
  AlertTriangle,
  Archive,
  ArrowRight,
  CheckCircle2,
  Copy,
  Database,
  Download,
  ExternalLink,
  Filter,
  Github,
  Merge,
  Monitor,
  PlugZap,
  RefreshCw,
  Save,
  ShieldAlert,
  Terminal,
  Upload,
  XCircle,
} from "lucide-react";
import { useEffect, useMemo, useState, type ChangeEvent } from "react";
import { AppShell } from "@/components/app-shell";
import { SectionCard } from "@/components/section-card";
import { SourceCardItem } from "@/components/source-card";
import { useApi } from "@/lib/api/hooks";
import { useApiMode } from "@/lib/api/mode";
import type {
  AuthenticatedBrowserCollectResult,
  AuthenticatedBrowserStatus,
  ExtensionCapture,
  OpportunityInboxItem,
  ProfileItem,
  SourceCaptureStatus,
  SourceDirectoryEntry,
  SourceOrigin,
} from "@/lib/api/types";
import { SOURCE_CARDS, SOURCE_FLOW } from "@/mocks/sources";
import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";

export const Route = createFileRoute("/sources")({
  head: () => ({
    meta: [
      { title: "Fontes e Captura — SotuHire" },
      {
        name: "description",
        content:
          "Importe, cole ou capture vagas com controle do usuário. Local-first, sem automação de contas de terceiros.",
      },
    ],
  }),
  component: SourcesPage,
});

const RELATED: { to: string; label: string }[] = [
  { to: "/job", label: "Vaga" },
  { to: "/match", label: "Análise de Compatibilidade" },
  { to: "/tracker", label: "Candidaturas" },
  { to: "/intelligence", label: "Inteligência" },
];

const AUTH_BROWSER_STEPS = [
  "Instalar as dependencias opcionais de scraping local.",
  "Abrir o Streamlit local e selecionar Navegador autenticado autorizado.",
  "Abrir Chromium dedicado, fazer login manualmente e testar CDP.",
  "Confirmar uso autorizado, limites e referencia de autorizacao.",
  "Coletar somente itens visiveis permitidos, sem candidatura automatica.",
];

const AUTH_BROWSER_LIMITS = [
  "Nao automatiza login.",
  "Interrompe em CAPTCHA, checkpoint ou nova tela de autenticacao.",
  "Nao envia candidatura e nao clica em auto apply.",
  "Usa perfil local dedicado em %LOCALAPPDATA%\\SotuHire.",
  "Requer autorizacao explicita antes da coleta.",
];

type FilePreview = {
  kind: "csv" | "json";
  name: string;
  text: string;
  rows: string[];
  error?: string;
};

type ExtensionCandidateReview = {
  captureId: string;
  title: string;
  isProject: boolean;
  candidates: ProfileItem[];
  selectedIds: string[];
  contextSummary: string;
  warnings: string[];
  message: string;
};

const MAX_IMPORT_FILE_BYTES = 512_000;

function SourcesPage() {
  return (
    <AppShell
      title="Fontes e Captura"
      description="Importe, cole ou capture vagas com controle do usuário. O SotuHire organiza e analisa sem automatizar ações em contas de terceiros."
    >
      <div className="space-y-6">
        <div className="flex items-start gap-3 rounded-xl border border-warning/40 bg-warning/5 p-4">
          <div className="grid h-9 w-9 shrink-0 place-items-center rounded-md bg-warning/15 text-warning">
            <ShieldAlert className="h-4 w-4" />
          </div>
          <div className="text-sm">
            <div className="font-medium">Aviso de segurança</div>
            <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
              O SotuHire não automatiza login, candidatura ou ações em contas de terceiros. A
              captura assistida depende de ação manual do usuário e serve apenas para organizar e
              analisar informações visíveis.
            </p>
          </div>
        </div>

        <SectionCard
          id="opportunity-inbox"
          title={
            <span className="flex items-center gap-2">
              <Database className="h-4 w-4 text-accent" />
              Caixa de Entrada de Oportunidades
            </span>
          }
          description="Importe texto, link, CSV ou JSON e revise tudo antes de enviar para Vaga, Compatibilidade ou Candidaturas."
        >
          <OpportunityInboxPanel />
        </SectionCard>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {SOURCE_CARDS.map((c) => (
            <SourceCardItem key={c.id} card={c} />
          ))}
        </div>

        <SectionCard
          id="local-extension"
          title={
            <span className="flex items-center gap-2">
              <PlugZap className="h-4 w-4 text-accent" />
              Extensão Local
            </span>
          }
          description="Capturas já enviadas pela extensão assistiva para a Local Companion API."
        >
          <LocalExtensionPanel />
        </SectionCard>

        <SectionCard
          id="authenticated-browser"
          title={
            <span className="flex items-center gap-2">
              <Monitor className="h-4 w-4 text-accent" />
              Navegador autenticado autorizado
            </span>
          }
          description="Fluxo existente do SotuHire local para fontes autorizadas que exigem sessao humana. O frontend moderno mostra o caminho e os limites; a execucao permanece no app local/backend."
        >
          <AuthenticatedBrowserPanel />
        </SectionCard>

        <div className="grid gap-6 lg:grid-cols-3">
          <SectionCard className="lg:col-span-2" title="Fluxo recomendado">
            <ol className="grid gap-3 sm:grid-cols-5">
              {SOURCE_FLOW.map((step, i) => (
                <li
                  key={step}
                  className="relative rounded-lg border border-border bg-muted/30 p-3 text-xs"
                >
                  <div className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-accent">
                    Etapa {i + 1}
                  </div>
                  <div className="font-medium leading-snug">{step}</div>
                </li>
              ))}
            </ol>
          </SectionCard>

          <SectionCard title="Conecta com">
            <ul className="space-y-1.5">
              {RELATED.map((r) => (
                <li key={r.to}>
                  <Link
                    to={r.to}
                    className="flex items-center justify-between rounded-md border border-border bg-muted/30 px-3 py-2 text-xs font-medium transition-colors hover:border-primary/40 hover:bg-muted"
                  >
                    <span>{r.label}</span>
                    <ArrowRight className="h-3.5 w-3.5 text-muted-foreground" />
                  </Link>
                </li>
              ))}
            </ul>
          </SectionCard>
        </div>
      </div>
    </AppShell>
  );
}

const SAMPLE_CSV = `cargo,empresa,link,local,descricao,fonte,status,observacoes
Analista de Dados,Empresa Exemplo,https://example.com/jobs/123,Remoto,"Python, SQL e dashboards",CSV Manual,nova,"vaga ficticia"
Desenvolvedor Backend,Tech Exemplo,https://example.com/jobs/456,Hibrido,"APIs, testes e bancos de dados",CSV Manual,nova,"vaga ficticia"`;

const SAMPLE_TEXT =
  "Cargo: Analista de Dados\nEmpresa: Empresa Exemplo\nLocalizacao: Remoto\nRequisitos: Python, SQL e dashboards.";
const SAMPLE_URL = "https://example.com/jobs/123";

const SAMPLE_JSON = JSON.stringify(
  [
    {
      cargo: "Analista de Dados",
      empresa: "Empresa Exemplo",
      link: "https://example.com/jobs/123",
      local: "Remoto",
      descricao: "Python, SQL e dashboards.",
      fonte: "JSON Manual",
      status: "nova",
      observacoes: "vaga ficticia",
    },
  ],
  null,
  2,
);

function OpportunityInboxPanel() {
  const api = useApi();
  const { mode, baseUrl } = useApiMode();
  const inboxQ = useQuery({
    queryKey: ["source-imports", mode, baseUrl],
    queryFn: () => api.sourceImports(),
    retry: false,
  });
  const statsQ = useQuery({
    queryKey: ["source-stats", mode, baseUrl],
    queryFn: () => api.sourceStats(),
    retry: false,
  });
  const [directoryQuery, setDirectoryQuery] = useState("");
  const directoryQ = useQuery({
    queryKey: ["source-directory", mode, baseUrl, directoryQuery],
    queryFn: () => api.sourceDirectory(directoryQuery),
    retry: false,
  });
  const [text, setText] = useState(mode === "demo" ? SAMPLE_TEXT : "");
  const [url, setUrl] = useState(mode === "demo" ? SAMPLE_URL : "");
  const [csvText, setCsvText] = useState(mode === "demo" ? SAMPLE_CSV : "");
  const [jsonText, setJsonText] = useState(mode === "demo" ? SAMPLE_JSON : "");
  const [filePreview, setFilePreview] = useState<FilePreview | null>(null);
  const [useAiImport, setUseAiImport] = useState(false);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [exportFormat, setExportFormat] = useState<"csv" | "json">("csv");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | SourceCaptureStatus>("all");
  const [originFilter, setOriginFilter] = useState<"all" | SourceOrigin>("all");

  useEffect(() => {
    if (mode === "real") {
      setText("");
      setUrl("");
      setCsvText("");
      setJsonText("");
      setFilePreview(null);
      return;
    }
    setText((current) => current || SAMPLE_TEXT);
    setUrl((current) => current || SAMPLE_URL);
    setCsvText((current) => current || SAMPLE_CSV);
    setJsonText((current) => current || SAMPLE_JSON);
  }, [mode]);

  const refresh = () => {
    inboxQ.refetch();
    statsQ.refetch();
  };

  const importText = useMutation({
    mutationFn: () =>
      api.sourceImportText({
        text,
        source_name: "Texto manual",
        title: "Analista de Dados",
        company: "Empresa Exemplo",
        url,
        use_ai: useAiImport,
      }),
    onSuccess: (data) => {
      toast.success(data.message || "Importacao concluida.");
      refresh();
    },
    onError: (error) =>
      toast.error(error instanceof Error ? error.message : "Nao foi possivel importar texto."),
  });

  const importUrl = useMutation({
    mutationFn: () => api.sourceImportUrl({ url, source_name: "Link manual", use_ai: useAiImport }),
    onSuccess: (data) => {
      toast.success(data.message || "Link registrado.");
      refresh();
    },
    onError: (error) =>
      toast.error(error instanceof Error ? error.message : "Nao foi possivel importar link."),
  });

  const importCsv = useMutation({
    mutationFn: (input?: string) =>
      api.sourceImportCsv({
        csv_text: input ?? csvText,
        source_name: "CSV Manual",
        use_ai: useAiImport,
      }),
    onSuccess: (data) => {
      toast.success(data.message || "CSV importado.");
      setFilePreview(null);
      refresh();
    },
    onError: (error) =>
      toast.error(error instanceof Error ? error.message : "Nao foi possivel importar CSV."),
  });

  const importJson = useMutation({
    mutationFn: (input?: string) =>
      api.sourceImportJson({
        json_text: input ?? jsonText,
        source_name: "JSON Manual",
        use_ai: useAiImport,
      }),
    onSuccess: (data) => {
      toast.success(data.message || "JSON importado.");
      setFilePreview(null);
      refresh();
    },
    onError: (error) =>
      toast.error(error instanceof Error ? error.message : "Nao foi possivel importar JSON."),
  });

  const patchCapture = useMutation({
    mutationFn: ({
      id,
      status,
      notes,
      duplicate_of,
    }: {
      id: string;
      status?: SourceCaptureStatus;
      notes?: string;
      duplicate_of?: string;
    }) => api.sourcePatchCapture(id, { status, notes, duplicate_of }),
    onSuccess: (data) => {
      toast.success(data.message || "Item atualizado.");
      refresh();
    },
    onError: (error) =>
      toast.error(error instanceof Error ? error.message : "Nao foi possivel atualizar item."),
  });

  const mergeCapture = useMutation({
    mutationFn: ({ id, duplicateOf }: { id: string; duplicateOf: string }) =>
      api.sourceMergeCapture(id, {
        duplicate_of: duplicateOf,
        notes: "Mescla confirmada pela Caixa de Entrada; histórico preservado.",
      }),
    onSuccess: (data) => {
      toast.success(data.message || "Duplicata mesclada.");
      refresh();
    },
    onError: (error) =>
      toast.error(error instanceof Error ? error.message : "Nao foi possivel mesclar duplicata."),
  });

  const exportInbox = useMutation({
    mutationFn: ({ ids }: { ids: string[] }) =>
      api.sourceExport({ format: exportFormat, item_ids: ids }),
    onSuccess: (data) => {
      downloadText(
        data.filename,
        data.content,
        data.format === "json" ? "application/json" : "text/csv",
      );
      toast.success(`Exportação concluída: ${data.item_count} item(ns).`);
    },
    onError: (error) =>
      toast.error(error instanceof Error ? error.message : "Não foi possível exportar."),
  });

  const importJob = useMutation({
    mutationFn: (id: string) => api.sourceImportCaptureJob(id),
    onSuccess: (data) => {
      toast.success(data.message || "Item enviado para Vaga.");
      refresh();
    },
    onError: (error) =>
      toast.error(error instanceof Error ? error.message : "Nao foi possivel enviar para Vaga."),
  });

  const saveTracker = useMutation({
    mutationFn: (id: string) => api.sourceSaveCaptureTracker(id),
    onSuccess: (data) => {
      toast.success(data.message || "Item salvo em Candidaturas.");
      refresh();
    },
    onError: (error) =>
      toast.error(error instanceof Error ? error.message : "Nao foi possivel salvar no tracker."),
  });

  const dedupe = useMutation({
    mutationFn: () => api.sourceDedupe(),
    onSuccess: (data) => {
      toast.success(`${data.duplicates.length} possiveis duplicatas encontradas.`);
      refresh();
    },
    onError: (error) =>
      toast.error(error instanceof Error ? error.message : "Nao foi possivel deduplicar."),
  });

  const items = useMemo(() => inboxQ.data?.items ?? [], [inboxQ.data?.items]);
  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return items.filter((item) => {
      const statusOk = statusFilter === "all" || item.status === statusFilter;
      const originOk = originFilter === "all" || item.origin === originFilter;
      const haystack = [
        item.title,
        item.company,
        item.job_url,
        item.source_name,
        item.origin,
        item.tags.join(" "),
      ]
        .join(" ")
        .toLowerCase();
      return statusOk && originOk && (!q || haystack.includes(q));
    });
  }, [items, originFilter, search, statusFilter]);
  const busy =
    importText.isPending ||
    importUrl.isPending ||
    importCsv.isPending ||
    importJson.isPending ||
    patchCapture.isPending ||
    importJob.isPending ||
    saveTracker.isPending ||
    dedupe.isPending ||
    mergeCapture.isPending ||
    exportInbox.isPending;

  const selectedFilteredIds = filtered.map((item) => item.id);
  const selectedInFilter = selectedIds.filter((id) => selectedFilteredIds.includes(id));

  async function handleSelectedFile(event: ChangeEvent<HTMLInputElement>, kind: "csv" | "json") {
    const file = event.currentTarget.files?.[0];
    event.currentTarget.value = "";
    await previewFile(file, kind);
  }

  async function previewFile(file: File | undefined, expectedKind: "csv" | "json") {
    if (!file) return;
    const extension = file.name.split(".").pop()?.toLowerCase();
    const kind = extension === "json" ? "json" : extension === "csv" ? "csv" : expectedKind;
    if (kind !== expectedKind || !["csv", "json"].includes(extension || "")) {
      setFilePreview({
        kind: expectedKind,
        name: file.name,
        text: "",
        rows: [],
        error: "Formato inválido. Selecione um arquivo .csv ou .json.",
      });
      return;
    }
    if (file.size > MAX_IMPORT_FILE_BYTES) {
      setFilePreview({
        kind,
        name: file.name,
        text: "",
        rows: [],
        error: "Arquivo muito grande para importação local. Limite: 512 KB.",
      });
      return;
    }
    const fileText = await file.text();
    const preview = validateFilePreview(kind, fileText);
    setFilePreview({ kind, name: file.name, text: fileText, ...preview });
  }

  function confirmFileImport() {
    if (!filePreview || filePreview.error) return;
    if (filePreview.kind === "csv") {
      setCsvText(filePreview.text);
      importCsv.mutate(filePreview.text);
      return;
    }
    setJsonText(filePreview.text);
    importJson.mutate(filePreview.text);
  }

  function toggleSelected(id: string, selected: boolean) {
    setSelectedIds((current) =>
      selected ? Array.from(new Set([...current, id])) : current.filter((item) => item !== id),
    );
  }

  function exportItems(scope: "all" | "filtered" | "selected") {
    const ids =
      scope === "all" ? [] : scope === "filtered" ? selectedFilteredIds : selectedInFilter;
    exportInbox.mutate({ ids });
  }

  return (
    <div className="space-y-5">
      <div className="grid gap-3 md:grid-cols-4">
        <InfoTile label="Itens" value={String(statsQ.data?.total ?? items.length)} />
        <InfoTile label="Duplicadas" value={String(statsQ.data?.duplicates ?? 0)} />
        <InfoTile label="Salvas" value={String(statsQ.data?.saved_to_tracker ?? 0)} />
        <InfoTile label="Erros" value={String(statsQ.data?.errors ?? 0)} />
      </div>

      <div className="flex flex-wrap items-center gap-2 text-xs">
        {mode === "demo" ? (
          <span
            data-testid="demo-data-badge"
            className="rounded-md border border-warning/30 bg-warning/10 px-2 py-1 font-medium text-warning"
          >
            Dados de demonstração
          </span>
        ) : (
          <span className="rounded-md border border-success/30 bg-success/10 px-2 py-1 font-medium text-success">
            API Real conectada à base local
          </span>
        )}
        <label className="inline-flex items-center gap-2 rounded-md border border-input bg-background px-2 py-1">
          <input
            type="checkbox"
            checked={useAiImport}
            onChange={(event) => setUseAiImport(event.target.checked)}
            data-testid="source-use-ai-import"
          />
          Usar IA nas importações se o provider estiver configurado
        </label>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <div className="rounded-lg border border-border bg-background p-3">
          <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            <Upload className="h-3.5 w-3.5" />
            Importar texto ou link
          </div>
          <div className="grid gap-2 sm:grid-cols-[1fr_auto]">
            <Field label="Link opcional" value={url} onChange={setUrl} />
            <button
              type="button"
              onClick={() => importUrl.mutate()}
              disabled={busy}
              data-testid="source-import-url"
              className="self-end rounded-md border border-input bg-background px-3 py-2 text-xs font-medium hover:bg-muted disabled:opacity-50"
            >
              Importar link
            </button>
          </div>
          <textarea
            value={text}
            onChange={(event) => setText(event.target.value)}
            className="mt-3 min-h-28 w-full rounded-md border border-input bg-background px-3 py-2 text-xs outline-none focus:border-accent/50 focus:ring-2 focus:ring-accent/20"
          />
          <button
            type="button"
            onClick={() => importText.mutate()}
            disabled={busy || !text.trim()}
            data-testid="source-import-text"
            className="mt-2 rounded-md bg-primary px-3 py-2 text-xs font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
          >
            Importar texto
          </button>
        </div>

        <div className="rounded-lg border border-border bg-background p-3">
          <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            <Database className="h-3.5 w-3.5" />
            Importar CSV/JSON
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <textarea
                value={csvText}
                onChange={(event) => setCsvText(event.target.value)}
                data-testid="source-csv-input"
                className="min-h-32 w-full rounded-md border border-input bg-background px-3 py-2 font-mono text-[11px] outline-none focus:border-accent/50 focus:ring-2 focus:ring-accent/20"
              />
              <button
                type="button"
                onClick={() => importCsv.mutate(undefined)}
                disabled={busy}
                data-testid="source-import-csv"
                className="mt-2 rounded-md border border-input bg-background px-3 py-2 text-xs font-medium hover:bg-muted disabled:opacity-50"
              >
                Importar CSV
              </button>
            </div>
            <div>
              <textarea
                value={jsonText}
                onChange={(event) => setJsonText(event.target.value)}
                data-testid="source-json-input"
                className="min-h-32 w-full rounded-md border border-input bg-background px-3 py-2 font-mono text-[11px] outline-none focus:border-accent/50 focus:ring-2 focus:ring-accent/20"
              />
              <button
                type="button"
                onClick={() => importJson.mutate(undefined)}
                disabled={busy}
                data-testid="source-import-json"
                className="mt-2 rounded-md border border-input bg-background px-3 py-2 text-xs font-medium hover:bg-muted disabled:opacity-50"
              >
                Importar JSON
              </button>
            </div>
          </div>

          <div
            data-testid="source-upload-panel"
            onDragOver={(event) => event.preventDefault()}
            onDrop={(event) => {
              event.preventDefault();
              const file = event.dataTransfer.files[0];
              const extension = file?.name.split(".").pop()?.toLowerCase();
              previewFile(file, extension === "json" ? "json" : "csv");
            }}
            className="mt-3 rounded-lg border border-dashed border-border bg-muted/20 p-3"
          >
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className="font-medium">Upload com preview</span>
              <label className="cursor-pointer rounded-md border border-input bg-background px-2.5 py-1 hover:bg-muted">
                Selecionar arquivo CSV
                <input
                  type="file"
                  accept=".csv,text/csv"
                  data-testid="source-upload-csv-input"
                  className="sr-only"
                  onChange={(event) => handleSelectedFile(event, "csv")}
                />
              </label>
              <label className="cursor-pointer rounded-md border border-input bg-background px-2.5 py-1 hover:bg-muted">
                Selecionar arquivo JSON
                <input
                  type="file"
                  accept=".json,application/json"
                  data-testid="source-upload-json-input"
                  className="sr-only"
                  onChange={(event) => handleSelectedFile(event, "json")}
                />
              </label>
              <span className="text-muted-foreground">ou arraste um arquivo aqui</span>
            </div>

            {filePreview && (
              <div
                data-testid="source-file-preview"
                className="mt-3 rounded-md border border-border bg-background p-3 text-xs"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <div className="font-semibold">{filePreview.name}</div>
                    <div className="text-muted-foreground">
                      Preview antes de confirmar · {filePreview.kind.toUpperCase()}
                    </div>
                  </div>
                  <div className="flex gap-1.5">
                    <button
                      type="button"
                      onClick={confirmFileImport}
                      disabled={busy || Boolean(filePreview.error)}
                      data-testid="source-upload-confirm"
                      className="rounded-md bg-primary px-2.5 py-1 font-medium text-primary-foreground disabled:opacity-50"
                    >
                      Confirmar importação
                    </button>
                    <button
                      type="button"
                      onClick={() => setFilePreview(null)}
                      data-testid="source-upload-cancel"
                      className="rounded-md border border-input bg-background px-2.5 py-1 font-medium hover:bg-muted"
                    >
                      Cancelar
                    </button>
                  </div>
                </div>
                {filePreview.error ? (
                  <p data-testid="source-upload-error" className="mt-2 text-destructive">
                    {filePreview.error}
                  </p>
                ) : (
                  <pre className="mt-2 max-h-32 overflow-auto whitespace-pre-wrap rounded bg-muted/50 p-2 font-mono text-[11px]">
                    {filePreview.rows.join("\n")}
                  </pre>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2 rounded-lg border border-border bg-muted/20 p-3">
        <Filter className="h-4 w-4 text-muted-foreground" />
        <input
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Buscar cargo, empresa, link, tag ou origem"
          className="min-w-[220px] flex-1 rounded-md border border-input bg-background px-3 py-2 text-xs outline-none focus:border-accent/50 focus:ring-2 focus:ring-accent/20"
        />
        <select
          value={statusFilter}
          onChange={(event) => setStatusFilter(event.target.value as typeof statusFilter)}
          className="rounded-md border border-input bg-background px-3 py-2 text-xs"
        >
          <option value="all">Todas</option>
          <option value="new">Novas</option>
          <option value="imported_to_job">Importadas</option>
          <option value="saved_to_tracker">Salvas</option>
          <option value="duplicate">Duplicadas</option>
          <option value="archived">Arquivadas</option>
          <option value="error">Com erro</option>
        </select>
        <select
          value={originFilter}
          onChange={(event) => setOriginFilter(event.target.value as typeof originFilter)}
          className="rounded-md border border-input bg-background px-3 py-2 text-xs"
        >
          <option value="all">Toda origem</option>
          <option value="manual_text">Texto manual</option>
          <option value="manual_url">Link manual</option>
          <option value="csv_import">CSV</option>
          <option value="json_import">JSON</option>
          <option value="extension_capture">Extensao</option>
        </select>
        <button
          type="button"
          onClick={() => dedupe.mutate()}
          disabled={busy}
          data-testid="source-run-dedupe"
          className="rounded-md border border-input bg-background px-3 py-2 text-xs font-medium hover:bg-muted disabled:opacity-50"
        >
          Deduplicar
        </button>
        <select
          value={exportFormat}
          onChange={(event) => setExportFormat(event.target.value as "csv" | "json")}
          className="rounded-md border border-input bg-background px-3 py-2 text-xs"
          aria-label="Formato de exportação"
        >
          <option value="csv">CSV</option>
          <option value="json">JSON</option>
        </select>
        <button
          type="button"
          onClick={() => exportItems("all")}
          disabled={busy || items.length === 0}
          data-testid="source-export-all"
          className="inline-flex items-center gap-1 rounded-md border border-input bg-background px-3 py-2 text-xs font-medium hover:bg-muted disabled:opacity-50"
        >
          <Download className="h-3.5 w-3.5" />
          Exportar todos
        </button>
        <button
          type="button"
          onClick={() => exportItems("filtered")}
          disabled={busy || filtered.length === 0}
          data-testid="source-export-filtered"
          className="inline-flex items-center gap-1 rounded-md border border-input bg-background px-3 py-2 text-xs font-medium hover:bg-muted disabled:opacity-50"
        >
          Exportar filtrados
        </button>
        <button
          type="button"
          onClick={() => exportItems("selected")}
          disabled={busy || selectedInFilter.length === 0}
          data-testid="source-export-selected"
          className="inline-flex items-center gap-1 rounded-md border border-input bg-background px-3 py-2 text-xs font-medium hover:bg-muted disabled:opacity-50"
        >
          Exportar selecionados
        </button>
      </div>

      {inboxQ.isLoading ? (
        <div className="rounded-lg border border-border bg-muted/20 p-4 text-sm text-muted-foreground">
          Carregando caixa de entrada...
        </div>
      ) : filtered.length === 0 ? (
        <div
          data-testid={mode === "real" && items.length === 0 ? "source-real-empty" : undefined}
          className="rounded-lg border border-dashed border-border bg-muted/20 p-4 text-sm text-muted-foreground"
        >
          {mode === "real" && items.length === 0
            ? "API Real sem oportunidades locais. Cole uma vaga, adicione um link ou importe um CSV/JSON."
            : "Você ainda não importou vagas. Cole uma vaga, adicione um link ou importe um CSV/JSON."}
        </div>
      ) : (
        <ul className="grid gap-2">
          {filtered.map((item) => (
            <OpportunityInboxRow
              key={item.id}
              item={item}
              duplicateTarget={items.find((candidate) => candidate.id === item.duplicate_of)}
              selected={selectedIds.includes(item.id)}
              busy={busy}
              onSelect={(selected) => toggleSelected(item.id, selected)}
              onImportJob={() => importJob.mutate(item.id)}
              onSaveTracker={() => saveTracker.mutate(item.id)}
              onArchive={() => patchCapture.mutate({ id: item.id, status: "archived" })}
              onIgnore={() => patchCapture.mutate({ id: item.id, status: "ignored" })}
              onMerge={() =>
                item.duplicate_of &&
                mergeCapture.mutate({ id: item.id, duplicateOf: item.duplicate_of })
              }
              onKeepSeparate={() =>
                patchCapture.mutate({
                  id: item.id,
                  status: "reviewed",
                  duplicate_of: "",
                })
              }
              onNotDuplicate={() =>
                patchCapture.mutate({
                  id: item.id,
                  status: "reviewed",
                  notes: "Marcada como não duplicata pelo usuário.",
                })
              }
            />
          ))}
        </ul>
      )}

      <SourceDirectoryPanel
        query={directoryQuery}
        onQueryChange={setDirectoryQuery}
        loading={directoryQ.isLoading}
        sources={directoryQ.data?.sources ?? []}
        warnings={directoryQ.data?.warnings ?? []}
      />
    </div>
  );
}

function SourceDirectoryPanel({
  query,
  onQueryChange,
  loading,
  sources,
  warnings,
}: {
  query: string;
  onQueryChange: (value: string) => void;
  loading: boolean;
  sources: SourceDirectoryEntry[];
  warnings: string[];
}) {
  return (
    <div
      id="source-directory"
      data-testid="source-directory-panel"
      className="rounded-lg border border-border bg-background p-3"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            <Database className="h-3.5 w-3.5" />
            Diretório de Fontes
          </div>
          <p className="mt-1 text-xs text-muted-foreground">
            Organização segura de fontes públicas, oficiais e manuais. Nada aqui faz login
            automático, bypass ou candidatura automática.
          </p>
        </div>
        <input
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          placeholder="Buscar fonte, tipo ou status"
          data-testid="source-directory-search"
          className="min-w-[220px] rounded-md border border-input bg-background px-3 py-2 text-xs outline-none focus:border-accent/50 focus:ring-2 focus:ring-accent/20"
        />
      </div>

      {warnings.length > 0 && (
        <div className="mt-3 rounded-md border border-warning/30 bg-warning/5 p-2 text-xs text-warning">
          {warnings[0]}
        </div>
      )}

      {loading ? (
        <div className="mt-3 rounded-md border border-border bg-muted/20 p-3 text-xs text-muted-foreground">
          Carregando diretório...
        </div>
      ) : (
        <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {sources.map((source) => (
            <div
              key={source.id}
              className="rounded-lg border border-border bg-muted/20 p-3 text-xs"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="font-semibold text-foreground">{source.name}</div>
                <span className="rounded-md bg-muted px-2 py-0.5 text-[10px] font-semibold text-muted-foreground">
                  {sourceDirectoryStatus(source.status)}
                </span>
              </div>
              <dl className="mt-2 grid gap-1 text-muted-foreground">
                <div className="flex gap-1">
                  <dt className="font-medium text-foreground">Tipo:</dt>
                  <dd>{sourceDirectoryKind(source.kind)}</dd>
                </div>
                <div className="flex gap-1">
                  <dt className="font-medium text-foreground">URL base:</dt>
                  <dd className="truncate">{source.base_url || "Definida pelo usuário"}</dd>
                </div>
                <div className="flex gap-1">
                  <dt className="font-medium text-foreground">Última verificação:</dt>
                  <dd>{source.last_checked_at || "Ainda não verificada"}</dd>
                </div>
              </dl>
              <p className="mt-2 text-muted-foreground">{source.observation}</p>
              {source.requires_manual_review && (
                <span className="mt-2 inline-flex rounded-md bg-warning/10 px-2 py-0.5 text-[10px] font-semibold text-warning">
                  Revisão manual necessária
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function OpportunityInboxRow({
  item,
  duplicateTarget,
  selected,
  busy,
  onSelect,
  onImportJob,
  onSaveTracker,
  onArchive,
  onIgnore,
  onMerge,
  onKeepSeparate,
  onNotDuplicate,
}: {
  item: OpportunityInboxItem;
  duplicateTarget?: OpportunityInboxItem;
  selected: boolean;
  busy: boolean;
  onSelect: (selected: boolean) => void;
  onImportJob: () => void;
  onSaveTracker: () => void;
  onArchive: () => void;
  onIgnore: () => void;
  onMerge: () => void;
  onKeepSeparate: () => void;
  onNotDuplicate: () => void;
}) {
  const duplicate = item.status === "duplicate";
  const metadata = item.metadata ?? {};
  const duplicateExplanation =
    typeof metadata.duplicate_explanation === "string"
      ? metadata.duplicate_explanation
      : "Critério local: URL normalizada, empresa+cargo ou descrição semelhante.";
  return (
    <li
      data-testid="source-inbox-row"
      className={`rounded-lg border bg-background p-3 ${
        duplicate ? "border-warning/40" : "border-border"
      }`}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <label className="mt-1 inline-flex items-center gap-2 text-xs text-muted-foreground">
          <input
            type="checkbox"
            checked={selected}
            onChange={(event) => onSelect(event.target.checked)}
            data-testid="source-select-item"
          />
          Selecionar
        </label>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="truncate text-sm font-semibold">{item.title}</h3>
            <span className="rounded-md bg-muted px-2 py-0.5 text-[10px] text-muted-foreground">
              {sourceOriginLabel(item.origin)}
            </span>
            <span
              className={`rounded-md px-2 py-0.5 text-[10px] font-semibold ${
                duplicate ? "bg-warning/10 text-warning" : "bg-muted text-muted-foreground"
              }`}
            >
              {captureStatusLabel(item.status)}
            </span>
          </div>
          <p className="mt-0.5 truncate text-xs text-muted-foreground">
            {item.company || "Empresa nao detectada"} · {item.location || "Local nao informado"}
          </p>
          {duplicate && (
            <div
              data-testid="source-duplicate-panel"
              className="mt-2 rounded-md border border-warning/30 bg-warning/5 p-3 text-xs"
            >
              <div className="font-semibold text-warning">
                Esta vaga parece duplicada de outra oportunidade já salva.
              </div>
              <div className="mt-2 grid gap-2 md:grid-cols-2">
                <div className="rounded-md bg-background/70 p-2">
                  <div className="text-[10px] font-semibold uppercase text-muted-foreground">
                    Item novo
                  </div>
                  <div className="font-medium">{item.title}</div>
                  <div className="text-muted-foreground">
                    {item.company || "Empresa não detectada"} · {sourceOriginLabel(item.origin)}
                  </div>
                </div>
                <div className="rounded-md bg-background/70 p-2">
                  <div className="text-[10px] font-semibold uppercase text-muted-foreground">
                    Item existente
                  </div>
                  <div className="font-medium">
                    {duplicateTarget?.title || item.duplicate_of || "Não localizado"}
                  </div>
                  <div className="text-muted-foreground">
                    {duplicateTarget?.company || "Histórico preservado"} ·{" "}
                    {duplicateTarget ? sourceOriginLabel(duplicateTarget.origin) : "origem local"}
                  </div>
                </div>
              </div>
              <div className="mt-2 grid gap-2 md:grid-cols-3">
                <div>
                  <div className="font-medium">Critério de deduplicação</div>
                  <p className="text-muted-foreground">{duplicateExplanation}</p>
                </div>
                <div>
                  <div className="font-medium">Campos diferentes</div>
                  <p className="text-muted-foreground">
                    {differentFields(item, duplicateTarget).join(", ") || "Nenhum campo crítico."}
                  </p>
                </div>
                <div>
                  <div className="font-medium">Histórico de origem</div>
                  <p className="text-muted-foreground">
                    Novo: {sourceOriginLabel(item.origin)} · Existente:{" "}
                    {duplicateTarget ? sourceOriginLabel(duplicateTarget.origin) : "não encontrado"}
                  </p>
                </div>
              </div>
              <div className="mt-3 flex flex-wrap gap-1.5">
                <button
                  type="button"
                  onClick={onMerge}
                  disabled={busy || !item.duplicate_of}
                  data-testid="source-merge-duplicate"
                  className="inline-flex items-center gap-1 rounded-md bg-warning px-2.5 py-1 text-[11px] font-medium text-warning-foreground disabled:opacity-50"
                >
                  <Merge className="h-3 w-3" />
                  Mesclar
                </button>
                <button
                  type="button"
                  onClick={onKeepSeparate}
                  disabled={busy}
                  data-testid="source-keep-separate"
                  className="rounded-md border border-input bg-background px-2.5 py-1 text-[11px] font-medium hover:bg-muted disabled:opacity-50"
                >
                  Manter separado
                </button>
                <button
                  type="button"
                  onClick={onArchive}
                  disabled={busy}
                  className="rounded-md border border-input bg-background px-2.5 py-1 text-[11px] font-medium hover:bg-muted disabled:opacity-50"
                >
                  Arquivar novo
                </button>
                <button
                  type="button"
                  onClick={onNotDuplicate}
                  disabled={busy}
                  data-testid="source-not-duplicate"
                  className="rounded-md border border-input bg-background px-2.5 py-1 text-[11px] font-medium hover:bg-muted disabled:opacity-50"
                >
                  Marcar como não duplicata
                </button>
              </div>
            </div>
          )}
          <div className="mt-2 flex flex-wrap gap-1.5">
            {item.tags.slice(0, 5).map((tag) => (
              <span key={tag} className="rounded-md bg-muted px-2 py-0.5 text-[10px]">
                {tag}
              </span>
            ))}
          </div>
          {item.job_url && (
            <a
              href={item.job_url}
              target="_blank"
              rel="noreferrer"
              className="mt-2 inline-flex max-w-full items-center gap-1 truncate text-[11px] text-accent hover:underline"
            >
              <ExternalLink className="h-3 w-3 shrink-0" />
              <span className="truncate">{item.job_url}</span>
            </a>
          )}
        </div>
        <div className="flex shrink-0 flex-wrap gap-1.5">
          <button
            type="button"
            onClick={onImportJob}
            disabled={busy}
            data-testid="source-import-to-job"
            className="inline-flex items-center gap-1 rounded-md border border-input bg-background px-2.5 py-1 text-[11px] font-medium hover:bg-muted disabled:opacity-50"
          >
            <ArrowRight className="h-3 w-3" />
            Importar para Vaga
          </button>
          <button
            type="button"
            onClick={onSaveTracker}
            disabled={busy}
            data-testid="source-save-tracker"
            className="inline-flex items-center gap-1 rounded-md bg-primary px-2.5 py-1 text-[11px] font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
          >
            <Save className="h-3 w-3" />
            Salvar em Candidaturas
          </button>
          <button
            type="button"
            onClick={() => navigator.clipboard?.writeText(item.job_url || item.title)}
            className="inline-flex items-center gap-1 rounded-md border border-input bg-background px-2.5 py-1 text-[11px] font-medium hover:bg-muted"
          >
            <Copy className="h-3 w-3" />
            Copiar link
          </button>
          <button
            type="button"
            onClick={onArchive}
            disabled={busy}
            data-testid="source-archive-item"
            className="inline-flex items-center gap-1 rounded-md border border-input bg-background px-2.5 py-1 text-[11px] font-medium hover:bg-muted disabled:opacity-50"
          >
            <Archive className="h-3 w-3" />
            Arquivar
          </button>
          <button
            type="button"
            onClick={onIgnore}
            disabled={busy}
            className="inline-flex items-center gap-1 rounded-md border border-input bg-background px-2.5 py-1 text-[11px] font-medium hover:bg-muted disabled:opacity-50"
          >
            <XCircle className="h-3 w-3" />
            Ignorar
          </button>
        </div>
      </div>
    </li>
  );
}

function sourceOriginLabel(origin: SourceOrigin): string {
  const labels: Record<SourceOrigin, string> = {
    manual_text: "Texto manual",
    manual_url: "Link manual",
    csv_import: "CSV",
    json_import: "JSON",
    extension_capture: "Extensão Local",
    companion_capture: "Companion",
    authenticated_assisted_capture: "Captura assistida autenticada",
    public_source: "Fonte pública",
    public_feed: "Feed público",
    official_api_future: "API oficial futura",
  };
  return labels[origin];
}

function captureStatusLabel(status: SourceCaptureStatus): string {
  const labels: Record<SourceCaptureStatus, string> = {
    new: "Nova",
    reviewed: "Revisada",
    imported_to_job: "Importada",
    saved_to_tracker: "Salva",
    ignored: "Ignorada",
    archived: "Arquivada",
    duplicate: "Duplicada",
    error: "Erro",
  };
  return labels[status];
}

function sourceDirectoryKind(kind: SourceDirectoryEntry["kind"]): string {
  const labels: Record<SourceDirectoryEntry["kind"], string> = {
    public_career_page: "Página de carreira aberta",
    public_feed: "Feed RSS público",
    official_api: "API oficial",
    recurring_csv_json: "CSV/JSON recorrente",
    manual_link: "Link manual",
    observed_origin: "Origem observada",
  };
  return labels[kind];
}

function sourceDirectoryStatus(status: SourceDirectoryEntry["status"]): string {
  const labels: Record<SourceDirectoryEntry["status"], string> = {
    available: "Disponível",
    planned: "Planejado",
    future: "Futuro",
    manual_review: "Revisão manual",
  };
  return labels[status];
}

function differentFields(
  item: OpportunityInboxItem,
  duplicateTarget: OpportunityInboxItem | undefined,
): string[] {
  if (!duplicateTarget) return ["item existente indisponível"];
  const fields: string[] = [];
  if ((item.company || "") !== (duplicateTarget.company || "")) fields.push("empresa");
  if ((item.location || "") !== (duplicateTarget.location || "")) fields.push("local");
  if (
    (item.job_url || item.source_url || "") !==
    (duplicateTarget.job_url || duplicateTarget.source_url || "")
  )
    fields.push("link");
  if (item.origin !== duplicateTarget.origin) fields.push("origem");
  return fields;
}

function validateFilePreview(
  kind: "csv" | "json",
  text: string,
): Pick<FilePreview, "rows" | "error"> {
  if (!text.trim()) return { rows: [], error: "Arquivo vazio." };
  if (kind === "json") {
    try {
      const parsed = JSON.parse(text);
      if (!Array.isArray(parsed)) {
        return { rows: [], error: "JSON deve ser uma lista de objetos." };
      }
      return {
        rows: parsed.slice(0, 5).map((item, index) => `${index + 1}. ${JSON.stringify(item)}`),
      };
    } catch {
      return { rows: [], error: "JSON inválido. Revise o arquivo antes de importar." };
    }
  }
  const rows = text.split(/\r?\n/).filter(Boolean);
  if (rows.length < 2 || !rows[0]?.includes(",")) {
    return { rows: [], error: "CSV inválido. Inclua cabeçalho e pelo menos uma linha." };
  }
  return { rows: rows.slice(0, 6) };
}

function downloadText(filename: string, content: string, type: string) {
  const blob = new Blob([content], { type: `${type};charset=utf-8` });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename || "sotuhire-opportunities.csv";
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

function LocalExtensionPanel() {
  const api = useApi();
  const { mode, baseUrl } = useApiMode();
  const statusQ = useQuery({
    queryKey: ["extension-status", mode, baseUrl],
    queryFn: () => api.extensionStatus(),
    retry: false,
  });
  const capturesQ = useQuery({
    queryKey: ["extension-captures", mode, baseUrl],
    queryFn: () => api.extensionCaptures(),
    retry: false,
  });
  const contextQ = useQuery({
    queryKey: ["extension-context", mode, baseUrl],
    queryFn: () => api.extensionContext(),
    retry: false,
  });

  const importJob = useMutation({
    mutationFn: (captureId: string) => api.extensionImportJob(captureId),
    onSuccess: (data) => toast.success(data.message || "Captura enviada para Vaga."),
    onError: (error) =>
      toast.error(error instanceof Error ? error.message : "Nao foi possivel importar a vaga."),
  });

  const importTracker = useMutation({
    mutationFn: (captureId: string) => api.extensionImportTracker(captureId),
    onSuccess: (data) => toast.success(data.message || "Captura salva em Candidaturas."),
    onError: (error) =>
      toast.error(error instanceof Error ? error.message : "Nao foi possivel salvar no tracker."),
  });

  const importGithub = useMutation({
    mutationFn: (captureId: string) => api.extensionImportGithub(captureId),
    onSuccess: (data) => toast.success(data.message || "Captura enviada para GitHub Analysis."),
    onError: (error) =>
      toast.error(
        error instanceof Error ? error.message : "Nao foi possivel enviar para GitHub Analysis.",
      ),
  });

  const [candidateReview, setCandidateReview] = useState<ExtensionCandidateReview | null>(null);

  const profileCandidates = useMutation({
    mutationFn: ({
      captureId,
      isProject,
    }: {
      captureId: string;
      title: string;
      isProject: boolean;
    }) =>
      isProject
        ? api.extensionProjectProfileCandidates(captureId)
        : api.extensionCaptureProfileCandidates(captureId),
    onSuccess: (data, variables) => {
      setCandidateReview({
        captureId: variables.captureId,
        title: variables.title,
        isProject: variables.isProject,
        candidates: data.candidates,
        selectedIds: data.candidates.map((item) => item.item_id),
        contextSummary: data.context_summary || "",
        warnings: data.warnings,
        message: data.message,
      });
      toast.success(data.message || "Evidencias geradas para revisao.");
    },
    onError: (error) =>
      toast.error(error instanceof Error ? error.message : "Nao foi possivel gerar evidencias."),
  });

  const addToProfile = useMutation({
    mutationFn: ({
      captureId,
      isProject,
      candidateIds,
    }: {
      captureId: string;
      isProject: boolean;
      candidateIds: string[];
    }) =>
      isProject
        ? api.extensionProjectAddToProfile(captureId, candidateIds)
        : api.extensionCaptureAddToProfile(captureId, candidateIds),
    onSuccess: (data) => {
      toast.success(data.message || "Itens adicionados ao Perfil.");
      setCandidateReview(null);
      capturesQ.refetch();
      contextQ.refetch();
    },
    onError: (error) =>
      toast.error(error instanceof Error ? error.message : "Nao foi possivel adicionar ao Perfil."),
  });

  const patchCapture = useMutation({
    mutationFn: ({ captureId, status }: { captureId: string; status: string }) =>
      api.extensionPatchCapture(captureId, status),
    onSuccess: (data) => {
      toast.success(data.message || "Captura atualizada.");
      capturesQ.refetch();
      statusQ.refetch();
    },
    onError: (error) =>
      toast.error(error instanceof Error ? error.message : "Nao foi possivel atualizar captura."),
  });

  const [ignoredIds, setIgnoredIds] = useState<string[]>([]);
  const allCaptures = useMemo(() => capturesQ.data?.captures ?? [], [capturesQ.data?.captures]);
  const captures = useMemo(
    () => allCaptures.filter((capture) => !ignoredIds.includes(capture.id)),
    [allCaptures, ignoredIds],
  );
  const companionOffline = statusQ.isError || statusQ.data?.available === false;
  const busy =
    importJob.isPending ||
    importTracker.isPending ||
    importGithub.isPending ||
    patchCapture.isPending ||
    profileCandidates.isPending ||
    addToProfile.isPending;
  const lastSync = statusQ.data?.last_capture_at || allCaptures[0]?.captured_at;

  function toggleCandidate(candidateId: string, selected: boolean) {
    setCandidateReview((current) =>
      current
        ? {
            ...current,
            selectedIds: selected
              ? Array.from(new Set([...current.selectedIds, candidateId]))
              : current.selectedIds.filter((id) => id !== candidateId),
          }
        : current,
    );
  }

  return (
    <div className="grid gap-5 lg:grid-cols-[0.9fr_1.1fr]">
      <div className="space-y-3">
        <div
          className={`rounded-lg border p-3 ${
            companionOffline ? "border-warning/30 bg-warning/5" : "border-success/30 bg-success/5"
          }`}
        >
          <div className="flex items-start gap-2">
            {statusQ.isFetching ? (
              <RefreshCw className="mt-0.5 h-4 w-4 animate-spin text-warning" />
            ) : (
              <Database className="mt-0.5 h-4 w-4 text-success" />
            )}
            <div>
              <div className="text-sm font-semibold">
                {companionOffline ? "Companion offline" : "Companion conectado"}
              </div>
              <p className="mt-0.5 text-xs text-muted-foreground">
                {statusQ.data?.message ||
                  "Leia capturas locais da extensao sem expor segredos ao frontend."}
              </p>
            </div>
          </div>
          <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
            <InfoTile label="Capturas" value={String(statusQ.data?.capture_count ?? 0)} />
            <InfoTile label="API local" value={statusQ.data?.companion_url ?? "127.0.0.1:8765"} />
            <InfoTile
              label="Última sincronização"
              value={lastSync ? new Date(lastSync).toLocaleString("pt-BR") : "Sem capturas"}
            />
            <InfoTile label="Visíveis" value={String(captures.length)} />
          </div>
        </div>

        {companionOffline && (
          <div className="rounded-lg border border-dashed border-warning/40 bg-warning/5 p-3 text-xs text-muted-foreground">
            Companion offline: rode{" "}
            <code className="rounded bg-background px-1 py-0.5">
              .\start-sotuhire.ps1 -WithCompanion
            </code>{" "}
            ou use o modo Demo para validar a interface com capturas fictícias.
          </div>
        )}

        <div className="rounded-lg border border-border bg-muted/30 p-3 text-xs text-muted-foreground">
          A extensão continua usando a Local Companion API existente. Esta tela apenas consulta e
          importa capturas já salvas localmente.
        </div>

        <div className="rounded-lg border border-border bg-background p-3 text-xs text-muted-foreground">
          <div className="mb-1 font-semibold text-foreground">Contexto relacionado</div>
          {contextQ.data?.context_summary ||
            "Perfil Universal, memoria local e capturas aparecem aqui quando houver evidencias."}
        </div>
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Capturas recentes
          </div>
          <button
            type="button"
            onClick={() => {
              statusQ.refetch();
              capturesQ.refetch();
            }}
            className="rounded-md border border-input bg-background px-2.5 py-1 text-[11px] font-medium hover:bg-muted"
          >
            Atualizar
          </button>
        </div>

        {capturesQ.isFetching ? (
          <div className="rounded-lg border border-border bg-muted/30 p-4 text-sm text-muted-foreground">
            Carregando capturas locais...
          </div>
        ) : captures.length === 0 ? (
          <div className="rounded-lg border border-dashed border-border bg-muted/20 p-4 text-sm text-muted-foreground">
            Nenhuma captura local encontrada. Use a extensão assistiva ou rode em modo Demo para ver
            exemplos fictícios.
          </div>
        ) : (
          <ul className="space-y-2">
            {captures.map((capture) => (
              <ExtensionCaptureRow
                key={capture.id}
                capture={capture}
                busy={busy}
                onImportJob={() => importJob.mutate(capture.id)}
                onImportTracker={() => importTracker.mutate(capture.id)}
                onImportGithub={() => importGithub.mutate(capture.id)}
                onProfileCandidates={() =>
                  profileCandidates.mutate({
                    captureId: capture.id,
                    title: capture.title,
                    isProject:
                      capture.kind === "github_repo" || capture.url.includes("github.com/"),
                  })
                }
                onReview={() => patchCapture.mutate({ captureId: capture.id, status: "reviewed" })}
                onArchive={() => patchCapture.mutate({ captureId: capture.id, status: "archived" })}
                onIgnore={() => setIgnoredIds((current) => [...current, capture.id])}
              />
            ))}
          </ul>
        )}
        {candidateReview && (
          <ExtensionProfileCandidatePanel
            review={candidateReview}
            busy={busy}
            onToggle={toggleCandidate}
            onClose={() => setCandidateReview(null)}
            onAdd={() =>
              addToProfile.mutate({
                captureId: candidateReview.captureId,
                isProject: candidateReview.isProject,
                candidateIds: candidateReview.selectedIds,
              })
            }
          />
        )}
      </div>
    </div>
  );
}

function ExtensionCaptureRow({
  capture,
  busy,
  onImportJob,
  onImportTracker,
  onImportGithub,
  onProfileCandidates,
  onReview,
  onArchive,
  onIgnore,
}: {
  capture: ExtensionCapture;
  busy: boolean;
  onImportJob: () => void;
  onImportTracker: () => void;
  onImportGithub: () => void;
  onProfileCandidates: () => void;
  onReview: () => void;
  onArchive: () => void;
  onIgnore: () => void;
}) {
  const kind = capture.kind || (capture.url.includes("github.com") ? "github_repo" : "job");
  const origin = capture.source || capture.domain || capture.company || "Fonte local";
  const date = capture.captured_at || capture.updated_at;
  const isGithub = kind === "github_repo" || capture.url.includes("github.com/");
  return (
    <li
      data-testid="extension-capture-row"
      className="rounded-lg border border-border bg-background p-3"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="truncate text-sm font-semibold">{capture.title}</div>
          <div className="mt-0.5 truncate text-xs text-muted-foreground">
            {capture.company || capture.domain || "Fonte local"} · {capture.status}
          </div>
          <div className="mt-2 flex flex-wrap gap-1.5 text-[10px] text-muted-foreground">
            <span className="rounded-md bg-muted px-2 py-0.5">Origem: {origin}</span>
            <span className="rounded-md bg-muted px-2 py-0.5">
              Tipo: {isGithub ? "GitHub/portfolio" : "Vaga"}
            </span>
            <span className="rounded-md bg-muted px-2 py-0.5">
              Perfil: {capture.profile_candidate_count ?? 0} candidato(s)
            </span>
            {date && (
              <span className="rounded-md bg-muted px-2 py-0.5">
                Data: {new Date(date).toLocaleString("pt-BR")}
              </span>
            )}
          </div>
          {capture.url && (
            <a
              href={capture.url}
              target="_blank"
              rel="noreferrer"
              className="mt-1 inline-flex max-w-full items-center gap-1 truncate text-[11px] text-accent hover:underline"
            >
              <ExternalLink className="h-3 w-3 shrink-0" />
              <span className="truncate">{capture.url}</span>
            </a>
          )}
          {capture.context_signal && (
            <p className="mt-1 max-w-2xl text-[11px] text-muted-foreground">
              {capture.context_signal}
            </p>
          )}
        </div>
        <div className="flex shrink-0 flex-wrap gap-1.5">
          <button
            type="button"
            onClick={onProfileCandidates}
            disabled={busy}
            data-testid="view-extension-profile-candidates"
            className="inline-flex items-center gap-1 rounded-md border border-accent/40 bg-accent/10 px-2.5 py-1 text-[11px] font-medium text-accent hover:bg-accent/15 disabled:opacity-50"
          >
            <CheckCircle2 className="h-3 w-3" />
            {isGithub ? "Adicionar projeto ao Perfil" : "Ver evidencias para Perfil"}
          </button>
          <button
            type="button"
            onClick={onImportJob}
            disabled={busy}
            data-testid="import-capture-job"
            className="inline-flex items-center gap-1 rounded-md border border-input bg-background px-2.5 py-1 text-[11px] font-medium hover:bg-muted disabled:opacity-50"
          >
            <ArrowRight className="h-3 w-3" />
            Importar para Vaga
          </button>
          <button
            type="button"
            onClick={onImportTracker}
            disabled={busy}
            data-testid="import-capture-tracker"
            className="inline-flex items-center gap-1 rounded-md bg-primary px-2.5 py-1 text-[11px] font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
          >
            <Save className="h-3 w-3" />
            Salvar em Candidaturas
          </button>
          {isGithub && (
            <button
              type="button"
              onClick={onImportGithub}
              disabled={busy}
              data-testid="import-capture-github"
              className="inline-flex items-center gap-1 rounded-md border border-input bg-background px-2.5 py-1 text-[11px] font-medium hover:bg-muted disabled:opacity-50"
            >
              <Github className="h-3 w-3" />
              Enviar para GitHub Analysis
            </button>
          )}
          <button
            type="button"
            onClick={onReview}
            disabled={busy}
            data-testid="review-capture-local"
            className="inline-flex items-center gap-1 rounded-md border border-input bg-background px-2.5 py-1 text-[11px] font-medium hover:bg-muted disabled:opacity-50"
          >
            <CheckCircle2 className="h-3 w-3" />
            Revisada
          </button>
          <button
            type="button"
            onClick={onArchive}
            disabled={busy}
            data-testid="archive-capture-local"
            className="inline-flex items-center gap-1 rounded-md border border-input bg-background px-2.5 py-1 text-[11px] font-medium hover:bg-muted disabled:opacity-50"
          >
            <Archive className="h-3 w-3" />
            Arquivar
          </button>
          <button
            type="button"
            onClick={onIgnore}
            disabled={busy}
            data-testid="ignore-capture-local"
            className="inline-flex items-center gap-1 rounded-md border border-input bg-background px-2.5 py-1 text-[11px] font-medium hover:bg-muted disabled:opacity-50"
          >
            <XCircle className="h-3 w-3" />
            Ignorar
          </button>
        </div>
      </div>
    </li>
  );
}

function ExtensionProfileCandidatePanel({
  review,
  busy,
  onToggle,
  onAdd,
  onClose,
}: {
  review: ExtensionCandidateReview;
  busy: boolean;
  onToggle: (candidateId: string, selected: boolean) => void;
  onAdd: () => void;
  onClose: () => void;
}) {
  const selectedCount = review.selectedIds.length;
  return (
    <div
      id="extension-profile-candidates"
      data-testid="extension-profile-candidates"
      className="rounded-lg border border-accent/30 bg-accent/5 p-3"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="text-sm font-semibold">Evidencias para o Perfil</div>
          <p className="mt-0.5 text-xs text-muted-foreground">
            {review.title} · {review.message || "Revise os candidatos antes de salvar."}
          </p>
          {review.contextSummary && (
            <p className="mt-1 text-[11px] text-muted-foreground">
              Contexto: {review.contextSummary}
            </p>
          )}
        </div>
        <button
          type="button"
          onClick={onClose}
          className="rounded-md border border-input bg-background px-2.5 py-1 text-[11px] font-medium hover:bg-muted"
        >
          Fechar
        </button>
      </div>

      <ul className="mt-3 space-y-2">
        {review.candidates.map((candidate) => (
          <li key={candidate.item_id} className="rounded-md border border-border bg-background p-2">
            <label className="flex items-start gap-2">
              <input
                type="checkbox"
                checked={review.selectedIds.includes(candidate.item_id)}
                onChange={(event) => onToggle(candidate.item_id, event.target.checked)}
                className="mt-1"
              />
              <span className="min-w-0 flex-1">
                <span className="flex flex-wrap items-center gap-1.5 text-xs font-semibold">
                  <span>{candidate.title}</span>
                  <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] font-normal text-muted-foreground">
                    {candidate.type}
                  </span>
                  <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] font-normal text-muted-foreground">
                    {candidate.source}
                  </span>
                  <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] font-normal text-muted-foreground">
                    {candidate.confidence}
                  </span>
                </span>
                {candidate.evidence && (
                  <span className="mt-1 line-clamp-2 block text-[11px] text-muted-foreground">
                    {candidate.evidence}
                  </span>
                )}
                <span className="mt-1 block text-[10px] text-muted-foreground">
                  confirmed_by_user=false ate voce confirmar
                </span>
              </span>
            </label>
          </li>
        ))}
      </ul>

      {review.warnings.length > 0 && (
        <div className="mt-3 rounded-md border border-warning/30 bg-warning/5 p-2 text-[11px] text-muted-foreground">
          {review.warnings.slice(0, 3).join(" ")}
        </div>
      )}

      <button
        type="button"
        onClick={onAdd}
        disabled={busy || selectedCount === 0}
        data-testid="add-extension-candidates-profile"
        className="mt-3 rounded-md bg-primary px-3 py-2 text-xs font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
      >
        Adicionar selecionados ao Perfil ({selectedCount})
      </button>
    </div>
  );
}

function AuthenticatedBrowserPanel() {
  const api = useApi();
  const [startUrl, setStartUrl] = useState("https://www.linkedin.com/jobs/");
  const [cdpUrl, setCdpUrl] = useState("http://127.0.0.1:9222");
  const [authorizationReference, setAuthorizationReference] = useState("");
  const [authorizedUse, setAuthorizedUse] = useState(false);
  const [maxItems, setMaxItems] = useState(20);
  const [maxPages, setMaxPages] = useState(3);
  const [busy, setBusy] = useState<"status" | "launch" | "collect" | "">("");
  const [statusMessage, setStatusMessage] = useState("Aguardando teste de conexao.");
  const [collected, setCollected] = useState(0);
  const [browserStatus, setBrowserStatus] = useState<AuthenticatedBrowserStatus | null>(null);
  const [lastResult, setLastResult] = useState<AuthenticatedBrowserCollectResult | null>(null);
  const [lastActionAt, setLastActionAt] = useState("");

  const testStatus = async () => {
    setBusy("status");
    try {
      const status = await api.authenticatedBrowserStatus(cdpUrl);
      setBrowserStatus(status);
      setLastActionAt(formatTime());
      setStatusMessage(status.message || (status.available ? "Conexao CDP pronta." : "Offline."));
      toast[status.available ? "success" : "message"](
        status.available ? "CDP pronto" : "CDP offline",
      );
    } catch (error) {
      setLastActionAt(formatTime());
      setStatusMessage(error instanceof Error ? error.message : "Falha ao testar CDP.");
      toast.error("Nao foi possivel testar o navegador.");
    } finally {
      setBusy("");
    }
  };

  const launchBrowser = async () => {
    setBusy("launch");
    try {
      const status = await api.authenticatedBrowserLaunch({
        start_url: startUrl,
        browser_cdp_url: cdpUrl,
      });
      setBrowserStatus(status);
      setLastActionAt(formatTime());
      setStatusMessage(status.message || "Navegador aberto para login manual.");
      toast.success("Navegador dedicado aberto");
    } catch (error) {
      setLastActionAt(formatTime());
      setStatusMessage(error instanceof Error ? error.message : "Falha ao abrir navegador.");
      toast.error("Nao foi possivel abrir o navegador local.");
    } finally {
      setBusy("");
    }
  };

  const collectSource = async () => {
    if (!authorizedUse) {
      toast.warning("Confirme o uso autorizado antes de coletar.");
      return;
    }
    setBusy("collect");
    try {
      const result = await api.authenticatedBrowserCollect({
        name: "LinkedIn autorizado",
        url: startUrl,
        browser_cdp_url: cdpUrl,
        max_items: maxItems,
        max_pages: maxPages,
        authorized_use: authorizedUse,
        authorization_reference: authorizationReference,
      });
      setCollected(result.new_count + result.updated_count);
      setLastResult(result);
      setLastActionAt(formatTime());
      setStatusMessage(
        result.failures[0] ||
          `Coleta concluida: ${result.new_count} novas, ${result.updated_count} atualizadas.`,
      );
      toast.success("Coleta finalizada");
    } catch (error) {
      setLastActionAt(formatTime());
      setStatusMessage(error instanceof Error ? error.message : "Falha na coleta autorizada.");
      toast.error("Nao foi possivel coletar a fonte.");
    } finally {
      setBusy("");
    }
  };

  return (
    <div className="grid gap-5 lg:grid-cols-[1.1fr_0.9fr]">
      <div className="space-y-4">
        <div className="grid gap-3 sm:grid-cols-3">
          <InfoTile label="Modo" value="AUTHENTICATED_BROWSER" />
          <InfoTile label="CDP local" value="127.0.0.1:9222" />
          <InfoTile label="Coletadas" value={String(collected)} />
        </div>

        <AuthenticatedStatusSummary
          status={browserStatus}
          busy={busy}
          message={statusMessage}
          lastActionAt={lastActionAt}
        />

        <div className="grid gap-3 sm:grid-cols-2">
          <Field
            label="URL inicial"
            value={startUrl}
            onChange={setStartUrl}
            placeholder="https://www.linkedin.com/jobs/"
          />
          <Field label="CDP local" value={cdpUrl} onChange={setCdpUrl} />
          <Field
            label="Referencia da autorizacao"
            value={authorizationReference}
            onChange={setAuthorizationReference}
            placeholder="Ex.: uso pessoal autorizado"
          />
          <div className="grid grid-cols-2 gap-2">
            <NumberField label="Itens" value={maxItems} min={1} max={100} onChange={setMaxItems} />
            <NumberField label="Paginas" value={maxPages} min={1} max={20} onChange={setMaxPages} />
          </div>
        </div>

        <label className="flex items-start gap-2 rounded-lg border border-border bg-muted/30 p-3 text-xs">
          <input
            type="checkbox"
            checked={authorizedUse}
            onChange={(event) => setAuthorizedUse(event.target.checked)}
            className="mt-0.5"
          />
          <span className="leading-relaxed text-muted-foreground">
            Confirmo que tenho autorizacao para usar esta fonte autenticada nesta sessao local.
          </span>
        </label>

        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={testStatus}
            disabled={Boolean(busy)}
            className="rounded-md border border-input bg-background px-3 py-2 text-xs font-medium hover:bg-muted disabled:opacity-50"
          >
            {busy === "status" ? "Testando..." : "Testar CDP"}
          </button>
          <button
            type="button"
            onClick={launchBrowser}
            disabled={Boolean(busy)}
            className="rounded-md border border-input bg-background px-3 py-2 text-xs font-medium hover:bg-muted disabled:opacity-50"
          >
            {busy === "launch" ? "Abrindo..." : "Abrir navegador para login"}
          </button>
          <button
            type="button"
            onClick={collectSource}
            disabled={Boolean(busy) || !authorizedUse}
            className="rounded-md bg-primary px-3 py-2 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            {busy === "collect" ? "Coletando..." : "Coletar fonte autorizada"}
          </button>
        </div>

        <p className="rounded-lg border border-border bg-background p-3 text-xs text-muted-foreground">
          {statusMessage}
        </p>

        <AuthenticatedResultSummary result={lastResult} />

        <ol className="grid gap-2">
          {AUTH_BROWSER_STEPS.map((step, index) => (
            <li
              key={step}
              className="flex gap-3 rounded-lg border border-border bg-muted/30 p-3 text-xs"
            >
              <span className="grid h-5 w-5 shrink-0 place-items-center rounded-full bg-accent/15 text-[10px] font-semibold text-accent">
                {index + 1}
              </span>
              <span className="leading-relaxed text-muted-foreground">{step}</span>
            </li>
          ))}
        </ol>
      </div>

      <div className="space-y-3">
        <div className="rounded-lg border border-border bg-background p-3">
          <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            <Terminal className="h-3.5 w-3.5" />
            Comandos locais
          </div>
          <div className="space-y-1.5 font-mono text-[11px]">
            <Command text="pip install -r docs/requirements/requirements-scraping.txt" />
            <Command text="playwright install chromium" />
            <Command text="python scripts/run_api.py" />
          </div>
        </div>

        <div className="rounded-lg border border-success/30 bg-success/5 p-3">
          <div className="mb-2 text-xs font-semibold text-foreground">Limites de seguranca</div>
          <ul className="space-y-2">
            {AUTH_BROWSER_LIMITS.map((limit) => (
              <li key={limit} className="flex gap-2 text-xs text-muted-foreground">
                <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-success" />
                <span>{limit}</span>
              </li>
            ))}
          </ul>
        </div>

        <a
          href="/SotuHire/data-sources/authenticated-browser-crawling/"
          className="inline-flex w-full items-center justify-center rounded-md border border-input bg-background px-3 py-2 text-xs font-medium hover:bg-muted"
        >
          Abrir doc do fluxo autenticado
        </a>
      </div>
    </div>
  );
}

function AuthenticatedStatusSummary({
  status,
  busy,
  message,
  lastActionAt,
}: {
  status: AuthenticatedBrowserStatus | null;
  busy: "status" | "launch" | "collect" | "";
  message: string;
  lastActionAt: string;
}) {
  const isBusy = Boolean(busy);
  const isReady = status?.available;
  const tone = isBusy
    ? "border-warning/30 bg-warning/5"
    : isReady
      ? "border-success/30 bg-success/5"
      : "border-border bg-background";
  const label = isBusy
    ? busy === "collect"
      ? "Coletando"
      : "Verificando"
    : isReady
      ? "CDP pronto"
      : status
        ? "CDP offline"
        : "Nao testado";

  return (
    <div className={`rounded-lg border p-3 ${tone}`}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-start gap-2">
          {isBusy ? (
            <RefreshCw className="mt-0.5 h-4 w-4 animate-spin text-warning" />
          ) : isReady ? (
            <CheckCircle2 className="mt-0.5 h-4 w-4 text-success" />
          ) : (
            <AlertTriangle className="mt-0.5 h-4 w-4 text-muted-foreground" />
          )}
          <div>
            <div className="text-sm font-semibold">{label}</div>
            <p className="mt-0.5 text-xs text-muted-foreground">{message}</p>
          </div>
        </div>
        <div className="grid gap-1 text-right text-[11px] text-muted-foreground">
          <span className="font-mono">{status?.endpoint || "http://127.0.0.1:9222"}</span>
          <span>{status?.browser || "Chromium dedicado"}</span>
          {lastActionAt && <span>Ultima acao: {lastActionAt}</span>}
        </div>
      </div>
    </div>
  );
}

function AuthenticatedResultSummary({
  result,
}: {
  result: AuthenticatedBrowserCollectResult | null;
}) {
  if (!result) {
    return (
      <div className="rounded-lg border border-dashed border-border bg-muted/20 p-3 text-xs text-muted-foreground">
        Nenhuma coleta executada nesta sessao. Quando a coleta real terminar, os totais, falhas e
        oportunidades retornadas aparecem aqui.
      </div>
    );
  }

  return (
    <div className="space-y-3 rounded-lg border border-border bg-background p-3">
      <div className="grid gap-2 sm:grid-cols-3">
        <MiniMetric label="Novas" value={result.new_count} />
        <MiniMetric label="Atualizadas" value={result.updated_count} />
        <MiniMetric label="Duplicadas" value={result.duplicate_count} />
      </div>

      {result.failures.length > 0 && (
        <div className="rounded-md border border-warning/30 bg-warning/5 p-2 text-xs text-muted-foreground">
          <div className="font-semibold text-foreground">Avisos da coleta</div>
          <ul className="mt-1 space-y-1">
            {result.failures.map((failure) => (
              <li key={failure}>{failure}</li>
            ))}
          </ul>
        </div>
      )}

      {result.opportunities.length > 0 ? (
        <div className="space-y-2">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
            Oportunidades retornadas
          </div>
          <ul className="space-y-2">
            {result.opportunities.slice(0, 5).map((opportunity, index) => (
              <li
                key={`${opportunity.title}-${opportunity.source_url}-${index}`}
                className="rounded-md border border-border bg-muted/30 p-2"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="truncate text-xs font-semibold">{opportunity.title}</div>
                    <div className="mt-0.5 truncate text-[11px] text-muted-foreground">
                      {opportunity.company || "Empresa nao detectada"}
                    </div>
                  </div>
                  <span className="rounded-md bg-background px-2 py-0.5 font-mono text-[11px] text-muted-foreground">
                    {Math.round(opportunity.confidence * 100)}%
                  </span>
                </div>
                {opportunity.source_url && (
                  <a
                    href={opportunity.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-1 inline-flex max-w-full items-center gap-1 truncate text-[11px] text-accent hover:underline"
                  >
                    <ExternalLink className="h-3 w-3 shrink-0" />
                    <span className="truncate">{opportunity.source_url}</span>
                  </a>
                )}
              </li>
            ))}
          </ul>
          {result.opportunities.length > 5 && (
            <p className="text-[11px] text-muted-foreground">
              Mostrando 5 de {result.opportunities.length} oportunidades retornadas.
            </p>
          )}
        </div>
      ) : (
        <div className="rounded-md border border-border bg-muted/30 p-2 text-xs text-muted-foreground">
          A coleta terminou sem oportunidades retornadas. Verifique login, URL inicial, limites e
          mensagens de aviso.
        </div>
      )}
    </div>
  );
}

function MiniMetric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border border-border bg-muted/30 p-2">
      <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
        {label}
      </div>
      <div className="mt-1 font-mono text-lg font-semibold">{value}</div>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}) {
  return (
    <label className="block">
      <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
        {label}
      </span>
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-xs outline-none focus:border-accent/50 focus:ring-2 focus:ring-accent/20"
      />
    </label>
  );
}

function NumberField({
  label,
  value,
  min,
  max,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  onChange: (value: number) => void;
}) {
  return (
    <label className="block">
      <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
        {label}
      </span>
      <input
        type="number"
        min={min}
        max={max}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
        className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-xs outline-none focus:border-accent/50 focus:ring-2 focus:ring-accent/20"
      />
    </label>
  );
}

function InfoTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border bg-background p-3">
      <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
        {label}
      </div>
      <div className="mt-1 font-mono text-xs text-foreground">{value}</div>
    </div>
  );
}

function Command({ text }: { text: string }) {
  return (
    <code className="block rounded-md bg-muted px-2 py-1.5 text-muted-foreground">{text}</code>
  );
}

function formatTime() {
  return new Intl.DateTimeFormat("pt-BR", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date());
}
