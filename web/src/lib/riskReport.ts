/**
 * The nightly risk report on the Live page: pure functions the panel and the
 * overview card share, pinned by riskReport.test.ts.
 *
 * The page never decides what a report does. The server previews it with the
 * deployment's own mapping (research/risk_overlay/preview.py) and the trader
 * maps it again when it applies it; what is here only words and orders what
 * they said.
 */
import type { Tone } from "@/lib/control";
import type { DeploymentSummary } from "@/types/control";
import type {
  RiskOverlay,
  RiskReportPreview,
  RiskReportsSummary,
  TraderRiskOverlay,
  Would,
} from "@/types/riskReport";

/** A refused report stays something the page says for this long. */
export const REFUSAL_HOURS = 18;

export interface Pasted {
  report: Record<string, unknown> | null;
  error: string | null;
}

/** The pasted text as one JSON object -- a code fence around it is allowed,
 * as an LLM's answer often has one. */
export function parsePasted(text: string): Pasted {
  const trimmed = text
    .trim()
    .replace(/^```(?:json)?\s*/i, "")
    .replace(/\s*```$/, "")
    .trim();
  if (!trimmed) return { report: null, error: null };
  try {
    const value: unknown = JSON.parse(trimmed);
    if (value === null || typeof value !== "object" || Array.isArray(value)) {
      return { report: null, error: "The report must be one JSON object." };
    }
    return { report: value as Record<string, unknown>, error: null };
  } catch (cause) {
    return { report: null, error: `Not JSON: ${cause instanceof Error ? cause.message : String(cause)}` };
  }
}

/** Every deployment configured for reports (a risk.overlay section), in the
 * order listed: the Apply step's rows. Real money is listed beside paper. */
export function reportDeployments(deployments: DeploymentSummary[]): DeploymentSummary[] {
  return deployments.filter((d) => !d.setup && !d.error && d.risk_reports?.settings);
}

const WOULD: Record<Would, { label: string; tone: Tone }> = {
  apply: { label: "applies", tone: "profit" },
  replace: { label: "replaces tonight's earlier report", tone: "stuck" },
  tighten: { label: "tightens the session already trading", tone: "stuck" },
  not_applied: { label: "archived, not applied: it would loosen a session already trading", tone: "neutral" },
  unchanged: { label: "already in force", tone: "neutral" },
  refused: { label: "refused", tone: "loss" },
};

export function would(preview: RiskReportPreview): { label: string; tone: Tone } {
  if (!preview.takes_reports) return { label: `takes no reports: ${preview.why_not ?? ""}`, tone: "neutral" };
  return WOULD[preview.would ?? "refused"];
}

/** Checked by default: every deployment the report would do something to. */
export function checkedByDefault(preview: RiskReportPreview): boolean {
  return (
    preview.takes_reports &&
    preview.audit.ok &&
    (preview.would === "apply" || preview.would === "replace" || preview.would === "tighten")
  );
}

/** What applying needs from the reader: the id typed back for real money. */
export function needsTyped(preview: RiskReportPreview): boolean {
  return preview.typed !== null;
}

export function percent(fraction: number | null | undefined, digits = 0): string {
  return fraction === null || fraction === undefined ? "--" : `${(fraction * 100).toFixed(digits)}%`;
}

/** The overlay as short chips: what changes, lever by lever. */
export function levers(overlay: RiskOverlay | null | undefined): string[] {
  if (!overlay) return [];
  const out: string[] = [];
  if (overlay.pause) out.push("no new grid buys");
  else if (overlay.buy_multiplier < 1) out.push(`buys ×${overlay.buy_multiplier.toFixed(2)}`);
  if (overlay.exposure_ceiling !== null) out.push(`lots ≤ ${percent(overlay.exposure_ceiling)} of equity`);
  if (overlay.step_multiplier > 1) out.push(`step ×${overlay.step_multiplier.toFixed(1)}`);
  if (overlay.target_multiplier > 1) out.push(`targets ×${overlay.target_multiplier.toFixed(1)}`);
  if (overlay.blackouts.length) out.push(`${overlay.blackouts.length} blackout(s)`);
  return out;
}

export function tierLabel(tier: number | null | undefined, abstained?: boolean | null): string {
  if (abstained) return "abstains";
  return tier === null || tier === undefined ? "--" : `tier ${tier}`;
}

export function tierTone(tier: number | null | undefined, abstained?: boolean | null): Tone {
  if (abstained || tier === null || tier === undefined || tier === 0) return "neutral";
  return tier >= 3 ? "loss" : "stuck";
}

/** "Fri Nov 20" for a session's ISO date, read as a calendar date. */
export function sessionDay(iso: string | null | undefined): string {
  if (!iso) return "--";
  const [year, month, day] = iso.split("-").map(Number);
  const when = new Date(Date.UTC(year ?? 1970, (month ?? 1) - 1, day ?? 1));
  return when.toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    timeZone: "UTC",
  });
}

/** The trader's report of its session's overlay, as one line and a tone. */
export function overlayLine(status: TraderRiskOverlay | null | undefined): { text: string; tone: Tone } | null {
  if (!status) return null;
  if (status.state === "none") return { text: "Risk report: none for this session -- trading as configured.", tone: "neutral" };
  if (status.state === "unchecked") return null;
  const how = status.state === "in_force" ? "in force" : "suggested (advisory: not traded)";
  const tone: Tone = status.overlay?.pause || (status.overlay?.tier ?? 0) >= 2 ? "stuck" : "neutral";
  return { text: `Risk report, ${how}: ${status.summary}`, tone };
}

/** A refusal of the newest report, while it is recent: said at the top of the page. */
export function refusal(summary: RiskReportsSummary | undefined, now: number): string | null {
  const last = summary?.last;
  if (!last || last.status !== "rejected") return null;
  const at = Date.parse(last.finished_at ?? last.created_at);
  if (Number.isNaN(at) || now - at > REFUSAL_HOURS * 3600 * 1000) return null;
  return last.detail || "the trader refused it";
}
