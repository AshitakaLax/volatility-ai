import { Activity, TriangleAlert } from "lucide-react";
import { useEffect, useState } from "react";

import { Badge, Card, CardContent, CardHeader, CardTitle } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import { cn, pct, usd } from "@/lib/utils";
import type { DeploymentState, IndicatorReading } from "@/types/telemetry";

/**
 * What the loop is doing, and what it was told to do.
 *
 * THE PARAMETERS ARE THE POINT. The store used to hold cash, lots and a
 * halt, but nothing about the configuration that produced them -- so a
 * reader could see a book of lots sitting at a 30% target without being
 * able to tell whether that was the intent or a misplaced decimal. It
 * was a misplaced decimal, and finding it took a config file and a
 * ledger side by side. Now the loop writes its own parameters through on
 * every tick and they are the first thing on this card.
 *
 * A profit target far from its configured range is flagged rather than
 * merely displayed, because the failure mode is not "wrong number on a
 * screen" -- it is capital committed at a target the market will not
 * reach for years.
 */

interface Props {
  state: DeploymentState | null;
}

// The paper config's own target is 0.3%. An order of magnitude either
// side of a plausible grid target is worth a second look, not a verdict:
// wide targets are a legitimate strategy, just not this one's default.
const IMPLAUSIBLE_TARGET = 0.05;

export function AlgorithmStatus({ state }: Props) {
  const [reading, setReading] = useState<IndicatorReading | null>(null);
  const symbol = state?.parameters.symbol ?? null;

  useEffect(() => {
    if (!symbol) {
      setReading(null);
      return;
    }
    let cancelled = false;
    api
      .indicators(symbol)
      .then((next) => {
        if (!cancelled) setReading(next);
      })
      .catch(() => {
        if (!cancelled) setReading(null);
      });
    return () => {
      cancelled = true;
    };
  }, [symbol, state?.revision]);

  const parameters = state?.parameters ?? {};
  const known = Object.keys(parameters).length > 0;
  const target = parameters.profit_target;
  const suspicious = target !== undefined && target > IMPLAUSIBLE_TARGET;

  // Exposure as a share of equity. Equity is cash plus the marked book,
  // which is what the loop itself uses -- not cash alone, which would
  // read as over-invested the moment anything is held.
  const committed = (state?.lots ?? []).reduce(
    (total, lot) => total + (lot.current_value ?? 0),
    0,
  );
  const equity = (state?.cash ?? 0) + committed;
  const allocation = equity > 0 ? (committed / equity) * 100 : null;

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <Activity className="size-4" />
          Algorithm status
        </CardTitle>
        <div className="flex items-center gap-2">
          {parameters.paper === false ? (
            <Badge tone="loss">LIVE CAPITAL</Badge>
          ) : parameters.paper ? (
            <Badge tone="profit">paper</Badge>
          ) : null}
          {parameters.extended_hours ? <Badge>extended hours</Badge> : null}
        </div>
      </CardHeader>

      <CardContent className="grid grid-cols-2 gap-5 sm:grid-cols-3 lg:grid-cols-6">
        <Stat label="Symbol" value={parameters.symbol ?? "--"} />
        <Stat label="Price" value={usd(state?.last_price)} />
        <Stat
          label={`RSI(${reading?.rsi_period ?? 14})`}
          value={reading?.rsi === null || reading?.rsi === undefined ? "--" : reading.rsi.toFixed(1)}
          hint={
            reading?.rsi === null
              ? "warming up"
              : reading?.rsi !== undefined
                ? reading.rsi < 30
                  ? "oversold"
                  : reading.rsi > 70
                    ? "overbought"
                    : undefined
                : undefined
          }
          tone={
            reading?.rsi === undefined || reading?.rsi === null
              ? undefined
              : reading.rsi < 30
                ? "profit"
                : reading.rsi > 70
                  ? "loss"
                  : undefined
          }
        />
        <Stat
          label="Grid step"
          value={parameters.step === undefined ? "--" : pct(parameters.step * 100, 3)}
        />
        <Stat
          label="Profit target"
          value={target === undefined ? "--" : pct(target * 100, 3)}
          tone={suspicious ? "loss" : undefined}
        />
        <Stat
          label="Allocation"
          value={allocation === null ? "--" : pct(allocation, 1)}
          hint={`${state?.lots.length ?? 0} lots · ${usd(committed, 0)}`}
        />
      </CardContent>

      {!known ? (
        <CardContent className="pt-0">
          <p className="text-xs text-muted-foreground">
            This store predates the loop recording its own parameters, so the configuration
            is unknown rather than absent. It will appear after the next tick of a current
            build.
          </p>
        </CardContent>
      ) : null}

      {suspicious ? (
        <CardContent className="pt-0">
          <p className="flex items-start gap-2 text-xs text-loss">
            <TriangleAlert className="mt-0.5 size-3.5 shrink-0" />
            A {pct((target ?? 0) * 100, 2)} profit target is far wider than this project's
            configurations use. Check it is not a decimal place — a target the market will
            not reach leaves capital committed indefinitely.
          </p>
        </CardContent>
      ) : null}

      {reading ? (
        <CardContent className="pt-0">
          {/* The bars are a FILE, not the loop's own feed. Saying so is
              cheaper than someone discovering it during a fast market. */}
          <p className="text-xs text-muted-foreground">
            RSI from {reading.bars_used} bars of {reading.source.split(/[\\/]/).pop()} — a
            data file, which can lag the loop's own feed.
          </p>
        </CardContent>
      ) : null}
    </Card>
  );
}

function Stat({
  label,
  value,
  hint,
  tone,
}: {
  label: string;
  value: string;
  hint?: string | undefined;
  tone?: "profit" | "loss" | undefined;
}) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span
        className={cn(
          "tnum text-lg font-semibold",
          tone === "profit" && "text-profit",
          tone === "loss" && "text-loss",
        )}
      >
        {value}
      </span>
      {hint ? <span className="text-xs text-muted-foreground">{hint}</span> : null}
    </div>
  );
}
