import { Server } from "lucide-react";
import type { ReactNode } from "react";

import { Badge, Card, CardContent, CardHeader, CardTitle } from "@/components/ui/primitives";
import { cn, pct } from "@/lib/utils";
import {
  ago,
  backupTone,
  bytes,
  diskTone,
  duration,
  queueEta,
  temperatureTone,
  whole,
} from "@/lib/warehouse";
import type { SystemStatus } from "@/types/warehouse";

/**
 * The machine the sweeps run on and the queue they come from: load and
 * temperatures, memory, disks, the work left and when it should be done,
 * and the newest backup.
 *
 * Every figure is measured or absent, never guessed: container CPU needs
 * two readings (the first poll shows none), temperatures exist only where
 * /sys reports them, and the ETA uses the warehouse's own count of
 * simulations finished in the last hour.
 */
export function ServerCard({
  system,
  lastHour,
  lastDay,
  now,
}: {
  system: SystemStatus;
  lastHour: number;
  lastDay: number;
  now: Date;
}) {
  const { host, container, queue, shards, backups, build } = system;
  const eta = queueEta(queue.remaining_configurations, lastHour, lastDay, now);
  const counts = Object.entries(queue.counts)
    .map(([status, n]) => `${n} ${status}`)
    .join(" · ");

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <Server className="size-4" />
          Server
        </CardTitle>
        <span className="text-xs text-muted-foreground">
          {build.commit ?? "unknown build"}
          {build.branch ? ` on ${build.branch}` : ""}
          {build.dirty ? " (uncommitted changes)" : ""} · up {duration(build.uptime_s / 3600)}
        </span>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        <Row label="CPU">
          {host.load ? (
            <>
              load {host.load.map((value) => value.toFixed(1)).join(" / ")} on {host.cpus} threads
            </>
          ) : (
            "load unavailable"
          )}
          {container?.cores_busy !== null && container?.cores_busy !== undefined
            ? ` · this container ${container.cores_busy.toFixed(1)} cores`
            : ""}
        </Row>

        <Row label="Temperature">
          {host.temperatures.length ? (
            <>
              <span className="flex flex-wrap gap-2">
                {host.temperatures.map((reading) => (
                  <Badge
                    key={reading.label}
                    tone={temperatureTone(reading)}
                    title={`hottest core ${reading.hottest} °C`}
                  >
                    {reading.label}: {reading.c.toFixed(0)} °C
                  </Badge>
                ))}
              </span>
              <div className="mt-1 text-xs text-muted-foreground">
                The CPU&apos;s own limits: cooling at full by{" "}
                {limit(host.temperatures[0]?.high ?? null)}, slowing itself down at{" "}
                {limit(host.temperatures[0]?.crit ?? null)}.
              </div>
            </>
          ) : (
            <span className="text-muted-foreground">no CPU sensors visible here</span>
          )}
          {host.throttling ? (
            <div
              className={cn(
                "mt-1 text-xs",
                host.throttling.throttled_cpus ? "text-loss" : "text-muted-foreground",
              )}
            >
              {host.throttling.throttled_cpus
                ? `${host.throttling.throttled_cpus} CPUs have throttled since boot (up to ${host.throttling.max_events} events)`
                : "No thermal throttling since boot"}
            </div>
          ) : host.temperatures.length ? (
            <div className="mt-1 text-xs text-muted-foreground">
              Throttle counters are not visible here (Docker hides them from containers).
            </div>
          ) : null}
        </Row>

        <Row label="Memory">
          {container ? (
            <>
              {bytes(container.mem_mb * 1_048_576)} used
              {container.mem_limit_mb !== null
                ? ` of ${bytes(container.mem_limit_mb * 1_048_576)} (${pct(
                    (container.mem_mb / container.mem_limit_mb) * 100,
                    0,
                  )})`
                : ""}
            </>
          ) : (
            <span className="text-muted-foreground">not in a container: no cgroup figures</span>
          )}
        </Row>

        <Row label="Disks">
          <div className="space-y-0.5">
            {system.disks.map((disk) => (
              <div key={disk.label} className="flex flex-wrap gap-x-2">
                <span className="w-20 text-muted-foreground">{disk.label}</span>
                <span
                  className={cn(
                    diskTone(disk.free, disk.total) === "loss" && "text-loss",
                    diskTone(disk.free, disk.total) === "stuck" && "text-stuck",
                  )}
                >
                  {bytes(disk.free)} free of {bytes(disk.total)}
                </span>
              </div>
            ))}
          </div>
        </Row>

        <Row label="Queue">
          <div>
            {counts || "empty"}
            {queue.paused ? <Badge tone="stuck" className="ml-2">paused</Badge> : null}
          </div>
          {queue.running.map((run) => (
            <div key={run.id} className="mt-2">
              <div className="flex justify-between gap-2 text-xs">
                <span className="truncate" title={run.name ?? run.id}>
                  {run.name ?? run.id}
                  {run.shard && run.shard !== "local" ? ` · on ${run.shard}` : ""}
                </span>
                <span className="tabular-nums">{pct(run.progress * 100, 0)}</span>
              </div>
              <div className="mt-1 h-1.5 rounded bg-secondary">
                <div
                  className="h-1.5 rounded bg-primary"
                  style={{ width: `${Math.min(100, run.progress * 100)}%` }}
                />
              </div>
              {run.msg ? <div className="mt-0.5 text-xs text-muted-foreground">{run.msg}</div> : null}
            </div>
          ))}
          <div className="mt-2">
            {whole(queue.remaining_configurations)} configurations left in{" "}
            {whole(queue.remaining_runs)} runs
            {eta
              ? ` · at ${whole(eta.perHour)} an hour, done in about ${duration(eta.hours)} (${eta.at.toLocaleString(
                  undefined,
                  { weekday: "short", month: "short", day: "numeric", hour: "numeric", minute: "2-digit" },
                )})`
              : ""}
          </div>
          {queue.some_unsized ? (
            <div className="text-xs text-stuck">
              A queued run no longer validates; it is not counted and will fail when it starts.
            </div>
          ) : null}
        </Row>

        <Row label="Shards">
          {shards.online} of {shards.total} connected · {shards.working} working
        </Row>

        <Row label="Backups">
          {backups ? (
            <div>
              <Badge tone={backupTone(backups, now)}>
                {backups.latest ? `newest ${ago(backups.latest.at, now)}` : "no archive yet"}
              </Badge>
              <span className="ml-2 text-xs text-muted-foreground">
                {backups.count} archives, {bytes(backups.bytes)}
                {backups.latest ? ` · ${backups.latest.name} (${bytes(backups.latest.bytes)})` : ""}
              </span>
            </div>
          ) : (
            <span className="text-muted-foreground">the backup directory is not visible here</span>
          )}
        </Row>
      </CardContent>
    </Card>
  );
}

function limit(celsius: number | null): string {
  return celsius !== null ? `${celsius.toFixed(0)} °C` : "--";
}

function Row({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="grid grid-cols-[7rem_1fr] gap-3">
      <div className="text-xs font-medium text-muted-foreground">{label}</div>
      <div>{children}</div>
    </div>
  );
}
