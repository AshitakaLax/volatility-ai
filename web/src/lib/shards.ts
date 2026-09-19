/**
 * How the shard panel describes and offers controls for each machine.
 *
 * Pure, like lib/runQueue.ts, and mirrored from the transitions
 * server/jobs.py accepts so the panel never offers a button the server
 * would answer with 409. Covered in shards.test.ts.
 */
import type { Shard, ShardConn, ShardSchedule, ShardState } from "@/types/backtest";

export interface ShardSummary {
  total: number;
  /** Heartbeating now (the local shard always is). */
  online: number;
  /** Running a sweep, including one that is finishing before a pause. */
  working: number;
  paused: number;
  /** Idle and inside its own lockout window, without also being
   * manually paused -- see the ShardState doc for why those never
   * overlap in this count. */
  lockedOut: number;
}

export function summarizeShards(shards: Shard[]): ShardSummary {
  return {
    total: shards.length,
    online: shards.filter((shard) => shard.conn === "online").length,
    working: shards.filter((shard) => shard.run !== null).length,
    paused: shards.filter((shard) => shard.state === "paused" || shard.state === "pausing").length,
    lockedOut: shards.filter((shard) => shard.state === "locked_out").length,
  };
}

export interface ShardActions {
  pause: boolean;
  resume: boolean;
  /** Drop it from the list -- only once it is offline, and never "local". */
  forget: boolean;
}

/**
 * A disconnected shard can still be paused: the pause is kept and applies
 * when that machine registers again.
 */
export function shardActions(shard: Shard): ShardActions {
  const paused = shard.state === "paused" || shard.state === "pausing";
  return {
    pause: !paused,
    resume: paused,
    forget: !shard.local && shard.conn === "offline",
  };
}

/** True only when both commits are known and differ. */
export function versionMismatch(shard: Shard, mainCommit: string | null): boolean {
  return Boolean(shard.commit && mainCommit && shard.commit !== mainCommit);
}

export function connLabel(conn: ShardConn): string {
  switch (conn) {
    case "online":
      return "connected";
    case "stale":
      return "not responding";
    case "offline":
      return "disconnected";
  }
}

export function stateLabel(state: ShardState): string {
  switch (state) {
    case "idle":
      return "idle";
    case "running":
      return "running";
    case "pausing":
      return "pausing -- finishing in-flight configurations";
    case "paused":
      return "paused";
    case "locked_out":
      return "locked out -- inside its scheduled window";
  }
}

/** "7:00 AM - 7:00 PM", or null if there is no window to show. Renders
 * even a disabled one (the modal's own toggle carries "on/off"; this is
 * just "what times", reused by both the chip tooltip and the modal). */
export function scheduleLabel(schedule: ShardSchedule | null): string | null {
  if (!schedule || !schedule.start || !schedule.end) return null;
  return `${formatHHMM(schedule.start)} - ${formatHHMM(schedule.end)}`;
}

function formatHHMM(value: string): string {
  const [hourStr, minuteStr] = value.split(":");
  const hour = Number(hourStr);
  const minute = Number(minuteStr);
  if (!Number.isFinite(hour) || !Number.isFinite(minute)) return value;
  const period = hour < 12 ? "AM" : "PM";
  const twelve = hour % 12 === 0 ? 12 : hour % 12;
  return `${twelve}:${String(minute).padStart(2, "0")} ${period}`;
}

/** "just now", "42s ago", "3m ago", "2h ago". */
export function describeSeen(seconds: number): string {
  if (seconds < 5) return "just now";
  if (seconds < 60) return `${Math.floor(seconds)}s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  return `${Math.floor(seconds / 3600)}h ago`;
}

/** The sweep's label: its submitted name, else a short id. */
export function sweepLabel(run: NonNullable<Shard["run"]>): string {
  return run.name?.trim() || run.id.slice(0, 10);
}
