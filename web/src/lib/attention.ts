/**
 * What needs the reader, across every deployment: said once at the top of
 * the Live page and in the browser tab's title, whichever deployment is
 * selected. Pure functions over GET /api/live/deployments, so
 * attention.test.ts can pin them.
 *
 * A paper deployment that is simply not running is not attention: it is a
 * choice. A Fidelity connection that cannot trade, a halted ledger, a
 * config that does not load and a trader that needs recovery are.
 */
import { chip, type Tone } from "@/lib/control";
import { verdict } from "@/lib/fidelity";
import { refusal } from "@/lib/riskReport";
import type { DeploymentSummary } from "@/types/control";

export interface Attention {
  id: string;
  label: string;
  title: string;
  detail: string;
  fix: string | null;
  tone: Tone;
}

const SITE = "volatility-ai";

/** Whether anything reports for it: its trader, or a Fidelity bridge host. */
function reporting(d: DeploymentSummary): boolean {
  const status = d.status;
  return Boolean(d.bridge) || Boolean(status && !status.stale && status.state !== "not_running");
}

function usable(d: DeploymentSummary): boolean {
  return !d.setup && !d.error;
}

export function attention(deployments: DeploymentSummary[], now: number): Attention[] {
  const out: Attention[] = [];
  for (const d of deployments) {
    if (d.setup) continue;
    const add = (title: string, detail: string, fix: string | null, tone: Tone) =>
      out.push({ id: d.id, label: d.label, title, detail, fix, tone });
    if (d.error) {
      add("Config error", d.error, null, "loss");
      continue;
    }
    if (d.broker === "fidelity") {
      const said = verdict(d, now);
      if (said.tone === "loss") add(said.label, said.detail, said.fix, "loss");
    }
    if (d.status && !d.status.stale && d.status.state === "recovery_required") {
      add("Recovery required", d.status.detail ?? "its trader stopped and needs a look", null, "loss");
    }
    if (d.ledger?.halt && d.status?.state !== "buys_paused") {
      add("Buys halted", d.ledger.halt, null, "stuck");
    }
    // A session without a report is not attention (it trades as configured);
    // a report the trader refused is.
    const refused = refusal(d.risk_reports, now);
    if (refused) {
      add("Risk report refused", refused, "Check the report and send it again from the risk report panel.", "stuck");
    }
  }
  // Real money first, then the order they are listed in.
  return out.sort((a, b) => rank(deployments, a.id) - rank(deployments, b.id));
}

function rank(deployments: DeploymentSummary[], id: string): number {
  const index = deployments.findIndex((d) => d.id === id);
  return (deployments[index]?.paper === false ? 0 : 1000) + index;
}

/**
 * The deployment the Live page shows before one is picked: real money that
 * something reports for, else anything that reports, else the first listed.
 */
export function defaultDeployment(deployments: DeploymentSummary[]): string | null {
  const candidates = deployments.filter(usable);
  const pick =
    candidates.find((d) => d.paper === false && reporting(d)) ??
    candidates.find(reporting) ??
    candidates[0] ??
    deployments[0];
  return pick?.id ?? null;
}

/** The browser tab's title: what needs attention, else how real money stands. */
export function pageTitle(deployments: DeploymentSummary[], now: number): string {
  const [first] = attention(deployments, now);
  if (first) return `⚠ ${first.title} · ${first.label} — ${SITE}`;
  const real = deployments.find((d) => usable(d) && d.paper === false && reporting(d));
  if (!real) return SITE;
  const state =
    real.broker === "fidelity" ? verdict(real, now).label : chip(real).label;
  return `${state}${real.symbol ? ` · ${real.symbol}` : ""} — ${SITE}`;
}
