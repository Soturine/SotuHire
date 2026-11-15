import { cn } from "@/lib/utils";

/**
 * SotuHire mark: a trajectory that leaves a confirmed point (bottom left) and reaches the next
 * one (top right) inside an ink seal. Decorative; the wordmark next to it carries the name.
 * The same drawing is public/favicon.svg.
 */
export function BrandMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 32 32"
      aria-hidden="true"
      focusable="false"
      className={cn("h-8 w-8 shrink-0", className)}
    >
      <rect x="1" y="1" width="30" height="30" rx="7" className="fill-primary" />
      <path
        d="M9 23c4.5 0 5-6.5 8.5-9.5S21.5 9 23 9"
        fill="none"
        strokeWidth="2.4"
        strokeLinecap="round"
        className="stroke-primary-foreground"
      />
      <circle cx="9" cy="23" r="2.6" className="fill-primary-foreground" />
      <circle cx="23" cy="9" r="3" className="fill-accent" />
    </svg>
  );
}

export function BrandWordmark({ tagline }: { tagline?: string }) {
  return (
    <span className="flex items-center gap-2.5">
      <BrandMark />
      <span className="flex flex-col leading-none">
        <span className="text-display text-[19px] tracking-tight">SotuHire</span>
        {tagline ? <span className="mt-1 text-[11px] text-muted-foreground">{tagline}</span> : null}
      </span>
    </span>
  );
}
