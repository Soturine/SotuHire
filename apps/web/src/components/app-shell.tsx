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
  ChevronRight,
  Menu,
  X,
} from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";
import { cn } from "@/lib/utils";
import { APP_VERSION, API_LOCAL_HOST } from "@/lib/labels";
import { ApiModeBadge } from "./api-mode-badge";

const nav = [
  {
    group: "Visão geral",
    items: [{ to: "/dashboard", label: "Dashboard", icon: LayoutDashboard }],
  },
  {
    group: "Análise",
    items: [
      { to: "/resume", label: "Currículo", icon: FileText },
      { to: "/job", label: "Vaga", icon: Briefcase },
      { to: "/match", label: "Compatibilidade", icon: Target },
      { to: "/ats", label: "Análise ATS", icon: ScanSearch },
      { to: "/tailor", label: "Ajuste de Currículo", icon: Wand2 },
      { to: "/github", label: "GitHub", icon: Github },
    ],
  },
  {
    group: "Pipeline",
    items: [
      { to: "/radar", label: "Radar", icon: RadioTower },
      { to: "/sources", label: "Fontes e Captura", icon: Inbox },
      { to: "/tracker", label: "Candidaturas", icon: Kanban },
      { to: "/intelligence", label: "Inteligência", icon: LineChart },
    ],
  },
  {
    group: "Conta",
    items: [
      { to: "/settings", label: "Configurações", icon: Settings },
      { to: "/privacy", label: "Privacidade", icon: ShieldCheck },
    ],
  },
];

function SidebarBody({ pathname, onNavigate }: { pathname: string; onNavigate?: () => void }) {
  return (
    <>
      <div className="flex items-center gap-2 px-5 py-5">
        <div className="grid h-9 w-9 place-items-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
          <Sparkles className="h-4 w-4" />
        </div>
        <div className="flex flex-col leading-tight">
          <span className="text-display text-lg">SotuHire</span>
          <span className="text-[11px] text-sidebar-foreground/60">
            Inteligência de carreira · local-first
          </span>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 pb-6">
        {nav.map((g) => (
          <div key={g.group} className="mb-5">
            <div className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-sidebar-foreground/40">
              {g.group}
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
                      <span className="flex-1 truncate">{item.label}</span>
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
          API local {API_LOCAL_HOST}
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

  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  return (
    <div className="flex min-h-screen w-full bg-background">
      {/* Desktop sidebar */}
      <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground lg:flex">
        <SidebarBody pathname={pathname} />
      </aside>

      {/* Mobile drawer */}
      {mobileOpen && (
        <>
          <div
            className="fixed inset-0 z-40 bg-black/50 lg:hidden"
            onClick={() => setMobileOpen(false)}
            aria-hidden
          />
          <aside className="fixed inset-y-0 left-0 z-50 flex w-72 max-w-[85vw] flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground shadow-xl lg:hidden">
            <button
              onClick={() => setMobileOpen(false)}
              className="absolute right-3 top-3 grid h-8 w-8 place-items-center rounded-md text-sidebar-foreground/70 hover:bg-sidebar-accent/60"
              aria-label="Fechar menu"
            >
              <X className="h-4 w-4" />
            </button>
            <SidebarBody pathname={pathname} onNavigate={() => setMobileOpen(false)} />
          </aside>
        </>
      )}

      <main className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex items-center gap-3 border-b border-border bg-background/85 px-4 py-3 backdrop-blur md:px-8 md:py-4">
          <button
            onClick={() => setMobileOpen(true)}
            className="grid h-9 w-9 shrink-0 place-items-center rounded-md border border-border bg-card text-muted-foreground hover:bg-muted lg:hidden"
            aria-label="Abrir menu"
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
