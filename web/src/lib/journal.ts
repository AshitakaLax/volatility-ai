/**
 * A trader's journals (fills, order events) polled incrementally: the first
 * load takes the window whole, each poll after it asks only for the rows
 * after the newest one held (`since`) and appends them. A busy paper trial
 * books hundreds of fills a session, and the page polls every 15 seconds.
 */

/** The Eastern session date ("YYYY-MM-DD") an epoch-seconds time falls on --
 * how the trader's journal files its rows. */
export function easternSession(seconds: number): string {
  return new Date(seconds * 1000).toLocaleDateString("en-CA", { timeZone: "America/New_York" });
}

/** The newest row's time, or undefined for none -- the next poll's `since`. */
export function newest<T extends { t: number }>(rows: readonly T[]): number | undefined {
  return rows.at(-1)?.t;
}

/** `have` with the rows of `next` that are newer than its newest appended,
 * oldest first; `have` itself when nothing is new (so nothing re-renders). */
export function appendNewer<T extends { t: number }>(have: T[], next: readonly T[]): T[] {
  const after = newest(have);
  const fresh = after === undefined ? [...next] : next.filter((row) => row.t > after);
  return fresh.length ? [...have, ...fresh] : have;
}

/** The rows of the last `sessions` Eastern sessions they cover -- what a full
 * reload would return once the journal moves on to a new session. */
export function lastSessions<T extends { t: number }>(rows: T[], sessions: number): T[] {
  const days = [...new Set(rows.map((row) => easternSession(row.t)))].sort();
  if (days.length <= sessions) return rows;
  const keep = new Set(days.slice(-sessions));
  return rows.filter((row) => keep.has(easternSession(row.t)));
}
