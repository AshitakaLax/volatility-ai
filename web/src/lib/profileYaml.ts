/**
 * A backtest configuration as a live algorithm profile
 * (config/live_profiles/<id>.yaml -- research/strategies/live_profiles.py),
 * for the operator to review and commit.
 *
 * TEXT, NOT A WRITE. config/ is read-only to the server on purpose: what a
 * deployment may switch to -- and for real money, what may trade at all --
 * stays a reviewable decision in git. The page proposes; a commit decides.
 *
 * Every string is written JSON-quoted (JSON strings are valid YAML), so a
 * run name with a colon or a quote cannot change the document's shape.
 */
import type { Cell, Report } from "@/types/backtest";

/** The profile id: the strategy and fund, a-z 0-9 and -, as the loader
 * requires -- and the file must be named after it. */
export function profileId(model: string, ticker: string): string {
  return `${model}-${ticker}`
    .toLowerCase()
    .replace(/[^a-z0-9-]+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 60);
}

function scalar(value: unknown): string {
  if (typeof value === "number") return Number.isFinite(value) ? String(value) : "null";
  if (typeof value === "boolean") return value ? "true" : "false";
  if (value === null || value === undefined) return "null";
  return JSON.stringify(String(value));
}

export function profileYaml(report: Report, ticker: string, cell: Cell): string {
  const model = report.model ?? "unknown";
  const id = profileId(model, ticker);
  const fund = report.funds[ticker];
  const m = cell.m;
  const lines = [
    `# Proposed from backtest ${report.id}${report.name ? ` (${report.name})` : ""}.`,
    `# Review it, save it as config/live_profiles/${id}.yaml and commit it. A paper`,
    "# deployment can switch to it from the Live page once it is in git; real money",
    "# also needs evidence.promotion naming a PASSING paper promotion.",
    `id: ${id}`,
    `label: ${scalar(`${model} on ${ticker} (backtest ${report.id})`)}`,
    `symbols: [${scalar(ticker)}]`,
    `strategy_id: ${scalar(model)}`,
  ];
  const params = Object.entries(cell.params);
  if (params.length === 0) {
    lines.push("strategy_params: {}");
  } else {
    lines.push("strategy_params:");
    for (const [name, value] of params) lines.push(`  ${name}: ${scalar(value)}`);
  }
  lines.push(
    `step: ${scalar(cell.grid)}`,
    `profit_target: ${scalar(cell.target)}`,
    "evidence:",
    "  backtest:",
    `    run: ${scalar(report.id)}`,
  );
  if (report.name) lines.push(`    name: ${scalar(report.name)}`);
  lines.push(
    `    net_yield_pct: ${scalar(m.net_yield_pct)}`,
    `    cagr_pct: ${scalar(m.cagr_pct)}`,
    `    max_drawdown_pct: ${scalar(m.max_drawdown_pct)}`,
  );
  if (m.return_over_drawdown !== undefined) {
    lines.push(`    return_over_drawdown: ${scalar(m.return_over_drawdown)}`);
  }
  if (fund) lines.push(`    window: ${scalar(`${fund.bars.start} to ${fund.bars.end}`)}`);
  return `${lines.join("\n")}\n`;
}
