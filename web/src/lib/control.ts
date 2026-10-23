/**
 * The Live page's judgement calls about a deployment, as pure functions so
 * control.test.ts can pin them: what state it is in, which commands it
 * offers, and when one needs the deployment's id typed back.
 *
 * The server decides all of this again (server/live_control.py) -- these
 * exist so the page offers what will be accepted and says why the rest is
 * not, rather than letting a click find out.
 */
import { usd } from "@/lib/utils";
import type {
  Algorithm,
  AlgorithmInForce,
  AlgorithmView,
  Broker,
  BuildInfo,
  CommandRow,
  CommandStatus,
  CommandType,
  DeploymentSummary,
  Diagnostics,
  FidelityConnection,
  TraderFill,
  Impact,
  RunState,
  Timing,
} from "@/types/control";
import type { LiveState } from "@/types/telemetry";

export type Tone = "neutral" | "profit" | "loss" | "stuck";

const CHIPS: Record<RunState, { label: string; tone: Tone }> = {
  trading: { label: "Trading", tone: "profit" },
  buys_paused: { label: "Buys paused", tone: "stuck" },
  winding_down: { label: "Winding down", tone: "stuck" },
  waiting_for_open: { label: "Waiting for open", tone: "neutral" },
  closed: { label: "Between sessions", tone: "neutral" },
  disabled: { label: "Disabled", tone: "loss" },
  starting: { label: "Starting", tone: "neutral" },
  restarting: { label: "Restarting", tone: "stuck" },
  stopping: { label: "Stopping", tone: "stuck" },
  stopped: { label: "Stopped", tone: "neutral" },
  recovery_required: { label: "Recovery required", tone: "loss" },
  not_running: { label: "Not running", tone: "loss" },
};

/** The deployment's state as one chip, with the line under it. */
export function chip(d: DeploymentSummary): { label: string; tone: Tone; detail: string } {
  if (d.error) return { label: "Config error", tone: "loss", detail: d.error };
  if (!d.controllable || !d.status) {
    return {
      label: "Not controlled",
      tone: "neutral",
      detail: "config/deployments.yaml names no control directory for it",
    };
  }
  const { label, tone } = CHIPS[d.status.state] ?? { label: d.status.state, tone: "neutral" };
  let detail = d.status.detail ?? "";
  if (d.status.state === "not_running" && d.service) {
    detail = `${detail} -- start it with \`docker compose up -d ${d.service}\``;
  }
  return { label, tone, detail };
}

export type ActionId =
  | "pause"
  | "resume"
  | "disable_now"
  | "wind_down"
  | "enable"
  | "reset_ledger";

export interface Action {
  id: ActionId;
  label: string;
  type: CommandType;
  args: Record<string, unknown>;
  /** null when it can be sent; otherwise why not. */
  blocked: string | null;
  /** The deployment's id must be typed back -- the server checks it too. */
  typed: string | null;
  /** Shown in the confirmation: what happens, plainly. */
  effect: string;
  danger: boolean;
}

function lots(d: DeploymentSummary): number {
  return d.ledger?.open_lots ?? d.status?.open_lots ?? 0;
}

/** Why a command needs the id typed back, or null. Mirrors
 * server/live_control.py confirmation_needed. */
export function typedReason(
  d: DeploymentSummary,
  type: CommandType,
  args: Record<string, unknown> = {},
): string | null {
  if (d.paper === false && type !== "pause_buys") return "this deployment trades real money";
  if (type === "reset_paper_ledger") return "the ledger it has is archived and a fresh one started";
  if (type === "disable" && (args.mode ?? "now") === "now") {
    const open = lots(d);
    if (open > 0) return `${open} open lot${open === 1 ? "" : "s"} would get no exits while disabled`;
  }
  return null;
}

function grant(
  d: DeploymentSummary,
  key: "resume_buys" | "enable_disable" | "ledger_reset",
): string | null {
  if (!d.controllable) return "no control directory";
  return d.caps?.[key] ? null : `its config does not grant live.control.${key}`;
}

/** The commands this deployment offers right now, in the order shown. */
export function actions(d: DeploymentSummary): Action[] {
  if (d.error || !d.controllable) return [];
  const halted = Boolean(d.ledger?.halt);
  const desired = d.desired ?? { enabled: true, wind_down: false };
  const open = lots(d);
  const result: Action[] = [];
  const add = (action: Omit<Action, "typed">) =>
    result.push({ ...action, typed: typedReason(d, action.type, action.args) });

  if (!halted) {
    add({
      id: "pause",
      label: "Pause buys",
      type: "pause_buys",
      args: {},
      blocked: null,
      effect: "No new buys from the next tick. Open lots keep exiting at their targets.",
      danger: false,
    });
  } else {
    add({
      id: "resume",
      label: "Resume buys",
      type: "resume_buys",
      args: {},
      blocked: grant(d, "resume_buys"),
      effect: "Clears the halt; buying resumes at the next tick.",
      danger: false,
    });
  }
  if (desired.enabled && !desired.wind_down) {
    add({
      id: "wind_down",
      label: "Wind down",
      type: "disable",
      args: { mode: "wind_down" },
      blocked: grant(d, "enable_disable"),
      effect:
        open > 0
          ? `Pauses buys now and keeps managing ${open} open lot${open === 1 ? "" : "s"}; ` +
            "trading stops by itself once none are left."
          : "Nothing is open, so this disables it now.",
      danger: false,
    });
    add({
      id: "disable_now",
      label: "Disable now",
      type: "disable",
      args: { mode: "now" },
      blocked: grant(d, "enable_disable"),
      effect:
        open > 0
          ? `Stops after the current tick. ${open} open lot${open === 1 ? "" : "s"} get NO exits ` +
            "-- not at a target, not by a regime exit -- until it is enabled."
          : "Stops after the current tick; no session starts until it is enabled.",
      danger: true,
    });
  } else {
    add({
      id: "enable",
      label: desired.wind_down ? "Cancel wind-down" : "Enable",
      type: "enable",
      args: {},
      blocked: grant(d, "enable_disable"),
      effect: desired.wind_down
        ? "Keeps trading; new buys stay paused until resumed."
        : "Sessions start again; inside market hours the loop starts now.",
      danger: false,
    });
  }
  if (d.paper && d.caps?.ledger_reset) {
    add({
      id: "reset_ledger",
      label: "Fresh paper ledger",
      type: "reset_paper_ledger",
      args: {},
      blocked: desired.enabled ? "disable it first" : null,
      effect:
        "Archives this ledger (moved beside it, not deleted) and starts a fresh one with the " +
        "paper account's cash. Refused unless the Alpaca paper account holds no positions and " +
        "no open orders -- reset the account in Alpaca's dashboard first.",
      danger: true,
    });
  }
  return result;
}

/** Deployments that report the same account tag as another enabled one:
 * two loops on one account diverge both ledgers from the venue. Keyed by
 * deployment id, naming the others. */
export function sharedAccounts(deployments: DeploymentSummary[]): Record<string, string[]> {
  const live = deployments.filter(
    (d) => d.status && !d.status.stale && d.status.account && d.desired?.enabled,
  );
  const out: Record<string, string[]> = {};
  for (const d of live) {
    const others = live
      .filter((o) => o.id !== d.id && o.status?.account === d.status?.account)
      .map((o) => o.label);
    if (others.length) out[d.id] = others;
  }
  return out;
}

const LABELS: Record<CommandType, string> = {
  pause_buys: "Pause buys",
  resume_buys: "Resume buys",
  disable: "Disable",
  enable: "Enable",
  switch_algorithm: "Switch algorithm",
  revert_algorithm: "Revert algorithm",
  rewarm: "Re-warm",
  reset_paper_ledger: "Fresh paper ledger",
};

export function commandLabel(row: Pick<CommandRow, "type" | "args">): string {
  if (row.type === "disable") return row.args.mode === "wind_down" ? "Wind down" : "Disable now";
  if (row.type === "resume_buys" && row.args.reset_drawdown_baseline) {
    return "Resume buys (drawdown baseline reset)";
  }
  return LABELS[row.type] ?? row.type;
}

export function statusTone(status: CommandStatus): Tone {
  if (status === "applied") return "profit";
  if (status === "rejected" || status === "expired") return "loss";
  if (status === "queued" || status === "applying") return "stuck";
  return "neutral";
}

const OPERATOR_KEY = "vai.operator";

/** The operator's name, remembered in this browser. Per-viewer only. */
export function rememberedOperator(): string {
  try {
    return window.localStorage.getItem(OPERATOR_KEY) ?? "";
  } catch {
    return "";
  }
}

export function rememberOperator(name: string): void {
  try {
    window.localStorage.setItem(OPERATOR_KEY, name);
  } catch {
    /* private mode: asked again next time */
  }
}

/* ------------------------------------------------------------------ */
/* The algorithm panel                                                 */
/* ------------------------------------------------------------------ */

function fraction(value: number | null | undefined): string {
  if (value === null || value === undefined) return "--";
  return `${Number((value * 100).toPrecision(6))}%`;
}

/** "ultimate · step 0.075% · target 30%" */
export function algorithmLabel(a: Pick<Algorithm, "strategy_id" | "step" | "profit_target">): string {
  return `${a.strategy_id} · step ${fraction(a.step)} · target ${fraction(a.profit_target)}`;
}

export interface AlgorithmDiff {
  field: string;
  from: string;
  to: string;
}

/** What a switch changes, field by field -- strategy, grid, then each
 * parameter that differs (a parameter only one side sets shows "--"). */
export function diffAlgorithms(from: Algorithm, to: Algorithm): AlgorithmDiff[] {
  const out: AlgorithmDiff[] = [];
  if (from.strategy_id !== to.strategy_id) {
    out.push({ field: "strategy", from: from.strategy_id, to: to.strategy_id });
  }
  if (from.step !== to.step) out.push({ field: "step", from: fraction(from.step), to: fraction(to.step) });
  if (from.profit_target !== to.profit_target) {
    out.push({
      field: "profit target",
      from: fraction(from.profit_target),
      to: fraction(to.profit_target),
    });
  }
  const names = new Set([...Object.keys(from.strategy_params), ...Object.keys(to.strategy_params)]);
  for (const name of [...names].sort()) {
    const before = from.strategy_params[name];
    const after = to.strategy_params[name];
    if (String(before) !== String(after)) {
      out.push({
        field: name,
        from: before === undefined ? "--" : String(before),
        to: after === undefined ? "--" : String(after),
      });
    }
  }
  return out;
}

/** When a switch should apply unless the operator says otherwise: a
 * strategy with a signal exit on either side changes how open lots leave,
 * so it waits for the next session; anything else takes the next tick. */
export function defaultTiming(impact: Impact | undefined): Timing {
  return impact && (impact.signal_exit_before || impact.signal_exit_after)
    ? "next_session"
    : "now";
}

/** Where the algorithm in force came from, for the panel's header. */
export function sourceLabel(view: Pick<AlgorithmView, "source" | "override">): string {
  if (view.source === "config" || !view.override) return "the config file";
  const by = view.override.changedBy ? ` by ${view.override.changedBy}` : "";
  const profile = view.override.profile ? ` (profile ${view.override.profile})` : "";
  const where = view.source === "web" ? "the Live page" : "the browser extension";
  return `${where}${by}${profile}`;
}

/* ------------------------------------------------------------------ */
/* Reading a deployment: its venue, its algorithm, what it is doing    */
/* ------------------------------------------------------------------ */

export interface BrokerSection {
  broker: Broker;
  title: string;
  blurb: string;
  deployments: DeploymentSummary[];
}

const SECTIONS: Record<Broker, { title: string; blurb: string }> = {
  alpaca: {
    title: "Alpaca",
    blurb: "Paper and real-money accounts, traded through Alpaca's API.",
  },
  fidelity: {
    title: "Fidelity",
    blurb: "Real money in a Fidelity account, traded through the Fidelity Bridge browser extension.",
  },
};

/** The deployments by venue, Alpaca first. Both sections always: an empty
 * Fidelity section says so rather than vanishing. */
export function byBroker(deployments: DeploymentSummary[]): BrokerSection[] {
  return (["alpaca", "fidelity"] as const).map((broker) => ({
    broker,
    ...SECTIONS[broker],
    deployments: deployments.filter((d) => (d.broker ?? "alpaca") === broker),
  }));
}

/** A profile's label when the algorithm is one, else its strategy id. */
export function algorithmName(a: Pick<AlgorithmInForce, "label" | "strategy_id">): string {
  return a.label ?? a.strategy_id;
}

/** The grid every strategy here trades, in words. */
export function gridWords(step: number | null, target: number | null): string {
  if (step === null || target === null) return "its grid is not stated";
  return `buys each ${fraction(step)} dip, sells each lot at +${fraction(target)}`;
}

/** Where the algorithm in force came from -- without the time, which the
 * page formats in the reader's own zone. */
export function algorithmOrigin(a: AlgorithmInForce): string {
  if (a.source === "config") return "the config file's algorithm";
  const where = a.source === "web" ? "the Live page" : "the browser extension";
  return `switched on ${where}${a.changed_by ? ` by ${a.changed_by}` : ""}`;
}

/** "Mon, Oct 26" for an ISO session date -- the session's own day, in any
 * reader's time zone. */
export function sessionDay(iso: string): string {
  return new Date(`${iso}T12:00:00Z`).toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    timeZone: "UTC",
  });
}

function capitalised(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/** Ultimate's regime in words, from its diagnostics -- null for a strategy
 * that has none. Why it is (not) grid-buying, and when that may change. */
export function regimeLine(diag: Diagnostics | null | undefined): string | null {
  const mode = diag?.ultimate_mode;
  if (typeof mode !== "string") return null;
  const since = typeof diag?.regime_since === "string" ? ` since ${sessionDay(diag.regime_since)}` : "";
  const natr = diag?.regime_natr;
  const median = diag?.regime_median;
  const reading =
    typeof natr === "number" && typeof median === "number"
      ? ` (volatility ${natr.toFixed(2)} against its median ${median.toFixed(2)} at the last close)`
      : "";
  const doing =
    mode === "turbulent"
      ? "no grid buys, only a reversal lot on a deep down day"
      : "buying on every dip";
  const earliest =
    typeof diag?.regime_earliest_change === "string"
      ? `; it can change ${sessionDay(diag.regime_earliest_change)} at the earliest`
      : "";
  return `${capitalised(mode)}${since}${reading}: ${doing}${earliest}.`;
}

export interface Line {
  text: string;
  tone: Tone;
}

/** What the deployment is doing about buying right now, in the trader's
 * terms; null when no loop is trading (the state chip says why). */
export function nowLine(d: DeploymentSummary): Line | null {
  const status = d.status;
  if (!status || status.stale || status.process !== "loop") return null;
  if (status.broker_unavailable) {
    return { text: `Waiting for the broker: ${status.broker_unavailable}`, tone: "stuck" };
  }
  const now = status.now;
  if (!now) return null;
  if (now.blocked) return { text: `Not buying: ${now.blocked}.`, tone: "stuck" };
  if (now.buy_level !== null) {
    const below = now.price > 0 ? ((now.price - now.buy_level) / now.price) * 100 : null;
    return {
      text:
        `Next buy at or below ${usd(now.buy_level)}` +
        (below !== null && below > 0 ? ` (${below.toFixed(2)}% under ${usd(now.price)})` : "") +
        ".",
      tone: "profit",
    };
  }
  return null;
}

/** While an override trades: what switching back to the config file's
 * algorithm would do right now, from the trader's shadow of it. */
export function shadowLine(d: DeploymentSummary): Line | null {
  const shadow = d.status?.shadow;
  const algorithm = d.algorithm;
  if (!shadow || !algorithm || algorithm.source === "config" || d.status?.stale) return null;
  const name = algorithm.config_file.strategy_id;
  const regime = regimeLine(shadow.strategy);
  const tail = regime ? ` ${name}: ${regime}` : "";
  if (shadow.strategy?.ultimate_exit_active === true) {
    const open = d.status?.open_lots ?? 0;
    const reversal = Number(shadow.strategy.ultimate_reversal_tagged ?? 0);
    const lots = Math.max(open - reversal, 0);
    return {
      tone: "loss",
      text:
        `Switching back to ${name} now would sell ${lots} open lot${lots === 1 ? "" : "s"} at ` +
        "market from an hour after the open, below cost if need be: its regime exit is " +
        `active until the market reads calm.${tail}`,
    };
  }
  if (shadow.would_sell > 0) {
    return {
      tone: "loss",
      text:
        `Switching back to ${name} now would sell ${shadow.would_sell} lot` +
        `${shadow.would_sell === 1 ? "" : "s"} (${usd(shadow.would_sell_cost, 0)} cost) at market.${tail}`,
    };
  }
  return { tone: "neutral", text: `Switching back to ${name} now would sell nothing.${tail}` };
}

export interface Position {
  lots: number;
  shares: number;
  cost: number;
  /** null without a mark to value the book at. */
  value: number | null;
  unrealized: number | null;
  average: number | null;
}

/** The open book, valued at the trader's last mark. */
export function position(state: LiveState | null): Position {
  const lots = state?.lots ?? [];
  const shares = lots.reduce((total, lot) => total + lot.qty, 0);
  const cost = lots.reduce((total, lot) => total + lot.qty * lot.px, 0);
  const mark = state?.last_px ?? null;
  const value = mark ? shares * mark : null;
  return {
    lots: lots.length,
    shares,
    cost,
    value,
    unrealized: value === null ? null : value - cost,
    average: shares > 0 ? cost / shares : null,
  };
}

/** A session's fills, totalled. Realised is what sales fetched against what
 * their lots cost -- from the trader's own fill journal, since the ledger
 * keeps no sale price. */
export function tradeTotals(fills: TraderFill[]): {
  buys: number;
  sells: number;
  bought: number;
  realized: number;
} {
  let buys = 0;
  let sells = 0;
  let bought = 0;
  let realized = 0;
  for (const fill of fills) {
    if (fill.side === "buy") {
      buys += 1;
      bought += fill.value ?? fill.qty * fill.price;
    } else {
      sells += 1;
      realized += fill.pnl ?? 0;
    }
  }
  return { buys, sells, bought, realized };
}

/** The Fidelity Bridge extension's connection as one chip. */
export function fidelityChip(
  f: FidelityConnection | null | undefined,
  reporting: boolean,
): { label: string; tone: Tone; detail: string } {
  if (!reporting) {
    return {
      label: "No report",
      tone: "neutral",
      detail: "The Fidelity engine is not running, so nothing reports the extension's state.",
    };
  }
  if (!f) {
    return {
      label: "Bridge not up",
      tone: "stuck",
      detail: "The engine has not reached the bridge yet (between sessions, or starting).",
    };
  }
  if (!f.connected) {
    return {
      label: "Extension disconnected",
      tone: "loss",
      detail:
        "No browser extension is connected: open the browser with Fidelity Bridge installed and " +
        "signed into Fidelity. The engine waits; nothing is placed meanwhile.",
    };
  }
  if (f.permissions && !f.permissions.place) {
    return {
      label: "Trading switched off",
      tone: "stuck",
      detail:
        "Allow trading is off in the extension: every order is refused in the browser until " +
        "it is switched back on. The engine keeps reading and applying fills.",
    };
  }
  if (f.mode === "preview") {
    return {
      label: "Preview only",
      tone: "neutral",
      detail: "live.fidelity.dry_run is on: orders stop at Fidelity's preview.",
    };
  }
  return {
    label: "Connected · trading allowed",
    tone: "profit",
    detail: "The extension is connected and allows trading: orders go to Fidelity.",
  };
}

/** Whether a trader runs the same code as this web server; null when either
 * cannot say. */
export function sameCode(
  trader: BuildInfo | null | undefined,
  web: string | null | undefined,
): boolean | null {
  if (!trader?.code || !web) return null;
  return trader.code === web;
}
