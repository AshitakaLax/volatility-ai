import { GitBranch, Server, Wifi, WifiOff } from "lucide-react";
import { useEffect, useState } from "react";

import { Badge, Card, CardContent, CardHeader, CardTitle } from "@/components/ui/primitives";
import { api, type Health } from "@/lib/api";
import { sameCode } from "@/lib/control";
import { cn, usd } from "@/lib/utils";
import type { DeploymentSummary } from "@/types/control";
import type { ConnectionHealth, LiveState } from "@/types/telemetry";

/**
 * Which build is running, against which account, and is it alive.
 *
 * THE STALENESS IS STATED, NOT IMPLIED. The live loop writes through to
 * its store once per tick, so everything here is up to one poll interval
 * behind -- 60 seconds by default. A dashboard that looks real-time and
 * is not will eventually be trusted at the wrong moment, so the age of
 * the last tick is a first-class field rather than something a reader
 * has to infer from a spinner.
 *
 * `last_write_age` and `last_tick_at` measure different things and both
 * are shown: the first is a file mtime, which cannot distinguish
 * "stopped" from "market closed"; the second is the loop's own record of
 * when it last saw a price.
 *
 * TWO PROCESSES, TWO BUILDS. The trader and this web server are different
 * containers, deployed at different times, and the image has no .git: each
 * reports a fingerprint of the code it loaded (engine/core/build_info.py),
 * and the card says whether the two match. The web server's own uptime and
 * memory are labelled as its own -- they say nothing about the trader.
 */

interface Props {
  state: LiveState | null;
  health: ConnectionHealth;
  /** The selected deployment, from config/deployments.yaml. */
  deployment: DeploymentSummary | null;
}

function since(iso: string | null): string {
  if (!iso) return "never";
  const seconds = (Date.now() - new Date(iso).getTime()) / 1000;
  if (seconds < 90) return `${Math.round(seconds)}s ago`;
  if (seconds < 5400) return `${Math.round(seconds / 60)}m ago`;
  return `${Math.round(seconds / 3600)}h ago`;
}

export function DeploymentHealth({ state, health, deployment }: Props) {
  const [info, setInfo] = useState<Health | null>(null);

  useEffect(() => {
    api
      .health()
      .then(setInfo)
      .catch(() => setInfo(null));
  }, []);

  const connected = health.status === "open";
  const status = deployment?.status && !deployment.status.stale ? deployment.status : null;
  const trader = status?.build ?? null;
  const process = status?.process ?? null;
  const same = sameCode(trader, info?.build.code);

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <Server className="size-4" />
          Deployment
        </CardTitle>
        <div className="flex items-center gap-2 text-xs">
          {connected ? (
            <Wifi className="size-3.5 text-profit" />
          ) : (
            <WifiOff className="size-3.5 text-loss" />
          )}
          <span className={cn(connected ? "text-profit" : "text-loss")}>{health.status}</span>
          {health.retries > 0 ? (
            <span className="text-muted-foreground">retry {health.retries}</span>
          ) : null}
        </div>
      </CardHeader>

      <CardContent className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <div className="flex flex-col gap-1">
          <span className="text-xs font-medium text-muted-foreground">Deployment</span>
          <span className="text-sm">{deployment?.label ?? "--"}</span>
          {/* From the deployment's config (live.paper_trading), a fact --
              not, as the old picker had it, a guess from a file name. */}
          {deployment?.paper === false ? (
            <Badge tone="loss">real money</Badge>
          ) : deployment?.paper ? (
            <span className="text-xs text-muted-foreground">paper account</span>
          ) : null}
          {deployment?.service ? (
            <span className="font-mono text-xs text-muted-foreground">
              service {deployment.service}
            </span>
          ) : null}
        </div>

        <div className="flex flex-col gap-1">
          <span className="text-xs font-medium text-muted-foreground">Trader's build</span>
          <span className="flex items-center gap-1.5 font-mono text-sm">
            <GitBranch className="size-3.5" />
            {trader?.commit ?? "commit not recorded"}
          </span>
          <span className="font-mono text-xs text-muted-foreground">
            code {trader?.code ?? "--"}
          </span>
          {same === null ? (
            <span className="text-xs text-muted-foreground">
              {trader ? "cannot compare with the web server" : "no report from the trader"}
            </span>
          ) : same ? (
            <span className="text-xs text-muted-foreground">same code as this web server</span>
          ) : (
            <Badge tone="stuck" title="One of the two was deployed after the other">
              different code from the web server ({info?.build.code})
            </Badge>
          )}
        </div>

        <div className="flex flex-col gap-1">
          <span className="text-xs font-medium text-muted-foreground">Last tick</span>
          <span className="tnum text-sm">{since(state?.last_tick ?? null)}</span>
          <span className="text-xs text-muted-foreground">
            {state?.last_px ? `at ${usd(state.last_px)}` : "no mark recorded"}
          </span>
          {/* Said explicitly. This is persisted state, not a live feed. */}
          <span className="text-xs text-muted-foreground">
            store written{" "}
            {state?.write_age_s === null || state?.write_age_s === undefined
              ? "--"
              : `${Math.round(state.write_age_s)}s ago`}
          </span>
        </div>

        <div className="flex flex-col gap-1">
          <span className="text-xs font-medium text-muted-foreground">Trader's process</span>
          <span className="tnum text-sm">
            {trader
              ? `${process ?? "process"} since ${new Date(trader.started_at).toLocaleString([], {
                  month: "short",
                  day: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
                })}`
              : "--"}
          </span>
          <span className="text-xs text-muted-foreground">
            {trader ? `python ${trader.python} · pid ${trader.pid}` : ""}
          </span>
          {/* The web server's own, said so: they describe this process, not
              the trader. Nulls rather than zeros outside a container. */}
          <span className="text-xs text-muted-foreground">
            web server: {info ? `up ${Math.round(info.build.uptime_s / 60)}m` : "--"}
            {info?.container
              ? ` · ${info.container.mem_mb} / ${info.container.mem_limit_mb ?? "∞"} MB`
              : ""}
          </span>
        </div>
      </CardContent>

      {deployment?.ledger && !deployment.ledger.exists ? (
        <CardContent className="pt-0">
          <p className="text-xs text-loss">
            This deployment has no ledger yet. One that has never run writes nothing —
            that is a normal state, not a failure.
          </p>
        </CardContent>
      ) : null}
    </Card>
  );
}
