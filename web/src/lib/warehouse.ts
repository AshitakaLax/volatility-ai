/**
 * The Warehouse tab's formatting and judgement calls, as pure functions so
 * warehouse.test.ts can pin them: what counts as stale, too hot, too full,
 * and when the queue will be done.
 */
import type { FundRow, SystemStatus, Temperature } from "@/types/warehouse";

export type Tone = "neutral" | "profit" | "loss" | "stuck";

const UNITS = ["B", "KB", "MB", "GB", "TB"];

/** Bytes, in the largest unit under 1024 of it: 124644656 -> "118.9 MB". */
export function bytes(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "--";
  let amount = value;
  let unit = 0;
  while (amount >= 1024 && unit < UNITS.length - 1) {
    amount /= 1024;
    unit += 1;
  }
  return `${unit === 0 ? amount : amount.toFixed(1)} ${UNITS[unit]}`;
}

/** A whole-number count with separators: 1055694 -> "1,055,694". */
export function whole(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "--";
  return Math.round(value).toLocaleString("en-US");
}

/** A span of hours as the two largest units: 52.5 -> "2d 4h", 0.75 -> "45m". */
export function duration(hours: number): string {
  const minutes = Math.round(hours * 60);
  if (minutes < 60) return `${minutes}m`;
  const days = Math.floor(minutes / 1440);
  const restHours = Math.floor((minutes % 1440) / 60);
  if (days > 0) return restHours ? `${days}d ${restHours}h` : `${days}d`;
  const restMinutes = minutes % 60;
  return restMinutes ? `${restHours}h ${restMinutes}m` : `${restHours}h`;
}

/** How long ago an ISO time was, at `now`: "40s ago", "5m ago", "3h ago", "2d ago". */
export function ago(iso: string | null | undefined, now: Date): string {
  if (!iso) return "never";
  const seconds = Math.max(0, (now.getTime() - new Date(iso).getTime()) / 1000);
  if (seconds < 90) return `${Math.round(seconds)}s ago`;
  if (seconds < 5400) return `${Math.round(seconds / 60)}m ago`;
  if (seconds < 172800) return `${Math.round(seconds / 3600)}h ago`;
  return `${Math.round(seconds / 86400)}d ago`;
}

/** Sessions behind past which a fund is called stale rather than lagging:
 * a week of trading. */
export const STALE_SESSIONS = 5;

/** A fund's freshness, as a badge. */
export function freshness(row: FundRow): { label: string; tone: Tone } {
  if (!row.ingested) return { label: "Not ingested", tone: "neutral" };
  const behind = row.sessions_behind ?? 0;
  if (behind === 0) return { label: "Up to date", tone: "profit" };
  const label = `${behind} session${behind === 1 ? "" : "s"} behind`;
  return { label: row.partial ? `${label} (last one partial)` : label, tone: behind > STALE_SESSIONS ? "loss" : "stuck" };
}

/** Within this many degrees of the CPU's own "high" limit is a warning. */
export const WARM_MARGIN_C = 5;

/** A CPU temperature against the limits the CPU reports for itself. */
export function temperatureTone(reading: Temperature): Tone {
  const high = reading.high ?? reading.crit;
  if (high === null) return "neutral";
  if (reading.c >= high) return "loss";
  if (reading.c >= high - WARM_MARGIN_C) return "stuck";
  return "profit";
}

/** The backup service runs daily; past this an archive is overdue. */
export const BACKUP_OVERDUE_HOURS = 26;

export function backupTone(backups: SystemStatus["backups"], now: Date): Tone {
  if (!backups?.latest) return "loss";
  const hours = (now.getTime() - new Date(backups.latest.at).getTime()) / 3_600_000;
  return hours > BACKUP_OVERDUE_HOURS ? "loss" : "profit";
}

/** A disk with less than 10% free is a problem; less than 20%, a warning. */
export function diskTone(free: number | null, total: number | null): Tone {
  if (free === null || total === null || total <= 0) return "neutral";
  const share = free / total;
  if (share < 0.1) return "loss";
  if (share < 0.2) return "stuck";
  return "neutral";
}

/**
 * When the queue will be empty, from what is left and the rate the last
 * hour ran at -- or the last day's average when the last hour saw nothing
 * (a restart, a pause). Null when nothing is left or nothing has run.
 */
export function queueEta(
  remaining: number,
  lastHour: number,
  lastDay: number,
  now: Date,
): { hours: number; at: Date; perHour: number } | null {
  const perHour = lastHour > 0 ? lastHour : lastDay / 24;
  if (remaining <= 0 || perHour <= 0) return null;
  const hours = remaining / perHour;
  return { hours, at: new Date(now.getTime() + hours * 3_600_000), perHour };
}

/** Each hour's height in the activity strip, as a percent of the busiest. */
export function barHeights(hourly: { n: number }[]): number[] {
  const peak = Math.max(0, ...hourly.map((hour) => hour.n));
  return hourly.map((hour) => (peak > 0 ? (hour.n / peak) * 100 : 0));
}
