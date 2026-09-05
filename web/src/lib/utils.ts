import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge class names, letting later Tailwind utilities win.
 *
 * shadcn/ui generates every component expecting this exact helper at
 * this exact path (see components.json's `aliases.utils`), so it is a
 * prerequisite rather than a convenience. `twMerge` is what makes an
 * override like `<Card className="p-0">` actually beat the component's
 * own `p-6`; plain `clsx` would emit both and let source order decide.
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/** Fixed-decimal percent, with an explicit sign for deltas. */
export function pct(value: number | null | undefined, digits = 2, signed = false): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "--";
  const sign = signed && value > 0 ? "+" : "";
  return `${sign}${value.toFixed(digits)}%`;
}

/** Currency, grouped. Returns "--" for absent rather than "$0.00",
 * which would read as a real zero balance. */
export function usd(value: number | null | undefined, digits = 2): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "--";
  return value.toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

/** Compact count, e.g. 19402 -> "19.4k". */
export function count(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "--";
  return Intl.NumberFormat("en-US", { notation: "compact" }).format(value);
}
