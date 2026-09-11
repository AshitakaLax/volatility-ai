import { Input, Select } from "@/components/ui/primitives";
import {
  MAX_SWEEP_POINTS,
  UNIMPLEMENTED_SWEEP_STRATEGIES,
  type SweepFieldState,
  type SweepStrategyKind,
} from "@/lib/sweepStrategies";

/**
 * The "Sweep strategy" dropdown + that strategy's own range inputs --
 * shared by GridStepPanel (grid step, profit target) and
 * SweepableParamField (arbitrary numeric strategy params) so this
 * markup exists exactly once.
 *
 * Module-scope, same reasoning as ParamField/GridStepPanel: redefined
 * inside a parent on every render, it would remount and drop focus
 * mid-keystroke.
 */

const STRATEGY_ORDER: SweepStrategyKind[] = [
  "linear",
  "logarithmic",
  "random",
  "multi_resolution",
  "adaptive",
];

const STRATEGY_LABEL: Record<SweepStrategyKind, string> = {
  linear: "Linear sweep",
  logarithmic: "Logarithmic",
  random: "Random / Monte Carlo",
  multi_resolution: "Multi-Resolution / coarse-to-fine (coming soon)",
  adaptive: "Adaptive / Heuristic (coming soon)",
};

interface Props {
  /** What a bound is a bound OF -- e.g. "Grid Step %", or a strategy
   * param's own name (e.g. "max_trade_pct"). Used to build the
   * Starting/Ending/Min/Max placeholders. */
  label: string;
  state: SweepFieldState;
  onChange: (next: SweepFieldState) => void;
  disabled: boolean;
}

export function SweepControls({ label, state, onChange, disabled }: Props) {
  const set = (patch: Partial<SweepFieldState>) => onChange({ ...state, ...patch });

  return (
    <div className="flex flex-col gap-2">
      <Select
        data-testid="sweep-strategy"
        className="w-full"
        value={state.strategy}
        disabled={disabled}
        onChange={(event) => set({ strategy: event.currentTarget.value as SweepStrategyKind })}
      >
        {STRATEGY_ORDER.map((strategy) => (
          <option
            key={strategy}
            value={strategy}
            disabled={UNIMPLEMENTED_SWEEP_STRATEGIES.includes(strategy)}
          >
            {STRATEGY_LABEL[strategy]}
          </option>
        ))}
      </Select>

      {state.strategy === "random" ? (
        <div className="flex items-center gap-2">
          <Input
            type="number"
            step="any"
            placeholder={`min ${label}`}
            className="w-20"
            value={state.start}
            disabled={disabled}
            onChange={(event) => set({ start: event.currentTarget.value })}
          />
          <span className="text-muted-foreground">–</span>
          <Input
            type="number"
            step="any"
            placeholder={`max ${label}`}
            className="w-20"
            value={state.end}
            disabled={disabled}
            onChange={(event) => set({ end: event.currentTarget.value })}
          />
          <Input
            type="number"
            step="1"
            min="1"
            max={MAX_SWEEP_POINTS}
            placeholder="n"
            className="w-16"
            value={state.count}
            disabled={disabled}
            onChange={(event) => set({ count: event.currentTarget.value })}
          />
          <Input
            type="text"
            placeholder="seed (optional)"
            className="w-28"
            value={state.seed}
            disabled={disabled}
            onChange={(event) => set({ seed: event.currentTarget.value })}
          />
        </div>
      ) : (
        <div className="flex items-center gap-2">
          <Input
            type="number"
            step="any"
            placeholder={`starting ${label}`}
            className="w-24"
            value={state.start}
            disabled={disabled}
            onChange={(event) => set({ start: event.currentTarget.value })}
          />
          <span className="text-muted-foreground">–</span>
          <Input
            type="number"
            step="any"
            placeholder={`ending ${label}`}
            className="w-24"
            value={state.end}
            disabled={disabled}
            onChange={(event) => set({ end: event.currentTarget.value })}
          />
          <Input
            type="number"
            step="1"
            min="1"
            max={MAX_SWEEP_POINTS}
            placeholder="n"
            className="w-16"
            value={state.count}
            disabled={disabled}
            onChange={(event) => set({ count: event.currentTarget.value })}
          />
        </div>
      )}
    </div>
  );
}
