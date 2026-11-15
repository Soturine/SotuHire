import { useId, type ReactNode } from "react";

import { cn } from "@/lib/utils";

/**
 * One labelled form field: the label points at the control (htmlFor), the hint and the error are
 * announced with it (aria-describedby), and an error marks the control invalid. Controls receive
 * these props from the render function, so any input, textarea or select can be used.
 */
export type FieldControlProps = {
  id: string;
  "aria-describedby"?: string;
  "aria-invalid"?: true;
};

export function Field({
  label,
  hint,
  error,
  optional,
  className,
  children,
}: {
  label: ReactNode;
  hint?: ReactNode;
  error?: ReactNode;
  optional?: boolean;
  className?: string;
  children: (control: FieldControlProps) => ReactNode;
}) {
  const id = useId();
  const hintId = hint ? `${id}-hint` : undefined;
  const errorId = error ? `${id}-error` : undefined;
  const describedBy = [errorId, hintId].filter(Boolean).join(" ") || undefined;
  return (
    <div className={cn("min-w-0", className)}>
      <label htmlFor={id} className="flex items-baseline gap-2 text-sm font-medium">
        {label}
        {optional ? " " : null}
        {optional ? (
          <span className="text-xs font-normal text-muted-foreground">opcional</span>
        ) : null}
      </label>
      <div className="mt-1.5">
        {children({
          id,
          "aria-describedby": describedBy,
          ...(error ? { "aria-invalid": true as const } : {}),
        })}
      </div>
      {error ? (
        <p id={errorId} className="mt-1.5 text-xs font-medium text-destructive-strong">
          {error}
        </p>
      ) : null}
      {hint ? (
        <p id={hintId} className="mt-1.5 text-xs text-muted-foreground">
          {hint}
        </p>
      ) : null}
    </div>
  );
}

/** Shared control styles: the same height, border, focus and invalid states everywhere. */
export const controlClass =
  "w-full rounded-lg border border-input bg-surface-raised px-3 py-2 text-sm shadow-[var(--shadow-soft)] outline-none transition-[border-color,box-shadow] duration-(--duration-1) placeholder:text-muted-foreground/80 hover:border-foreground/25 focus-visible:border-accent focus-visible:ring-3 focus-visible:ring-accent/20 aria-invalid:border-destructive aria-invalid:ring-destructive/15 disabled:opacity-60";

export const textareaClass = cn(controlClass, "min-h-28 resize-y leading-relaxed");

/** A labelled single-line input: the common case, so screens do not each keep their own copy. */
export function TextField({
  label,
  value,
  onChange,
  type = "text",
  required,
  placeholder,
  hint,
  className,
}: {
  label: ReactNode;
  value: string;
  onChange: (value: string) => void;
  type?: string;
  required?: boolean;
  placeholder?: string;
  hint?: ReactNode;
  className?: string;
}) {
  return (
    <Field label={label} hint={hint} className={className}>
      {(control) => (
        <input
          {...control}
          type={type}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          required={required}
          placeholder={placeholder}
          className={controlClass}
        />
      )}
    </Field>
  );
}
