import { AlertTriangle, Ban, OctagonX, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";

import { Badge, Button, Card, CardContent, CardHeader, CardTitle, Input } from "@/components/ui/primitives";
import { api, type Capabilities } from "@/lib/api";
import type { DeploymentState } from "@/types/telemetry";

/**
 * The only controls in this application that change anything.
 *
 * ONE OF THREE IS IMPLEMENTED, AND THE OTHER TWO SAY WHY. Hiding a
 * control a reader expects makes the absence look like a bug; showing it
 * greyed with its reason makes it look like the decision it is.
 *
 *   emergency_halt      real. Maps onto the existing CircuitBreaker,
 *                       which already persists, survives a restart and
 *                       is operator-reversible. It blocks NEW BUYS only:
 *                       the loop keeps tracking the market and keeps
 *                       exiting open lots.
 *   liquidate_all       refused. src/live_trading_loop.py: "NO FORCED
 *                       LIQUIDATION, EVER." There is no code path to
 *                       call, and building one would mean forced selling
 *                       at a loss.
 *   parameter_override  refused. Live parameters come from a committed
 *                       config, not a browser.
 *
 * CAPABILITIES ARE READ FROM THE SERVER, not compiled in. A bundle that
 * carried its own idea of what is allowed could disagree with the
 * deployment it is talking to, and it would be the bundle that is wrong.
 */

interface Props {
  path: string | null;
  state: DeploymentState | null;
  onHalted: () => void;
}

const REFUSED: Record<string, { label: string; reason: string }> = {
  liquidate: {
    label: "Liquidate all positions",
    reason:
      "Not implemented, by design. The trading loop has no code path that sells a lot " +
      "for any reason other than its profit target being met and the no-loss guard " +
      "permitting it — not on shutdown, not on a drawdown halt, not on a reconciliation " +
      "failure. Adding one would mean forced selling at a loss.",
  },
  parameter_override: {
    label: "Override live parameters",
    reason:
      "Live parameters come from a committed config file, so that routing real capital " +
      "stays a reviewable decision rather than something typed into a browser.",
  },
};

export function CommandCenter({ path, state, onHalted }: Props) {
  const [capabilities, setCapabilities] = useState<Capabilities | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .health()
      .then((body) => setCapabilities(body.capabilities))
      .catch(() => setCapabilities(null));
  }, []);

  const halted = state?.halted ?? false;

  const halt = async () => {
    if (!path) return;
    setBusy(true);
    setError(null);
    try {
      await api.halt(path, reason.trim());
      setConfirming(false);
      setReason("");
      onHalted();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <ShieldCheck className="size-4" />
          Command centre
        </CardTitle>
        {halted ? (
          <Badge tone="loss" className="gap-1">
            <OctagonX className="size-3" />
            halted
          </Badge>
        ) : (
          <Badge tone="profit">accepting buys</Badge>
        )}
      </CardHeader>

      <CardContent className="space-y-4">
        {halted ? (
          <div className="rounded-md border border-border bg-secondary/40 p-3">
            <p className="text-sm font-medium">New buys are blocked.</p>
            <p className="mt-1 text-sm text-muted-foreground">{state?.halt_reason}</p>
            {/* Both halves, because the asymmetry is the point: a halt
                is not a stop. */}
            <p className="mt-2 text-xs text-muted-foreground">
              Open lots are still tracked and still exit at their targets. Clearing this is
              a deliberate operator action outside the dashboard.
            </p>
          </div>
        ) : !confirming ? (
          <div className="flex flex-wrap items-center gap-3">
            <Button
              variant="destructive"
              disabled={!path || capabilities?.halt === false}
              onClick={() => setConfirming(true)}
            >
              <AlertTriangle className="size-3.5" />
              Emergency halt
            </Button>
            <span className="text-xs text-muted-foreground">
              Blocks new buys. Does not sell anything.
            </span>
          </div>
        ) : (
          <div className="space-y-3 rounded-md border border-destructive/40 p-3">
            <p className="text-sm font-medium">Halt new buys on this deployment?</p>
            <p className="text-xs text-muted-foreground">
              The loop keeps running: it will continue tracking the market and exiting open
              lots at their targets. It will not open new positions until an operator
              clears the halt. This survives a restart.
            </p>
            <Input
              autoFocus
              placeholder="Why — stored with the halt and shown to whoever finds it"
              value={reason}
              onChange={(event) => setReason(event.currentTarget.value)}
              className="w-full"
            />
            <div className="flex items-center gap-2">
              {/* The reason is required by the API (min_length=3) and
                  required here, so the refusal is immediate rather than
                  a 422 from a round trip. */}
              <Button
                variant="destructive"
                disabled={busy || reason.trim().length < 3}
                onClick={() => void halt()}
              >
                {busy ? "Halting…" : "Confirm halt"}
              </Button>
              <Button variant="ghost" disabled={busy} onClick={() => setConfirming(false)}>
                Cancel
              </Button>
            </div>
            {error ? <p className="text-xs text-loss">{error}</p> : null}
          </div>
        )}

        <div className="space-y-2 border-t border-border pt-4">
          {Object.entries(REFUSED).map(([key, command]) => (
            <div key={key} className="flex items-start gap-3 opacity-60">
              <Button variant="outline" disabled className="mt-0.5 shrink-0">
                <Ban className="size-3.5" />
                {command.label}
              </Button>
              <p className="text-xs text-muted-foreground">{command.reason}</p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
