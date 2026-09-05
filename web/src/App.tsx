import { useEffect, useState } from "react";
import { Activity, LineChart } from "lucide-react";

import type { MultiFundBacktestReport } from "@/types/backtest";
import { cn, pct, usd } from "@/lib/utils";

/**
 * Phase 1 shell: proves the environment and the types agree with the
 * data the Python side actually emits.
 *
 * Section 1 (backtesting) is the priority view and therefore the
 * default tab; live telemetry is Phase 5. Both are placeholders here --
 * the point of this file today is that a real exported report parses
 * against `MultiFundBacktestReport` with strict TypeScript on.
 */
type Tab = "backtest" | "live";

export default function App() {
  const [tab, setTab] = useState<Tab>("backtest");
  const [report, setReport] = useState<MultiFundBacktestReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // The static export (tools/export_ui_data.py). Phase 2 replaces this
    // with /api/backtest/runs; the SHAPE does not change, which is the
    // reason the exporter was written first.
    fetch("/data/backtest_report.json")
      .then((response) => {
        if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
        return response.json() as Promise<MultiFundBacktestReport>;
      })
      .then(setReport)
      .catch((cause: unknown) => {
        setError(
          cause instanceof Error ? cause.message : "could not read the exported report",
        );
      });
  }, []);

  const funds = report ? Object.entries(report.funds) : [];

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border">
        <div className="mx-auto flex max-w-7xl items-center gap-6 px-6 py-4">
          <span className="text-sm font-semibold tracking-tight">volatility-ai</span>
          <nav className="flex gap-1">
            {(
              [
                { id: "backtest", label: "Backtesting", icon: LineChart },
                { id: "live", label: "Live", icon: Activity },
              ] as const
            ).map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                type="button"
                onClick={() => setTab(id)}
                className={cn(
                  "flex items-center gap-2 rounded-md px-3 py-1.5 text-sm transition-colors",
                  tab === id
                    ? "bg-secondary text-secondary-foreground"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                <Icon className="size-4" />
                {label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-8">
        {tab === "live" ? (
          <p className="text-sm text-muted-foreground">
            Live telemetry is Phase 5. Until it lands, the Streamlit dashboard
            (<code className="text-foreground">streamlit run dashboard.py</code>) remains
            the operator view.
          </p>
        ) : error ? (
          <div className="rounded-lg border border-border p-6">
            <p className="text-sm font-medium">No exported report found.</p>
            <p className="mt-2 text-sm text-muted-foreground">
              Generate one with{" "}
              <code className="text-foreground">
                python tools/export_ui_data.py --tickers TQQQ
              </code>
              . ({error})
            </p>
          </div>
        ) : !report ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : (
          <div className="space-y-6">
            <div className="text-sm text-muted-foreground">
              <span className="text-foreground">{report.run_id}</span> ·{" "}
              {report.parameters.sizing_model} · step{" "}
              {pct((report.parameters.grid_step_pct ?? 0) * 100)} · target{" "}
              {pct((report.parameters.profit_target_pct ?? 0) * 100)} ·{" "}
              {report.parameters.fill_model} fills
            </div>

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {funds.map(([ticker, fund]) => (
                <article key={ticker} className="rounded-lg border border-border p-5">
                  <h2 className="text-sm font-semibold">{ticker}</h2>
                  <dl className="mt-4 space-y-2 text-sm">
                    <Row label="Net yield" value={pct(fund.metrics.net_yield_pct)} />
                    <Row label="CAGR" value={pct(fund.metrics.cagr_pct)} />
                    <Row
                      label="Max drawdown"
                      value={pct(fund.metrics.max_drawdown_pct)}
                    />
                    <Row label="Win rate" value={pct(fund.metrics.win_rate_pct, 1)} />
                    <Row
                      label="Stuck capital"
                      value={usd(fund.metrics.stuck_capital_value)}
                    />
                    <Row
                      label="Executions"
                      value={String(fund.executions.length)}
                    />
                  </dl>
                </article>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline justify-between gap-4">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="tnum font-medium">{value}</dd>
    </div>
  );
}
