import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  CalendarDays,
  CheckCircle2,
  ClipboardCheck,
  FileSearch,
  GraduationCap,
  Loader2,
  Save,
  Scale,
  ScrollText,
  ShieldCheck,
  Sparkles,
  WalletCards,
  type LucideIcon,
} from "lucide-react";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { toast } from "sonner";
import { AppShell } from "@/components/app-shell";
import { ProviderBadge } from "@/components/provider-badge";
import { SectionCard } from "@/components/section-card";
import { EmptyState } from "@/components/states";
import { useApi } from "@/lib/api/hooks";
import { useApiMode } from "@/lib/api/mode";
import type {
  ExamNotice,
  ExamRequirement,
  ExamRole,
  ExamSubject,
  PublicExamAnalyzeResult,
  PublicExamImportResult,
  PublicExamStudyPlanResult,
} from "@/lib/api/types";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/public-exams")({
  head: () => ({
    meta: [
      { title: "Editais e Concursos - SotuHire" },
      {
        name: "description",
        content:
          "Fundação local-first para interpretar editais, comparar requisitos com o Perfil Profissional Universal e criar plano inicial de estudos.",
      },
    ],
  }),
  component: PublicExamsPage,
});

const OFFICIAL_WARNING =
  "O SotuHire ajuda a organizar e interpretar editais, mas o edital oficial sempre prevalece. Revise manualmente requisitos, datas, taxa, documentos, conteúdo programático e regras da banca.";

const SAMPLE_NOTICE = `Edital nº 01/2026 - Concurso Público Prefeitura Exemplo
Órgão: Prefeitura Municipal de Exemplo
Banca organizadora: Instituto Exemplo
Cargo: Engenheiro Civil
Vagas: 2
Local de prova: São José dos Campos
Salário: R$ 6.200,00
Taxa de inscrição: R$ 120,00
Carga horária: 40h semanais
Inscrições: 01/08/2026 a 20/08/2026
Pagamento da taxa: até 21/08/2026
Prova objetiva: 13/09/2026
Requisitos: graduação concluída em Engenharia Civil e registro ativo no CREA.
Documentos: documento de identidade, CPF, diploma, registro profissional e quitação eleitoral.
Etapas: prova objetiva e prova de títulos.
Conteúdo programático:
Língua Portuguesa: interpretação de texto, concordância, pontuação.
Conhecimentos Específicos: licitações, obras públicas, fiscalização de contratos, segurança do trabalho.`;

function PublicExamsPage() {
  const api = useApi();
  const { mode, baseUrl } = useApiMode();
  const qc = useQueryClient();
  const [text, setText] = useState(mode === "demo" ? SAMPLE_NOTICE : "");
  const [sourceUrl, setSourceUrl] = useState("https://example.invalid/edital-01-2026.pdf");
  const [sourceName, setSourceName] = useState("Prefeitura Exemplo");
  const [weeklyHours, setWeeklyHours] = useState(8);
  const [useAi, setUseAi] = useState(false);
  const [draft, setDraft] = useState<PublicExamImportResult | null>(null);
  const [savedNotice, setSavedNotice] = useState<ExamNotice | null>(null);
  const [selectedRoleId, setSelectedRoleId] = useState("");
  const [analysis, setAnalysis] = useState<PublicExamAnalyzeResult | null>(null);
  const [studyPlan, setStudyPlan] = useState<PublicExamStudyPlanResult | null>(null);

  useEffect(() => {
    if (mode === "demo" && !text.trim()) setText(SAMPLE_NOTICE);
    if (mode === "real" && text === SAMPLE_NOTICE) setText("");
  }, [mode, text]);

  const noticesQ = useQuery({
    queryKey: ["public-exams", mode, baseUrl],
    queryFn: () => api.publicExamList(),
    retry: false,
  });

  const importExam = useMutation({
    mutationFn: () =>
      api.publicExamImport({
        text,
        source_url: sourceUrl,
        source_name: sourceName,
        use_ai: useAi,
      }),
    onSuccess: (data) => {
      setDraft(data);
      setSavedNotice(null);
      setAnalysis(null);
      setStudyPlan(null);
      setSelectedRoleId(data.roles[0]?.role_id || data.notice.roles[0]?.role_id || "");
      toast.success("Rascunho de edital gerado. Revise antes de salvar.");
    },
    onError: (error) =>
      toast.error(error instanceof Error ? error.message : "Falha ao analisar edital."),
  });

  const confirmExam = useMutation({
    mutationFn: (notice: ExamNotice) => api.publicExamConfirm(notice.notice_id, notice),
    onSuccess: (data) => {
      setSavedNotice(data.notice);
      qc.invalidateQueries({ queryKey: ["public-exams"] });
      toast.success(data.message || "Edital salvo localmente.");
    },
    onError: (error) =>
      toast.error(error instanceof Error ? error.message : "Falha ao salvar edital."),
  });

  const analyzeExam = useMutation({
    mutationFn: async () => {
      const notice = await ensureSaved();
      return api.publicExamAnalyze(notice.notice_id, selectedRoleId);
    },
    onSuccess: (data) => {
      setAnalysis(data);
      toast.success("Comparação inicial com o Perfil concluída.");
    },
    onError: (error) =>
      toast.error(error instanceof Error ? error.message : "Falha ao comparar com o Perfil."),
  });

  const generatePlan = useMutation({
    mutationFn: async () => {
      const notice = await ensureSaved();
      return api.publicExamStudyPlan(notice.notice_id, {
        role_id: selectedRoleId,
        weekly_hours: weeklyHours,
      });
    },
    onSuccess: (data) => {
      setStudyPlan(data);
      toast.success("Plano de estudo inicial gerado.");
    },
    onError: (error) =>
      toast.error(error instanceof Error ? error.message : "Falha ao gerar plano de estudo."),
  });

  async function ensureSaved(): Promise<ExamNotice> {
    if (savedNotice) return savedNotice;
    const notice = draft?.notice;
    if (!notice) throw new Error("Analise um edital antes.");
    const result = await confirmExam.mutateAsync(notice);
    return result.notice;
  }

  const notice = savedNotice ?? draft?.notice ?? null;
  const roles = notice?.roles.length ? notice.roles : (draft?.roles ?? []);
  const selectedRole = roles.find((role) => role.role_id === selectedRoleId) ?? roles[0] ?? null;
  const busy =
    importExam.isPending ||
    confirmExam.isPending ||
    analyzeExam.isPending ||
    generatePlan.isPending;

  return (
    <AppShell
      title="Editais / Concursos"
      description="Fundação para entender editais, comparar requisitos com o Perfil e planejar estudos."
      actions={
        <ProviderBadge
          provider={draft?.provider_used || "local"}
          mode={draft?.analysis_mode || "local"}
          fallback={draft?.analysis_mode === "fallback"}
        />
      }
    >
      <div className="mx-auto flex max-w-7xl flex-col gap-5" data-testid="public-exams-page">
        <section
          data-testid="public-exams-official-warning"
          className="flex items-start gap-3 rounded-xl border border-warning/40 bg-warning/5 p-4"
        >
          <div className="grid h-9 w-9 shrink-0 place-items-center rounded-md bg-warning/15 text-warning">
            <ShieldCheck className="h-4 w-4" />
          </div>
          <div>
            <div className="text-sm font-semibold">Edital oficial prevalece</div>
            <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{OFFICIAL_WARNING}</p>
          </div>
        </section>

        <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
          <SectionCard
            title={
              <span className="flex items-center gap-2">
                <ScrollText className="h-4 w-4 text-accent" />
                Importar edital por texto
              </span>
            }
            description="Cole o texto do edital. O rascunho não é salvo sem confirmação."
            actions={
              <button
                type="button"
                onClick={() => importExam.mutate()}
                disabled={!text.trim() || importExam.isPending}
                data-testid="public-exams-analyze"
                className="inline-flex items-center gap-2 rounded-md bg-primary px-3 py-2 text-xs font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
              >
                {importExam.isPending ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <FileSearch className="h-3.5 w-3.5" />
                )}
                Analisar edital
              </button>
            }
          >
            <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_280px]">
              <TextArea
                label="Texto do edital"
                value={text}
                onChange={setText}
                testId="public-exams-textarea"
                placeholder="Cole o texto oficial do edital ou chamada pública."
              />
              <div className="space-y-3">
                <TextField label="URL oficial opcional" value={sourceUrl} onChange={setSourceUrl} />
                <TextField label="Fonte" value={sourceName} onChange={setSourceName} />
                <label className="flex items-center gap-2 rounded-md border border-border px-3 py-2 text-sm">
                  <input
                    type="checkbox"
                    checked={useAi}
                    onChange={(event) => setUseAi(event.target.checked)}
                  />
                  Usar IA/Gemini se configurada
                </label>
                <NumberField label="Horas semanais" value={weeklyHours} onChange={setWeeklyHours} />
              </div>
            </div>
          </SectionCard>

          <SectionCard title="Editais salvos" description="Rascunhos confirmados localmente.">
            <div className="space-y-3">
              {(noticesQ.data?.notices ?? []).slice(0, 5).map((item) => (
                <button
                  key={item.notice_id}
                  type="button"
                  onClick={() => {
                    setSavedNotice(item);
                    setDraft(null);
                    setSelectedRoleId(item.roles[0]?.role_id || "");
                    setAnalysis(null);
                    setStudyPlan(null);
                  }}
                  className="w-full rounded-lg border border-border bg-background p-3 text-left text-sm hover:bg-muted/50"
                >
                  <div className="font-semibold">{item.title}</div>
                  <div className="mt-1 text-xs text-muted-foreground">
                    {item.organization || "Órgão a revisar"} ·{" "}
                    {item.exam_board || "Banca a revisar"}
                  </div>
                </button>
              ))}
              {!noticesQ.isLoading && !(noticesQ.data?.notices.length ?? 0) && (
                <EmptyState
                  title="Nenhum edital salvo"
                  description="Analise e salve um edital revisado para acompanhar localmente."
                />
              )}
            </div>
          </SectionCard>
        </div>

        {notice && (
          <>
            <section className="grid gap-3 md:grid-cols-4">
              <InfoTile icon={Scale} label="Órgão" value={notice.organization || "A revisar"} />
              <InfoTile
                icon={GraduationCap}
                label="Banca"
                value={notice.exam_board || "A revisar"}
              />
              <InfoTile
                icon={WalletCards}
                label="Taxa"
                value={notice.registration_fee || "A revisar"}
              />
              <InfoTile
                icon={CalendarDays}
                label="Prova"
                value={notice.timeline.exam_date || "A revisar"}
              />
            </section>

            <SectionCard
              title="Rascunho extraído"
              description="Revise campos, cargos, requisitos e datas antes de salvar."
              actions={
                <button
                  type="button"
                  onClick={() => confirmExam.mutate(notice)}
                  disabled={busy}
                  data-testid="public-exams-save"
                  className="inline-flex items-center gap-2 rounded-md border border-input px-3 py-2 text-xs font-semibold hover:bg-muted disabled:opacity-60"
                >
                  <Save className="h-3.5 w-3.5" />
                  Salvar edital revisado
                </button>
              }
            >
              <div className="grid gap-5 lg:grid-cols-[1fr_1fr]">
                <div className="space-y-4">
                  <div>
                    <h2 className="text-lg font-semibold">{notice.title}</h2>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {notice.notice_number || "Número a revisar"} ·{" "}
                      {notice.source_name || "Fonte manual"}
                    </p>
                  </div>
                  <RoleSelector
                    roles={roles}
                    selectedRoleId={selectedRole?.role_id || ""}
                    onChange={setSelectedRoleId}
                  />
                  {selectedRole && <RoleSummary role={selectedRole} />}
                </div>
                <div className="space-y-4">
                  <TimelineBox notice={notice} />
                  <WarningsList warnings={[...notice.warnings, ...(draft?.warnings ?? [])]} />
                </div>
              </div>
            </SectionCard>

            <div className="grid gap-5 lg:grid-cols-[1fr_1fr]">
              <SectionCard title="Requisitos e documentos">
                <RequirementList
                  requirements={[
                    ...(selectedRole?.requirements ?? []),
                    ...notice.general_requirements,
                  ]}
                />
                <div className="mt-4">
                  <h3 className="mb-2 text-sm font-semibold">Checklist de documentos</h3>
                  <ChipList items={notice.documents} empty="Documentos não detectados." />
                </div>
              </SectionCard>

              <SectionCard title="Conteúdo programático">
                <SubjectList
                  subjects={selectedRole?.subjects.length ? selectedRole.subjects : notice.subjects}
                />
              </SectionCard>
            </div>

            <SectionCard
              title="Comparar com meu Perfil"
              description="Usa Perfil Profissional Universal, contexto de carreira e evidências acadêmicas/Lattes já confirmadas."
              actions={
                <button
                  type="button"
                  onClick={() => analyzeExam.mutate()}
                  disabled={busy}
                  data-testid="public-exams-compare"
                  className="inline-flex items-center gap-2 rounded-md bg-primary px-3 py-2 text-xs font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
                >
                  {analyzeExam.isPending ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Sparkles className="h-3.5 w-3.5" />
                  )}
                  Comparar com meu Perfil
                </button>
              }
            >
              {analysis ? (
                <FitScorePanel analysis={analysis} />
              ) : (
                <EmptyState
                  title="Score ainda não gerado"
                  description="Compare o cargo com seu Perfil para ver requisitos atendidos, ausentes e incertos."
                />
              )}
            </SectionCard>

            <SectionCard
              title="Plano de estudo inicial"
              description="Rascunho simples por disciplinas e prioridades. Não é um produto completo de estudos."
              actions={
                <button
                  type="button"
                  onClick={() => generatePlan.mutate()}
                  disabled={busy}
                  data-testid="public-exams-generate-study-plan"
                  className="inline-flex items-center gap-2 rounded-md border border-input px-3 py-2 text-xs font-semibold hover:bg-muted disabled:opacity-60"
                >
                  {generatePlan.isPending ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <ClipboardCheck className="h-3.5 w-3.5" />
                  )}
                  Gerar plano de estudo inicial
                </button>
              }
            >
              {studyPlan ? (
                <StudyPlanPanel result={studyPlan} />
              ) : (
                <EmptyState
                  title="Plano ainda não gerado"
                  description="Use as disciplinas extraídas para montar uma primeira distribuição semanal."
                />
              )}
            </SectionCard>
          </>
        )}
      </div>
    </AppShell>
  );
}

function RoleSelector({
  roles,
  selectedRoleId,
  onChange,
}: {
  roles: ExamRole[];
  selectedRoleId: string;
  onChange: (value: string) => void;
}) {
  if (!roles.length) return null;
  return (
    <label className="block">
      <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
        Cargo detectado
      </span>
      <select
        value={selectedRoleId}
        onChange={(event) => onChange(event.target.value)}
        data-testid="public-exams-role-select"
        className="mt-1.5 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
      >
        {roles.map((role) => (
          <option key={role.role_id} value={role.role_id}>
            {role.title}
          </option>
        ))}
      </select>
    </label>
  );
}

function RoleSummary({ role }: { role: ExamRole }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2" data-testid="public-exams-role-summary">
      <MiniInfo label="Cargo" value={role.title} />
      <MiniInfo label="Salário/bolsa" value={role.salary || "A revisar"} />
      <MiniInfo
        label="Escolaridade"
        value={role.education_level || role.required_degree || "A revisar"}
      />
      <MiniInfo label="Registro" value={role.required_registry || "Não detectado"} />
      <MiniInfo label="Vagas" value={role.vacancies || "A revisar"} />
      <MiniInfo label="Local" value={role.location || "A revisar"} />
    </div>
  );
}

function TimelineBox({ notice }: { notice: ExamNotice }) {
  const timeline = notice.timeline;
  const items = [
    ["Início inscrições", timeline.registration_start],
    ["Fim inscrições", timeline.registration_end],
    ["Pagamento", timeline.payment_deadline],
    ["Prova", timeline.exam_date],
    ["Resultado", timeline.result_date],
  ];
  return (
    <div>
      <h3 className="mb-2 text-sm font-semibold">Timeline</h3>
      <div className="grid gap-2 sm:grid-cols-2">
        {items.map(([label, value]) => (
          <MiniInfo key={label} label={label} value={value || "A revisar"} />
        ))}
      </div>
    </div>
  );
}

function RequirementList({ requirements }: { requirements: ExamRequirement[] }) {
  const unique = useMemo(() => {
    const seen = new Set<string>();
    return requirements.filter((item) => {
      const key = `${item.kind}:${item.description}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }, [requirements]);

  if (!unique.length) {
    return <EmptyState title="Requisitos não detectados" description="Revise o edital oficial." />;
  }

  return (
    <div className="space-y-2" data-testid="public-exams-requirements">
      {unique.map((item) => (
        <div
          key={item.requirement_id}
          className="rounded-lg border border-border bg-background p-3"
        >
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone={requirementTone(item.match_status)}>
              {statusLabel(item.match_status)}
            </Badge>
            <Badge>{item.kind}</Badge>
            {item.mandatory && <Badge tone="warning">Obrigatório</Badge>}
          </div>
          <p className="mt-2 text-sm text-muted-foreground">{item.description}</p>
          {item.evidence_needed && (
            <p className="mt-1 text-xs text-muted-foreground">Evidência: {item.evidence_needed}</p>
          )}
        </div>
      ))}
    </div>
  );
}

function SubjectList({ subjects }: { subjects: ExamSubject[] }) {
  if (!subjects.length) {
    return (
      <EmptyState
        title="Conteúdo não detectado"
        description="Cole a seção de conteúdo programático do edital."
      />
    );
  }
  return (
    <div className="space-y-3" data-testid="public-exams-subjects">
      {subjects.map((subject) => (
        <div
          key={`${subject.name}-${subject.stage}`}
          className="rounded-lg border border-border bg-background p-3"
        >
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-semibold">{subject.name}</h3>
            <Badge tone={subject.priority === "high" ? "success" : "neutral"}>
              {subject.priority === "high" ? "Prioridade alta" : "Prioridade média"}
            </Badge>
          </div>
          <ChipList items={subject.topics} empty="Tópicos a revisar." className="mt-2" />
        </div>
      ))}
    </div>
  );
}

function FitScorePanel({ analysis }: { analysis: PublicExamAnalyzeResult }) {
  const score = analysis.fit_score;
  return (
    <div
      className="grid gap-5 lg:grid-cols-[300px_minmax(0,1fr)]"
      data-testid="public-exams-fit-score"
    >
      <div className="rounded-xl border border-border bg-background p-4">
        <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Exam Fit Score
        </div>
        <div className="mt-2 text-5xl font-semibold tabular-nums">{score.overall_score}</div>
        <Badge tone={recommendationTone(score.recommendation)}>
          {recommendationLabel(score.recommendation)}
        </Badge>
        <div className="mt-4 grid gap-2 text-xs">
          <ScoreRow label="Requisitos" value={score.requirement_score} />
          <ScoreRow label="Timeline" value={score.timeline_score} />
          <ScoreRow label="Local" value={score.location_score} />
          <ScoreRow label="Estudo" value={score.study_effort_score} />
          <ScoreRow label="Risco" value={score.risk_score} />
        </div>
      </div>
      <div className="space-y-4">
        {analysis.context_summary && (
          <p className="rounded-lg border border-border bg-muted/30 p-3 text-xs text-muted-foreground">
            Contexto: {analysis.context_summary}
          </p>
        )}
        <div className="grid gap-3 md:grid-cols-3">
          <MiniRequirement title="Atendidos" items={score.matched_requirements} tone="success" />
          <MiniRequirement title="Ausentes" items={score.missing_requirements} tone="error" />
          <MiniRequirement title="Incertos" items={score.uncertain_requirements} tone="warning" />
        </div>
        <div data-testid="public-exams-checklist">
          <h3 className="mb-2 text-sm font-semibold">Checklist de revisão</h3>
          <RequirementList requirements={analysis.checklist} />
        </div>
      </div>
    </div>
  );
}

function StudyPlanPanel({ result }: { result: PublicExamStudyPlanResult }) {
  const plan = result.study_plan;
  return (
    <div className="space-y-4" data-testid="public-exams-study-plan">
      <div className="grid gap-3 md:grid-cols-3">
        <MiniInfo
          label="Dias até a prova"
          value={plan.days_until_exam == null ? "Sem data" : String(plan.days_until_exam)}
        />
        <MiniInfo label="Horas semanais" value={`${plan.weekly_hours}h`} />
        <MiniInfo label="Disciplinas" value={String(plan.subjects.length)} />
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <MiniList title="Tópicos prioritários" items={plan.priority_topics} />
        <MiniList title="Blocos sugeridos" items={plan.schedule_blocks} />
      </div>
      <WarningsList warnings={plan.warnings} />
    </div>
  );
}

function WarningsList({ warnings }: { warnings: string[] }) {
  const unique = Array.from(new Set(warnings.filter(Boolean)));
  if (!unique.length) return null;
  return (
    <div className="space-y-2" data-testid="public-exams-warnings">
      {unique.slice(0, 6).map((warning) => (
        <div
          key={warning}
          className="flex items-start gap-2 rounded-lg border border-warning/30 bg-warning/5 p-3 text-xs text-muted-foreground"
        >
          <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-warning" />
          <span>{warning}</span>
        </div>
      ))}
    </div>
  );
}

function MiniRequirement({
  title,
  items,
  tone,
}: {
  title: string;
  items: ExamRequirement[];
  tone: "success" | "warning" | "error";
}) {
  return (
    <div className="rounded-lg border border-border bg-background p-3">
      <Badge tone={tone}>{title}</Badge>
      <ul className="mt-2 space-y-1 text-xs text-muted-foreground">
        {(items.length
          ? items
          : [
              {
                requirement_id: title,
                description: "Sem itens.",
                kind: "",
                mandatory: false,
                evidence_needed: "",
                matched_profile_item_ids: [],
                match_status: "uncertain" as const,
                confidence: "low" as const,
                warnings: [],
              },
            ]
        )
          .slice(0, 4)
          .map((item) => (
            <li key={item.requirement_id}>{item.description}</li>
          ))}
      </ul>
    </div>
  );
}

function MiniList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded-lg border border-border bg-background p-3">
      <h3 className="text-sm font-semibold">{title}</h3>
      <ul className="mt-2 space-y-1 text-xs text-muted-foreground">
        {(items.length ? items : ["A revisar."]).slice(0, 8).map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function InfoTile({
  icon: Icon,
  label,
  value,
}: {
  icon: LucideIcon;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <Icon className="h-4 w-4 text-accent" />
      <div className="mt-2 text-xs text-muted-foreground">{label}</div>
      <div className="mt-1 truncate text-sm font-semibold">{value}</div>
    </div>
  );
}

function MiniInfo({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border bg-background p-3">
      <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
        {label}
      </div>
      <div className="mt-1 text-sm font-medium">{value || "A revisar"}</div>
    </div>
  );
}

function ScoreRow({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-mono font-semibold">{value}</span>
    </div>
  );
}

function ChipList({
  items,
  empty,
  className,
}: {
  items: string[];
  empty: string;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-wrap gap-1.5", className)}>
      {(items.length ? items : [empty]).slice(0, 12).map((item) => (
        <Badge key={item}>{item}</Badge>
      ))}
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
    <label className="block">
      <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
        {label}
      </span>
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="mt-1.5 w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:border-accent/50 focus:ring-2 focus:ring-accent/20"
      />
    </label>
  );
}

function NumberField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
}) {
  return (
    <label className="block">
      <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
        {label}
      </span>
      <input
        type="number"
        min={1}
        max={80}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
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
      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        data-testid={testId}
        className="mt-1.5 min-h-80 w-full resize-y rounded-md border border-input bg-background px-3 py-2 text-sm leading-relaxed outline-none focus:border-accent/50 focus:ring-2 focus:ring-accent/20"
      />
    </label>
  );
}

function Badge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: "neutral" | "success" | "warning" | "error";
}) {
  const cls =
    tone === "success"
      ? "border-success/30 bg-success/10 text-success-foreground"
      : tone === "warning"
        ? "border-warning/30 bg-warning/10 text-warning-foreground"
        : tone === "error"
          ? "border-destructive/30 bg-destructive/10 text-destructive"
          : "border-border bg-muted text-muted-foreground";
  return (
    <span className={cn("rounded-full border px-2 py-0.5 text-[11px] font-medium", cls)}>
      {children}
    </span>
  );
}

function requirementTone(status: ExamRequirement["match_status"]) {
  if (status === "matched") return "success";
  if (status === "missing") return "error";
  return "warning";
}

function statusLabel(status: ExamRequirement["match_status"]) {
  if (status === "matched") return "Atendido";
  if (status === "missing") return "Ausente";
  return "Incerto";
}

function recommendationTone(
  recommendation: PublicExamAnalyzeResult["fit_score"]["recommendation"],
) {
  if (recommendation === "strong_fit" || recommendation === "good_fit") return "success";
  if (recommendation === "risky" || recommendation === "not_recommended") return "error";
  return "warning";
}

function recommendationLabel(
  recommendation: PublicExamAnalyzeResult["fit_score"]["recommendation"],
) {
  const labels: Record<PublicExamAnalyzeResult["fit_score"]["recommendation"], string> = {
    strong_fit: "Forte compatibilidade",
    good_fit: "Boa compatibilidade",
    review_requirements: "Revisar requisitos",
    risky: "Risco alto",
    not_recommended: "Não recomendado",
    insufficient_information: "Informação insuficiente",
  };
  return labels[recommendation];
}
