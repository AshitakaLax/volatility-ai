import { Ban, OctagonX, ShieldCheck } from "lucide-react";
import { useState } from "react";

import {
  Badge,
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Checkbox,
  Input,
} from "@/components/ui/primitives";
import { api } from "@/lib/api";
import {
  actions,
  chip,
  commandLabel,
  rememberedOperator,
  rememberOperator,
  type Action,
} from "@/lib/control";
import type { DeploymentDetail } from "@/types/control";

/**
 * What an operator can do to the selected deployment: pause and resume
 * buying, wind down, disable, enable.
 *
 * NOTHING HERE CHANGES THE DEPLOYMENT DIRECTLY. A command is queued in the
 * deployment's control directory and its trader applies it -- between ticks
 * while trading, at once between sessions -- through the circuit breaker it
 * actually reads. The old halt wrote the ledger behind the loop's back, and
 * the loop, which reads the halt once at startup, kept buying. The command
 * log below says when each command took effect, in the trader's own words.
 *
 * Every command names its operator and a reason; both are recorded with
 * it. One with large consequences (disabling a book of open lots, anything
 * but a pause on real money) needs the deployment's id typed back -- the
 * server checks that too. What a deployment takes at all is its config's
 * live.control: an unavailable command says which grant it lacks.
 *
 * Liquidation stays absent, and says why: the loop sells a lot only at its
 * target under the no-loss guard, or by the Ultimate regime exit.
 */

interface Props {
  deployment: DeploymentDetail;
  onSent: () => void;
}

const LIQUIDATE_REASON =
  "Not implemented, by design. The trading loop sells a lot only when its profit target is " +
  "met and the no-loss guard permits it (or by the Ultimate family's regime exit) -- not on " +
  "shutdown, not on a halt, not on a disable. Adding one would mean forced selling at a loss.";

function newKey(): string {
  // Not crypto.randomUUID: the page is served over plain HTTP on the LAN,
  // where browsers do not offer it.
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

export function ControlBar({ deployment, onSent }: Props) {
  const [open, setOpen] = useState<Action | null>(null);
  const [key, setKey] = useState("");
  const [reason, setReason] = useState("");
  const [operator, setOperator] = useState(rememberedOperator);
  const [typed, setTyped] = useState("");
  const [resetBaseline, setResetBaseline] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const state = chip(deployment);
  const offered = actions(deployment);
  const desired = deployment.desired;
  const halt = deployment.ledger?.halt ?? deployment.state?.halt ?? null;

  const begin = (action: Action) => {
    setOpen(action);
    setKey(newKey());
    setReason("");
    setTyped("");
    setResetBaseline(false);
    setError(null);
    setNotice(null);
  };

  const ready =
    open !== null &&
    reason.trim().length >= 3 &&
    operator.trim().length > 0 &&
    (!open.typed || typed.trim() === deployment.id);

  const send = async () => {
    if (!open || !ready) return;
    setBusy(true);
    setError(null);
    try {
      const response = await api.sendCommand(deployment.id, {
        type: open.type,
        args: open.id === "resume" ? { reset_drawdown_baseline: resetBaseline } : open.args,
        reason: reason.trim(),
        operator: operator.trim(),
        idempotency_key: key,
        ...(open.typed ? { confirm: typed.trim() } : {}),
      });
      rememberOperator(operator.trim());
      setNotice(
        response.warning ??
          `${commandLabel(response.command)} queued -- ${
            deployment.status?.process === "loop"
              ? "the loop applies it after its current tick"
              : "the trader applies it within seconds"
          }. Its outcome appears in the command log.`,
      );
      setOpen(null);
      onSent();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card>
      <CardHeader className="flex-row flex-wrap items-center justify-between gap-2">
        <CardTitle className="flex items-center gap-2">
          <ShieldCheck className="size-4" />
          Controls · {deployment.label}
        </CardTitle>
        <div className="flex items-center gap-2">
          {halt ? (
            <Badge tone="loss" className="gap-1">
              <OctagonX className="size-3" />
              buys halted
            </Badge>
          ) : null}
          <Badge tone={state.tone}>{state.label}</Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {state.detail ? <p className="text-xs text-muted-foreground">{state.detail}</p> : null}
        {halt ? (
          <div className="rounded-md border border-border bg-secondary/40 p-3 text-sm">
            <span className="font-medium">New buys are blocked:</span> {halt}
            <p className="mt-1 text-xs text-muted-foreground">
              Open lots are still tracked and still exit at their targets.
            </p>
          </div>
        ) : null}
        {desired && (!desired.enabled || desired.wind_down) ? (
          <p className="text-sm">
            {desired.wind_down ? "Winding down" : "Disabled"}
            {desired.by ? ` by ${desired.by}` : ""}
            {desired.reason ? `: ${desired.reason}` : ""}
          </p>
        ) : null}

        <div className="flex flex-wrap items-center gap-2">
          {offered.map((action) => (
            <Button
              key={action.id}
              variant={action.danger ? "destructive" : "outline"}
              disabled={busy || action.blocked !== null}
              title={action.blocked ?? action.effect}
              onClick={() => begin(action)}
            >
              {action.label}
            </Button>
          ))}
          {offered.length === 0 ? (
            <span className="text-xs text-muted-foreground">No commands for this deployment.</span>
          ) : null}
        </div>
        {offered.some((action) => action.blocked) ? (
          <p className="text-xs text-muted-foreground">
            {offered
              .filter((action) => action.blocked)
              .map((action) => `${action.label}: ${action.blocked}`)
              .join(" · ")}
          </p>
        ) : null}

        {open ? (
          <div
            className={`space-y-3 rounded-md border p-3 ${
              open.danger ? "border-destructive/50" : "border-border"
            }`}
          >
            <p className="text-sm font-medium">
              {open.label} · {deployment.label}?
            </p>
            <p className="text-xs text-muted-foreground">{open.effect}</p>
            <div className="grid gap-2 sm:grid-cols-[1fr_12rem]">
              <Input
                autoFocus
                placeholder="Why -- recorded with the command and shown to whoever looks next"
                value={reason}
                onChange={(event) => setReason(event.currentTarget.value)}
              />
              <Input
                placeholder="Your name"
                value={operator}
                onChange={(event) => setOperator(event.currentTarget.value)}
              />
            </div>
            {open.id === "resume" ? (
              <label className="flex items-start gap-2 text-xs">
                <Checkbox
                  checked={resetBaseline}
                  onChange={(event) => setResetBaseline(event.currentTarget.checked)}
                />
                <span>
                  Also reset the drawdown baseline to the current equity, so a drawdown halt
                  does not trip again on the next tick. Strategies that size on drawdown see it
                  reset too.
                </span>
              </label>
            ) : null}
            {open.typed ? (
              <div className="space-y-1">
                <p className="text-xs text-loss">
                  Type <code className="font-mono">{deployment.id}</code> to confirm: {open.typed}.
                </p>
                <Input
                  placeholder={deployment.id}
                  value={typed}
                  onChange={(event) => setTyped(event.currentTarget.value)}
                />
              </div>
            ) : null}
            <div className="flex items-center gap-2">
              <Button
                variant={open.danger ? "destructive" : "default"}
                disabled={busy || !ready}
                onClick={() => void send()}
              >
                {busy ? "Sending…" : `Confirm ${open.label.toLowerCase()}`}
              </Button>
              <Button variant="ghost" disabled={busy} onClick={() => setOpen(null)}>
                Cancel
              </Button>
            </div>
            {error ? <p className="text-xs text-loss">{error}</p> : null}
          </div>
        ) : null}
        {notice ? <p className="text-xs text-muted-foreground">{notice}</p> : null}

        <div className="flex items-start gap-3 border-t border-border pt-4 opacity-60">
          <Button variant="outline" disabled className="mt-0.5 shrink-0">
            <Ban className="size-3.5" />
            Liquidate all positions
          </Button>
          <p className="text-xs text-muted-foreground">{LIQUIDATE_REASON}</p>
        </div>
      </CardContent>
    </Card>
  );
}
