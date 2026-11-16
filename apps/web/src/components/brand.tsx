import { useId } from "react";

import { cn } from "@/lib/utils";

/**
 * SotuHire mark: a trajectory that leaves a confirmed point (bottom left) and reaches the next
 * one (top right) inside a petrol-to-azure seal that reads on the navy rail and on light canvas. Decorative; the wordmark next to it carries the name.
 * The same drawing is public/favicon.svg.
 */
export function BrandMark({ className }: { className?: string }) {
  const gradient = `brand-${useId().replaceAll(":", "")}`;
  return (
    <svg
      viewBox="0 0 32 32"
      aria-hidden="true"
      focusable="false"
      className={cn("h-8 w-8 shrink-0", className)}
    >
      <defs>
        <linearGradient id={gradient} x1="0" y1="1" x2="1" y2="0">
          <stop offset="0" stopColor="oklch(0.48 0.1 222)" />
          <stop offset="1" stopColor="oklch(0.62 0.12 185)" />
        </linearGradient>
      </defs>
      <rect x="1" y="1" width="30" height="30" rx="8" fill={`url(#${gradient})`} />
      <path
        d="M9 23c4.5 0 5-6.5 8.5-9.5S21.5 9 23 9"
        fill="none"
        stroke="white"
        strokeWidth="2.4"
        strokeLinecap="round"
      />
      <circle cx="9" cy="23" r="2.6" fill="white" />
      <circle cx="23" cy="9" r="3.2" fill="oklch(0.9 0.11 95)" stroke="white" strokeWidth="1.2" />
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
