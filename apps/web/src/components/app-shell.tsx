import { Link, useRouterState } from "@tanstack/react-router";
import {
  LayoutDashboard,
  FileText,
  Briefcase,
  Target,
  ScanSearch,
  Wand2,
  Github,
  Kanban,
  LineChart,
  Settings,
  ShieldCheck,
  Inbox,
  Sparkles,
  Activity,
  RadioTower,
  ScrollText,
  UserRound,
  BrainCircuit,
  FlaskConical,
  Files,
  CalendarCheck,
  ListTodo,
  ChevronRight,
  Menu,
} from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";
import { ContextHelp } from "./context-help";
import { PreferencesDialog } from "./preferences-dialog";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "./ui/sheet";
import type { TranslationKey } from "@/lib/i18n";
import { usePreferences } from "@/lib/preferences";
import { cn } from "@/lib/utils";
import { APP_VERSION, API_LOCAL_HOST } from "@/lib/labels";
import { ApiModeBadge } from "./api-mode-badge";

const nav = [
  {
    group: "nav.group.overview" as TranslationKey,
    items: [
      {
        to: "/dashboard" as const,
        label: "route.dashboard.label" as TranslationKey,
        icon: LayoutDashboard,
      },
    ],
  },
  {
    group: "nav.group.profile" as TranslationKey,
    items: [
      { to: "/profile" as const, label: "route.profile.label" as TranslationKey, icon: UserRound },
      { to: "/resume" as const, label: "route.resume.label" as TranslationKey, icon: FileText },
      {
        to: "/resume-studio" as const,
        label: "route.resumeStudio.label" as TranslationKey,
        icon: Files,
      },
    ],
  },
  {
    group: "nav.group.opportunities" as TranslationKey,
    items: [
      { to: "/radar" as const, label: "route.radar.label" as TranslationKey, icon: RadioTower },
      { to: "/job" as const, label: "route.job.label" as TranslationKey, icon: Briefcase },
      {
        to: "/public-exams" as const,
        label: "route.publicExams.label" as TranslationKey,
        icon: ScrollText,
      },
      { to: "/sources" as const, label: "route.sources.label" as TranslationKey, icon: Inbox },
    ],
  },
  {
    group: "nav.group.applications" as TranslationKey,
    items: [
      {
        to: "/application-lab" as const,
        label: "route.applicationLab.label" as TranslationKey,
        icon: FlaskConical,
      },
      { to: "/tracker" as const, label: "route.tracker.label" as TranslationKey, icon: Kanban },
      {
        to: "/interviews" as const,
        label: "route.interviews.label" as TranslationKey,
        icon: CalendarCheck,
      },
      { to: "/career" as const, label: "route.career.label" as TranslationKey, icon: ListTodo },
      {
        to: "/intelligence" as const,
        label: "route.intelligence.label" as TranslationKey,
        icon: LineChart,
      },
      { to: "/match" as const, label: "route.match.label" as TranslationKey, icon: Target },
      { to: "/ats" as const, label: "route.ats.label" as TranslationKey, icon: ScanSearch },
      { to: "/tailor" as const, label: "route.tailor.label" as TranslationKey, icon: Wand2 },
    ],
  },
  {
    group: "nav.group.integrations" as TranslationKey,
    items: [
      { to: "/github" as const, label: "route.github.label" as TranslationKey, icon: Github },
      {
        to: "/ai-quality" as const,
        label: "route.aiQuality.label" as TranslationKey,
        icon: BrainCircuit,
      },
    ],
  },
  {
    group: "nav.group.settings" as TranslationKey,
    items: [
      { to: "/settings" as const, label: "route.settings.label" as TranslationKey, icon: Settings },
      {
        to: "/privacy" as const,
        label: "route.privacy.label" as TranslationKey,
        icon: ShieldCheck,
      },
    ],
  },
];

function SidebarBody({ pathname, onNavigate }: { pathname: string; onNavigate?: () => void }) {
  const { t } = usePreferences();
  return (
    <>
      <div className="flex items-center gap-2 px-5 py-5">
        <div className="grid h-9 w-9 place-items-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
          <Sparkles className="h-4 w-4" />
        </div>
        <div className="flex flex-col leading-tight">
          <span className="text-display text-lg">SotuHire</span>
          <span className="text-[11px] text-sidebar-foreground/60">{t("shell.tagline")}</span>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 pb-6" aria-label={t("shell.navigation")}>
        {nav.map((g) => (
          <div key={g.group} className="mb-5">
            <div className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-sidebar-foreground/40">
              {t(g.group)}
            </div>
            <ul className="space-y-0.5">
              {g.items.map((item) => {
                const active = pathname === item.to;
                const Icon = item.icon;
                return (
                  <li key={item.to}>
                    <Link
                      to={item.to}
                      onClick={onNavigate}
                      className={cn(
                        "group flex items-center gap-2.5 rounded-md px-3 py-2 text-sm transition-colors",
                        active
                          ? "bg-sidebar-accent text-sidebar-accent-foreground"
                          : "text-sidebar-foreground/75 hover:bg-sidebar-accent/60 hover:text-sidebar-foreground",
                      )}
                    >
                      <Icon
                        className={cn(
                          "h-4 w-4 shrink-0",
                          active ? "text-sidebar-primary" : "text-sidebar-foreground/50",
                        )}
                      />
                      <span className="flex-1 truncate">{t(item.label)}</span>
                      {active && (
                        <ChevronRight className="h-3.5 w-3.5 shrink-0 text-sidebar-primary" />
                      )}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      <div className="flex items-start gap-1.5 border-t border-sidebar-border px-4 py-3 text-[10px] leading-tight text-sidebar-foreground/55">
        <Activity className="h-3 w-3 shrink-0 text-accent" />
        <span>
          SotuHire · v{APP_VERSION}
          <br />
          {t("shell.localApi", { host: API_LOCAL_HOST })}
        </span>
      </div>
    </>
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
  const [mobileOpen, setMobileOpen] = useState(false);
  const { t } = usePreferences();

  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  return (
    <div className="flex min-h-screen w-full bg-background">
      {/* Desktop sidebar */}
      <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground lg:flex">
        <SidebarBody pathname={pathname} />
      </aside>

      <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
        <SheetContent
          side="left"
          className="flex w-72 max-w-[85vw] flex-col border-sidebar-border bg-sidebar p-0 text-sidebar-foreground lg:hidden"
        >
          <SheetHeader className="sr-only">
            <SheetTitle>{t("shell.navigation")}</SheetTitle>
            <SheetDescription>{t("shell.tagline")}</SheetDescription>
          </SheetHeader>
          <div className="flex min-h-0 flex-1 flex-col">
            <SidebarBody pathname={pathname} onNavigate={() => setMobileOpen(false)} />
          </div>
        </SheetContent>
      </Sheet>

      <main className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex items-center gap-3 border-b border-border bg-background/85 px-4 py-3 backdrop-blur md:px-8 md:py-4">
          <button
            onClick={() => setMobileOpen(true)}
            className="grid h-9 w-9 shrink-0 place-items-center rounded-md border border-border bg-card text-muted-foreground hover:bg-muted lg:hidden"
            aria-label={t("shell.openMenu")}
          >
            <Menu className="h-4 w-4" />
          </button>
          <div className="min-w-0 flex-1">
            {title && <h1 className="text-display truncate text-xl md:text-[26px]">{title}</h1>}
            {description && (
              <p className="mt-0.5 line-clamp-1 text-xs text-muted-foreground md:text-sm">
                {description}
              </p>
            )}
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <div className="hidden sm:flex sm:items-center sm:gap-2">{actions}</div>
            <ContextHelp pathname={pathname} />
            <PreferencesDialog />
            <ApiModeBadge />
          </div>
        </header>

        {actions && (
          <div className="flex flex-wrap items-center gap-2 border-b border-border bg-background px-4 py-2 sm:hidden">
            {actions}
          </div>
        )}

        <div className="flex-1 px-4 py-6 md:px-8 md:py-8">{children}</div>
      </main>
    </div>
  );
}
