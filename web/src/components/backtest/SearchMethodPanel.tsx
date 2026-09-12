import { Field, Input, Select } from "@/components/ui/primitives";
import {
  MAX_TRIALS,
  MIN_TRIALS,
  RANK_BY_OPTIONS,
  type SearchMethodState,
} from "@/lib/searchMethod";

/**
 * "Search method": grid (exhaustive) vs. bayesian (Optuna TPE, a trial
 * budget over the same combination space). Rendered only where a
 * submission actually sweeps more than one combination -- ParameterForm
 * decides that, this component just draws the fields.
 *
 * Module-scope, same reasoning as every other field component here: one
 * defined inside a parent re-renders and drops focus mid-keystroke.
 */

interface Props {
  state: SearchMethodState;
  onChange: (next: SearchMethodState) => void;
  /** For the helper line under the trial-budget input -- "N of M
   * possible combinations", so a trial budget reads as a fraction of
   * something concrete rather than a bare number. */
  totalCombinations: number;
  errors: string[];
  disabled: boolean;
}

export function SearchMethodPanel({ state, onChange, totalCombinations, errors, disabled }: Props) {
  const set = (patch: Partial<SearchMethodState>) => onChange({ ...state, ...patch });

  return (
    <div className="flex flex-col gap-2">
      <span className="text-xs font-medium text-muted-foreground">Search method</span>
      <Select
        data-testid="search-method"
        className="w-56"
        value={state.strategy}
        disabled={disabled}
        onChange={(event) => set({ strategy: event.currentTarget.value as SearchMethodState["strategy"] })}
      >
        <option value="grid">Grid (exhaustive)</option>
        <option value="bayesian">Bayesian (Optuna)</option>
      </Select>

      {state.strategy === "bayesian" ? (
        <div className="flex flex-col gap-2 rounded-md border border-border p-2">
          <div className="flex flex-wrap items-end gap-3">
            <Field label="Trial budget">
              <Input
                type="number"
                step="1"
                min={MIN_TRIALS}
                max={MAX_TRIALS}
                placeholder={`${MIN_TRIALS}-${MAX_TRIALS}`}
                className="w-24"
                value={state.nTrials}
                disabled={disabled}
                onChange={(event) => set({ nTrials: event.currentTarget.value })}
              />
            </Field>
            <Field label="Rank by">
              <Select
                className="w-48"
                value={state.rankBy}
                disabled={disabled}
                onChange={(event) => set({ rankBy: event.currentTarget.value })}
              >
                {RANK_BY_OPTIONS.map((column) => (
                  <option key={column} value={column}>
                    {column}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Direction">
              <Select
                className="w-32"
                value={state.direction}
                disabled={disabled}
                onChange={(event) =>
                  set({ direction: event.currentTarget.value as SearchMethodState["direction"] })
                }
              >
                <option value="maximize">Maximize</option>
                <option value="minimize">Minimize</option>
              </Select>
            </Field>
            <Field label="Seed">
              <Input
                type="text"
                placeholder="random"
                className="w-24"
                value={state.seed}
                disabled={disabled}
                onChange={(event) => set({ seed: event.currentTarget.value })}
              />
            </Field>
          </div>
          <p className="text-[11px] leading-tight text-muted-foreground">
            {totalCombinations > 1
              ? `Samples the requested trial budget out of ${totalCombinations} possible combinations, guided by Optuna's TPE sampler -- not every combination runs.`
              : "Enable a Sweep checkbox above, or a grid step/profit target sweep, to give Optuna a space to search."}
          </p>
          {errors.map((error, index) => (
            <span key={index} className="text-[11px] leading-tight text-loss">
              {error}
            </span>
          ))}
        </div>
      ) : null}
    </div>
  );
}
