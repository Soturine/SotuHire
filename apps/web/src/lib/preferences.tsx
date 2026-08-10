import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import {
  createIntlFormatters,
  resolveLocale,
  translate,
  type LocalePreference,
  type SupportedLocale,
  type TranslationKey,
  type TranslationValues,
} from "@/lib/i18n";

export type ThemePreference = "system" | "light" | "dark";
export type ResolvedTheme = "light" | "dark";

const STORAGE_KEY = "sotuhire.ui-preferences.v1";
const ONBOARDING_KEY = "sotuhire.onboarding.v1.complete";

interface StoredPreferences {
  locale: LocalePreference;
  theme: ThemePreference;
}

interface PreferencesContextValue {
  localePreference: LocalePreference;
  locale: SupportedLocale;
  setLocalePreference: (value: LocalePreference) => void;
  themePreference: ThemePreference;
  theme: ResolvedTheme;
  setThemePreference: (value: ThemePreference) => void;
  onboardingComplete: boolean;
  completeOnboarding: () => void;
  restartOnboarding: () => void;
  t: (key: TranslationKey, values?: TranslationValues) => string;
  format: ReturnType<typeof createIntlFormatters>;
}

const PreferencesContext = createContext<PreferencesContextValue | null>(null);

function readPreferences(): StoredPreferences {
  if (typeof window === "undefined") return { locale: "system", theme: "system" };
  try {
    const value = JSON.parse(
      window.localStorage.getItem(STORAGE_KEY) ?? "{}",
    ) as Partial<StoredPreferences>;
    const locale = ["system", "pt-BR", "en-US"].includes(value.locale ?? "")
      ? (value.locale as LocalePreference)
      : "system";
    const theme = ["system", "light", "dark"].includes(value.theme ?? "")
      ? (value.theme as ThemePreference)
      : "system";
    return { locale, theme };
  } catch {
    return { locale: "system", theme: "system" };
  }
}

function systemTheme(): ResolvedTheme {
  return typeof window !== "undefined" && window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

function resolveTheme(preference: ThemePreference): ResolvedTheme {
  return preference === "system" ? systemTheme() : preference;
}

function applyAppearance(preferences: StoredPreferences): void {
  if (typeof document === "undefined") return;
  const locale = resolveLocale(preferences.locale);
  const theme = resolveTheme(preferences.theme);
  document.documentElement.lang = locale;
  document.documentElement.classList.toggle("dark", theme === "dark");
  document.documentElement.style.colorScheme = theme;
}

export function applyStoredAppearance(): void {
  applyAppearance(readPreferences());
}

export function PreferencesProvider({ children }: { children: ReactNode }) {
  const initial = useMemo(readPreferences, []);
  const [localePreference, setLocalePreference] = useState<LocalePreference>(initial.locale);
  const [themePreference, setThemePreference] = useState<ThemePreference>(initial.theme);
  const [systemRevision, setSystemRevision] = useState(0);
  const [onboardingComplete, setOnboardingComplete] = useState(
    () => typeof window !== "undefined" && window.localStorage.getItem(ONBOARDING_KEY) === "true",
  );
  const locale = resolveLocale(localePreference);
  const theme = resolveTheme(themePreference);

  useEffect(() => {
    const color = window.matchMedia("(prefers-color-scheme: dark)");
    const language = () => setSystemRevision((value) => value + 1);
    color.addEventListener("change", language);
    window.addEventListener("languagechange", language);
    return () => {
      color.removeEventListener("change", language);
      window.removeEventListener("languagechange", language);
    };
  }, []);

  useEffect(() => {
    const preferences = { locale: localePreference, theme: themePreference };
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences));
    applyAppearance(preferences);
  }, [localePreference, themePreference, systemRevision]);

  const value = useMemo<PreferencesContextValue>(
    () => ({
      localePreference,
      locale,
      setLocalePreference,
      themePreference,
      theme,
      setThemePreference,
      onboardingComplete,
      completeOnboarding: () => {
        window.localStorage.setItem(ONBOARDING_KEY, "true");
        setOnboardingComplete(true);
      },
      restartOnboarding: () => {
        window.localStorage.removeItem(ONBOARDING_KEY);
        setOnboardingComplete(false);
      },
      t: (key, values) => translate(locale, key, values),
      format: createIntlFormatters(locale),
    }),
    [localePreference, locale, themePreference, theme, onboardingComplete],
  );

  return <PreferencesContext.Provider value={value}>{children}</PreferencesContext.Provider>;
}

export function usePreferences(): PreferencesContextValue {
  const context = useContext(PreferencesContext);
  if (!context) throw new Error("usePreferences must be used inside PreferencesProvider");
  return context;
}

export const preferenceStorageKeys = { preferences: STORAGE_KEY, onboarding: ONBOARDING_KEY };
