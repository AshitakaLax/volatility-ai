import { ColorType, type IChartApi, type Time, createChart } from "lightweight-charts";
import { useEffect, useRef } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/primitives";
import { cn, pct, usd } from "@/lib/utils";
import type { FundResult } from "@/types/backtest";

/**
 * Several funds, one run, side by side.
 *
 * THE OVERLAY IS NORMALISED, AND THAT IS THE WHOLE POINT. Two funds
 * starting at different prices cannot be read on one axis, and a chart
 * of raw equity would say nothing except which had the bigger opening
 * balance. Every curve is rebased to 100 at its own first bar, so the
 * lines answer "which grew more", which is the question being asked.
 *
 * The table beside it is deliberately not sorted by return. This
 * project's own results repeatedly show the highest-return column
 * belonging to a configuration nobody would deploy, and a table that
 * ranked by it would put that row first every time.
 */

interface Props {
  funds: Record<string, FundResult>;
}

// Distinguishable in both themes and at 1px. Not the semantic
// profit/loss/stuck tokens -- those mean something specific here, and
// reusing them for fund identity would make a fund look like a verdict.
const SERIES_COLORS = [
  "#60a5fa",
  "#f59e0b",
  "#a78bfa",
  "#34d399",
  "#f472b6",
  "#22d3ee",
  "#fb923c",
  "#94a3b8",
];

/**
 * Total by construction, so callers get a `string` rather than
 * `string | undefined`.
 *
 * noUncheckedIndexedAccess is on and is right to be: with more funds
 * than colours the index really can run past the end. This wraps rather
 * than pretending it cannot.
 */
function colorFor(index: number): string {
  return SERIES_COLORS[index % SERIES_COLORS.length] ?? "#94a3b8";
}

export function FundComparison({ funds }: Props) {
  const container = useRef<HTMLDivElement>(null);
  const chart = useRef<IChartApi | null>(null);
  const entries = Object.entries(funds);

  useEffect(() => {
    if (!container.current || entries.length === 0) return;

    const created = createChart(container.current, {
      height: 320,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: getComputedStyle(document.documentElement)
          .getPropertyValue("--muted-foreground")
          .trim(),
        fontFamily: "inherit",
      },
      grid: {
        vertLines: { color: "rgba(128,128,128,0.08)" },
        horzLines: { color: "rgba(128,128,128,0.08)" },
      },
      rightPriceScale: { borderVisible: false },
      timeScale: { borderVisible: false },
    });
    chart.current = created;

    entries.forEach(([ticker, fund], index) => {
      const series = created.addLineSeries({
        color: colorFor(index),
        lineWidth: 2,
        title: ticker,
        priceLineVisible: false,
        lastValueVisible: true,
      });
      const { dates, normalized } = fund.equity_curve;
      series.setData(
        dates.map((date, position) => ({
          time: date as Time,
          value: normalized[position] ?? 100,
        })),
      );
    });

    created.timeScale().fitContent();
    const resize = () => {
      if (container.current) created.applyOptions({ width: container.current.clientWidth });
    };
    resize();
    window.addEventListener("resize", resize);
    return () => {
      window.removeEventListener("resize", resize);
      created.remove();
      chart.current = null;
    };
  }, [funds, entries]);

  if (entries.length === 0) {
    return null;
  }

  return (
    <div className="grid gap-4">
      <Card>
        <CardHeader>
          <CardTitle>Relative growth</CardTitle>
          <p className="text-xs text-muted-foreground">
            Each fund rebased to 100 at its own first bar, so the lines are comparable
            regardless of starting price.
          </p>
        </CardHeader>
        <CardContent>
          <div ref={container} />
          <div className="mt-3 flex flex-wrap gap-4 text-xs">
            {entries.map(([ticker], index) => (
              <span key={ticker} className="flex items-center gap-1.5">
                <span
                  className="h-0.5 w-4 rounded"
                  style={{ background: colorFor(index) }}
                />
                {ticker}
              </span>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Side by side</CardTitle>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs text-muted-foreground">
                <th className="pb-2 font-medium">Fund</th>
                <th className="pb-2 text-right font-medium">Net yield</th>
                <th className="pb-2 text-right font-medium">CAGR</th>
                <th className="pb-2 text-right font-medium">Max DD</th>
                <th className="pb-2 text-right font-medium">Sharpe</th>
                <th className="pb-2 text-right font-medium">Win rate</th>
                <th className="pb-2 text-right font-medium">Stuck capital</th>
                <th className="pb-2 text-right font-medium">Trades</th>
              </tr>
            </thead>
            <tbody className="tnum">
              {entries.map(([ticker, fund]) => {
                const m = fund.metrics;
                return (
                  <tr key={ticker} className="border-b border-border/50 last:border-0">
                    <td className="py-2 font-medium">{ticker}</td>
                    <td
                      className={cn(
                        "py-2 text-right",
                        m.net_yield_pct >= 0 ? "text-profit" : "text-loss",
                      )}
                    >
                      {pct(m.net_yield_pct)}
                    </td>
                    <td className="py-2 text-right">{pct(m.cagr_pct)}</td>
                    <td className="py-2 text-right text-loss">{pct(m.max_drawdown_pct)}</td>
                    <td className="py-2 text-right">{m.sharpe_ratio.toFixed(2)}</td>
                    <td className="py-2 text-right">{pct(m.win_rate_pct, 1)}</td>
                    <td
                      className={cn(
                        "py-2 text-right",
                        m.stuck_capital_value > 0 && "text-stuck",
                      )}
                    >
                      {usd(m.stuck_capital_value, 0)}
                    </td>
                    <td className="py-2 text-right">
                      {m.closed_trades}
                      <span className="text-muted-foreground"> / {m.total_trades}</span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {entries.some(([, fund]) => fund.executions.length === 0) ? (
            <p className="mt-3 text-xs text-muted-foreground">
              A fund with no executions is not an error: a low-volatility instrument on a
              grid tuned for a leveraged one legitimately never triggers.
            </p>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
