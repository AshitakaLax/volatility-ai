/**
 * Where the reader is, kept in the address: `#live`, `#live/fidelity`,
 * `#backtest`. A reload, a bookmark and the back button all land on the
 * same page -- before this the tab was React state and every reload opened
 * the parameter form.
 *
 * Live is where the page opens: it is the one looked at every day, and the
 * one that says when real money needs attention. `?run=<id>` (a run opened
 * in its own browser tab, lib/utils.ts runUrl) still lands on its result.
 */
export const TABS = [
  "backtest",
  "result",
  "live",
  "forecast",
  "algorithms",
  "ml",
  "warehouse",
] as const;

export type Tab = (typeof TABS)[number];

export interface Place {
  tab: Tab;
  /** The Live page's deployment, when the address names one. */
  deployment: string | null;
}

export const DEFAULT_TAB: Tab = "live";

const DEPLOYMENT_ID = /^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$/;

export function parsePlace(hash: string, search = ""): Place {
  const [name = "", rest = ""] = hash.replace(/^#\/?/, "").split("/");
  const tab = (TABS as readonly string[]).includes(name) ? (name as Tab) : null;
  if (!tab) {
    const run = new URLSearchParams(search).get("run");
    return { tab: run ? "result" : DEFAULT_TAB, deployment: null };
  }
  const deployment = tab === "live" && DEPLOYMENT_ID.test(rest) ? rest : null;
  return { tab, deployment };
}

export function placeHash(place: Place): string {
  return place.tab === "live" && place.deployment
    ? `#live/${place.deployment}`
    : `#${place.tab}`;
}
