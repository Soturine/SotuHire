import { Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { FlaskConical, Loader2, PlugZap, Unplug } from "lucide-react";
import { useApiMode } from "@/lib/api/mode";
import { useApi } from "@/lib/api/hooks";
import { usePreferences } from "@/lib/preferences";
import { cn } from "@/lib/utils";

export type ApiStatus = "demo" | "checking" | "online" | "offline" | "error";

export function useApiStatus(): { status: ApiStatus; message: string; version?: string } {
  const { mode } = useApiMode();
  const { t } = usePreferences();
  const api = useApi();
  const q = useQuery({
    queryKey: ["health-status", mode],
    queryFn: () => api.health(),
    retry: false,
    refetchInterval: mode === "real" ? 30_000 : false,
    enabled: mode === "real",
  });
  if (mode === "demo") return { status: "demo", message: t("shell.status.demoHint") };
  if (q.isLoading) return { status: "checking", message: t("shell.status.checking") };
  if (q.isError) {
    const msg = (q.error as Error)?.message ?? "";
    const isCors = /CORS|Failed to fetch|NetworkError/i.test(msg);
    return { status: isCors ? "error" : "offline", message: t("shell.status.offlineHint") };
  }
  return {
    status: "online",
    message: `${t("shell.status.real")} · v${q.data?.version ?? "—"}`,
    version: q.data?.version,
  };
}

const STATUS_STYLE: Record<ApiStatus, { icon: typeof PlugZap; cls: string; label: string }> = {
  demo: {
    icon: FlaskConical,
    cls: "border-highlight bg-highlight text-highlight-foreground",
    label: "shell.status.demo",
  },
  checking: {
    icon: Loader2,
    cls: "border-border bg-muted text-muted-foreground",
    label: "shell.status.checking",
  },
  online: {
    icon: PlugZap,
    cls: "border-success/40 bg-success/10 text-success-strong",
    label: "shell.status.real",
  },
  offline: {
    icon: Unplug,
    cls: "border-destructive/40 bg-destructive/10 text-destructive-strong",
    label: "shell.status.offline",
  },
  error: {
    icon: Unplug,
    cls: "border-destructive/40 bg-destructive/10 text-destructive-strong",
    label: "shell.status.offline",
  },
};

/** The data source as a fact the person can act on: sample data, connected, or down. */
export function ApiModeBadge({ className, compact }: { className?: string; compact?: boolean }) {
  const { status, message } = useApiStatus();
  const { t } = usePreferences();
  const config = STATUS_STYLE[status];
  const Icon = config.icon;
  const label = t(config.label as Parameters<typeof t>[0]);
  return (
    <Link
      to="/settings"
      title={message}
      aria-label={compact ? `${label}. ${message}` : undefined}
      className={cn(
        "inline-flex min-h-8 items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium transition-colors duration-(--duration-1) hover:brightness-95",
        config.cls,
        className,
      )}
    >
      <Icon aria-hidden className={cn("h-3.5 w-3.5", status === "checking" && "animate-spin")} />
      <span className={cn(compact && "sr-only sm:not-sr-only")}>{label}</span>
    </Link>
  );
}
