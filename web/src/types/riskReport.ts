/**
 * The nightly risk report on the Live page (docs/daily_risk_report_plan.md).
 *
 * Hand-mirrored from server/: the overlay is engine/core/risk_overlay.py's
 * SessionOverlay.to_dict(), a mapped report research/risk_overlay/mapping.py's
 * Mapped.to_dict(), the preview research/risk_overlay/preview.py's, the
 * archive rows server/live.py's _slim_entry. Change both sides together.
 */

/** What one session is told. Every lever can only take risk away. */
export interface RiskOverlay {
  session: string | null;
  pause: boolean;
  buy_multiplier: number;
  exposure_ceiling: number | null;
  step_multiplier: number;
  target_multiplier: number;
  /** UTC [start, end] windows with no new buys. */
  blackouts: [string, string][];
  /** The strategy's day-level levers this report stands in for. */
  supersedes: ("governor" | "event_boosts")[];
  mode: "advisory" | "enforce";
  tier: number | null;
  weekly_ceiling: number | null;
  reasons: string[];
  mapping_id: string | null;
  report_sha256: string | null;
  exempt: string[];
}

export interface AuditFinding {
  level: "error" | "warning";
  where: string;
  message: string;
}

export interface Audit {
  ok: boolean;
  errors: AuditFinding[];
  warnings: AuditFinding[];
}

export interface Catalyst {
  event: string;
  impact: "low" | "medium" | "high";
  at: string | null;
  source: "report" | "engine";
}

/** How the mapping reached its overlay. */
export interface MappedReport {
  overlay: RiskOverlay;
  abstained: boolean;
  mapping_id: string;
  score: number | null;
  components: Partial<Record<"volatility" | "gap" | "regime" | "catalyst" | "tail", number>>;
  tier: number | null;
  move_pct: number | null;
  move_source: string | null;
  step_multiplier: number;
  weekly_ceiling: number | null;
  weekly_ratio: number | null;
  catalysts: Catalyst[];
  reasons: string[];
  /** The tier thresholds are not yet calibrated on the proxy. */
  provisional: boolean;
  summary: string;
}

export type Would = "apply" | "replace" | "tighten" | "not_applied" | "unchanged" | "refused";

/** POST .../risk-report/preview: what the report would do to one deployment. Writes nothing. */
export interface RiskReportPreview {
  deployment: string;
  label: string;
  symbol: string;
  paper: boolean;
  takes_reports: boolean;
  why_not: string | null;
  settings: OverlaySettings | null;
  /** Why the deployment's id must be typed back (real money), or null. */
  typed: string | null;
  audit: Audit;
  session?: string;
  sha256?: string;
  mapped?: MappedReport;
  notes?: string[];
  would?: Would;
  detail?: string | null;
  /** The session's overlay with the week's cap composed in. */
  overlay?: RiskOverlay;
  summary?: string;
  mode?: "advisory" | "enforce";
  existing?: { sha256: string; received_at: string; operator: string; summary: string } | null;
}

export interface OverlaySettings {
  mode: "advisory" | "enforce";
  mapping: string;
  levers: { daily: boolean; spacing: boolean; weekly: boolean };
}

/** DeploymentSummary.risk_reports: whether the page may send it a report. */
export interface RiskReportsSummary {
  takes: boolean;
  why_not: string | null;
  settings: OverlaySettings | null;
  /** The newest apply_risk_report and what came of it. */
  last?: {
    id: string;
    status: string;
    detail: string;
    created_at: string;
    finished_at: string | null;
    operator: string;
  } | null;
}

/** One received report (the archive's `receipts`). */
export interface ReportReceipt {
  sha256: string;
  received_at: string;
  operator: string;
  outcome: "applied" | "tightened" | "not_applied";
  detail: string;
  tier: number | null;
  abstained: boolean;
  weekly_ceiling: number | null;
}

/** One session's archived report (GET .../risk-reports). */
export interface RiskReportEntry {
  session: string;
  source: string;
  received_at: string;
  operator: string;
  as_of: string;
  sha256: string;
  mode: "advisory" | "enforce";
  mapping_id: string;
  outcome: "applied" | "tightened" | "not_applied";
  summary: string;
  overlay: RiskOverlay;
  tier: number | null;
  score: number | null;
  components: MappedReport["components"] | null;
  abstained: boolean | null;
  reasons: string[];
  warnings: number;
  /** What the trader made of it at the session's start. */
  start?: { at: string; overlay: RiskOverlay; summary: string; notes: string[] } | null;
  receipts: ReportReceipt[];
}

export interface RiskReports extends RiskReportsSummary {
  /** The overlay the next session would trade under, as its trader would read it now. */
  next: { session: string; overlay: RiskOverlay; summary: string; has_report: boolean } | null;
  sessions: RiskReportEntry[];
}

/** TraderStatus.risk_overlay: the session's report as the running trader holds it. */
export interface TraderRiskOverlay {
  session: string | null;
  mode: "advisory" | "enforce";
  state: "in_force" | "suggested" | "none" | "unchecked";
  summary: string;
  overlay: RiskOverlay | null;
  report: {
    sha256: string;
    received_at: string;
    operator: string;
    as_of: string;
    outcome: string;
    tier: number | null;
    score: number | null;
    abstained: boolean | null;
  } | null;
  notes: string[];
  checked_at: string | null;
}
