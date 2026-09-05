import { GitBranch, Server, Wifi, WifiOff } from "lucide-react";
import { useEffect, useState } from "react";

import { Badge, Card, CardContent, CardHeader, CardTitle, Field, Select } from "@/components/ui/primitives";
import { api, type DeploymentInfo } from "@/lib/api";
import { cn, usd } from "@/lib/utils";
import type { ConnectionHealth, DeploymentState } from "@/types/telemetry";

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
 */

interface Props {
  state: DeploymentState | null;
  health: ConnectionHealth;
  stores: { path: string; label: string; paper: boolean }[];
  selected: string | null;
  onSelect: (path: string) => void;
}

function since(iso: string | null): string {
  if (!iso) return "never";
  const seconds = (Date.now() - new Date(iso).getTime()) / 1000;
  if (seconds < 90) return `${Math.round(seconds)}s ago`;
  if (seconds < 5400) return `${Math.round(seconds / 60)}m ago`;
  return `${Math.round(seconds / 3600)}h ago`;
}

export function DeploymentHealth({ state, health, stores, selected, onSelect }: Props) {
  const [info, setInfo] = useState<DeploymentInfo | null>(null);

  useEffect(() => {
    api
      .deployment()
      .then(setInfo)
      .catch(() => setInfo(null));
  }, []);

  const connected = health.status === "open";

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
        <Field label="Account">
          <Select
            value={selected ?? ""}
            onChange={(event) => onSelect(event.currentTarget.value)}
          >
            {stores.length === 0 ? <option value="">no stores found</option> : null}
            {stores.map((store) => (
              <option key={store.path} value={store.path}>
                {store.label}
              </option>
            ))}
          </Select>
          {/* A NAMING CONVENTION, NOT A FACT. The store does not record
              whether it was paper or live, so this is a hint and nothing
              may gate a decision on it. */}
          <span className="text-xs text-muted-foreground">
            {stores.find((store) => store.path === selected)?.paper
              ? "filename suggests paper"
              : "mode not recorded in the store"}
          </span>
        </Field>

        <div className="flex flex-col gap-1">
          <span className="text-xs font-medium text-muted-foreground">Build</span>
          <span className="flex items-center gap-1.5 font-mono text-sm">
            <GitBranch className="size-3.5" />
            {info?.git_branch ?? "--"}
            <span className="text-muted-foreground">@</span>
            {info?.git_commit ?? "--"}
          </span>
          {info?.git_dirty === null ? (
            <span className="text-xs text-muted-foreground">working tree unknown</span>
          ) : info?.git_dirty ? (
            <Badge tone="stuck">uncommitted changes</Badge>
          ) : (
            <span className="text-xs text-muted-foreground">clean</span>
          )}
        </div>

        <div className="flex flex-col gap-1">
          <span className="text-xs font-medium text-muted-foreground">Last tick</span>
          <span className="tnum text-sm">{since(state?.last_tick_at ?? null)}</span>
          <span className="text-xs text-muted-foreground">
            {state?.last_price ? `at ${usd(state.last_price)}` : "no mark recorded"}
          </span>
          {/* Said explicitly. This is persisted state, not a live feed. */}
          <span className="text-xs text-muted-foreground">
            store written{" "}
            {state?.last_write_age === null || state?.last_write_age === undefined
              ? "--"
              : `${Math.round(state.last_write_age)}s ago`}
          </span>
        </div>

        <div className="flex flex-col gap-1">
          <span className="text-xs font-medium text-muted-foreground">Process</span>
          <span className="tnum text-sm">
            {info ? `up ${Math.round(info.uptime_seconds / 60)}m` : "--"}
          </span>
          <span className="text-xs text-muted-foreground">
            {info ? `python ${info.python} · pid ${info.pid}` : ""}
          </span>
          {/* Nulls rather than zeros outside a container. A "CPU 0%" that
              means "could not measure" is a number someone would act on. */}
          <span className="text-xs text-muted-foreground">
            {info?.containerised
              ? `${info.memory_mb} / ${info.memory_limit_mb ?? "∞"} MB`
              : "container stats unavailable (not containerised)"}
          </span>
        </div>
      </CardContent>

      {state?.exists === false ? (
        <CardContent className="pt-0">
          <p className="text-xs text-loss">
            This store does not exist yet. A deployment that has never run writes nothing —
            that is a normal state, not a failure.
          </p>
        </CardContent>
      ) : null}
    </Card>
  );
}
