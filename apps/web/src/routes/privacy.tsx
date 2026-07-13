import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  Archive,
  CheckCircle2,
  Database,
  Download,
  Eye,
  FileArchive,
  Globe,
  HeartPulse,
  Loader2,
  Lock,
  RefreshCw,
  RotateCcw,
  Server,
  ShieldCheck,
} from "lucide-react";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { SectionCard } from "@/components/section-card";
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
import { Input } from "@/components/ui/input";
import { useApi } from "@/lib/api/hooks";
import { useApiMode } from "@/lib/api/mode";
import type { DataArchive, DataHealthIssue } from "@/lib/api/types";
import { toast } from "@/lib/notify";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/privacy")({
  head: () => ({ meta: [{ title: "Privacidade — SotuHire" }] }),
  component: PrivacyPage,
});

function PrivacyPage() {
  return (
    <AppShell
      title="Privacidade e dados"
      description="Controle local de integridade, backups, exportação e restauração dos seus dados."
    >
      <div className="space-y-6">
        <DataReliabilityPanel />

        <div className="grid gap-6 lg:grid-cols-3">
          <SectionCard className="lg:col-span-2" title="Princípios de privacidade">
            <ul className="space-y-3 text-sm">
              {[
                {
                  icon: Server,
                  title: "API roda localmente",
                  description:
                    "A API opera em localhost. Não há servidor remoto obrigatório para usar o produto.",
                },
                {
                  icon: Database,
                  title: "Dados ficam no disco",
                  description:
                    "Perfil, vagas, snapshots e histórico são persistidos no diretório local configurado.",
                },
                {
                  icon: Lock,
                  title: "Segredos fora dos arquivos",
                  description:
                    "Backups e exports excluem chaves de API, tokens, cookies e storage da extensão.",
                },
                {
                  icon: Eye,
                  title: "Sem rastreamento",
                  description:
                    "O SotuHire não depende de analytics, cookies de identidade ou telemetria remota.",
                },
                {
                  icon: ShieldCheck,
                  title: "Revisão humana",
                  description:
                    "Sugestões não inventam experiência, certificação, formação ou registro profissional.",
                },
                {
                  icon: Globe,
                  title: "Saídas externas opcionais",
                  description:
                    "Chamadas ao GitHub público ou ao provedor de IA ocorrem apenas em fluxos habilitados.",
                },
              ].map((item) => (
                <li
                  key={item.title}
                  className="flex gap-3 rounded-lg border border-border bg-muted/30 p-3"
                >
                  <div className="grid h-9 w-9 shrink-0 place-items-center rounded-md bg-card text-accent">
                    <item.icon className="h-4 w-4" />
                  </div>
                  <div>
                    <div className="font-medium">{item.title}</div>
                    <div className="text-xs text-muted-foreground">{item.description}</div>
                  </div>
                </li>
              ))}
            </ul>
          </SectionCard>

          <SectionCard title="O que sai da máquina?">
            <ul className="space-y-2 text-sm">
              <PrivacyLevel
                tone="success"
                title="Por padrão"
                description="Nada. Dados e análises locais permanecem no seu ambiente."
              />
              <PrivacyLevel
                tone="warning"
                title="Sob demanda"
                description="Somente a entrada necessária para o provedor que você habilitar."
              />
              <PrivacyLevel
                tone="destructive"
                title="Nunca"
                description="Chaves, cookies, tokens e storage da extensão em backup ou export."
              />
            </ul>
          </SectionCard>
        </div>
      </div>
    </AppShell>
  );
}

function DataReliabilityPanel() {
  const api = useApi();
  const { mode } = useApiMode();
  const queryClient = useQueryClient();
  const [selectedArchive, setSelectedArchive] = useState("");
  const [validatedArchive, setValidatedArchive] = useState("");
  const [confirmation, setConfirmation] = useState("");

  const healthQ = useQuery({
    queryKey: ["data-health", mode],
    queryFn: () => api.dataHealth(),
    retry: false,
  });
  const archivesQ = useQuery({
    queryKey: ["data-archives", mode],
    queryFn: () => api.dataArchives(),
    retry: false,
  });

  useEffect(() => {
    if (!selectedArchive && archivesQ.data?.archives[0]) {
      setSelectedArchive(archivesQ.data.archives[0].archive_name);
    }
  }, [archivesQ.data, selectedArchive]);

  const createMutation = useMutation({
    mutationFn: (kind: DataArchive["kind"]) => api.dataCreateArchive(kind),
    onSuccess: (archive) => {
      setSelectedArchive(archive.archive_name);
      setValidatedArchive("");
      setConfirmation("");
      void queryClient.invalidateQueries({ queryKey: ["data-archives", mode] });
      toast.success(
        archive.kind === "export"
          ? "Export portátil criado sem segredos."
          : "Backup local criado e verificado.",
      );
    },
    onError: (error) => toast.error(errorMessage(error)),
  });

  const validateMutation = useMutation({
    mutationFn: (archiveName: string) =>
      api.dataRestore({ archive_name: archiveName, apply: false }),
    onSuccess: (result) => {
      setValidatedArchive(result.archive_name);
      setConfirmation("");
      toast.success(result.message);
    },
    onError: (error) => {
      setValidatedArchive("");
      toast.error(errorMessage(error));
    },
  });

  const restoreMutation = useMutation({
    mutationFn: (archiveName: string) =>
      api.dataRestore({
        archive_name: archiveName,
        apply: true,
        confirmation,
      }),
    onSuccess: (result) => {
      setValidatedArchive("");
      setConfirmation("");
      void queryClient.invalidateQueries({ queryKey: ["data-health", mode] });
      void queryClient.invalidateQueries({ queryKey: ["data-archives", mode] });
      toast.success(result.message);
    },
    onError: (error) => toast.error(errorMessage(error)),
  });

  const health = healthQ.data;
  const archives = archivesQ.data?.archives ?? [];
  const selected = archives.find((archive) => archive.archive_name === selectedArchive);
  const records = health
    ? Object.values(health.counts).reduce((total, count) => total + count, 0)
    : 0;
  const canApply =
    validatedArchive === selectedArchive &&
    confirmation === "RESTAURAR" &&
    !restoreMutation.isPending;

  const downloadArchive = (archive: DataArchive) => {
    if (mode === "demo") {
      toast.info("O download fica disponível no modo API Real.");
      return;
    }
    window.open(api.dataArchiveDownloadUrl(archive.archive_name), "_blank", "noopener,noreferrer");
  };

  return (
    <div id="data-reliability">
      <SectionCard
        title="Confiabilidade dos dados"
        description="Diagnóstico somente leitura, arquivos com checksum e restauração protegida em duas etapas."
        actions={
          <Button
            type="button"
            size="sm"
            variant="outline"
            onClick={() => {
              void healthQ.refetch();
              void archivesQ.refetch();
            }}
            disabled={healthQ.isFetching || archivesQ.isFetching}
          >
            <RefreshCw
              className={cn(
                "h-4 w-4",
                (healthQ.isFetching || archivesQ.isFetching) && "animate-spin",
              )}
            />
            Atualizar
          </Button>
        }
      >
        {(healthQ.isLoading || archivesQ.isLoading) && <LoadingState />}

        {(healthQ.isError || archivesQ.isError) && (
          <ErrorState
            message={errorMessage(healthQ.error ?? archivesQ.error)}
            onRetry={() => {
              void healthQ.refetch();
              void archivesQ.refetch();
            }}
          />
        )}

        {health && !healthQ.isError && (
          <div className="space-y-5">
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              <Metric
                icon={health.healthy ? CheckCircle2 : AlertTriangle}
                label="Integridade"
                value={health.healthy ? "Saudável" : "Requer atenção"}
                tone={health.healthy ? "success" : "destructive"}
              />
              <Metric
                icon={Database}
                label="SQLite local"
                value={
                  health.database_present ? `Schema ${health.schema_version}` : "Ainda não criado"
                }
                tone={health.database_present ? "accent" : "muted"}
              />
              <Metric
                icon={HeartPulse}
                label="Registros verificados"
                value={String(records)}
                tone="accent"
              />
              <Metric
                icon={FileArchive}
                label="Arquivos disponíveis"
                value={String(archives.length)}
                tone="accent"
              />
            </div>

            {health.issues.length > 0 && <HealthIssues issues={health.issues} />}

            <div className="grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
              <div className="rounded-xl border border-border bg-muted/20 p-4">
                <div className="flex items-start gap-3">
                  <div className="grid h-10 w-10 place-items-center rounded-lg bg-accent/10 text-accent">
                    <Archive className="h-5 w-5" />
                  </div>
                  <div>
                    <h4 className="font-semibold">Backup e export portátil</h4>
                    <p className="mt-1 text-xs text-muted-foreground">
                      Inclui banco, stores legados e metadados não secretos. Chaves, tokens, cookies
                      e dados da extensão são excluídos.
                    </p>
                  </div>
                </div>
                <div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
                  <Button
                    type="button"
                    onClick={() => createMutation.mutate("backup")}
                    disabled={createMutation.isPending}
                  >
                    {createMutation.isPending ? <Loader2 className="animate-spin" /> : <Archive />}
                    Criar backup
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => createMutation.mutate("export")}
                    disabled={createMutation.isPending}
                  >
                    <Download />
                    Criar export
                  </Button>
                </div>
              </div>

              <div className="rounded-xl border border-border bg-muted/20 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h4 className="font-semibold">Arquivos locais</h4>
                    <p className="mt-1 text-xs text-muted-foreground">
                      O caminho completo nunca é exposto ao navegador.
                    </p>
                  </div>
                  {selected && (
                    <Button
                      type="button"
                      size="sm"
                      variant="ghost"
                      onClick={() => downloadArchive(selected)}
                    >
                      <Download />
                      Baixar
                    </Button>
                  )}
                </div>
                {archives.length ? (
                  <label className="mt-4 block text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Selecionar arquivo
                    <select
                      value={selectedArchive}
                      onChange={(event) => {
                        setSelectedArchive(event.target.value);
                        setValidatedArchive("");
                        setConfirmation("");
                      }}
                      className="mt-1.5 w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-normal normal-case tracking-normal text-foreground"
                      data-testid="data-archive-select"
                    >
                      {archives.map((archive) => (
                        <option key={archive.archive_name} value={archive.archive_name}>
                          {archive.kind === "backup" ? "Backup" : "Export"} ·{" "}
                          {formatDate(archive.created_at)} · {formatBytes(archive.size)}
                        </option>
                      ))}
                    </select>
                  </label>
                ) : (
                  <p className="mt-4 rounded-lg border border-dashed border-border p-4 text-center text-sm text-muted-foreground">
                    Nenhum arquivo criado ainda.
                  </p>
                )}
              </div>
            </div>

            {selected && (
              <div className="rounded-xl border border-warning/30 bg-warning/5 p-4">
                <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
                  <div className="max-w-2xl">
                    <div className="flex items-center gap-2 font-semibold">
                      <RotateCcw className="h-4 w-4 text-warning" />
                      Restauração protegida
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">
                      Primeiro valide checksum e compatibilidade. Para aplicar, digite RESTAURAR. Um
                      backup de segurança é criado automaticamente antes da sobrescrita.
                    </p>
                  </div>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => validateMutation.mutate(selected.archive_name)}
                    disabled={validateMutation.isPending || restoreMutation.isPending}
                    data-testid="validate-restore"
                  >
                    {validateMutation.isPending ? (
                      <Loader2 className="animate-spin" />
                    ) : (
                      <ShieldCheck />
                    )}
                    Validar sem alterar
                  </Button>
                </div>

                {validatedArchive === selected.archive_name && (
                  <div
                    className="mt-4 grid gap-3 rounded-lg border border-success/30 bg-background p-3 md:grid-cols-[1fr_auto] md:items-end"
                    aria-live="polite"
                  >
                    <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                      Confirmação obrigatória
                      <Input
                        value={confirmation}
                        onChange={(event) => setConfirmation(event.target.value)}
                        placeholder="Digite RESTAURAR"
                        className="mt-1.5 font-mono normal-case tracking-normal"
                        autoComplete="off"
                        data-testid="restore-confirmation"
                      />
                    </label>
                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <Button
                          type="button"
                          variant="destructive"
                          disabled={!canApply}
                          data-testid="apply-restore"
                        >
                          <RotateCcw />
                          Aplicar restauração
                        </Button>
                      </AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader>
                          <AlertDialogTitle>Restaurar este arquivo local?</AlertDialogTitle>
                          <AlertDialogDescription>
                            Esta ação substituirá os dados correspondentes. O SotuHire criará um
                            backup de segurança antes de gravar qualquer arquivo.
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel>Cancelar</AlertDialogCancel>
                          <AlertDialogAction
                            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                            onClick={() => restoreMutation.mutate(selected.archive_name)}
                          >
                            Confirmar restauração
                          </AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </SectionCard>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="grid min-h-40 place-items-center text-sm text-muted-foreground" role="status">
      <div className="flex items-center gap-2">
        <Loader2 className="h-4 w-4 animate-spin" />
        Verificando dados locais…
      </div>
    </div>
  );
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-4" role="alert">
      <div className="flex items-start gap-3">
        <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-destructive" />
        <div className="flex-1">
          <div className="font-medium">Não foi possível verificar os dados</div>
          <p className="mt-1 text-xs text-muted-foreground">{message}</p>
        </div>
        <Button type="button" size="sm" variant="outline" onClick={onRetry}>
          Tentar novamente
        </Button>
      </div>
    </div>
  );
}

function HealthIssues({ issues }: { issues: DataHealthIssue[] }) {
  return (
    <div className="rounded-xl border border-warning/30 bg-warning/5 p-4">
      <div className="flex items-center gap-2 font-medium">
        <AlertTriangle className="h-4 w-4 text-warning" />
        {issues.length} {issues.length === 1 ? "aviso encontrado" : "avisos encontrados"}
      </div>
      <ul className="mt-3 grid gap-2 md:grid-cols-2">
        {issues.slice(0, 8).map((issue, index) => (
          <li
            key={`${issue.code}-${issue.record_id}-${index}`}
            className="rounded-lg bg-background p-3"
          >
            <div className="flex items-center justify-between gap-2">
              <span className="text-xs font-semibold">{issue.message}</span>
              <span
                className={cn(
                  "rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase",
                  issue.severity === "error"
                    ? "bg-destructive/10 text-destructive"
                    : issue.severity === "warning"
                      ? "bg-warning/10 text-warning"
                      : "bg-muted text-muted-foreground",
                )}
              >
                {issue.severity}
              </span>
            </div>
            {issue.store && (
              <div className="mt-1 truncate font-mono text-[10px] text-muted-foreground">
                {issue.store}
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

function Metric({
  icon: Icon,
  label,
  value,
  tone,
}: {
  icon: typeof Database;
  label: string;
  value: string;
  tone: "success" | "destructive" | "accent" | "muted";
}) {
  const tones = {
    success: "border-success/30 bg-success/5 text-success",
    destructive: "border-destructive/30 bg-destructive/5 text-destructive",
    accent: "border-accent/20 bg-accent/5 text-accent",
    muted: "border-border bg-muted/30 text-muted-foreground",
  };
  return (
    <div className={cn("rounded-xl border p-4", tones[tone])}>
      <Icon className="h-4 w-4" />
      <div className="mt-3 text-xs text-muted-foreground">{label}</div>
      <div className="mt-0.5 font-semibold text-foreground">{value}</div>
    </div>
  );
}

function PrivacyLevel({
  tone,
  title,
  description,
}: {
  tone: "success" | "warning" | "destructive";
  title: string;
  description: string;
}) {
  const tones = {
    success: "border-success/30 bg-success/5",
    warning: "border-warning/30 bg-warning/5",
    destructive: "border-destructive/30 bg-destructive/5",
  };
  return (
    <li className={cn("rounded-lg border p-3", tones[tone])}>
      <div className="font-medium">{title}</div>
      <div className="text-xs text-muted-foreground">{description}</div>
    </li>
  );
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Falha inesperada na API local.";
}

function formatBytes(value: number): string {
  if (!Number.isFinite(value) || value <= 0) return "0 B";
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "data indisponível";
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(date);
}
