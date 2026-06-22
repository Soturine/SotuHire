import { cn } from "@/lib/utils";

export function ScoreRing({
  value,
  label,
  size = 96,
  tone = "primary",
  sub,
}: {
  value: number;
  label?: string;
  size?: number;
  tone?: "primary" | "accent" | "warning" | "destructive";
  sub?: string;
}) {
  const clamped = Math.max(0, Math.min(100, Math.round(value)));
  const r = (size - 10) / 2;
  const c = 2 * Math.PI * r;
  const offset = c * (1 - clamped / 100);

  const stroke = {
    primary: "stroke-[var(--color-chart-1)]",
    accent: "stroke-[var(--color-accent)]",
    warning: "stroke-[var(--color-warning)]",
    destructive: "stroke-[var(--color-destructive)]",
  }[tone];

  return (
    <div className="flex flex-col items-center gap-1.5">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            className="fill-none stroke-muted"
            strokeWidth={8}
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            className={cn("fill-none transition-all duration-700", stroke)}
            strokeWidth={8}
            strokeLinecap="round"
            strokeDasharray={c}
            strokeDashoffset={offset}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-display text-2xl tabular-nums">{clamped}</span>
          {sub && (
            <span className="text-[10px] uppercase tracking-wider text-muted-foreground">
              {sub}
            </span>
          )}
        </div>
      </div>
      {label && <span className="text-xs font-medium text-muted-foreground">{label}</span>}
    </div>
  );
}
