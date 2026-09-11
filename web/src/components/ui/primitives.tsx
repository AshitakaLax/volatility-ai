import type {
  ButtonHTMLAttributes,
  HTMLAttributes,
  InputHTMLAttributes,
  LabelHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
} from "react";

import { cn } from "@/lib/utils";

/**
 * The handful of shadcn/ui primitives this app uses, written out rather
 * than generated.
 *
 * `npx shadcn add` is interactive and would pull a component tree far
 * larger than five elements. These follow the same conventions --
 * className merged through cn(), variants as data, tokens from
 * index.css -- so a generated component dropped in beside them behaves
 * identically.
 */

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("rounded-lg border border-border bg-card text-card-foreground", className)}
      {...props}
    />
  );
}

export function CardHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("flex flex-col gap-1 p-5 pb-3", className)} {...props} />;
}

export function CardTitle({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) {
  return <h3 className={cn("text-sm font-semibold tracking-tight", className)} {...props} />;
}

export function CardContent({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("p-5 pt-0", className)} {...props} />;
}

type ButtonVariant = "default" | "outline" | "ghost" | "destructive";

const BUTTON_VARIANTS: Record<ButtonVariant, string> = {
  default: "bg-primary text-primary-foreground hover:opacity-90",
  outline: "border border-border bg-transparent hover:bg-accent",
  ghost: "bg-transparent hover:bg-accent",
  destructive: "bg-destructive text-white hover:opacity-90",
};

export function Button({
  className,
  variant = "default",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: ButtonVariant }) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium",
        "transition-colors focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none",
        "disabled:pointer-events-none disabled:opacity-50",
        BUTTON_VARIANTS[variant],
        className,
      )}
      {...props}
    />
  );
}

export function Label({ className, ...props }: LabelHTMLAttributes<HTMLLabelElement>) {
  return (
    <label
      className={cn("text-xs font-medium text-muted-foreground", className)}
      {...props}
    />
  );
}

export function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-1.5">
      <Label>{label}</Label>
      {children}
    </div>
  );
}

const CONTROL =
  "h-8 rounded-md border border-input bg-transparent px-2 text-sm " +
  "focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none " +
  "disabled:cursor-not-allowed disabled:opacity-50";

// InputHTMLAttributes, not HTMLAttributes: the latter has no `value`,
// `type` or `onChange`, so every controlled input would fail to
// typecheck -- which is the compiler correctly refusing a primitive
// that could not actually be controlled.
export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={cn(CONTROL, className)} {...props} />;
}

export function Checkbox({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      type="checkbox"
      className={cn(
        "size-3.5 rounded border border-input accent-primary " +
          "focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none " +
          "disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
    />
  );
}

export function Select({ className, ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={cn(
        CONTROL,
        "pr-6",
        // The closed control is fine transparent over a card, but the
        // POP-UP list is drawn by the browser. color-scheme (index.css)
        // handles most engines; pinning the option colours to the dark
        // popover tokens makes it deterministic on the ones that still
        // paint the list white -- otherwise the near-white inherited
        // text is invisible until a row is highlighted.
        "[&>option]:bg-popover [&>option]:text-popover-foreground",
        className,
      )}
      {...props}
    />
  );
}

type Tone = "neutral" | "profit" | "loss" | "stuck";

const TONES: Record<Tone, string> = {
  neutral: "bg-secondary text-secondary-foreground",
  profit: "bg-profit/15 text-profit",
  loss: "bg-loss/15 text-loss",
  stuck: "bg-stuck/15 text-stuck",
};

export function Badge({
  tone = "neutral",
  className,
  ...props
}: HTMLAttributes<HTMLSpanElement> & { tone?: Tone }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
        TONES[tone],
        className,
      )}
      {...props}
    />
  );
}
