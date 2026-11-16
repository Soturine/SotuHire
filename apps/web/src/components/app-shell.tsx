import { Link, useRouterState } from "@tanstack/react-router";
import { ChevronDown, Menu, Search, Unplug } from "lucide-react";
import { useEffect, useId, useState, type ReactNode } from "react";

import { CommandPalette, openSearch } from "@/features/career-copilot/command-palette";
import { CopilotDrawer } from "@/features/career-copilot/copilot-drawer";
import { APP_VERSION, API_LOCAL_HOST } from "@/lib/labels";
import { useApiMode } from "@/lib/api/mode";
import { JOURNEYS, MOBILE_TABS, entryFor, journeyFor, type Journey } from "@/lib/navigation";
import { usePreferences } from "@/lib/preferences";
import { cn } from "@/lib/utils";
import { ApiModeBadge, useApiStatus } from "./api-mode-badge";
import { BrandMark, BrandWordmark } from "./brand";
import { ContextHelp } from "./context-help";
import { PreferencesDialog } from "./preferences-dialog";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "./ui/sheet";

const PRIMARY_JOURNEYS = JOURNEYS.filter((journey) => journey.id !== "system");
const SYSTEM = JOURNEYS.find((journey) => journey.id === "system")!;

function SearchTrigger({ className }: { className?: string }) {
  const { t } = usePreferences();
  return (
    <button
      type="button"
      onClick={openSearch}
      aria-keyshortcuts="Control+K"
      className={cn(
        "flex w-full items-center gap-2 rounded-lg border border-sidebar-border bg-sidebar-accent/50 px-3 py-2 text-left text-sm text-sidebar-muted transition-colors duration-(--duration-1) hover:border-sidebar-primary/50 hover:bg-sidebar-accent hover:text-sidebar-foreground",
        className,
      )}
    >
      <Search aria-hidden className="h-4 w-4 shrink-0" />
      <span className="flex-1">{t("search.open")}</span>
      <kbd
        className="rounded border border-sidebar-border px-1.5 py-0.5 font-mono text-[10px] tracking-wide"
        aria-hidden
      >
        Ctrl K
      </kbd>
    </button>
  );
}

function JourneySection({
  journey,
  pathname,
  open,
  onToggle,
  onNavigate,
}: {
  journey: Journey;
  pathname: string;
  open: boolean;
  onToggle: () => void;
  onNavigate?: () => void;
}) {
  const { t } = usePreferences();
  const listId = useId();
  const current = journey.entries.some((entry) => entry.path === pathname);
  const Icon = journey.icon;
  return (
    <li>
      <button
        type="button"
        aria-expanded={open}
        aria-controls={listId}
        onClick={onToggle}
        className={cn(
          "group flex w-full items-start gap-2.5 rounded-lg px-2.5 py-2 text-left transition-colors duration-(--duration-1)",
          current
            ? "bg-sidebar-accent/60 text-sidebar-accent-foreground"
            : "text-sidebar-foreground/90 hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground",
        )}
      >
        <Icon
          aria-hidden
          className={cn(
            "mt-0.5 h-4 w-4 shrink-0",
            current
              ? "text-sidebar-primary"
              : "text-sidebar-muted group-hover:text-sidebar-foreground",
          )}
        />
        <span className="min-w-0 flex-1">
          <span className="block text-sm font-semibold">{t(journey.label)}</span>
          {open ? (
            <span className="mt-0.5 block text-xs leading-snug text-sidebar-muted">
              {t(journey.purpose)}
            </span>
          ) : null}
        </span>
        <ChevronDown
          aria-hidden
          className={cn(
            "mt-0.5 h-4 w-4 shrink-0 text-sidebar-muted transition-transform duration-(--duration-2) ease-(--ease-out)",
            open && "rotate-180",
          )}
        />
      </button>
      <div
        className={cn(
          "grid transition-[grid-template-rows] duration-(--duration-2) ease-(--ease-out)",
          open ? "grid-rows-[1fr]" : "grid-rows-[0fr]",
        )}
      >
        <ul id={listId} className="overflow-hidden" hidden={!open}>
          {journey.entries.map((entry) => {
            const active = pathname === entry.path;
            return (
              <li key={entry.path}>
                <Link
                  to={entry.path}
                  onClick={onNavigate}
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    "relative ml-[17px] flex items-center gap-2 border-l py-1.5 pl-4 pr-2 text-sm transition-colors duration-(--duration-1)",
                    active
                      ? "border-sidebar-primary font-medium text-sidebar-accent-foreground"
                      : "border-sidebar-border text-sidebar-muted hover:border-sidebar-muted hover:text-sidebar-foreground",
                  )}
                >
                  {active ? (
                    <span
                      aria-hidden
                      className="absolute -left-[4px] h-[7px] w-[7px] rounded-full bg-sidebar-primary shadow-[0_0_0_3px_var(--sidebar)]"
                    />
                  ) : null}
                  <span className="truncate">{t(entry.label)}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </div>
    </li>
  );
}

function ConnectionNote() {
  const { status, message } = useApiStatus();
  const { t } = usePreferences();
  return (
    <div className="border-t border-sidebar-border px-4 py-3">
      <ApiModeBadge />
      <p className="mt-2 text-[11px] leading-snug text-sidebar-muted">
        {status === "online" ? t("shell.localApi", { host: API_LOCAL_HOST }) : message}
      </p>
      <p className="mt-1 font-mono text-[10px] text-sidebar-muted">v{APP_VERSION}</p>
    </div>
  );
}

function NavigationBody({ pathname, onNavigate }: { pathname: string; onNavigate?: () => void }) {
  const { t } = usePreferences();
  const currentJourney = journeyFor(pathname)?.id;
  // The journey of the current screen is open; the person can open or close any other.
  const [toggled, setToggled] = useState<Record<string, boolean>>({});
  const isOpen = (id: string) => toggled[id] ?? id === currentJourney;
  return (
    <>
      <div className="px-4 pb-3 pt-5">
        <Link to="/dashboard" onClick={onNavigate} className="rounded-md">
          <BrandWordmark tagline={t("shell.tagline")} />
        </Link>
        <SearchTrigger className="mt-4" />
      </div>
      <nav className="flex-1 overflow-y-auto px-2 pb-4" aria-label={t("shell.navigation")}>
        <ul className="space-y-0.5">
          {PRIMARY_JOURNEYS.map((journey) => (
            <JourneySection
              key={journey.id}
              journey={journey}
              pathname={pathname}
              open={isOpen(journey.id)}
              onToggle={() =>
                setToggled((state) => ({ ...state, [journey.id]: !isOpen(journey.id) }))
              }
              onNavigate={onNavigate}
            />
          ))}
        </ul>
        <p className="eyebrow mt-6 px-2.5 text-sidebar-muted">{t(SYSTEM.label)}</p>
        <ul className="mt-1.5 grid grid-cols-2 gap-1">
          {SYSTEM.entries.map((entry) => {
            const Icon = entry.icon;
            const active = pathname === entry.path;
            return (
              <li key={entry.path}>
                <Link
                  to={entry.path}
                  onClick={onNavigate}
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    "flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs transition-colors duration-(--duration-1)",
                    active
                      ? "bg-sidebar-accent font-medium text-sidebar-accent-foreground"
                      : "text-sidebar-muted hover:bg-sidebar-accent/60 hover:text-sidebar-foreground",
                  )}
                >
                  <Icon aria-hidden className="h-3.5 w-3.5 shrink-0" />
                  <span className="leading-tight">{t(entry.label)}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
      <ConnectionNote />
    </>
  );
}

function OfflineNotice() {
  const { status } = useApiStatus();
  const { setMode } = useApiMode();
  const { t } = usePreferences();
  if (status !== "offline" && status !== "error") return null;
  return (
    <div
      role="status"
      className="flex flex-wrap items-center gap-x-3 gap-y-2 border-b border-destructive/30 bg-destructive/8 px-4 py-2.5 text-sm md:px-8"
    >
      <Unplug aria-hidden className="h-4 w-4 shrink-0 text-destructive-strong" />
      <p className="min-w-0 flex-1">
        <strong className="font-semibold text-destructive-strong">
          {t("shell.status.offline")}.
        </strong>{" "}
        <span className="text-muted-foreground">{t("shell.status.offlineHint")}</span>
      </p>
      <span className="flex gap-2">
        <button
          type="button"
          onClick={() => setMode("demo")}
          className="rounded-md border border-border bg-card px-2.5 py-1 text-xs font-medium hover:bg-muted"
        >
          {t("shell.status.demo")}
        </button>
        <Link
          to="/settings"
          className="rounded-md bg-primary px-2.5 py-1 text-xs font-medium text-primary-foreground hover:opacity-90"
        >
          {t("shell.status.manage")}
        </Link>
      </span>
    </div>
  );
}

function MobileTabBar({ pathname, onMore }: { pathname: string; onMore: () => void }) {
  const { t } = usePreferences();
  const current = journeyFor(pathname)?.id;
  return (
    <nav
      aria-label={t("shell.journeys")}
      className="dark fixed inset-x-0 bottom-0 z-40 border-t border-sidebar-border bg-sidebar/95 pb-[env(safe-area-inset-bottom)] text-sidebar-foreground backdrop-blur lg:hidden"
    >
      <ul className="mx-auto grid max-w-xl grid-cols-6">
        {MOBILE_TABS.map((tab) => {
          const journey = JOURNEYS.find((item) => item.id === tab.journey)!;
          const Icon = journey.icon;
          const active = current === tab.journey;
          return (
            <li key={tab.journey}>
              <Link
                to={tab.path}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "flex min-h-14 flex-col items-center justify-center gap-0.5 px-1 text-[10.5px] leading-tight",
                  active ? "font-semibold text-sidebar-accent-foreground" : "text-sidebar-muted",
                )}
              >
                <span
                  className={cn(
                    "grid h-7 w-10 place-items-center rounded-full transition-colors duration-(--duration-1)",
                    active && "bg-sidebar-accent text-sidebar-primary",
                  )}
                >
                  <Icon aria-hidden className="h-4 w-4" />
                </span>
                <span className="max-w-full truncate">{t(journey.short)}</span>
              </Link>
            </li>
          );
        })}
        <li>
          <button
            type="button"
            onClick={onMore}
            className="flex min-h-14 w-full flex-col items-center justify-center gap-0.5 text-[10.5px] text-sidebar-muted"
          >
            <span className="grid h-7 w-10 place-items-center">
              <Menu aria-hidden className="h-4 w-4" />
            </span>
            {t("shell.more")}
          </button>
        </li>
      </ul>
    </nav>
  );
}

export function AppShell({
  children,
  title,
  description,
  actions,
}: {
  children: ReactNode;
  title?: string;
  description?: string;
  actions?: ReactNode;
}) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const [moreOpen, setMoreOpen] = useState(false);
  const { t } = usePreferences();
  const journey = journeyFor(pathname);
  const entry = entryFor(pathname);

  useEffect(() => {
    setMoreOpen(false);
  }, [pathname]);

  return (
    <div className="flex min-h-screen w-full bg-background">
      <a
        href="#content"
        className="sr-only z-50 rounded-md bg-primary px-3 py-2 text-sm text-primary-foreground focus:not-sr-only focus:fixed focus:left-3 focus:top-3"
      >
        {t("shell.skipToContent")}
      </a>
      <aside className="dark sticky top-0 hidden h-screen w-[17rem] shrink-0 flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground lg:flex">
        <NavigationBody pathname={pathname} />
      </aside>

      <Sheet open={moreOpen} onOpenChange={setMoreOpen}>
        <SheetContent
          side="left"
          className="dark flex w-80 max-w-[88vw] flex-col border-sidebar-border bg-sidebar p-0 text-sidebar-foreground lg:hidden"
        >
          <SheetHeader className="sr-only">
            <SheetTitle>{t("shell.navigation")}</SheetTitle>
            <SheetDescription>{t("shell.tagline")}</SheetDescription>
          </SheetHeader>
          <div className="flex min-h-0 flex-1 flex-col">
            <NavigationBody pathname={pathname} onNavigate={() => setMoreOpen(false)} />
          </div>
        </SheetContent>
      </Sheet>

      <div className="flex min-w-0 flex-1 flex-col pb-16 lg:pb-0">
        <header className="sticky top-0 z-30 border-b border-border bg-background/85 backdrop-blur-md">
          <div className="flex items-center gap-2 px-4 pt-3 md:px-8 lg:pt-4">
            <Link to="/dashboard" className="rounded-md lg:hidden" aria-label="SotuHire">
              <BrandMark className="h-7 w-7" />
            </Link>
            <p className="eyebrow min-w-0 flex-1 truncate text-muted-foreground">
              {journey ? (
                <>
                  <span>{t(journey.label)}</span>
                  {entry && title !== t(entry.label) ? (
                    <span aria-hidden> · {t(entry.label)}</span>
                  ) : null}
                </>
              ) : null}
            </p>
            <div className="flex shrink-0 items-center gap-1.5">
              <button
                type="button"
                onClick={openSearch}
                aria-label={t("search.open")}
                aria-keyshortcuts="Control+K"
                className="grid h-9 w-9 place-items-center rounded-md border border-border bg-card text-muted-foreground hover:text-foreground lg:hidden"
              >
                <Search aria-hidden className="h-4 w-4" />
              </button>
              <CopilotDrawer pathname={pathname} />
              <ContextHelp pathname={pathname} />
              <PreferencesDialog />
              <ApiModeBadge compact className="lg:hidden" />
            </div>
          </div>
          <div className="flex flex-wrap items-end gap-x-6 gap-y-2 px-4 pb-3 pt-1.5 md:px-8 lg:pb-5">
            <div className="min-w-0 flex-1">
              {title && (
                <h1 className="text-display text-[26px] leading-tight md:text-[30px]">{title}</h1>
              )}
              {description && (
                <p className="mt-1 max-w-3xl text-sm text-muted-foreground">{description}</p>
              )}
            </div>
            {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
          </div>
        </header>
        <OfflineNotice />

        <main id="content" tabIndex={-1} className="flex-1 px-4 py-6 outline-none md:px-8 md:py-8">
          <div key={pathname} className="animate-page-in">
            {children}
          </div>
        </main>
      </div>
      <MobileTabBar pathname={pathname} onMore={() => setMoreOpen(true)} />
      <CommandPalette />
    </div>
  );
}
