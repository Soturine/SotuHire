import { messages, type TranslationKey } from "./messages";

export const SUPPORTED_LOCALES = ["pt-BR", "en-US"] as const;
export type SupportedLocale = (typeof SUPPORTED_LOCALES)[number];
export type LocalePreference = "system" | SupportedLocale;
export type TranslationValues = Record<string, string | number>;

export function detectBrowserLocale(languages?: readonly string[]): SupportedLocale {
  const candidates =
    languages ??
    (typeof navigator === "undefined"
      ? []
      : [...(navigator.languages ?? []), navigator.language].filter(Boolean));

  return candidates.some((language) => language.toLowerCase().startsWith("pt")) ? "pt-BR" : "en-US";
}

export function resolveLocale(
  preference: LocalePreference,
  languages?: readonly string[],
): SupportedLocale {
  return preference === "system" ? detectBrowserLocale(languages) : preference;
}

export function translate(
  locale: SupportedLocale,
  key: TranslationKey,
  values: TranslationValues = {},
): string {
  const template = messages[locale][key];
  return Object.entries(values).reduce(
    (result, [name, value]) => result.replaceAll(`{{${name}}}`, String(value)),
    template,
  );
}

export type { TranslationKey } from "./messages";
export { createIntlFormatters, formatDate, formatNumber } from "./format";
