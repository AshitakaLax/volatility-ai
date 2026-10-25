import { Gauge } from "lucide-react";

import { Badge, Card, CardContent, CardHeader, CardTitle } from "@/components/ui/primitives";
import {
  algorithmName,
  algorithmOrigin,
  algorithmWords,
  nowLine,
  position,
  regimeLine,
  shadowLine,
  tradeTotals,
  type Line,
} from "@/lib/control";
import { cn, usd } from "@/lib/utils";
import type { DeploymentDetail, TraderFill } from "@/types/control";
import type { LiveState } from "@/types/telemetry";

/**
 * The selected deployment at a glance: the fund it trades and its price,
 * what it holds and what that is worth, what it did today -- and, in the
 * trader's own terms, what it will do next and why. "Why is it not buying?"
 * is the question this card exists to answer without a log: the trader
 * reports the price its next buy triggers at, or what blocks one, every
 * tick (engine/trading/live_trading_loop.py, WHAT IT SAYS ABOUT ITSELF).
 *
 * The fund is the deployment's: a switch changes the algorithm, never the
 * symbol, because lots of the old fund would be left with no loop to sell
 * them.
 */
interface Props {
  deployment: DeploymentDetail;
  state: LiveState | null;
  /** Today's fills from the trader's journal; null while loading. */
  fills: TraderFill[] | null;
}

const TONE_TEXT: Record<Line["tone"], string> = {
  neutral: "text-muted-foreground",
  profit: "text-profit",
  loss: "text-loss",
  stuck: "text-stuck",
};

function time(iso: string | null | undefined): string {
  return iso ? new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "--";
}

export function OverviewCard({ deployment, state, fills }: Props) {
  const book = position(state);
  const today = tradeTotals(fills ?? []);
  const status = deployment.status;
  const algorithm = deployment.algorithm;
  const now = nowLine(deployment);
  const regime = regimeLine(status?.now?.strategy);
  const revert = shadowLine(deployment);
  const cash = status && !status.stale && status.cash != null ? status.cash : state?.cash;

  return (
    <Card>
      <CardHeader className="flex-row flex-wrap items-center justify-between gap-2">
        <CardTitle className="flex items-center gap-2">
          <Gauge className="size-4" />
          <span className="text-lg">{deployment.symbol ?? "--"}</span>
          <span className="text-sm font-normal text-muted-foreground">· {deployment.label}</span>
        </CardTitle>
        <div className="flex flex-wrap items-center gap-2">
          <Badge>{deployment.broker === "fidelity" ? "Fidelity · browser extension" : "Alpaca"}</Badge>
          {deployment.paper === false ? (
            <Badge tone="loss">real money</Badge>
          ) : deployment.paper ? (
            <Badge tone="profit">paper</Badge>
          ) : null}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
          <Stat
            label="Price"
            value={usd(state?.last_px)}
            hint={state?.last_tick ? `last tick ${time(state.last_tick)}` : "no tick yet"}
          />
          <Stat
            label="Holding"
            value={book.lots ? `${book.shares.toFixed(book.shares < 10 ? 3 : 1)} sh` : "nothing"}
            hint={`${book.lots} lot${book.lots === 1 ? "" : "s"}${
              book.average !== null ? ` · avg ${usd(book.average)}` : ""
            }`}
          />
          <Stat
            label="Market value"
            value={book.lots ? usd(book.value, 0) : "--"}
            hint={book.lots ? `cost ${usd(book.cost, 0)}` : undefined}
          />
          <Stat
            label="Open P&L"
            value={book.unrealized === null || !book.lots ? "--" : usd(book.unrealized)}
            tone={
              book.unrealized === null || !book.lots
                ? undefined
                : book.unrealized >= 0
                  ? "profit"
                  : "loss"
            }
          />
          <Stat label="Cash" value={usd(cash, 0)} />
          <Stat
            label="Today"
            value={fills === null ? "--" : `${today.buys} buys · ${today.sells} sells`}
            hint={fills === null ? undefined : `realised ${usd(today.realized)}`}
            tone={today.realized > 0 ? "profit" : today.realized < 0 ? "loss" : undefined}
          />
        </div>

        {algorithm ? (
          <p className="text-sm">
            <span className="text-muted-foreground">Trading </span>
            <span className="font-medium">{algorithmName(algorithm)}</span>
            <span className="text-muted-foreground">
              {" "}
              -- {algorithmWords(algorithm)}. {capital(algorithmOrigin(algorithm))}
              {algorithm.changed_at ? `, ${new Date(algorithm.changed_at).toLocaleString()}` : ""}.
            </span>
          </p>
        ) : null}

        {now || regime || revert ? (
          <div className="space-y-1 rounded-md border border-border bg-secondary/30 p-3 text-sm">
            {now ? <p className={TONE_TEXT[now.tone]}>{now.text}</p> : null}
            {regime ? <p className="text-muted-foreground">{regime}</p> : null}
            {revert ? <p className={TONE_TEXT[revert.tone]}>{revert.text}</p> : null}
          </div>
        ) : null}

        <p className="text-xs text-muted-foreground">
          The fund is fixed per deployment: a switch changes the algorithm, never the symbol.
          Another fund is another deployment, with its own config, ledger and account.
        </p>
      </CardContent>
    </Card>
  );
}

function capital(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1);
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
