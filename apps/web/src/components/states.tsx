import { CircleDashed, RotateCcw, Unplug } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

/**
 * Shared screen states. Loading shows the shape of what is coming instead of a lone spinner;
 * errors say what failed in words, keep the technical message available, and offer a retry the
 * person triggers; empty states say what would fill the screen and how.
 */

export function LoadingState({
  className,
  label = "Carregando…",
}: {
  className?: string;
  label?: string;
}) {
  return (
    <div role="status" className={cn("space-y-4 py-6", className)}>
      <p className="eyebrow text-muted-foreground">{label}</p>
      <div aria-hidden className="space-y-3">
        <Skeleton className="h-9 w-2/3" />
        <Skeleton className="h-4 w-1/2" />
        <div className="grid gap-3 pt-2 sm:grid-cols-3">
          <Skeleton className="h-20" />
          <Skeleton className="h-20" />
          <Skeleton className="h-20" />
        </div>
      </div>
    </div>
  );
}

const NETWORK = /Failed to fetch|NetworkError|Load failed|ECONNREFUSED/i;

export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const message = error instanceof Error ? error.message : String(error ?? "Erro desconhecido.");
  const network = NETWORK.test(message);
  return (
    <div
      role="alert"
      className="flex flex-col gap-4 rounded-lg border border-destructive/30 border-l-4 border-l-destructive bg-card px-6 py-6 sm:flex-row sm:items-start"
    >
      <Unplug aria-hidden className="h-5 w-5 shrink-0 text-destructive-strong" />
      <div className="min-w-0 flex-1 space-y-1">
        <p className="font-medium">
          {network ? "A API local não respondeu." : "Não foi possível carregar."}
        </p>
        <p className="text-sm text-muted-foreground">
          {network
            ? "Nenhum dado foi mostrado no lugar: o que aparece aqui vem só dos seus dados locais."
            : message}
        </p>
        {network ? <p className="font-mono text-xs text-muted-foreground">{message}</p> : null}
      </div>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="inline-flex items-center gap-1.5 self-start rounded-md border border-input bg-background px-3 py-1.5 text-sm font-medium transition-colors hover:bg-secondary"
        >
          <RotateCcw aria-hidden className="h-3.5 w-3.5" />
          Tentar novamente
        </button>
      )}
    </div>
  );
}

export function EmptyState({
  title,
  description,
  icon,
  action,
}: {
  title: string;
  description?: string;
  icon?: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-start gap-3 rounded-lg border border-dashed border-input bg-card/60 px-6 py-8">
      <div className="grid h-9 w-9 place-items-center rounded-md bg-highlight text-highlight-foreground">
        {icon ?? <CircleDashed aria-hidden className="h-5 w-5" />}
      </div>
      <div className="space-y-1">
        <p className="text-display text-lg">{title}</p>
        {description && <p className="max-w-prose text-sm text-muted-foreground">{description}</p>}
      </div>
      {action}
    </div>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("animate-pulse rounded-md bg-muted", className)} />;
}
