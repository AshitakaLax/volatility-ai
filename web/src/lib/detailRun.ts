/**
 * The "View full detail" re-run: one configuration of a sweep, run again
 * on its own so its chart and trade log exist. Only the engine's top pick
 * ships executions on the wire, so every other cell needs this.
 *
 * Pure, like lib/filters.ts, because every field here is one where a
 * small mistake re-runs a DIFFERENT backtest than the cell it claims to
 * be -- and the result still looks entirely plausible on screen.
 */
import { configurationLabel } from "@/lib/sweepSummary";
import type { Cell, Fund, RunMeta, RunReq } from "@/types/backtest";

/**
 * The request that reproduces `config` on `ticker` over exactly the bars
 * the original run saw. null when the cell has no grid/target to submit.
 *
 * THE WINDOW. `start` is the first bar's exact timestamp. `end` is the
 * last bar's UTC DATE, not its timestamp: the server's window() treats
 * `end` as the whole day (`< end + 1 day`), so a full timestamp would pull
 * in up to a day of extra bars past the original's last one. The date is
 * exact: the original's cutoff was the end of that day or later, and its
 * last bar was the last one before that cutoff, so no bar later that same
 * day exists to be picked up.
 *
 * NO `limit`. With both bounds exact the frame is already the original
 * one, so a cap has nothing to trim -- and the server refuses a limit
 * under 500, which made every run shorter than that (a single trading day
 * is ~390 bars) impossible to re-run at all.
 *
 * `cashYieldPct` is the ORIGINAL request's value when known. The report
 * does not carry it, and omitting it means the smart historical rate --
 * right for most runs, wrong for one submitted with a fixed rate or 0,
 * where cash, buying power and percent-of-equity sizing would all differ.
 */
export function buildDetailRequest(
  report: Pick<RunMeta, "model" | "fill" | "no_loss">,
  ticker: string,
  fund: Pick<Fund, "bars">,
  config: Cell,
  cashYieldPct: number | null | undefined,
): RunReq | null {
  if (config.grid === null || config.target === null) return null;
  return {
    name: `detail: ${configurationLabel(config)}`,
    tickers: [ticker],
    grid_steps: [config.grid],
    targets: [config.target],
    ...(report.model ? { model: report.model } : {}),
    params: config.params,
    fill: report.fill === "intrabar" ? "intrabar" : "close",
    no_loss: report.no_loss,
    ...(typeof cashYieldPct === "number" ? { cash_yield_pct: cashYieldPct } : {}),
    start: fund.bars.start,
    end: fund.bars.end.slice(0, 10),
  };
}
