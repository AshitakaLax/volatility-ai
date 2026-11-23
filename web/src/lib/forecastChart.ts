/**
 * The Live page's forecast-against-the-close chart: pure functions
 * ForecastChart draws from, pinned by forecastChart.test.ts.
 *
 * Each session is one column: its report's 1-day forecast (the 90% range
 * p05-p95, the middle 50% p25-p75, the median) and, once the tracking
 * service has recorded the close, where the close-to-close return landed in
 * it. The landing comes from the server's score (tools/score_risk_reports.py)
 * when there is one; the same rule is applied here only for a session closed
 * but not scored yet.
 */
import type { Tone } from "@/lib/control";
import type { ForecastSession } from "@/types/riskReport";

export type Landing = "in50" | "in90" | "above" | "below" | "pending";

export const LANDING: Record<Landing, { label: string; tone: Tone }> = {
  in50: { label: "inside its middle 50%", tone: "profit" },
  in90: { label: "inside its 90% range", tone: "stuck" },
  above: { label: "above its 90% range", tone: "loss" },
  below: { label: "below its 90% range", tone: "loss" },
  pending: { label: "waiting for the close", tone: "neutral" },
};

/** Where the session's close landed in its forecast. */
export function landing(row: ForecastSession): Landing {
  if (!row.actual) return "pending";
  const value = row.actual.return_pct;
  const q = row.quantiles;
  const in50 = row.score ? row.score.in_50 : q.p25 <= value && value <= q.p75;
  const in90 = row.score ? row.score.in_90 : q.p05 <= value && value <= q.p95;
  if (in50) return "in50";
  if (in90) return "in90";
  return value > q.p95 ? "above" : "below";
}

/** The y axis: symmetric about 0, reaching every range and close drawn,
 * rounded up to the tick step. */
export function yExtent(rows: ForecastSession[]): number {
  const reach = Math.max(
    5,
    ...rows.flatMap((row) => [
      Math.abs(row.quantiles.p05),
      Math.abs(row.quantiles.p95),
      Math.abs(row.actual?.return_pct ?? 0),
    ]),
  );
  const step = tickStep(reach);
  return Math.ceil(reach / step) * step;
}

function tickStep(extent: number): number {
  return extent <= 20 ? 5 : extent <= 50 ? 10 : 25;
}

/** The gridlines, from -extent to +extent. */
export function yTicks(extent: number): number[] {
  const step = tickStep(extent);
  const out: number[] = [];
  for (let value = -extent; value <= extent + 1e-9; value += step) out.push(value);
  return out;
}

/** How many closes landed inside each band, of those with a close. */
export function coverage(rows: ForecastSession[]): { closed: number; in90: number; in50: number } {
  const landed = rows.map(landing).filter((where) => where !== "pending");
  return {
    closed: landed.length,
    in90: landed.filter((where) => where === "in50" || where === "in90").length,
    in50: landed.filter((where) => where === "in50").length,
  };
}

/** Which x labels to print: every one while they fit, else every second
 * or third counted back from the newest, which is always labelled. */
export function labelled(count: number, slot: number): (index: number) => boolean {
  const every = slot < 30 ? 3 : slot < 46 ? 2 : 1;
  return (index) => (count - 1 - index) % every === 0;
}

/** "+3.5%", "−13.4%", "0.0%" -- a true minus sign. */
export function signed(value: number, digits = 1): string {
  const text = Math.abs(value).toFixed(digits);
  if (Number(text) === 0) return `${text}%`;
  return `${value > 0 ? "+" : "−"}${text}%`;
}
