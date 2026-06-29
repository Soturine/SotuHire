// Centralized public-facing labels for SotuHire.
// Keep internal API enum values intact; this file translates them for the UI.

export const APP_VERSION = "1.9.0";
export const APP_NAME = "SotuHire";
export const APP_TAGLINE = "Inteligência de carreira · local-first";
export const API_LOCAL_HOST = "127.0.0.1:8787";

export const APPLICATION_STATUS_LABELS: Record<string, string> = {
  found: "Encontrada",
  saved: "Salva",
  analyzed: "Salva",
  good_fit: "Boa para aplicar",
  ready_to_apply: "Boa para aplicar",
  applied: "Aplicada",
  message_sent: "Mensagem enviada",
  follow_up: "Follow-up",
  response: "Com resposta",
  technical_test: "Teste técnico",
  tech_test: "Teste técnico",
  interview: "Entrevista",
  offer: "Oferta",
  rejected: "Rejeitada",
  archived: "Arquivada",
};

export function statusLabel(status?: string | null): string {
  if (!status) return "—";
  return APPLICATION_STATUS_LABELS[status] ?? status;
}

export const SCORE_LABELS = {
  compatibility: "Pontuação de compatibilidade",
  compatibilityShort: "Compat.",
  confidence: "Confiança",
  ats: "Alinhamento ATS",
  opportunityFit: "Aderência à vaga",
  risk: "Risco",
} as const;
