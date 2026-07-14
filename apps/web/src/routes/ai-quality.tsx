import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { Activity, BadgeCheck, Clock3, Coins, Database, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { SectionCard } from "@/components/section-card";
import { StatCard } from "@/components/stat-card";
import { ErrorState, LoadingState } from "@/components/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useApi } from "@/lib/api/hooks";
import { useApiMode } from "@/lib/api/mode";
import type { SampleConfidence } from "@/lib/api/types";

export const Route = createFileRoute("/ai-quality")({
  head: () => ({ meta: [{ title: "IA e Qualidade — SotuHire" }] }),
  component: AiQualityPage,
});

export function sampleLabel(value: SampleConfidence | string): string {
  if (value === "comparable") return "comparável";
  if (value === "indicative") return "indicativo";
  return "insuficiente";
}

const percent = (value?: number | null) =>
  value === null || value === undefined ? "—" : `${Math.round(value * 100)}%`;

function AiQualityPage() {
  const api = useApi();
  const { mode } = useApiMode();
  const queryClient = useQueryClient();
  const summary = useQuery({
    queryKey: ["ai-quality-summary", mode],
    queryFn: api.aiQualitySummary,
  });
  const runs = useQuery({ queryKey: ["ai-quality-runs", mode], queryFn: api.aiQualityRuns });
  const providers = useQuery({
    queryKey: ["ai-quality-providers", mode],
    queryFn: api.aiQualityProviders,
  });
  const prompts = useQuery({
    queryKey: ["ai-quality-prompts", mode],
    queryFn: api.aiQualityPrompts,
  });
  const benchmarks = useQuery({
    queryKey: ["ai-quality-benchmarks", mode],
    queryFn: api.aiQualityBenchmarks,
  });
  const feedback = useQuery({ queryKey: ["ai-feedback", mode], queryFn: api.aiFeedback });
  const outcomes = useQuery({ queryKey: ["outcomes-summary", mode], queryFn: api.outcomesSummary });
  const [runId, setRunId] = useState("");
  const [rating, setRating] = useState<"useful" | "partial" | "not_useful">("useful");
  const [decision, setDecision] = useState<"accepted" | "edited" | "rejected" | "ignored">(
    "accepted",
  );
  const [unsupported, setUnsupported] = useState(false);
  const [comment, setComment] = useState("");

  useEffect(() => {
    if (!runId && runs.data?.items[0]) setRunId(runs.data.items[0].run_id);
  }, [runId, runs.data]);

  const submit = useMutation({
    mutationFn: () => {
      const run = runs.data?.items.find((item) => item.run_id === runId);
      if (!run) throw new Error("Selecione uma execução.");
      return api.aiFeedbackCreate({
        run_id: runId,
        task_id: run.task_id,
        rating,
        decision,
        edited: decision === "edited",
        unsupported_claim: unsupported,
        comment,
      });
    },
    onSuccess: () => {
      setComment("");
      void queryClient.invalidateQueries({ queryKey: ["ai-feedback", mode] });
      void queryClient.invalidateQueries({ queryKey: ["ai-quality-summary", mode] });
    },
  });

  const loading = [summary, runs, providers, prompts, benchmarks, feedback, outcomes].some(
    (query) => query.isLoading,
  );
  const error = [summary, runs, providers, prompts, benchmarks, feedback, outcomes].find(
    (query) => query.error,
  )?.error;
  if (loading)
    return (
      <AppShell title="IA e Qualidade">
        <LoadingState label="Carregando métricas seguras…" />
      </AppShell>
    );
  if (error)
    return (
      <AppShell title="IA e Qualidade">
        <ErrorState error={error} />
      </AppShell>
    );

  const data = summary.data!;
  return (
    <AppShell
      title="IA e Qualidade"
      description="Avaliação determinística, traces sem conteúdo integral, feedback humano e outcomes exploratórios."
    >
      <div className="space-y-6">
        {data.empty_state && (
          <div className="rounded-lg border border-dashed p-6 text-sm text-muted-foreground">
            Não há execuções suficientes para gerar métricas confiáveis.
          </div>
        )}
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
          <StatCard label="Execuções" value={data.executions} icon={Activity} tone="accent" />
          <StatCard label="Schema válido" value={percent(data.schema_validity)} icon={BadgeCheck} />
          <StatCard label="Fallback" value={percent(data.fallback_rate)} icon={Database} />
          <StatCard
            label="Latência média"
            value={data.average_latency_ms ? `${Math.round(data.average_latency_ms)} ms` : "—"}
            icon={Clock3}
          />
          <StatCard
            label="Custo estimado"
            value={data.estimated_cost ? `US$ ${data.estimated_cost.toFixed(4)}` : "não disponível"}
            icon={Coins}
          />
        </div>

        <Tabs defaultValue="summary" className="space-y-4">
          <TabsList className="flex h-auto flex-wrap justify-start">
            <TabsTrigger value="summary">Resumo</TabsTrigger>
            <TabsTrigger value="providers">Providers</TabsTrigger>
            <TabsTrigger value="prompts">Prompts</TabsTrigger>
            <TabsTrigger value="benchmarks">Benchmarks</TabsTrigger>
            <TabsTrigger value="feedback">Feedback</TabsTrigger>
            <TabsTrigger value="outcomes">Resultados profissionais</TabsTrigger>
            <TabsTrigger value="privacy">Privacidade</TabsTrigger>
          </TabsList>

          <TabsContent value="summary">
            <SectionCard title="Qualidade observada" description={data.message}>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <Metric label="Aceitas" value={percent(data.human_acceptance_rate)} />
                <Metric label="Editadas" value={percent(data.human_edit_rate)} />
                <Metric label="Rejeitadas" value={percent(data.human_rejection_rate)} />
                <Metric
                  label="Afirmação sem evidência"
                  value={percent(data.unsupported_claim_rate)}
                />
              </div>
              <p className="mt-4 text-xs text-muted-foreground">
                Amostra: {sampleLabel(data.sample_confidence)}. Nenhum vencedor é declarado sem
                amostra comparável.
              </p>
            </SectionCard>
          </TabsContent>

          <TabsContent value="providers">
            <SectionCard
              title="Comparação de providers e modelos"
              description="Qualidade é descritiva e inclui validade de schema e feedback disponível."
            >
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Task</TableHead>
                    <TableHead>Provider</TableHead>
                    <TableHead>Modelo</TableHead>
                    <TableHead>Qualidade</TableHead>
                    <TableHead>Latência</TableHead>
                    <TableHead>Custo</TableHead>
                    <TableHead>Fallback</TableHead>
                    <TableHead>Aceitação</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {providers.data!.items.map((item) => (
                    <TableRow key={`${item.task}-${item.provider}-${item.model}`}>
                      <TableCell>
                        {item.task}
                        <div className="text-xs text-muted-foreground">
                          n={item.sample_size} · {sampleLabel(item.sample_confidence)}
                        </div>
                      </TableCell>
                      <TableCell>{item.provider}</TableCell>
                      <TableCell>{item.model}</TableCell>
                      <TableCell>{percent(item.quality)}</TableCell>
                      <TableCell>
                        {item.latency_ms ? `${Math.round(item.latency_ms)} ms` : "—"}
                      </TableCell>
                      <TableCell>{item.cost ? `US$ ${item.cost.toFixed(4)}` : "—"}</TableCell>
                      <TableCell>{percent(item.fallback_rate)}</TableCell>
                      <TableCell>{percent(item.acceptance_rate)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </SectionCard>
          </TabsContent>

          <TabsContent value="prompts">
            <SectionCard
              title="Prompts ativos"
              description="Cada prompt tem uma task, versão, schema e suite de avaliação."
            >
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Task</TableHead>
                    <TableHead>Prompt</TableHead>
                    <TableHead>Versão</TableHead>
                    <TableHead>Suite</TableHead>
                    <TableHead>Runs</TableHead>
                    <TableHead>Baseline</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {prompts.data!.items.map((item) => (
                    <TableRow key={item.task_id}>
                      <TableCell>{item.task_id}</TableCell>
                      <TableCell>{item.prompt_id}</TableCell>
                      <TableCell>{item.prompt_version}</TableCell>
                      <TableCell>{item.evaluation_suite}</TableCell>
                      <TableCell>{item.run_count}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{item.baseline_status}</Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </SectionCard>
          </TabsContent>

          <TabsContent value="benchmarks">
            <SectionCard
              title="Benchmarks reproduzíveis"
              description="Relatórios armazenam métricas, nunca inputs ou outputs pessoais integrais."
            >
              {benchmarks.data!.items.length ? (
                benchmarks.data!.items.map((item) => (
                  <div key={item.benchmark_run_id} className="mb-3 rounded-md border p-4 text-sm">
                    <div className="font-medium">
                      {item.suite} · {item.status}
                    </div>
                    <div className="mt-1 text-muted-foreground">
                      {item.providers.join(", ")} · dataset {item.dataset_version} ·{" "}
                      {item.environment}
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">
                  Nenhum benchmark persistido neste banco local.
                </p>
              )}
            </SectionCard>
          </TabsContent>

          <TabsContent value="feedback">
            <div className="grid gap-6 lg:grid-cols-2">
              <SectionCard
                title="Avaliar resultado"
                description="Feedback é apagável e fica ligado ao run_id, sem copiar o conteúdo gerado."
              >
                <div className="space-y-4">
                  <Select value={runId} onValueChange={setRunId}>
                    <SelectTrigger>
                      <SelectValue placeholder="Execução" />
                    </SelectTrigger>
                    <SelectContent>
                      {runs.data!.items.map((item) => (
                        <SelectItem key={item.run_id} value={item.run_id}>
                          {item.task_id} · {item.provider_used} · {item.run_id.slice(0, 8)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <Select
                      value={rating}
                      onValueChange={(value) => setRating(value as typeof rating)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="useful">Útil</SelectItem>
                        <SelectItem value="partial">Parcialmente útil</SelectItem>
                        <SelectItem value="not_useful">Não útil</SelectItem>
                      </SelectContent>
                    </Select>
                    <Select
                      value={decision}
                      onValueChange={(value) => setDecision(value as typeof decision)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="accepted">Aceito</SelectItem>
                        <SelectItem value="edited">Editado</SelectItem>
                        <SelectItem value="rejected">Rejeitado</SelectItem>
                        <SelectItem value="ignored">Ignorado</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <label className="flex items-center gap-2 text-sm">
                    <Checkbox
                      checked={unsupported}
                      onCheckedChange={(value) => setUnsupported(value === true)}
                    />
                    Contém afirmação sem evidência
                  </label>
                  <Input
                    value={comment}
                    onChange={(event) => setComment(event.target.value)}
                    placeholder="Comentário opcional"
                    maxLength={1000}
                  />
                  <Button onClick={() => submit.mutate()} disabled={!runId || submit.isPending}>
                    Salvar feedback
                  </Button>
                </div>
              </SectionCard>
              <SectionCard
                title="Feedback recente"
                description="Útil, parcial, não útil; aceito, editado, rejeitado ou ignorado."
              >
                <div className="space-y-3">
                  {feedback.data!.items.map((item) => (
                    <div key={item.feedback_id} className="rounded-md border p-3 text-sm">
                      <div className="flex justify-between gap-3">
                        <span className="font-medium">{item.task_id}</span>
                        <Badge variant="outline">
                          {item.rating} · {item.decision}
                        </Badge>
                      </div>
                      <p className="mt-2 text-muted-foreground">
                        {item.comment || "Sem comentário."}
                      </p>
                    </div>
                  ))}
                </div>
              </SectionCard>
            </div>
          </TabsContent>

          <TabsContent value="outcomes">
            <SectionCard title="Outcome Learning" description={outcomes.data!.note}>
              <div className="grid gap-4 sm:grid-cols-3">
                <Metric
                  label="Taxa de resposta"
                  value={percent(outcomes.data!.response_rate.value)}
                  detail={outcomes.data!.response_rate.note}
                />
                <Metric
                  label="Taxa de entrevista"
                  value={percent(outcomes.data!.interview_rate.value)}
                  detail={outcomes.data!.interview_rate.note}
                />
                <Metric
                  label="Taxa de oferta"
                  value={percent(outcomes.data!.offer_rate.value)}
                  detail={outcomes.data!.offer_rate.note}
                />
              </div>
              <p className="mt-4 text-xs text-muted-foreground">
                n={outcomes.data!.sample_size} · {sampleLabel(outcomes.data!.confidence)}. O sistema
                não altera Perfil ou pesos automaticamente.
              </p>
            </SectionCard>
          </TabsContent>

          <TabsContent value="privacy">
            <SectionCard title="Privacidade de traces" description="Default seguro da v1.9.7.">
              <div className="grid gap-4 sm:grid-cols-3">
                <PrivacyItem title="Inputs completos" value="não armazenados" />
                <PrivacyItem title="Outputs completos" value="não armazenados" />
                <PrivacyItem title="Trechos" value="somente metadados redigidos" />
              </div>
              <div className="mt-4 flex items-start gap-2 rounded-md bg-muted p-4 text-sm">
                <ShieldCheck className="mt-0.5 h-4 w-4 text-accent" />
                <p>
                  API keys, Authorization, cookies, tokens, currículo, vaga, prompt e resposta
                  integral não entram no AiRunStore.
                </p>
              </div>
            </SectionCard>
          </TabsContent>
        </Tabs>
      </div>
    </AppShell>
  );
}

function Metric({ label, value, detail }: { label: string; value: string; detail?: string }) {
  return (
    <div className="rounded-md border p-4">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="mt-1 text-xl font-semibold">{value}</div>
      {detail && <p className="mt-2 text-xs text-muted-foreground">{detail}</p>}
    </div>
  );
}

function PrivacyItem({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-md border p-4">
      <div className="text-sm font-medium">{title}</div>
      <div className="mt-1 text-sm text-muted-foreground">{value}</div>
    </div>
  );
}
