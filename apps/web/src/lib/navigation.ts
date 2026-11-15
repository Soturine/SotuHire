import {
  BadgeCheck,
  BrainCircuit,
  Briefcase,
  CalendarCheck,
  Compass,
  Files,
  FileText,
  FlaskConical,
  FolderKanban,
  Github,
  Inbox,
  Kanban,
  LifeBuoy,
  LineChart,
  ListTodo,
  Network,
  RadioTower,
  ScanSearch,
  ScrollText,
  Settings,
  ShieldCheck,
  Target,
  UserRound,
  Wand2,
  type LucideIcon,
} from "lucide-react";

import type { TranslationKey } from "@/lib/i18n";

/**
 * The one registry of navigable screens. The sidebar, the mobile tab bar, the page header
 * (journey eyebrow) and the search palette all read it, so a screen is either here once or
 * nowhere. Journeys group screens by what the person is trying to do, not by module; the last
 * group holds settings and diagnostics.
 */

export type JourneyId =
  "today" | "profile" | "resumes" | "opportunities" | "applications" | "system";

export interface NavEntry {
  path: string;
  label: TranslationKey;
  icon: LucideIcon;
  /** Extra words people type for this screen (both languages, without accents is fine). */
  keywords: string;
}

export interface Journey {
  id: JourneyId;
  label: TranslationKey;
  /** Fits a mobile tab (about 9 characters). */
  short: TranslationKey;
  purpose: TranslationKey;
  icon: LucideIcon;
  entries: NavEntry[];
}

export const JOURNEYS: Journey[] = [
  {
    id: "today",
    label: "journey.today.label",
    short: "journey.today.short",
    purpose: "journey.today.purpose",
    icon: Compass,
    entries: [
      {
        path: "/dashboard",
        label: "route.dashboard.label",
        icon: Compass,
        keywords: "inicio home cockpit painel dashboard resumo proximos passos next steps",
      },
      {
        path: "/approvals",
        label: "route.approvals.label",
        icon: BadgeCheck,
        keywords: "aprovar aprovacoes approve approvals pendente fila queue copilot undo desfazer",
      },
    ],
  },
  {
    id: "profile",
    label: "journey.profile.label",
    short: "journey.profile.short",
    purpose: "journey.profile.purpose",
    icon: UserRound,
    entries: [
      {
        path: "/profile",
        label: "route.profile.label",
        icon: UserRound,
        keywords:
          "perfil profile experiencia formacao skills competencias dados pessoais universal",
      },
      {
        path: "/evidence",
        label: "route.evidence.label",
        icon: Network,
        keywords: "evidencias evidence provas confirmar fatos inbox",
      },
      {
        path: "/portfolio",
        label: "route.portfolio.label",
        icon: FolderKanban,
        keywords: "portfolio projetos projects trabalhos",
      },
      {
        path: "/github",
        label: "route.github.label",
        icon: Github,
        keywords: "github repositorios repos codigo code",
      },
    ],
  },
  {
    id: "resumes",
    label: "journey.resumes.label",
    short: "journey.resumes.short",
    purpose: "journey.resumes.purpose",
    icon: FileText,
    entries: [
      {
        path: "/resume-studio",
        label: "route.resumeStudio.label",
        icon: Files,
        keywords: "curriculo mestre resume studio cv variantes exportar docx pdf editor",
      },
      {
        path: "/resume",
        label: "route.resume.label",
        icon: FileText,
        keywords: "curriculo curriculos resume cv importar import",
      },
      {
        path: "/tailor",
        label: "route.tailor.label",
        icon: Wand2,
        keywords: "ajustar ajuste tailor adaptar curriculo vaga",
      },
      {
        path: "/ats",
        label: "route.ats.label",
        icon: ScanSearch,
        keywords: "ats robo triagem leitura palavras-chave keywords",
      },
    ],
  },
  {
    id: "opportunities",
    label: "journey.opportunities.label",
    short: "journey.opportunities.short",
    purpose: "journey.opportunities.purpose",
    icon: RadioTower,
    entries: [
      {
        path: "/radar",
        label: "route.radar.label",
        icon: RadioTower,
        keywords: "radar vagas oportunidades buscar jobs opportunities alertas",
      },
      {
        path: "/job",
        label: "route.job.label",
        icon: Briefcase,
        keywords: "vaga vagas job jobs descricao colar analisar",
      },
      {
        path: "/public-exams",
        label: "route.publicExams.label",
        icon: ScrollText,
        keywords: "concurso concursos edital editais public exams cargo publico",
      },
      {
        path: "/sources",
        label: "route.sources.label",
        icon: Inbox,
        keywords: "fontes sources captura extensao extension feeds rss",
      },
    ],
  },
  {
    id: "applications",
    label: "journey.applications.label",
    short: "journey.applications.short",
    purpose: "journey.applications.purpose",
    icon: Kanban,
    entries: [
      {
        path: "/application-lab",
        label: "route.applicationLab.label",
        icon: FlaskConical,
        keywords: "preparar candidatura application lab kit carta sugestoes",
      },
      {
        path: "/match",
        label: "route.match.label",
        icon: Target,
        keywords: "compatibilidade match aderencia fit requisitos",
      },
      {
        path: "/tracker",
        label: "route.tracker.label",
        icon: Kanban,
        keywords: "tracker acompanhamento candidaturas status kanban follow-up",
      },
      {
        path: "/interviews",
        label: "route.interviews.label",
        icon: CalendarCheck,
        keywords: "entrevistas interviews agenda star preparacao",
      },
      {
        path: "/career",
        label: "route.career.label",
        icon: ListTodo,
        keywords: "plano carreira career plan metas tarefas lembretes",
      },
      {
        path: "/intelligence",
        label: "route.intelligence.label",
        icon: LineChart,
        keywords: "inteligencia intelligence mercado tendencias metricas",
      },
    ],
  },
  {
    id: "system",
    label: "journey.system.label",
    short: "journey.system.short",
    purpose: "journey.system.purpose",
    icon: Settings,
    entries: [
      {
        path: "/settings",
        label: "route.settings.label",
        icon: Settings,
        keywords: "configuracoes settings preferencias api local provider ia ai chave",
      },
      {
        path: "/privacy",
        label: "route.privacy.label",
        icon: ShieldCheck,
        keywords: "privacidade privacy dados locais backup exportar apagar",
      },
      {
        path: "/ai-quality",
        label: "route.aiQuality.label",
        icon: BrainCircuit,
        keywords: "qualidade ia ai quality providers fallback benchmark",
      },
      {
        path: "/help",
        label: "route.help.label",
        icon: LifeBuoy,
        keywords: "ajuda help duvidas como usar guia",
      },
    ],
  },
];

/** Journeys shown in the mobile tab bar, in order; the rest open from "Mais". */
export const MOBILE_TABS: { journey: JourneyId; path: string }[] = [
  { journey: "today", path: "/dashboard" },
  { journey: "profile", path: "/profile" },
  { journey: "resumes", path: "/resume-studio" },
  { journey: "opportunities", path: "/radar" },
  { journey: "applications", path: "/tracker" },
];

export const NAV_ENTRIES: (NavEntry & { journey: Journey })[] = JOURNEYS.flatMap((journey) =>
  journey.entries.map((entry) => ({ ...entry, journey })),
);

export function journeyFor(pathname: string): Journey | undefined {
  return JOURNEYS.find((journey) => journey.entries.some((entry) => entry.path === pathname));
}

export function entryFor(pathname: string) {
  return NAV_ENTRIES.find((entry) => entry.path === pathname);
}
