import { AlertCircle, Play } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import { GridStepPanel } from "@/components/backtest/GridStepPanel";
import { ParamField } from "@/components/backtest/ParamField";
import { SweepableParamField } from "@/components/backtest/SweepableParamField";
import { SweepControls } from "@/components/backtest/SweepControls";
import { api, type FundAvailability } from "@/lib/api";
import { Badge, Button, Card, CardContent, CardHeader, CardTitle, Checkbox, Field, Input, Select } from "@/components/ui/primitives";
import { buildGridSteps } from "@/lib/gridSteps";
import { GENERIC_GRID_TRIGGER, initialTriggerMethod } from "@/lib/gridTrigger";
import { DEFAULT_SWEEP_FIELD_STATE, type SweepFieldState } from "@/lib/sweepStrategies";
import {
  blankRequired,
  buildParamSweep,
  buildStrategyParams,
  diffFromDefaults,
  paramErrorsFor,
  seedValues,
} from "@/lib/strategyParams";
import type {
  BacktestRunRequest,
  BacktestRunState,
  DateRange,
  GridTrigger,
  GridTriggerMethod,
  ParamSpec,
  SizingParamsEntry,
  ValidateResponse,
} from "@/types/backtest";

// Mirrors server/backtest.py's MAX_SWEEP_COMBINATIONS default -- catches
// an oversized sweep client-side, before the round trip to a 400.
const MAX_SWEEP_COMBINATIONS = 2000;

/**
 * The bidirectional half: submit a run and watch it.
 *
 * This is the one control in the application that causes work to happen
 * rather than changing what is drawn. It is visually separated from
 * FilterPanel for that reason -- filtering is free and instant, a run
 * costs real engine time, and a user should be able to tell which
 * button does which before pressing it.
 *
 * The sizing-model dropdown drives a DYNAMIC field set: `/funds` carries
 * one spec per constructor argument of every model, and selecting a
 * model swaps the visible inputs to exactly that model's arguments,
 * pre-filled from the project's committed configs. Editing them submits
 * an explicit `strategy_params`; a debounced `/validate` call shows a
 * bad value under its field before the run is ever queued.
 */

interface Props {
  onSubmit: (request: BacktestRunRequest) => void;
  run: BacktestRunState | null;
  submitting: boolean;
  error: string | null;
  /**
   * The filter panel's window, submitted WITH the run.
   *
   * One date range, two jobs: it filters what is drawn, and it bounds
   * what the engine reads. Two separate pickers for the same concept
   * would let them disagree, and the chart would then be showing a
   * different period than the metrics beside it.
   */
  range: DateRange;
  /**
   * Parameters staged from a sweep-matrix cell, as PERCENTAGES.
   *
   * Applied to the inputs rather than submitted, so a click loads a
   * configuration for review and the run stays an explicit act.
   */
  staged?: { gridStep: number; profitTarget: number } | null;
}

export function ParameterForm({ onSubmit, run, submitting, error, range, staged }: Props) {
  const [funds, setFunds] = useState<FundAvailability[]>([]);
  const [models, setModels] = useState<string[]>([]);
  const [paramSpecs, setParamSpecs] = useState<Record<string, SizingParamsEntry>>({});
  const [gridTriggerMap, setGridTriggerMap] = useState<Record<string, GridTrigger>>({});
  const [tickers, setTickers] = useState<string[]>(["TQQQ"]);
  const [name, setName] = useState("");
  const [gridStep, setGridStep] = useState(1.0);
  // The "enable sweep" state, one entry per sweepable argument: always
  // `grid_step` and `profit_target`, plus one per sweepable strategy
  // param of the current model (reseeded on model change, below).
  const [sweepFields, setSweepFields] = useState<Record<string, SweepFieldState>>({
    grid_step: { ...DEFAULT_SWEEP_FIELD_STATE, start: "0.5", end: "1.5" },
    profit_target: DEFAULT_SWEEP_FIELD_STATE,
  });
  // The grid-step trigger method, used only when the model offers a choice.
  const [triggerMethod, setTriggerMethod] = useState<GridTriggerMethod>("last_buy");
  const [profitTarget, setProfitTarget] = useState(0.5);
  const [model, setModel] = useState("fixed");
  const [fillModel, setFillModel] = useState<"close" | "intrabar">("close");
  const [limit, setLimit] = useState(50_000);
  const [loadError, setLoadError] = useState<string | null>(null);

  // Per-field text for the current model, keyed by parameter name. Held
  // as strings so "" is a distinct blank/unset state (not "0"); parsing
  // to the declared type happens once, in buildStrategyParams.
  const [paramValues, setParamValues] = useState<Record<string, string>>({});
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [validation, setValidation] = useState<ValidateResponse | null>(null);
  const validateSeq = useRef(0);

  const specs = useMemo(() => paramSpecs[model]?.params ?? [], [paramSpecs, model]);

  // Grid-step trigger method for the current model. `method` is the
  // EFFECTIVE choice -- forced to the only option when the model has no
  // choice, so a stale selection cannot leak onto a model after a fast
  // switch. `hidden` is the strategy_param that IS the rolling-high
  // window: it moves out of the param grid and into the grid-step panel.
  const trigger = gridTriggerMap[model] ?? GENERIC_GRID_TRIGGER;
  const methodLocked = trigger.methods.length === 1;
  const method: GridTriggerMethod = methodLocked ? trigger.methods[0]! : triggerMethod;
  const windowParam = trigger.window_param;

  const gridStepSweep = sweepFields.grid_step ?? DEFAULT_SWEEP_FIELD_STATE;
  const profitTargetSweep = sweepFields.profit_target ?? DEFAULT_SWEEP_FIELD_STATE;

  const gridSteps = useMemo(
    () =>
      buildGridSteps({
        mode: gridStepSweep.enabled ? "sweep" : "fixed",
        fixedPct: String(gridStep),
        minPct: gridStepSweep.start,
        maxPct: gridStepSweep.end,
        count: gridStepSweep.count,
        strategy: gridStepSweep.strategy,
        seed: gridStepSweep.seed,
      }),
    [gridStep, gridStepSweep],
  );
  const profitSteps = useMemo(
    () =>
      buildGridSteps({
        mode: profitTargetSweep.enabled ? "sweep" : "fixed",
        fixedPct: String(profitTarget),
        minPct: profitTargetSweep.start,
        maxPct: profitTargetSweep.end,
        count: profitTargetSweep.count,
        strategy: profitTargetSweep.strategy,
        seed: profitTargetSweep.seed,
      }),
    [profitTarget, profitTargetSweep],
  );

  const setSweepField = (name: string, next: SweepFieldState) =>
    setSweepFields((current) => ({ ...current, [name]: next }));

  // Every currently-enabled strategy-param sweep's own generated result,
  // so its errors surface the same way grid step/profit target's do and
  // its value count feeds the combinations estimate below.
  const paramSweepResults = useMemo(
    () =>
      specs
        .filter((entry) => entry.sweepable && sweepFields[entry.name]?.enabled)
        .map((entry) => buildParamSweep(entry, sweepFields[entry.name]!)),
    [specs, sweepFields],
  );
  const sweepErrors = [
    ...gridSteps.errors,
    ...profitSteps.errors,
    ...paramSweepResults.flatMap((result) => result.errors),
  ];
  // 1 for a param with no valid sweep yet -- the combinations estimate
  // stays a lower bound rather than momentarily reading 0.
  const totalCombinations =
    Math.max(1, gridSteps.steps.length) *
    Math.max(1, profitSteps.steps.length) *
    paramSweepResults.reduce((product, result) => product * Math.max(1, result.values.length), 1);

  useEffect(() => {
    api
      .funds()
      .then((body) => {
        setFunds(body.funds);
        setModels(body.sizing_models);
        setParamSpecs(body.sizing_params ?? {});
        setGridTriggerMap(body.grid_trigger ?? {});
      })
      .catch((cause: unknown) => {
        setLoadError(
          cause instanceof Error
            ? `${cause.message} — is the API running? uvicorn server.app:app`
            : "could not reach the API",
        );
      });
  }, []);

  // Selecting a different model REPLACES the field set with that model's
  // specs, seeded from their suggested values -- so switching adds the
  // new model's fields and drops the old one's.
  //
  // A per-instrument model (ml_reachability_*) has a LOCKED `ticker`: it
  // only makes sense over that one fund, and `build_config` refuses a
  // run whose funds do not include it. So swap `tickers` to exactly that
  // fund while such a model is selected, and put the prior selection
  // back on the way out -- never silently leave an extra fund the user
  // did not choose (which would double the runtime, or fail if its data
  // is not downloaded).
  const priorTickers = useRef<string[] | null>(null);
  useEffect(() => {
    const seeded = seedValues(specs);
    setParamValues(seeded);
    setValidation(null);
    setShowAdvanced(false);
    // Reconcile the trigger method to the new model: locked models pin
    // their only option; a model whose window param was seeded (a saved
    // report reloaded, or hf's committed lookback_days) preselects
    // local_reference.
    setTriggerMethod(initialTriggerMethod(gridTriggerMap[model] ?? GENERIC_GRID_TRIGGER, seeded));
    // REPLACE the strategy-param slice of sweepFields the same way --
    // grid_step/profit_target are untouched, they are not tied to the
    // model.
    setSweepFields((current) => {
      const next: Record<string, SweepFieldState> = {
        grid_step: current.grid_step ?? DEFAULT_SWEEP_FIELD_STATE,
        profit_target: current.profit_target ?? DEFAULT_SWEEP_FIELD_STATE,
      };
      for (const spec of specs) {
        if (spec.sweepable) next[spec.name] = DEFAULT_SWEEP_FIELD_STATE;
      }
      return next;
    });
    const tickerSpec = specs.find((spec) => spec.name === "ticker" && !spec.editable);
    const requiredFund =
      tickerSpec && typeof tickerSpec.suggested === "string" ? tickerSpec.suggested : null;
    if (requiredFund) {
      setTickers((current) => {
        if (priorTickers.current === null) priorTickers.current = current;
        return [requiredFund];
      });
    } else if (priorTickers.current !== null) {
      setTickers(priorTickers.current);
      priorTickers.current = null;
    }
  }, [specs]);

  useEffect(() => {
    if (!staged) return;
    // One sweep-matrix cell is one step -- drop back to a Fixed value.
    setGridStep(Number((staged.gridStep * 100).toFixed(4)));
    setProfitTarget(Number((staged.profitTarget * 100).toFixed(4)));
    setSweepFields((current) => ({
      ...current,
      grid_step: { ...(current.grid_step ?? DEFAULT_SWEEP_FIELD_STATE), enabled: false },
      profit_target: { ...(current.profit_target ?? DEFAULT_SWEEP_FIELD_STATE), enabled: false },
    }));
  }, [staged]);

  const toggle = (ticker: string) =>
    setTickers((current) =>
      current.includes(ticker)
        ? current.filter((value) => value !== ticker)
        : [...current, ticker],
    );

  // Only the POST itself gates the form -- a PREVIOUSLY submitted run
  // still processing does not. The server already queues a follow-on
  // sweep correctly (server/jobs.py's JobQueue is a real FIFO); this is
  // what actually lets a reader submit one instead of being blocked
  // until the first sweep finishes.
  const busy = submitting;
  const priorRunActive = run?.status === "queued" || run?.status === "running";

  const buildRequest = (): BacktestRunRequest => ({
    ...(name.trim() ? { name: name.trim() } : {}),
    tickers,
    // Percentages in the UI, fractions on the wire. A well-formed list
    // even mid-edit (Run is disabled while gridSteps has errors).
    grid_steps: gridSteps.steps.length > 0 ? gridSteps.steps : [gridStep / 100],
    profit_targets: profitSteps.steps.length > 0 ? profitSteps.steps : [profitTarget / 100],
    sizing_model: model,
    fill_model: fillModel,
    // Built explicitly from the rendered fields -- see buildStrategyParams
    // for exactly which are included. A sweepable field with its
    // checkbox on is sent as a list; a no-edit, no-sweep submit
    // reproduces the model's committed defaults byte-for-byte.
    strategy_params: buildStrategyParams(specs, paramValues, sweepFields),
    limit,
    ...(range.start ? { start: range.start } : {}),
    ...(range.end ? { end: range.end } : {}),
  });

  // Debounced pre-flight: the same build_config the submit path runs,
  // minus the queue. A stale response (model switched while in flight)
  // is dropped via the sequence counter.
  const paramsKey = JSON.stringify(paramValues);
  const stepsKey = JSON.stringify(gridSteps.steps);
  const profitStepsKey = JSON.stringify(profitSteps.steps);
  const sweepFieldsKey = JSON.stringify(sweepFields);
  useEffect(() => {
    const request = buildRequest();
    const seq = ++validateSeq.current;
    const timer = window.setTimeout(() => {
      // A client-invalid sweep (grid step, profit target, or any
      // strategy param) never gets a pre-flight -- clearing validation
      // stops a stale green from showing under a bad field.
      if (sweepErrors.length > 0) {
        setValidation(null);
        return;
      }
      api
        .validateRun(request)
        .then((result) => {
          if (seq === validateSeq.current) setValidation(result);
        })
        .catch(() => {
          /* a failed pre-flight must not block the form; submit still validates */
        });
    }, 400);
    return () => window.clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    model,
    tickers,
    profitTarget,
    fillModel,
    limit,
    range.start,
    range.end,
    paramsKey,
    stepsKey,
    profitStepsKey,
    sweepFieldsKey,
  ]);

  const setParam = (paramName: string, value: string) =>
    setParamValues((current) => ({ ...current, [paramName]: value }));
  const resetParam = (paramName: string) => {
    const spec = specs.find((entry) => entry.name === paramName);
    if (spec) setParam(paramName, spec.suggested == null ? "" : String(spec.suggested));
  };
  const resetAll = () => {
    const seeded = seedValues(specs);
    setParamValues(seeded);
    setTriggerMethod(initialTriggerMethod(trigger, seeded));
    setSweepFields((current) => {
      const next = { ...current };
      for (const spec of specs) {
        if (spec.sweepable) next[spec.name] = DEFAULT_SWEEP_FIELD_STATE;
      }
      return next;
    });
  };

  // Writing the trigger method's window param is the ONLY place the
  // method touches strategy_params -- always via setParam so paramsKey
  // changes and the debounced /validate refires.
  const changeMethod = (next: GridTriggerMethod) => {
    if (windowParam) {
      setParam(
        windowParam,
        next === "local_reference"
          ? (paramValues[windowParam] ?? "").trim() || String(trigger.window_default ?? "")
          : "",
      );
    }
    setTriggerMethod(next);
  };

  // The FULL specs array stays load-bearing for buildStrategyParams /
  // blankRequired / diffFromDefaults; only the RENDER lists drop the
  // window param -- it gets its one editor inside the grid-step panel.
  const blanks = blankRequired(specs, paramValues, sweepFields);
  const diffs = diffFromDefaults(specs, paramValues, sweepFields);
  const primary = specs.filter((spec) => spec.group === "primary" && spec.name !== windowParam);
  const advanced = specs.filter((spec) => spec.group === "advanced" && spec.name !== windowParam);
  // Unattached errors, PLUS any pinned to a field that is not on screen
  // right now (an advanced field while Advanced is collapsed, or the
  // window param when its input is showing in the grid-step panel) --
  // so a disabled Run button always has a visible reason.
  const renderedFields = new Set(
    [...primary, ...(showAdvanced ? advanced : [])].map((spec) => spec.name),
  );
  if (method === "local_reference" && windowParam) renderedFields.add(windowParam);
  const bannerErrors = (validation?.errors ?? []).filter(
    (entry) => entry.field === null || !renderedFields.has(entry.field),
  );
  // `0.7 / 100` is `0.006999999999999999`; show a clean number, keep the
  // exact float on the wire.
  const cleanNumber = (value: number): string => String(Number(value.toFixed(10)));
  const mirroredTarget = cleanNumber(profitTarget / 100);
  const alignedNoteFor = (paramName: string): string | undefined => {
    const value = validation?.aligned?.[paramName];
    if (value == null) return undefined;
    return typeof value === "number" ? cleanNumber(value) : String(value);
  };

  // A sweepable spec gets the checkbox-and-dropdown treatment; every
  // other spec (locked, mirrored, or non-numeric) renders exactly as
  // before -- ParamField is otherwise untouched by this feature.
  const renderParamField = (spec: ParamSpec) =>
    spec.sweepable ? (
      <SweepableParamField
        key={spec.name}
        spec={spec}
        value={paramValues[spec.name] ?? ""}
        onChange={setParam}
        onReset={resetParam}
        sweep={sweepFields[spec.name] ?? DEFAULT_SWEEP_FIELD_STATE}
        onSweepChange={setSweepField}
        errors={paramErrorsFor(spec.name, validation?.errors)}
        disabled={busy}
      />
    ) : (
      <ParamField
        key={spec.name}
        spec={spec}
        value={paramValues[spec.name] ?? ""}
        onChange={setParam}
        onReset={resetParam}
        errors={paramErrorsFor(spec.name, validation?.errors)}
        disabled={busy}
        mirroredValue={spec.mirrors === "profit_target" ? mirroredTarget : undefined}
        alignedNote={spec.mirrors === "profit_target" ? alignedNoteFor(spec.name) : undefined}
      />
    );

  const submit = () => onSubmit(buildRequest());

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <div>
          <CardTitle className="flex items-center gap-2">
            <Play className="size-4" />
            Run a backtest
          </CardTitle>
          <p className="mt-1 text-xs text-muted-foreground">
            Queued on the server. A full ten-year run is roughly 23 seconds per
            configuration.
            {range.start || range.end
              ? ` Windowed to ${range.start ?? "start"} – ${range.end ?? "end"} from the Backtest result filters.`
              : ""}
          </p>
        </div>
        {run ? <RunStatus run={run} /> : null}
      </CardHeader>

      <CardContent className="flex flex-wrap items-end gap-4">
        <Field label="Name">
          <Input
            type="text"
            className="w-48"
            placeholder="optional — labels this sweep"
            maxLength={120}
            value={name}
            disabled={busy}
            onChange={(event) => setName(event.currentTarget.value)}
          />
        </Field>

        <div className="flex flex-col gap-1.5">
          <span className="text-xs font-medium text-muted-foreground">Funds</span>
          <div className="flex flex-wrap gap-1.5">
            {funds.map((fund) => (
              <button
                key={fund.ticker}
                type="button"
                disabled={!fund.available || busy}
                onClick={() => toggle(fund.ticker)}
                title={fund.available ? fund.path : "not downloaded — see cli.py fetch-data"}
                className={
                  "rounded-md border px-2 py-1 text-xs transition-colors disabled:opacity-40 " +
                  (tickers.includes(fund.ticker)
                    ? "border-primary bg-primary text-primary-foreground"
                    : "border-border hover:bg-accent")
                }
              >
                {fund.ticker}
              </button>
            ))}
            {funds.length === 0 && !loadError ? (
              <span className="text-xs text-muted-foreground">loading…</span>
            ) : null}
          </div>
        </div>

        <GridStepPanel
          gridStep={gridStep}
          onGridStepChange={setGridStep}
          sweep={gridStepSweep}
          onSweepChange={(next) => setSweepField("grid_step", next)}
          gridSteps={gridSteps}
          trigger={trigger}
          method={method}
          onMethodChange={changeMethod}
          windowValue={windowParam ? (paramValues[windowParam] ?? "") : ""}
          onWindowChange={(value) => windowParam && setParam(windowParam, value)}
          windowErrors={windowParam ? paramErrorsFor(windowParam, validation?.errors) : []}
          disabled={busy}
        />

        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-muted-foreground">Profit target %</span>
            <label className="flex items-center gap-1 text-xs text-muted-foreground">
              <Checkbox
                data-testid="profit-target-sweep"
                checked={profitTargetSweep.enabled}
                disabled={busy}
                onChange={(event) =>
                  setSweepField("profit_target", { ...profitTargetSweep, enabled: event.currentTarget.checked })
                }
              />
              Sweep
            </label>
          </div>
          {profitTargetSweep.enabled ? (
            <SweepControls
              label="Profit Target %"
              state={profitTargetSweep}
              onChange={(next) => setSweepField("profit_target", next)}
              disabled={busy}
            />
          ) : (
            <Input
              type="number"
              step="0.05"
              min="0.01"
              className="w-24"
              value={profitTarget}
              disabled={busy}
              onChange={(event) => setProfitTarget(Number(event.currentTarget.value))}
            />
          )}
          {profitSteps.errors.map((error, index) => (
            <p key={index} className="text-[11px] leading-tight text-loss">
              {error}
            </p>
          ))}
        </div>

        <Field label="Sizing model">
          <Select
            data-testid="sizing-model"
            value={model}
            disabled={busy}
            onChange={(event) => setModel(event.currentTarget.value)}
          >
            {models.map((entry) => (
              <option key={entry} value={entry}>
                {entry}
              </option>
            ))}
          </Select>
        </Field>

        <Field label="Fill model">
          <Select
            value={fillModel}
            disabled={busy}
            onChange={(event) => setFillModel(event.currentTarget.value as "close" | "intrabar")}
          >
            <option value="close">close</option>
            <option value="intrabar">intrabar</option>
          </Select>
        </Field>

        <Field label="Bars">
          <Select
            data-testid="bars"
            value={String(limit)}
            disabled={busy}
            onChange={(event) => setLimit(Number(event.currentTarget.value))}
          >
            <option value="20000">20k (fast)</option>
            <option value="50000">50k</option>
            <option value="200000">200k</option>
            <option value="2000000">everything (slow)</option>
          </Select>
        </Field>

        <Button
          data-testid="run"
          onClick={submit}
          disabled={
            busy ||
            tickers.length === 0 ||
            blanks.length > 0 ||
            validation?.ok === false ||
            sweepErrors.length > 0 ||
            totalCombinations > MAX_SWEEP_COMBINATIONS ||
            (method === "local_reference" &&
              windowParam !== null &&
              ((paramValues[windowParam] ?? "").trim() === "" ||
                Number(paramValues[windowParam]) <= 0))
          }
        >
          {busy ? "Running…" : "Run"}
        </Button>
      </CardContent>

      {priorRunActive ? (
        <CardContent className="pt-0">
          <p className="text-xs text-muted-foreground">
            A previous sweep is still processing — this one will queue behind it. See Active
            runs below for the queue.
          </p>
        </CardContent>
      ) : null}

      {specs.length > 0 ? (
        <CardContent className="flex flex-col gap-3 pt-0">
          <div className="flex flex-wrap items-start gap-4">{primary.map(renderParamField)}</div>

          {advanced.length > 0 ? (
            <div>
              <button
                type="button"
                onClick={() => setShowAdvanced((value) => !value)}
                className="text-xs font-medium text-muted-foreground hover:text-foreground"
              >
                {showAdvanced ? "▾" : "▸"} Advanced parameters ({advanced.length})
              </button>
              {showAdvanced ? (
                <div className="mt-2 flex flex-wrap items-start gap-4">
                  {advanced.map(renderParamField)}
                </div>
              ) : null}
            </div>
          ) : null}

          <p className="text-xs text-muted-foreground">
            {diffs.length === 0 ? (
              <>
                <span className="text-foreground">{model}</span> — matches this project's
                committed defaults.
              </>
            ) : (
              <>
                <span className="text-foreground">{diffs.length}</span> changed from committed
                defaults:{" "}
                {diffs.map((diff) => `${diff.name} ${diff.from}→${diff.to}`).join(", ")}
                {" · "}
                <button
                  type="button"
                  className="underline hover:text-foreground"
                  onClick={resetAll}
                >
                  reset all
                </button>
              </>
            )}
          </p>

          {totalCombinations > 1 ? (
            <p
              className={
                totalCombinations > MAX_SWEEP_COMBINATIONS
                  ? "text-[11px] leading-tight text-loss"
                  : "text-[11px] leading-tight text-muted-foreground"
              }
            >
              {totalCombinations} configurations across every enabled sweep
              {totalCombinations > MAX_SWEEP_COMBINATIONS
                ? ` — exceeds the ${MAX_SWEEP_COMBINATIONS} limit for one submission; narrow a swept range.`
                : "."}
            </p>
          ) : null}

          {validation?.degraded ? (
            <p className="text-[11px] text-muted-foreground">
              Live pre-flight validation is unavailable on this server — parameters are
              checked when you press Run.
            </p>
          ) : null}
        </CardContent>
      ) : null}

      {/* Only COWZ showed a measured, fold-consistent lift over the
          bar-only baseline (Model research tab). RSP and SPYD are offered
          to test against, not because they are proven. */}
      {model.startsWith("ml_reachability") ? (
        <CardContent className="pt-0">
          <p className="text-xs text-muted-foreground">
            Research strategy, backtest-only —{" "}
            <span className="text-foreground">
              only {model === "ml_reachability_cowz" ? "this fund" : "COWZ"}
            </span>{" "}
            has shown a measured, fold-consistent edge over the bar-only baseline (see the{" "}
            <span className="text-foreground">Model research</span> tab); the others are here to
            test against, not because they are proven. It also runs roughly 25x slower than this
            project's other strategies — a per-bar model call, not a per-trade one — so a full
            run is minutes, not seconds.
          </p>
        </CardContent>
      ) : null}

      {/* intrabar fills a level TOUCHED during a bar rather than requiring
          the close to reach it -- roughly 1.85x more fills on both sides. */}
      {fillModel === "intrabar" ? (
        <CardContent className="pt-0">
          <p className="text-xs text-muted-foreground">
            Intrabar fills a level touched during the bar — roughly 1.85x more fills than
            “close” on this project's own minute data. Not comparable with a close-model run.
          </p>
        </CardContent>
      ) : null}

      {error || loadError || bannerErrors.length > 0 ? (
        <CardContent className="space-y-1 pt-0">
          {(error ?? loadError) ? (
            <p className="flex items-start gap-2 text-xs text-loss">
              <AlertCircle className="mt-0.5 size-3.5 shrink-0" />
              {error ?? loadError}
            </p>
          ) : null}
          {bannerErrors.map((entry, index) => (
            <p key={index} className="flex items-start gap-2 text-xs text-loss">
              <AlertCircle className="mt-0.5 size-3.5 shrink-0" />
              {entry.message}
            </p>
          ))}
        </CardContent>
      ) : null}
    </Card>
  );
}

function RunStatus({ run }: { run: BacktestRunState }) {
  const tone =
    run.status === "failed" ? "loss" : run.status === "complete" ? "profit" : "stuck";
  return (
    <div className="flex items-center gap-3">
      {run.status === "running" ? (
        <div className="h-1 w-28 overflow-hidden rounded-full bg-secondary">
          <div
            className="h-full bg-primary transition-all"
            style={{ width: `${Math.round(run.progress * 100)}%` }}
          />
        </div>
      ) : null}
      <Badge tone={tone}>{run.message ?? run.status}</Badge>
    </div>
  );
}
