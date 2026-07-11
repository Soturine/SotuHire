// Mock data para a tela "Fontes e Captura" — apenas UI, sem efeitos reais.
import {
  ClipboardPaste,
  Link2,
  FileSpreadsheet,
  Puzzle,
  Radar,
  Plug,
  Monitor,
  type LucideIcon,
} from "lucide-react";

export type SourceStatus = "available" | "demo" | "planned" | "future" | "extension" | "api";

export const SOURCE_STATUS_LABEL: Record<SourceStatus, string> = {
  available: "Disponível",
  demo: "Demo",
  planned: "Planejado",
  future: "Futuro",
  extension: "Requer extensão local",
  api: "Requer API oficial",
};

export type SourceCard = {
  id: string;
  title: string;
  description: string;
  cta: string;
  status: SourceStatus;
  icon: LucideIcon;
  to?: string;
  anchor?: string;
  disabled?: boolean;
};

export const SOURCE_CARDS: SourceCard[] = [
  {
    id: "paste",
    title: "Colar vaga manualmente",
    description: "Cole o texto da vaga para análise imediata.",
    cta: "Colar vaga",
    status: "available",
    icon: ClipboardPaste,
    to: "/job",
  },
  {
    id: "link",
    title: "Colar link da vaga",
    description: "Salve o link junto da vaga para referência e rastreamento.",
    cta: "Adicionar link",
    status: "available",
    icon: Link2,
    to: "/job",
  },
  {
    id: "import",
    title: "Importar CSV/JSON",
    description: "Importe listas de vagas exportadas manualmente.",
    cta: "Importar arquivo",
    status: "available",
    icon: FileSpreadsheet,
  },
  {
    id: "authenticated-browser",
    title: "Navegador autenticado autorizado",
    description:
      "Use o Chromium dedicado do SotuHire para uma sessão autorizada, com login manual e limites explícitos.",
    cta: "Ver fluxo local",
    status: "available",
    icon: Monitor,
    anchor: "#authenticated-browser",
  },
  {
    id: "extension",
    title: "Captura assistida via extensão",
    description:
      "Use a extensão/local companion para capturar informações visíveis da página, com ação manual do usuário.",
    cta: "Ver extensão",
    status: "extension",
    icon: Puzzle,
  },
  {
    id: "radar",
    title: "Radar de vagas públicas",
    description:
      "Buscar oportunidades em fontes públicas e páginas abertas, respeitando limites e regras.",
    cta: "Configurar radar",
    status: "available",
    icon: Radar,
    to: "/radar",
  },
  {
    id: "apis",
    title: "APIs oficiais e integrações",
    description: "Conectar integrações oficiais quando disponíveis.",
    cta: "Ver integrações",
    status: "api",
    icon: Plug,
    disabled: true,
  },
];

export const SOURCE_FLOW = [
  "Capturar ou importar vaga",
  "Extrair requisitos",
  "Comparar com currículo",
  "Salvar em Candidaturas",
  "Acompanhar métricas em Inteligência",
];
