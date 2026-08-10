import { pairedApiFetch } from "@/features/local-security/api-pairing";
import type { ApiMode } from "@/lib/api/mode";

export interface NextBestAction {
  action_id: string;
  type: string;
  priority: number;
  urgency: "low" | "medium" | "high" | "critical";
  reason: string;
  evidence_refs: string[];
  impact: string;
  estimated_effort: string;
  blocking: boolean;
}

export interface CareerState {
  profile_summary: string;
  career_goals: string[];
  current_focus: string[];
  confirmed_strengths: string[];
  evidence_gaps: string[];
  portfolio_gaps: string[];
  academic_strengths: string[];
  active_applications: number;
  upcoming_interviews: number;
  pending_followups: number;
  overdue_tasks: number;
  stale_artifacts: number;
  top_opportunities: Array<Record<string, unknown>>;
  provider_health: string;
  data_health: string;
  recommendation_candidates: NextBestAction[];
  confidence: {
    data_coverage: number;
    rule_confidence: number;
    provider_confidence: number | null;
  };
  dependency_hash: string;
  generated_at: string;
}

export interface EvidenceNode {
  node_id: string;
  node_type: string;
  title: string;
  summary: string;
  source_refs: string[];
  review_status: "candidate" | "confirmed" | "rejected" | "stale";
  confidence: number;
  sensitive: boolean;
  updated_at: string;
}

export interface PortfolioItem {
  portfolio_item_id: string;
  title: string;
  type: string;
  description: string;
  role: string;
  links: string[];
  skills: string[];
  tools: string[];
  evidence_refs: string[];
  review_status: string;
  visibility: string;
}

export interface ProposedAction {
  proposal_id: string;
  action_type: string;
  title: string;
  description: string;
  reason: string;
  evidence_refs: string[];
  affected_entities: string[];
  before_snapshot: Record<string, unknown>;
  after_preview: Record<string, unknown>;
  risk: string;
  reversible: boolean;
  undo_strategy: string;
  status: string;
  created_at: string;
}

interface Envelope<T> {
  ok: boolean;
  data: T;
  error?: { message?: string };
}

const demoState: CareerState = {
  profile_summary: "12 evidências confirmadas e 3 para revisar.",
  career_goals: ["Engenharia de dados com impacto público"],
  current_focus: ["INTERVIEW_PREP_DUE", "PROFILE_REVIEW_REQUIRED"],
  confirmed_strengths: ["Python", "Pesquisa aplicada", "Comunicação técnica"],
  evidence_gaps: ["Resultado do Projeto Aurora", "Publicação em revisão", "Mentoria voluntária"],
  portfolio_gaps: ["Transformar o Projeto Aurora em case study"],
  academic_strengths: ["Iniciação científica", "Análise de dados"],
  active_applications: 4,
  upcoming_interviews: 1,
  pending_followups: 2,
  overdue_tasks: 1,
  stale_artifacts: 1,
  top_opportunities: [{ opportunity_id: "demo-1", fit_score: 86 }],
  provider_health: "explicit-check-required",
  data_health: "healthy",
  recommendation_candidates: [
    {
      action_id: "demo-action-1",
      type: "INTERVIEW_PREP_DUE",
      priority: 90,
      urgency: "high",
      reason: "Há entrevista agendada nos próximos sete dias.",
      evidence_refs: ["project-demo"],
      impact: "Cria espaço para preparação baseada em evidências.",
      estimated_effort: "30–60 min",
      blocking: true,
    },
    {
      action_id: "demo-action-2",
      type: "PROFILE_REVIEW_REQUIRED",
      priority: 82,
      urgency: "high",
      reason: "3 evidências aguardam confirmação.",
      evidence_refs: ["evidence-demo"],
      impact: "Melhora a cobertura sem transformar inferência em fato.",
      estimated_effort: "10–20 min",
      blocking: false,
    },
  ],
  confidence: { data_coverage: 0.8, rule_confidence: 1, provider_confidence: null },
  dependency_hash: "demo-fictitious",
  generated_at: "2026-08-10T12:00:00Z",
};

const demoEvidence: EvidenceNode[] = [
  {
    node_id: "project-demo",
    node_type: "project",
    title: "Projeto Aurora",
    summary: "Pipeline fictício de dados públicos.",
    source_refs: ["manual:demo"],
    review_status: "confirmed",
    confidence: 1,
    sensitive: false,
    updated_at: "2026-08-10T12:00:00Z",
  },
  {
    node_id: "skill-demo",
    node_type: "skill",
    title: "Python",
    summary: "Associada ao Projeto Aurora.",
    source_refs: ["portfolio:demo"],
    review_status: "confirmed",
    confidence: 1,
    sensitive: false,
    updated_at: "2026-08-10T12:00:00Z",
  },
  {
    node_id: "evidence-demo",
    node_type: "publication",
    title: "Resumo para congresso",
    summary: "Extração candidata; requer confirmação.",
    source_refs: ["document:demo"],
    review_status: "candidate",
    confidence: 0.72,
    sensitive: false,
    updated_at: "2026-08-10T12:00:00Z",
  },
];

const demoPortfolio: PortfolioItem[] = [
  {
    portfolio_item_id: "portfolio-demo",
    title: "Projeto Aurora",
    type: "data",
    description: "Case fictício de integração de dados com proveniência.",
    role: "Engenharia de dados",
    links: ["https://example.org/demo"],
    skills: ["Python", "SQL"],
    tools: ["FastAPI"],
    evidence_refs: ["project-demo"],
    review_status: "confirmed",
    visibility: "private",
  },
];

const demoApprovals: ProposedAction[] = [
  {
    proposal_id: "proposal-demo",
    action_type: "create_task",
    title: "Preparar entrevista técnica",
    description: "Cria uma tarefa local somente após aprovação.",
    reason: "Entrevista fictícia em três dias.",
    evidence_refs: ["project-demo"],
    affected_entities: ["career_tasks"],
    before_snapshot: {},
    after_preview: { title: "Preparar entrevista técnica", priority: "high" },
    risk: "low",
    reversible: true,
    undo_strategy: "Remover a tarefa criada",
    status: "proposed",
    created_at: "2026-08-10T12:00:00Z",
  },
];

function v2Base(baseUrl: string): string {
  return baseUrl.replace(/\/api\/v1\/?$/, "/api/v2");
}

async function request<T>(baseUrl: string, path: string, init?: RequestInit): Promise<T> {
  const response = await pairedApiFetch(v2Base(baseUrl), path, {
    ...init,
    headers: { "content-type": "application/json", ...(init?.headers ?? {}) },
  });
  const envelope = (await response.json()) as Envelope<T>;
  if (!response.ok || !envelope.ok) {
    throw new Error(envelope.error?.message || `HTTP ${response.status}`);
  }
  return envelope.data;
}

export const v2Api = (mode: ApiMode, baseUrl: string) => ({
  careerState: () =>
    mode === "demo" ? Promise.resolve(demoState) : request<CareerState>(baseUrl, "/career-state"),
  evidence: () =>
    mode === "demo" ? Promise.resolve(demoEvidence) : request<EvidenceNode[]>(baseUrl, "/evidence"),
  reviewEvidence: (nodeId: string, review_status: EvidenceNode["review_status"]) =>
    mode === "demo"
      ? Promise.resolve({ ...demoEvidence.find((item) => item.node_id === nodeId)!, review_status })
      : request<EvidenceNode>(baseUrl, `/evidence/${encodeURIComponent(nodeId)}/review`, {
          method: "PATCH",
          body: JSON.stringify({ review_status }),
        }),
  portfolio: () =>
    mode === "demo"
      ? Promise.resolve(demoPortfolio)
      : request<PortfolioItem[]>(baseUrl, "/portfolio"),
  approvals: () =>
    mode === "demo"
      ? Promise.resolve(demoApprovals)
      : request<ProposedAction[]>(baseUrl, "/approvals"),
  transition: (proposalId: string, action: "approve" | "reject" | "execute" | "undo") =>
    mode === "demo"
      ? Promise.resolve({
          ...demoApprovals[0],
          status:
            action === "approve"
              ? "approved"
              : action === "reject"
                ? "rejected"
                : action === "undo"
                  ? "undone"
                  : "executed",
        })
      : request<ProposedAction | { proposal: ProposedAction; result: Record<string, unknown> }>(
          baseUrl,
          `/approvals/${encodeURIComponent(proposalId)}/${action}`,
          { method: "POST" },
        ),
  createProposal: (payload: {
    tool_id: string;
    input: Record<string, unknown>;
    reason: string;
    evidence_refs?: string[];
  }) =>
    mode === "demo"
      ? Promise.resolve(demoApprovals[0])
      : request<ProposedAction>(baseUrl, "/approvals", {
          method: "POST",
          body: JSON.stringify(payload),
        }),
  search: (query: string) =>
    mode === "demo"
      ? Promise.resolve(
          [...demoEvidence, ...demoPortfolio]
            .filter((item) => item.title.toLowerCase().includes(query.toLowerCase()))
            .map((item) => ({
              entity_type: "node_id" in item ? "evidence" : "portfolio",
              entity_id: "node_id" in item ? item.node_id : item.portfolio_item_id,
              title: item.title,
              route: "node_id" in item ? "/evidence" : "/portfolio",
            })),
        )
      : request<Array<{ entity_type: string; entity_id: string; title: string; route: string }>>(
          baseUrl,
          `/search?query=${encodeURIComponent(query)}`,
        ),
});
