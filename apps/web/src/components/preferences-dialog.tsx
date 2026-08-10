import { Languages } from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { usePreferences } from "@/lib/preferences";

export function PreferenceFields() {
  const preferences = usePreferences();
  const { t } = preferences;
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <label className="grid gap-1.5 text-sm font-medium">
        {t("preferences.locale")}
        <select
          value={preferences.localePreference}
          onChange={(event) =>
            preferences.setLocalePreference(event.target.value as "system" | "pt-BR" | "en-US")
          }
          className="rounded-md border border-input bg-background px-3 py-2 text-sm"
        >
          <option value="system">{t("preferences.locale.system")}</option>
          <option value="pt-BR">{t("preferences.locale.pt-BR")}</option>
          <option value="en-US">{t("preferences.locale.en-US")}</option>
        </select>
        <span className="text-xs font-normal text-muted-foreground">
          {t("preferences.resolved", { value: preferences.locale })}
        </span>
      </label>
      <label className="grid gap-1.5 text-sm font-medium">
        {t("preferences.theme")}
        <select
          value={preferences.themePreference}
          onChange={(event) =>
            preferences.setThemePreference(event.target.value as "system" | "light" | "dark")
          }
          className="rounded-md border border-input bg-background px-3 py-2 text-sm"
        >
          <option value="system">{t("preferences.theme.system")}</option>
          <option value="light">{t("preferences.theme.light")}</option>
          <option value="dark">{t("preferences.theme.dark")}</option>
        </select>
        <span className="text-xs font-normal text-muted-foreground">
          {t("preferences.resolved", {
            value: t(`preferences.theme.${preferences.theme}`),
          })}
        </span>
      </label>
    </div>
  );
}

export function PreferencesDialog() {
  const { t, restartOnboarding } = usePreferences();
  return (
    <Dialog>
      <DialogTrigger asChild>
        <button
          type="button"
          className="grid h-9 w-9 place-items-center rounded-md border border-border bg-card text-muted-foreground hover:bg-muted"
          aria-label={t("preferences.open")}
        >
          <Languages className="h-4 w-4" />
        </button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t("preferences.title")}</DialogTitle>
          <DialogDescription>{t("preferences.description")}</DialogDescription>
        </DialogHeader>
        <PreferenceFields />
        <button
          type="button"
          onClick={restartOnboarding}
          className="w-fit rounded-md border border-input px-3 py-2 text-sm hover:bg-muted"
        >
          {t("preferences.restartOnboarding")}
        </button>
      </DialogContent>
    </Dialog>
  );
}
