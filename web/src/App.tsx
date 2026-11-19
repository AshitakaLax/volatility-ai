import {
  Activity,
  ArrowRight,
  BarChart3,
  Database,
  FlaskConical,
  LineChart,
  ListChecks,
  Monitor,
  Moon,
  Sun,
} from "lucide-react";
import { lazy, Suspense, useCallback, useEffect, useState } from "react";

import { LiveTab } from "@/components/live/LiveTab";
import { Button, Card, CardContent } from "@/components/ui/primitives";
import { useBacktestRun } from "@/hooks/useBacktestRun";
import { usePolled } from "@/hooks/usePolled";
import { api } from "@/lib/api";
import { pageTitle } from "@/lib/attention";
import { parsePlace, placeHash, type Place, type Tab } from "@/lib/nav";
import { nextTheme, setTheme, themeChoice, watchSystemTheme, type ThemeChoice } from "@/lib/theme";
import { cn } from "@/lib/utils";
import { DEFAULT_FILTERS, type ExecutionFilters, type Report } from "@/types/backtest";

// Every tab but Live is its own chunk, fetched the first time it is opened:
// the page opens on Live, and the backtest form, result charts, warehouse and
// ML views were most of the one bundle it downloaded before showing it.
const ActiveRuns = lazy(() =>
  import("@/components/backtest/ActiveRuns").then((m) => ({ default: m.ActiveRuns })),
);
const BacktestResult = lazy(() =>
  import("@/components/backtest/BacktestResult").then((m) => ({ default: m.BacktestResult })),
);
const ParameterForm = lazy(() =>
  import("@/components/backtest/ParameterForm").then((m) => ({ default: m.ParameterForm })),
);
const RunHistory = lazy(() =>
  import("@/components/backtest/RunHistory").then((m) => ({ default: m.RunHistory })),
);
const ShardPanel = lazy(() =>
  import("@/components/backtest/ShardPanel").then((m) => ({ default: m.ShardPanel })),
);
const AlgorithmsTab = lazy(() =>
  import("@/components/algorithms/AlgorithmsTab").then((m) => ({ default: m.AlgorithmsTab })),
);
const ModelInsights = lazy(() =>
  import("@/components/ml/ModelInsights").then((m) => ({ default: m.ModelInsights })),
);
const WarehouseTab = lazy(() =>
  import("@/components/warehouse/WarehouseTab").then((m) => ({ default: m.WarehouseTab })),
);

/**
 * The tabs keep the brief's order, Backtesting first. The page OPENS on
 * Live -- the one looked at every day -- and where the reader is lives in
 * the address (lib/nav.ts), so a reload or a bookmark returns there.
 *
 * "Backtest result" is a fourth tab rather than a panel inside
 * Backtesting: opening a run loads a whole report, and rendering that
 * between the parameter form and the history table it came from pushed
 * the controls off screen. The Backtesting tab is now purely the
 * instrument (form, active runs, history); the report it produces --
 * from a submission or from opening a saved run -- shows next door in
 * BacktestResult. The report falls back to the static export when there
 * is no run, so the page is useful before the API is up, which is also
 * how it was developed.
 */
const TITLE_POLL_MS = 30_000;

const THEME_ICONS = { system: Monitor, light: Sun, dark: Moon } as const;

function here(): Place {
  return parsePlace(window.location.hash, window.location.search);
}

export default function App() {
  const [place, setPlace] = useState<Place>(here);
  const tab = place.tab;
  const [theme, setThemeChoice] = useState<ThemeChoice>(themeChoice);

  // The address is the state: going somewhere writes it, and the back
  // button (or an edited address) is read back.
  const go = useCallback((next: Place) => {
    setPlace(next);
    const hash = placeHash(next);
    if (window.location.hash !== hash) window.history.pushState(null, "", hash);
  }, []);
  const setTab = useCallback(
    (next: Tab) => go({ tab: next, deployment: next === "live" ? place.deployment : null }),
    [go, place.deployment],
  );
  const setDeployment = useCallback(
    (deployment: string) => go({ tab: "live", deployment }),
    [go],
  );
  useEffect(() => {
    const read = () => setPlace(here());
    window.addEventListener("hashchange", read);
    window.addEventListener("popstate", read);
    return () => {
      window.removeEventListener("hashchange", read);
      window.removeEventListener("popstate", read);
    };
  }, []);

  useEffect(() => watchSystemTheme(), []);

  // The browser tab says how real money stands -- or what needs attention --
  // whichever page is open, so a pinned tab is worth a glance.
  const deployments = usePolled(api.deployments, TITLE_POLL_MS);
  useEffect(() => {
    document.title = pageTitle(deployments.data ?? [], Date.now());
  }, [deployments.data]);
  const [staticReport, setStaticReport] = useState<Report | null>(null);
  const [filters, setFilters] = useState<ExecutionFilters>(DEFAULT_FILTERS);
  const { run, batch, submit, attach, submitting, error } = useBacktestRun();
  // Bumped whenever a run settles, so history reloads without the
  // reader having to press anything.
  const [historyToken, setHistoryToken] = useState(0);
  const [engineVersion, setEngineVersion] = useState<string | null>(null);
  const [staged, setStaged] = useState<{ gridStep: number; profitTarget: number } | null>(
    null,
  );

  useEffect(() => {
    api
      .health()
      .then((h) => setEngineVersion(h.build.version ?? null))
      .catch(() => setEngineVersion(null));
  }, []);

  useEffect(() => {
    void api.staticReport().then(setStaticReport);
  }, []);

  // Selecting a run (Run history, Active runs) opens ?run=<id> in a NEW
  // browser tab rather than swapping the current view -- see runUrl() in
  // lib/utils.ts. This is that tab's other half: on load, notice the
  // param, land on the Backtest result tab, and attach to exactly that
  // run -- the same path a run this session submitted itself takes once
  // it completes.
  useEffect(() => {
    const runId = new URLSearchParams(window.location.search).get("run");
    if (!runId) return;
    // parsePlace already landed this tab on the result page.
    void attach(runId);
  }, [attach]);

  // A completed run wins over the export; nothing else changes the view.
  const report = run?.report ?? staticReport;

  // A run submitted from the form finishes on THIS tab -- the button and
  // the status badge report it -- but the report itself now lives next
  // door. Rather than force-navigate mid-render (which races the "run
  // complete" state a test and a reader both watch for), the Backtesting
  // tab offers the jump when there is something to jump to.
  const submittedReportReady = run?.status === "complete" && Boolean(run.report);

  const stageCell = (gridStep: number, profitTarget: number) => {
    // A sweep-matrix click on the result tab prefills the form on the
    // Backtesting tab -- move there so the staged configuration is
    // visible rather than silently applied on a tab out of view.
    setStaged({ gridStep, profitTarget });
    setTab("backtest");
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border">
        <div className="mx-auto flex max-w-[1600px] flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3 sm:px-6 sm:py-4">
          <div className="flex shrink-0 flex-col leading-tight">
            <span className="text-sm font-semibold tracking-tight">volatility-ai</span>
            <span
              className="tnum text-[10px] text-muted-foreground"
              title="Web UI release version · engine release version"
              data-testid="version-line"
            >
              web v{__WEB_VERSION__} · engine {engineVersion ? `v${engineVersion}` : "…"}
            </span>
          </div>
          {/* On a phone the tabs take their own row and scroll sideways
              rather than pushing the page wider than the screen. */}
          <nav className="order-last flex w-full min-w-0 gap-1 overflow-x-auto sm:order-none sm:w-auto">
            {(
              [
                { id: "backtest", label: "Backtesting", icon: LineChart },
                { id: "result", label: "Backtest result", icon: BarChart3 },
                { id: "live", label: "Live", icon: Activity },
                { id: "algorithms", label: "Algorithms", icon: ListChecks },
                { id: "ml", label: "Model research", icon: FlaskConical },
                { id: "warehouse", label: "Warehouse", icon: Database },
              ] as const
            ).map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                type="button"
                onClick={() => setTab(id)}
                aria-current={tab === id ? "page" : undefined}
                className={cn(
                  "flex shrink-0 items-center gap-2 rounded-md px-3 py-1.5 text-sm whitespace-nowrap transition-colors",
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
          <div className="ml-auto flex min-w-0 items-center gap-3">
          {report && (tab === "backtest" || tab === "result") ? (
            <span className="hidden truncate text-xs text-muted-foreground xl:inline">
              {report.name ? (
                <span className="font-medium text-foreground">{report.name} · </span>
              ) : null}
              {report.id} · {report.model} · step {((report.grid ?? 0) * 100).toFixed(2)}% ·
              target {((report.target ?? 0) * 100).toFixed(2)}% · {report.fill} fills
              {report.jobs && report.jobs > 1 ? ` · ${report.jobs} workers` : ""}
            </span>
          ) : null}
            <ThemeButton
              choice={theme}
              onChange={(next) => {
                setTheme(next);
                setThemeChoice(next);
              }}
            />
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-[1600px] space-y-4 px-3 py-4 sm:px-6 sm:py-6">
        <Suspense fallback={<p className="text-sm text-muted-foreground">Loading…</p>}>
          {tab === "live" ? (
            <LiveTab chosen={place.deployment} onChoose={setDeployment} />
          ) : tab === "algorithms" ? (
            <AlgorithmsTab />
          ) : tab === "ml" ? (
            <ModelInsights />
          ) : tab === "warehouse" ? (
            <WarehouseTab />
          ) : tab === "result" ? (
            <BacktestResult
              report={report}
              run={run}
              filters={filters}
              onFiltersChange={setFilters}
              onLoadIntoForm={stageCell}
            />
          ) : (
            <>
              {/* Above the form on purpose: which machines are connected
                  decides where a sweep submitted below will actually run. */}
              <ShardPanel />

              <ParameterForm
                onSubmit={(request) => submit(request)}
                run={run}
                batch={batch}
                submitting={submitting}
                error={error}
                range={filters.range}
                staged={staged}
              />

              {submittedReportReady ? (
                <Card>
                  <CardContent className="flex items-center justify-between gap-4 pt-5">
                    <p className="text-sm text-muted-foreground">
                      Run complete
                      {run?.report?.name
                        ? ` — ${run.report.name}`
                        : ""}
                      . The chart, trade log and sweep surface are on the Backtest result tab.
                    </p>
                    <Button variant="outline" onClick={() => setTab("result")}>
                      Backtest result
                      <ArrowRight className="size-3.5" />
                    </Button>
                  </CardContent>
                </Card>
              ) : null}

              {/* Selecting a run from either of these opens it in its own
                  browser tab (runUrl() in lib/utils.ts), which lands on
                  the Backtest result tab -- so an in-progress submission
                  here is never displaced by a click meant to glance at
                  something else. */}
              <ActiveRuns onSettled={() => setHistoryToken((value) => value + 1)} />

              <RunHistory refreshToken={historyToken} />
            </>
          )}
        </Suspense>
      </main>
    </div>
  );
}

/** System, light, dark: one button that steps through them. */
function ThemeButton({
  choice,
  onChange,
}: {
  choice: ThemeChoice;
  onChange: (next: ThemeChoice) => void;
}) {
  const Icon = THEME_ICONS[choice];
  const label = `Theme: ${choice}`;
  return (
    <button
      type="button"
      title={`${label}. Click to change.`}
      aria-label={label}
      data-testid="theme"
      onClick={() => onChange(nextTheme(choice))}
      className="shrink-0 rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
    >
      <Icon className="size-4" />
    </button>
  );
}
