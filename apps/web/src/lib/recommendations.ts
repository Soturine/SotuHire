/**
 * Recommendation types of the career state (Career Copilot v2): what to call each one and where
 * the person acts on it. Shared by the Cockpit and the Copilot drawer so both say the same thing.
 */
export type Locale = "pt-BR" | "en-US";

/** Each recommendation type: what to call it and where the person acts on it. */
export const ACTIONS: Record<string, { to: string; label: Record<Locale, [string, string]> }> = {
  APPLICATION_FOLLOW_UP_DUE: {
    to: "/tracker",
    label: {
      "pt-BR": ["Retomar candidaturas com prazo vencido", "Abrir Tracker"],
      "en-US": ["Follow up on overdue applications", "Open Tracker"],
    },
  },
  INTERVIEW_PREP_DUE: {
    to: "/interviews",
    label: {
      "pt-BR": ["Preparar a próxima entrevista", "Preparar"],
      "en-US": ["Prepare for the next interview", "Prepare"],
    },
  },
  PROFILE_REVIEW_REQUIRED: {
    to: "/evidence",
    label: {
      "pt-BR": ["Confirmar evidências pendentes", "Revisar evidências"],
      "en-US": ["Confirm pending evidence", "Review evidence"],
    },
  },
  PORTFOLIO_GAP: {
    to: "/portfolio",
    label: {
      "pt-BR": ["Levar projetos confirmados ao portfólio", "Abrir portfólio"],
      "en-US": ["Bring confirmed projects to the portfolio", "Open portfolio"],
    },
  },
  MISSING_CRITICAL_EVIDENCE: {
    to: "/evidence",
    label: {
      "pt-BR": ["Comprovar competências sem evidência", "Ver lacunas"],
      "en-US": ["Back skills that have no evidence", "See gaps"],
    },
  },
  RESUME_STALE: {
    to: "/resume-studio",
    label: {
      "pt-BR": ["Atualizar o Currículo Mestre", "Abrir Resume Studio"],
      "en-US": ["Update the Master Resume", "Open Resume Studio"],
    },
  },
  HIGH_FIT_OPPORTUNITY: {
    to: "/radar",
    label: {
      "pt-BR": ["Avaliar uma oportunidade com boa aderência", "Ver no Radar"],
      "en-US": ["Review a well-matched opportunity", "See in Radar"],
    },
  },
};

export function actionCopy(type: string, locale: Locale) {
  const known = ACTIONS[type];
  if (known) return { to: known.to, title: known.label[locale][0], cta: known.label[locale][1] };
  // Unknown types still render, readable, and go to the approval queue as before.
  const readable = type.toLowerCase().replaceAll("_", " ");
  return {
    to: "/approvals",
    title: readable.charAt(0).toUpperCase() + readable.slice(1),
    cta: locale === "pt-BR" ? "Revisar" : "Review",
  };
}
