import { cn } from "@/lib/utils";

export function ScoreRing({
  value,
  label,
  size = 96,
  tone = "primary",
  sub,
  ariaLabel,
  suffix,
}: {
  value: number;
  label?: string;
  size?: number;
  /** "hero" draws on the navy hero plane (light track, mint stroke). */
  tone?: "primary" | "accent" | "warning" | "destructive" | "hero";
  sub?: string;
  /** When set, the ring is exposed as a progressbar with this name. */
  ariaLabel?: string;
  suffix?: string;
}) {
  const clamped = Math.max(0, Math.min(100, Math.round(value)));
  const ringWidth = Math.max(6, Math.round(size / 12));
  const r = (size - ringWidth - 2) / 2;
  const c = 2 * Math.PI * r;
  const offset = c * (1 - clamped / 100);

  const stroke = {
    primary: "stroke-[var(--color-chart-1)]",
    accent: "stroke-[var(--color-accent)]",
    warning: "stroke-[var(--color-warning)]",
    destructive: "stroke-[var(--color-destructive)]",
    hero: "stroke-[var(--color-hero-accent)]",
  }[tone];

  return (
    <div className="flex flex-col items-center gap-1.5">
      <div
        className="relative"
        style={{ width: size, height: size }}
        {...(ariaLabel
          ? {
              role: "progressbar",
              "aria-label": ariaLabel,
              "aria-valuenow": clamped,
              "aria-valuemin": 0,
              "aria-valuemax": 100,
            }
          : {})}
      >
        <svg width={size} height={size} className="-rotate-90" aria-hidden>
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            className={cn("fill-none", tone === "hero" ? "stroke-white/15" : "stroke-muted")}
            strokeWidth={ringWidth}
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            className={cn(
              "fill-none transition-[stroke-dashoffset] duration-700 ease-(--ease-out)",
              stroke,
            )}
            strokeWidth={ringWidth}
            strokeLinecap="round"
            strokeDasharray={c}
            strokeDashoffset={offset}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={cn("text-metric", size >= 120 ? "text-4xl" : "text-2xl")}>
            {clamped}
            {suffix ? (
              <span className="ml-0.5 text-[0.5em] font-medium opacity-80">{suffix}</span>
            ) : null}
          </span>
          {sub && (
            <span
              className={cn(
                "text-[10px] uppercase tracking-wider",
                tone === "hero" ? "text-hero-muted" : "text-muted-foreground",
              )}
            >
              {sub}
            </span>
          )}
        </div>
      </div>
      {label && <span className="text-xs font-medium text-muted-foreground">{label}</span>}
    </div>
  );
}
