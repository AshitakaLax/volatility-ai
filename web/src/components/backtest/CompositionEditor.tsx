import { AlertTriangle, ArrowDownRight, ArrowUpRight } from "lucide-react";
import { useMemo, useState } from "react";

import { ParamField } from "@/components/backtest/ParamField";
import { Badge, Input } from "@/components/ui/primitives";
import {
  cellCount,
  lossCapable,
  setValue,
  specsFor,
  toggle,
  type ChosenPolicy,
  type CompositionState,
  type Side,
} from "@/lib/composition";
import { paramErrorsFor } from "@/lib/strategyParams";
import type { Composition, ParamSpec, ValidateError } from "@/types/backtest";

/**
 * The `composed` model's editor: a buy algorithm and a sell algorithm, chosen
 * independently (research/composition/ on the server). Tick several on
 * either side and the run is the buy x sell MATRIX -- every pairing, each
 * as its own configuration, compared in the result's heatmap.
 *
 * Sell algorithms that may sell below cost (signal exits) are listed by
 * default and MARKED: a badge on the option and a warning while one is
 * chosen (owner, Oct 31). The server runs them with signal exits on; a live
 * deployment still refuses them without execution.allow_signal_exit in its
 * own file.
 */

interface Props {
  composition: Composition;
  state: CompositionState;
  onChange: (next: CompositionState) => void;
  errors: ValidateError[];
  disabled: boolean;
  /** One buy and one sell (a live deployment trades a pairing, not a matrix). */
  single?: boolean;
}

export function CompositionEditor({ composition, state, onChange, errors, disabled, single = false }: Props) {
  const losses = lossCapable(state, composition);
  const cells = cellCount(state);
  return (
    <div className="flex w-full flex-col gap-3" data-testid="composition-editor">
      <div className="grid gap-4 lg:grid-cols-2">
        <PolicyColumn
          side="buy"
          title="Buy algorithms — when and how much to buy"
          ids={Object.keys(composition.buys).sort()}
          composition={composition}
          state={state}
          onChange={onChange}
          errors={errors}
          disabled={disabled}
          single={single}
        />
        <PolicyColumn
          side="sell"
          title="Sell algorithms — when and how much to sell"
          ids={Object.keys(composition.sells).sort()}
          composition={composition}
          state={state}
          onChange={onChange}
          errors={errors}
          disabled={disabled}
          single={single}
        />
      </div>
      {single ? null : (
      <p className="text-xs text-muted-foreground">
        {state.buys.length} buy × {state.sells.length} sell ={" "}
        <span className="text-foreground">{cells}</span> pairing{cells === 1 ? "" : "s"}
        {cells > 1 ? ", each run as its own configuration and compared in the result's matrix." : "."}
      </p>
      )}
      {losses.length > 0 ? (
        <p
          className="flex items-start gap-2 rounded-md border border-loss/40 bg-loss/10 px-3 py-2 text-xs text-loss"
          data-testid="loss-warning"
        >
          <AlertTriangle className="mt-0.5 size-3.5 shrink-0" />
          <span>
            {losses.join(", ")} may sell below cost: {losses.length === 1 ? "it exits" : "they exit"} on
            a signal, not a price, and can realise a loss. The backtest runs with signal exits on; a live
            deployment trades it only if its own config sets execution.allow_signal_exit.
          </span>
        </p>
      ) : null}
    </div>
  );
}

function PolicyColumn({
  side,
  title,
  ids,
  composition,
  state,
  onChange,
  errors,
  disabled,
  single,
}: {
  side: Side;
  title: string;
  ids: string[];
  composition: Composition;
  state: CompositionState;
  onChange: (next: CompositionState) => void;
  errors: ValidateError[];
  disabled: boolean;
  single: boolean;
}) {
  const [filter, setFilter] = useState("");
  const chosen = side === "buy" ? state.buys : state.sells;
  const chosenIds = new Set(chosen.map((policy) => policy.id));
  const shown = ids.filter((id) => id.toLowerCase().includes(filter.trim().toLowerCase()));
  const Icon = side === "buy" ? ArrowDownRight : ArrowUpRight;
  return (
    <div className="flex flex-col gap-2 rounded-md border border-border p-3" data-testid={`${side}-policies`}>
      <span className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
        <Icon className="size-3.5" />
        {title}
      </span>
      <Input
        type="search"
        placeholder={`filter ${ids.length} ${side} algorithms`}
        value={filter}
        disabled={disabled}
        onChange={(event) => setFilter(event.currentTarget.value)}
      />
      <div className="flex max-h-40 flex-wrap gap-1.5 overflow-y-auto">
        {shown.map((id) => {
          const sell = side === "sell" ? composition.sells[id] : undefined;
          const on = chosenIds.has(id);
          return (
            <button
              key={id}
              type="button"
              disabled={disabled}
              data-testid={`${side}-${id}`}
              onClick={() => onChange(toggle(state, composition, side, id, single))}
              title={sell?.label ?? id}
              className={
                "flex items-center gap-1 rounded-md border px-2 py-1 text-xs transition-colors disabled:opacity-40 " +
                (on ? "border-primary bg-primary text-primary-foreground" : "border-border hover:bg-accent")
              }
            >
              {id}
              {sell?.loss ? (
                <Badge tone="loss" className="px-1.5 py-0 text-[10px]" title="may sell below cost">
                  may sell below cost
                </Badge>
              ) : null}
              {sell?.partial ? (
                <Badge tone="stuck" className="px-1.5 py-0 text-[10px]" title="sells lots in parts">
                  partial
                </Badge>
              ) : null}
            </button>
          );
        })}
      </div>
      {chosen.length === 0 ? (
        <p className="text-[11px] text-loss">Choose at least one {side} algorithm.</p>
      ) : null}
      {paramErrorsFor(side, errors).map((error, index) => (
        <p key={index} className="text-[11px] leading-tight text-loss">
          {error.msg}
        </p>
      ))}
      {chosen.map((policy) => (
        <PolicyFields
          key={policy.id}
          side={side}
          policy={policy}
          specs={specsFor(composition, side, policy.id)}
          state={state}
          onChange={onChange}
          disabled={disabled}
        />
      ))}
    </div>
  );
}

function PolicyFields({
  side,
  policy,
  specs,
  state,
  onChange,
  disabled,
}: {
  side: Side;
  policy: ChosenPolicy;
  specs: ParamSpec[];
  state: CompositionState;
  onChange: (next: CompositionState) => void;
  disabled: boolean;
}) {
  const [advanced, setAdvanced] = useState(false);
  const primary = useMemo(() => specs.filter((spec) => spec.group === "primary"), [specs]);
  const rest = useMemo(() => specs.filter((spec) => spec.group === "advanced"), [specs]);
  const set = (name: string, value: string) => onChange(setValue(state, side, policy.id, name, value));
  const reset = (name: string) => {
    const spec = specs.find((entry) => entry.name === name);
    if (spec) set(name, spec.suggested == null ? "" : String(spec.suggested));
  };
  const field = (spec: ParamSpec) => (
    <ParamField
      key={spec.name}
      spec={spec}
      value={policy.values[spec.name] ?? ""}
      onChange={set}
      onReset={reset}
      errors={[]}
      disabled={disabled}
    />
  );
  return (
    <div className="flex flex-col gap-2 border-t border-border pt-2">
      <span className="text-xs text-foreground">{policy.id}</span>
      {specs.length === 0 ? (
        <span className="text-[11px] text-muted-foreground">no parameters</span>
      ) : (
        <div className="flex flex-wrap items-start gap-3">{primary.map(field)}</div>
      )}
      {rest.length > 0 ? (
        <div>
          <button
            type="button"
            onClick={() => setAdvanced((value) => !value)}
            className="text-[11px] font-medium text-muted-foreground hover:text-foreground"
          >
            {advanced ? "▾" : "▸"} Advanced ({rest.length})
          </button>
          {advanced ? <div className="mt-2 flex flex-wrap items-start gap-3">{rest.map(field)}</div> : null}
        </div>
      ) : null}
    </div>
  );
}
