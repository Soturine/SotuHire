import { createFileRoute, Link } from "@tanstack/react-router";
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  ExternalLink,
  Monitor,
  RefreshCw,
  ShieldAlert,
  Terminal,
} from "lucide-react";
import { useState } from "react";
import { AppShell } from "@/components/app-shell";
import { SectionCard } from "@/components/section-card";
import { SourceCardItem } from "@/components/source-card";
import { useApi } from "@/lib/api/hooks";
import type {
  AuthenticatedBrowserCollectResult,
  AuthenticatedBrowserStatus,
} from "@/lib/api/types";
import { SOURCE_CARDS, SOURCE_FLOW } from "@/mocks/sources";
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

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {SOURCE_CARDS.map((c) => (
            <SourceCardItem key={c.id} card={c} />
          ))}
        </div>

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
