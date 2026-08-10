import { createFileRoute } from "@tanstack/react-router";
import { Search } from "lucide-react";
import { useMemo, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { SectionCard } from "@/components/section-card";
import { usePreferences } from "@/lib/preferences";
import { ROUTES } from "@/lib/route-metadata";

export const Route = createFileRoute("/help")({
  head: () => ({ meta: [{ title: "Ajuda — SotuHire" }] }),
  component: HelpPage,
});

function HelpPage() {
  const { t, locale } = usePreferences();
  const [query, setQuery] = useState("");
  const topics = useMemo(() => {
    const needle = query.trim().toLocaleLowerCase(locale);
    if (!needle) return ROUTES.filter((route) => route.path !== "/help");
    return ROUTES.filter((route) =>
      `${t(route.label)} ${t(route.title)} ${t(route.description)}`
        .toLocaleLowerCase(locale)
        .includes(needle),
    );
  }, [locale, query, t]);

  return (
    <AppShell title={t("route.help.title")} description={t("route.help.description")}>
      <div className="mx-auto grid max-w-5xl gap-5">
        <label className="relative block">
          <span className="sr-only">{t("help.center.search")}</span>
          <Search className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder={t("help.center.searchPlaceholder")}
            className="w-full rounded-lg border border-input bg-card py-2.5 pl-10 pr-3 text-sm outline-none focus:ring-2 focus:ring-ring"
          />
        </label>

        {topics.length ? (
          <div className="grid gap-4 md:grid-cols-2">
            {topics.map((route) => (
              <SectionCard key={route.path} title={t(route.title)}>
                <p className="text-sm leading-6 text-muted-foreground">{t(route.description)}</p>
                <a
                  href={route.path}
                  className="mt-4 inline-flex text-sm font-medium text-accent underline-offset-4 hover:underline"
                >
                  {t("help.center.openTopic")}
                </a>
              </SectionCard>
            ))}
          </div>
        ) : (
          <p className="rounded-lg border border-dashed border-border p-8 text-center text-sm text-muted-foreground">
            {t("help.center.noResults")}
          </p>
        )}
      </div>
    </AppShell>
  );
}
