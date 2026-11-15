import { useQuery } from "@tanstack/react-query";
import { useNavigate, useRouterState } from "@tanstack/react-router";
import { Command as CommandPrimitive } from "cmdk";
import { CircleDashed, CornerDownLeft, FileSearch, History, Loader2, Search } from "lucide-react";
import { useDeferredValue, useEffect, useMemo, useState } from "react";

import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import { useApiMode } from "@/lib/api/mode";
import { NAV_ENTRIES } from "@/lib/navigation";
import { usePreferences } from "@/lib/preferences";
import { highlight, search } from "@/lib/search";
import { cn } from "@/lib/utils";
import { v2Api } from "./api";

/**
 * One search for the whole app: every screen of the navigation registry (accent-insensitive,
 * ranked), screens visited recently, and the person's local data (evidence and portfolio, through
 * GET /search). Choosing a result only navigates; nothing here writes, sends or approves.
 */

const OPEN_EVENT = "sotuhire:open-search";
const RECENT_KEY = "sotuhire.recent-screens.v1";
const RECENT_LIMIT = 5;

export function openSearch() {
  window.dispatchEvent(new Event(OPEN_EVENT));
}

function readRecent(): string[] {
  try {
    const value = JSON.parse(localStorage.getItem(RECENT_KEY) ?? "[]");
    return Array.isArray(value) ? value.filter((item) => typeof item === "string") : [];
  } catch {
    return [];
  }
}

function rememberScreen(path: string) {
  try {
    const next = [path, ...readRecent().filter((item) => item !== path)].slice(0, RECENT_LIMIT);
    localStorage.setItem(RECENT_KEY, JSON.stringify(next));
  } catch {
    // storage unavailable: recents are a convenience only
  }
}

function Highlighted({ text, query }: { text: string; query: string }) {
  return (
    <>
      {highlight(text, query).map((part, index) =>
        part.match ? (
          <mark key={index} className="rounded-[2px] bg-highlight px-0.5 text-highlight-foreground">
            {part.text}
          </mark>
        ) : (
          <span key={index}>{part.text}</span>
        ),
      )}
    </>
  );
}

const itemClass =
  "flex cursor-pointer items-center gap-3 rounded-md px-3 py-2.5 text-sm outline-none data-[selected=true]:bg-secondary data-[selected=true]:text-foreground";

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const deferred = useDeferredValue(query);
  const navigate = useNavigate();
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const { mode, baseUrl } = useApiMode();
  const { t } = usePreferences();

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpen((value) => !value);
      }
    };
    const onOpen = () => setOpen(true);
    document.addEventListener("keydown", onKey);
    window.addEventListener(OPEN_EVENT, onOpen);
    return () => {
      document.removeEventListener("keydown", onKey);
      window.removeEventListener(OPEN_EVENT, onOpen);
    };
  }, []);

  useEffect(() => {
    if (NAV_ENTRIES.some((entry) => entry.path === pathname)) rememberScreen(pathname);
  }, [pathname]);

  const screens = useMemo(
    () =>
      NAV_ENTRIES.map((entry) => ({
        ...entry,
        text: t(entry.label),
        group: t(entry.journey.label),
      })),
    [t],
  );
  const trimmed = deferred.trim();
  const screenResults = useMemo(
    () =>
      trimmed
        ? search(trimmed, screens, (screen) => ({
            label: screen.text,
            detail: screen.group,
            keywords: screen.keywords,
          })).slice(0, 8)
        : [],
    [screens, trimmed],
  );
  const recent = useMemo(
    () =>
      open && !trimmed
        ? readRecent()
            .map((path) => screens.find((screen) => screen.path === path))
            .filter((screen): screen is (typeof screens)[number] => Boolean(screen))
        : [],
    [open, screens, trimmed],
  );

  // Each query has its own key, so an answer for an older query is never shown for a newer one;
  // the AbortSignal cancels the superseded request.
  const data = useQuery({
    queryKey: ["v2", "search", mode, baseUrl, trimmed],
    queryFn: ({ signal }) => v2Api(mode, baseUrl).search(trimmed, signal),
    enabled: open && trimmed.length >= 2,
    staleTime: 30_000,
  });
  const dataResults = (data.data ?? []).slice(0, 8);

  const go = (path: string) => {
    setOpen(false);
    setQuery("");
    void navigate({ to: path });
  };

  // Typing moves the highlight to the best result, so Enter opens what the list shows first
  // (cmdk keeps the previous selection when filtering is done outside it).
  const firstValue = trimmed
    ? screenResults[0]
      ? `screen ${screenResults[0].path}`
      : dataResults[0]
        ? `data ${dataResults[0].entity_type} ${dataResults[0].entity_id}`
        : ""
    : recent[0]
      ? `recent ${recent[0].path}`
      : "";
  const [selected, setSelected] = useState("");
  useEffect(() => {
    setSelected(firstValue);
  }, [firstValue]);

  const nothing =
    trimmed.length > 0 && !screenResults.length && !dataResults.length && !data.isFetching;

  return (
    <Dialog
      open={open}
      onOpenChange={(value) => {
        setOpen(value);
        if (!value) setQuery("");
      }}
    >
      <DialogContent className="top-[12vh] max-w-xl translate-y-0 gap-0 overflow-hidden p-0 sm:top-[14vh]">
        <DialogTitle className="sr-only">{t("search.open")}</DialogTitle>
        <DialogDescription className="sr-only">{t("search.hint")}</DialogDescription>
        <CommandPrimitive
          shouldFilter={false}
          loop
          value={selected}
          onValueChange={setSelected}
          className="flex flex-col"
        >
          <div className="flex items-center gap-2 border-b border-border px-4">
            <Search aria-hidden className="h-4 w-4 shrink-0 text-muted-foreground" />
            <CommandPrimitive.Input
              value={query}
              onValueChange={setQuery}
              placeholder={t("search.placeholder")}
              className="h-13 w-full bg-transparent text-[15px] outline-none placeholder:text-muted-foreground"
            />
            {data.isFetching ? (
              <Loader2
                aria-hidden
                className="h-4 w-4 shrink-0 animate-spin text-muted-foreground"
              />
            ) : null}
          </div>
          <CommandPrimitive.List className="max-h-[min(60vh,28rem)] overflow-y-auto p-2">
            {!trimmed && recent.length ? (
              <CommandPrimitive.Group
                heading={t("search.groupRecent")}
                className="[&_[cmdk-group-heading]]:eyebrow [&_[cmdk-group-heading]]:px-3 [&_[cmdk-group-heading]]:py-2 [&_[cmdk-group-heading]]:text-muted-foreground"
              >
                {recent.map((screen) => (
                  <CommandPrimitive.Item
                    key={screen.path}
                    value={`recent ${screen.path}`}
                    onSelect={() => go(screen.path)}
                    className={itemClass}
                  >
                    <History aria-hidden className="h-4 w-4 shrink-0 text-muted-foreground" />
                    <span className="flex-1 truncate">{screen.text}</span>
                    <span className="text-xs text-muted-foreground">{screen.group}</span>
                  </CommandPrimitive.Item>
                ))}
              </CommandPrimitive.Group>
            ) : null}
            {!trimmed ? (
              <CommandPrimitive.Group
                heading={t("search.groupScreens")}
                className="[&_[cmdk-group-heading]]:eyebrow [&_[cmdk-group-heading]]:px-3 [&_[cmdk-group-heading]]:py-2 [&_[cmdk-group-heading]]:text-muted-foreground"
              >
                {screens
                  .filter((screen) => screen.journey.id !== "system")
                  .map((screen) => {
                    const Icon = screen.icon;
                    return (
                      <CommandPrimitive.Item
                        key={screen.path}
                        value={`screen ${screen.path}`}
                        onSelect={() => go(screen.path)}
                        className={itemClass}
                      >
                        <Icon aria-hidden className="h-4 w-4 shrink-0 text-muted-foreground" />
                        <span className="flex-1 truncate">{screen.text}</span>
                        <span className="text-xs text-muted-foreground">{screen.group}</span>
                      </CommandPrimitive.Item>
                    );
                  })}
              </CommandPrimitive.Group>
            ) : null}
            {screenResults.length ? (
              <CommandPrimitive.Group
                heading={t("search.groupScreens")}
                className="[&_[cmdk-group-heading]]:eyebrow [&_[cmdk-group-heading]]:px-3 [&_[cmdk-group-heading]]:py-2 [&_[cmdk-group-heading]]:text-muted-foreground"
              >
                {screenResults.map((screen) => {
                  const Icon = screen.icon;
                  return (
                    <CommandPrimitive.Item
                      key={screen.path}
                      value={`screen ${screen.path}`}
                      onSelect={() => go(screen.path)}
                      className={itemClass}
                    >
                      <Icon aria-hidden className="h-4 w-4 shrink-0 text-muted-foreground" />
                      <span className="flex-1 truncate">
                        <Highlighted text={screen.text} query={trimmed} />
                      </span>
                      <span className="text-xs text-muted-foreground">{screen.group}</span>
                    </CommandPrimitive.Item>
                  );
                })}
              </CommandPrimitive.Group>
            ) : null}
            {trimmed.length >= 2 && dataResults.length ? (
              <CommandPrimitive.Group
                heading={t("search.groupData")}
                className="[&_[cmdk-group-heading]]:eyebrow [&_[cmdk-group-heading]]:px-3 [&_[cmdk-group-heading]]:py-2 [&_[cmdk-group-heading]]:text-muted-foreground"
              >
                {dataResults.map((item) => (
                  <CommandPrimitive.Item
                    key={`${item.entity_type}-${item.entity_id}`}
                    value={`data ${item.entity_type} ${item.entity_id}`}
                    onSelect={() => go(item.route)}
                    className={itemClass}
                  >
                    <FileSearch aria-hidden className="h-4 w-4 shrink-0 text-muted-foreground" />
                    <span className="flex-1 truncate">
                      <Highlighted text={item.title} query={trimmed} />
                    </span>
                    <span className="font-mono text-[11px] text-muted-foreground">
                      {item.entity_type}
                    </span>
                  </CommandPrimitive.Item>
                ))}
              </CommandPrimitive.Group>
            ) : null}
            {nothing ? (
              <div className="px-3 py-8 text-center">
                <CircleDashed aria-hidden className="mx-auto h-5 w-5 text-muted-foreground" />
                <p className="mt-2 text-sm">{t("search.empty", { query: trimmed })}</p>
                <p className="mt-1 text-xs text-muted-foreground">{t("search.emptyHint")}</p>
              </div>
            ) : null}
          </CommandPrimitive.List>
          <div className="flex flex-wrap items-center justify-between gap-2 border-t border-border bg-muted/50 px-4 py-2 text-[11px] text-muted-foreground">
            <span aria-live="polite">
              {data.isError
                ? t("search.dataError")
                : trimmed.length === 1
                  ? t("search.minChars")
                  : mode === "demo" && trimmed.length >= 2
                    ? t("search.dataDemo")
                    : ""}
            </span>
            <span className={cn("hidden items-center gap-1 sm:flex")}>
              <CornerDownLeft aria-hidden className="h-3 w-3" />
              {t("search.hint")}
            </span>
          </div>
        </CommandPrimitive>
      </DialogContent>
    </Dialog>
  );
}
