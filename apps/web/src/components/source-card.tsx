import { Link } from "@tanstack/react-router";
import type { SourceCard } from "@/mocks/sources";
import { SOURCE_STATUS_LABEL } from "@/mocks/sources";
import { cn } from "@/lib/utils";

const STATUS_TONE: Record<SourceCard["status"], string> = {
  available: "border-success/40 bg-success/10 text-success",
  demo: "border-warning/40 bg-warning/10 text-warning",
  planned: "border-warning/40 bg-warning/10 text-warning",
  future: "border-border bg-muted text-muted-foreground",
  extension: "border-accent/40 bg-accent/10 text-accent",
  api: "border-primary/40 bg-primary/10 text-primary",
};

export function SourceCardItem({ card }: { card: SourceCard }) {
  const Icon = card.icon;
  const disabled = card.disabled || (!card.to && !card.anchor);

  const button = (
    <button
      type="button"
      disabled={disabled}
      className={cn(
        "inline-flex w-full items-center justify-center rounded-md px-3 py-2 text-xs font-medium transition-colors",
        disabled
          ? "cursor-not-allowed border border-border bg-muted/50 text-muted-foreground"
          : "bg-primary text-primary-foreground hover:bg-primary/90",
      )}
    >
      {card.cta}
    </button>
  );

  return (
    <article className="group flex flex-col gap-4 rounded-xl border border-border bg-card p-5 shadow-[var(--shadow-soft)] transition-all hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-md">
      <div className="flex items-start justify-between gap-3">
        <div className="grid h-10 w-10 place-items-center rounded-lg bg-muted text-accent">
          <Icon className="h-5 w-5" />
        </div>
        <span
          className={cn(
            "rounded-full border px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider",
            STATUS_TONE[card.status],
          )}
        >
          {SOURCE_STATUS_LABEL[card.status]}
        </span>
      </div>
      <div className="space-y-1.5">
        <h3 className="text-sm font-semibold tracking-tight">{card.title}</h3>
        <p className="text-xs leading-relaxed text-muted-foreground">{card.description}</p>
      </div>
      <div className="mt-auto">
        {card.anchor && !card.disabled ? (
          <a href={card.anchor} className="block">
            {button}
          </a>
        ) : card.to && !card.disabled ? (
          <Link to={card.to} className="block">
            {button}
          </Link>
        ) : (
          button
        )}
      </div>
    </article>
  );
}
