import { Database, Loader2, RefreshCw, TriangleAlert } from "lucide-react";
import type { ReactNode } from "react";

import { Button, Card, CardContent } from "@/components/ui/primitives";
import { usePolled } from "@/hooks/usePolled";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { ago, bytes, whole, type Tone } from "@/lib/warehouse";

import { FundsTable } from "./FundsTable";
import { ResultsActivity } from "./ResultsActivity";
import { ServerCard } from "./ServerCard";
import { StorageCard } from "./StorageCard";

/**
 * What the warehouse holds and the state of the machine filling it.
 *
 * READ-ONLY BY CONSTRUCTION: two GETs (server/warehouse_status.py), polled
 * while this tab is open and never otherwise -- App renders it only when
 * selected, so leaving the tab stops both polls.
 *
 * The warehouse read is cached server-side (the bar scan only reruns after
 * an ingest; results every 30 s), so polling it every 30 s costs nothing.
 * The system read is a handful of /sys and /proc files, every 10 s.
 */

const WAREHOUSE_POLL_MS = 30_000;
const SYSTEM_POLL_MS = 10_000;

export function WarehouseTab() {
  const warehouse = usePolled(api.warehouse, WAREHOUSE_POLL_MS);
  const system = usePolled(api.system, SYSTEM_POLL_MS);
  // "Now" is the server's latest answer, not the browser clock: render stays
  // pure, and every age on the page is measured from the same instant.
  const now = new Date(system.data?.at ?? warehouse.data?.at ?? 0);
  const status = warehouse.data;

  const refresh = () => {
    warehouse.refresh();
    system.refresh();
  };

  return (
    <>
      <div className="flex flex-wrap items-center gap-3">
        <h2 className="flex items-center gap-2 text-sm font-semibold">
          <Database className="size-4" />
          Warehouse
        </h2>
        <span className="text-xs text-muted-foreground">
          {status ? `as of ${new Date(status.at).toLocaleTimeString()}` : "loading…"}
          {status ? ` · up to date means through ${status.through}` : ""}
        </span>
        <Button
          variant="outline"
          className="ml-auto"
          onClick={refresh}
          disabled={warehouse.loading && system.loading}
        >
          {warehouse.loading ? (
            <Loader2 className="size-3.5 animate-spin" />
          ) : (
            <RefreshCw className="size-3.5" />
          )}
          Refresh
        </Button>
      </div>

      {warehouse.error || system.error ? (
        <Banner tone="loss">
          {warehouse.error ?? system.error} — is the API running?
          {warehouse.data ? " Showing the last answer." : ""}
        </Banner>
      ) : null}
      {status?.busy ? (
        <Banner tone="stuck">
          Another process is writing the warehouse (an ingest, a backtest on the host). These
          figures are the last good read; it tries again on the next refresh.
        </Banner>
      ) : null}
      {status?.error ? <Banner tone="loss">The warehouse could not be read: {status.error}</Banner> : null}
      {status && !status.available ? (
        <Banner tone="stuck">
          No warehouse here yet. Build one with{" "}
          <code className="text-foreground">python tools/build_warehouse.py --ingest-all</code>.
        </Banner>
      ) : null}

      {status ? (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 xl:grid-cols-8">
          <Tile label="Funds" value={whole(status.summary.funds)} />
          <Tile label="Bars" value={whole(status.summary.bars)} />
          <Tile label="Sweeps" value={whole(status.summary.sweeps)} />
          <Tile label="Simulations" value={whole(status.summary.simulations)} />
          <Tile label="Simulations, last hour" value={whole(status.summary.last_hour)} />
          <Tile label="Trade executions" value={whole(status.summary.executions)} />
          <Tile label="Warehouse size" value={bytes(status.summary.bytes)} />
          <Tile label="Disk free" value={bytes(status.summary.free)} />
        </div>
      ) : null}

      {status ? <FundsTable funds={status.funds} through={status.through} /> : null}
      {status ? <ResultsActivity status={status} now={now} /> : null}

      <div className="grid gap-4 xl:grid-cols-2">
        {system.data ? (
          <ServerCard
            system={system.data}
            lastHour={status?.summary.last_hour ?? 0}
            lastDay={status?.summary.last_day ?? 0}
            now={now}
          />
        ) : null}
        {status ? <StorageCard storage={status.storage} now={now} /> : null}
      </div>

      {status ? (
        <p className="text-xs text-muted-foreground">
          Read {ago(status.at, now)}. The fund scan reruns only after an ingest changes the bar
          lake; results and storage refresh every 30 seconds.
        </p>
      ) : null}
    </>
  );
}

function Banner({ tone, children }: { tone: Tone; children: ReactNode }) {
  return (
    <Card>
      <CardContent
        className={cn(
          "flex items-start gap-2 pt-5 text-sm",
          tone === "loss" ? "text-loss" : tone === "stuck" ? "text-stuck" : "text-muted-foreground",
        )}
      >
        <TriangleAlert className="mt-0.5 size-4 shrink-0" />
        <span>{children}</span>
      </CardContent>
    </Card>
  );
}

function Tile({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <Card>
      <CardContent className="p-3">
        <div className="text-xs text-muted-foreground">{label}</div>
        <div className="mt-1 text-lg font-semibold tabular-nums">{value}</div>
        {hint ? <div className="text-xs text-muted-foreground">{hint}</div> : null}
      </CardContent>
    </Card>
  );
}
