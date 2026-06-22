import { Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { Beaker, Loader2, Radio, WifiOff } from "lucide-react";
import { useApiMode } from "@/lib/api/mode";
import { useApi } from "@/lib/api/hooks";
import { cn } from "@/lib/utils";

export type ApiStatus = "demo" | "checking" | "online" | "offline" | "error";

export function useApiStatus(): { status: ApiStatus; message: string; version?: string } {
  const { mode } = useApiMode();
  const api = useApi();
  const q = useQuery({
    queryKey: ["health-status", mode],
    queryFn: () => api.health(),
    retry: false,
    refetchInterval: mode === "real" ? 30_000 : false,
    enabled: mode === "real",
  });
  if (mode === "demo")
    return { status: "demo", message: "Modo Demo ativo — usando dados fictícios." };
  if (q.isLoading) return { status: "checking", message: "Verificando API local…" };
  if (q.isError) {
    const msg = (q.error as Error)?.message ?? "";
    const isCors = /CORS|Failed to fetch|NetworkError/i.test(msg);
    return {
      status: isCors ? "error" : "offline",
      message: isCors
        ? "Erro de CORS/API ao consultar a API local."
        : "A API local não foi detectada. Rode `python scripts/run_api.py` ou use o modo Demo.",
    };
  }
  return {
    status: "online",
    message: `API online · v${q.data?.version ?? "—"}`,
    version: q.data?.version,
  };
}

export function ApiModeBadge({ className }: { className?: string }) {
  const { status, message } = useApiStatus();
  const config = {
    demo: {
      icon: Beaker,
      label: "Modo Demo",
      cls: "border-warning/40 bg-warning/15 text-warning-foreground hover:bg-warning/25",
    },
    checking: {
      icon: Loader2,
      label: "Verificando…",
      cls: "border-border bg-muted text-muted-foreground",
    },
    online: {
      icon: Radio,
      label: "API Online",
      cls: "border-success/40 bg-success/15 text-success-foreground hover:bg-success/25",
    },
    offline: {
      icon: WifiOff,
      label: "API Offline",
      cls: "border-destructive/40 bg-destructive/10 text-destructive hover:bg-destructive/20",
    },
    error: {
      icon: WifiOff,
      label: "Erro API",
      cls: "border-destructive/40 bg-destructive/10 text-destructive hover:bg-destructive/20",
    },
  }[status];
  const Icon = config.icon;
  return (
    <Link
      to="/settings"
      title={message}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium transition-colors",
        config.cls,
        className,
      )}
    >
      <Icon className={cn("h-3 w-3", status === "checking" && "animate-spin")} />
      {config.label}
    </Link>
  );
}
