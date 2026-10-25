/**
 * A Fidelity deployment's connection, as the Live page says it: one verdict,
 * the chain of links from this server to the account, and the bridge host's
 * journal as a timeline -- pure functions over what the bridge host reports
 * (fidelity_gateway/bridge/host.py, readiness.py), so fidelity.test.ts can
 * pin them.
 *
 * The bridge host stays up between sessions, so all of this reads correctly
 * at 2 a.m. as well as during one. A deployment with no bridge host (one
 * whose trading loop holds the bridge itself) falls back to what its trader
 * reports, which exists only while a loop runs.
 */
import { fidelityChip, type Tone } from "@/lib/control";
import type {
  BridgeAttached,
  BridgeEvent,
  BridgeStatus,
  DeploymentSummary,
  ReadinessItem,
} from "@/types/control";

const EASTERN = "America/New_York";
const ACTIVE = new Set(["trading", "buys_paused", "winding_down"]);

export interface Verdict {
  label: string;
  tone: Tone;
  detail: string;
  /** What to do about it, when something is wrong; null otherwise. */
  fix: string | null;
}

export type StepState = ReadinessItem["state"];

export interface Step {
  id: ReadinessItem["id"] | "trader";
  label: string;
  state: StepState;
  detail: string;
  fix: string | null;
}

export interface TimelineRow {
  t: number;
  kind: string;
  text: string;
  tone: Tone;
  /** For a reconnect: how long the extension was gone. */
  span: string | null;
}

/** "45 s", "10 min", "2 h 5 min", "3 d 4 h". */
export function duration(seconds: number): string {
  const s = Math.max(0, Math.round(seconds));
  if (s < 90) return `${s} s`;
  const minutes = Math.round(s / 60);
  if (minutes < 90) return `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  if (hours < 48) return minutes % 60 ? `${hours} h ${minutes % 60} min` : `${hours} h`;
  const days = Math.floor(hours / 24);
  return hours % 24 ? `${days} d ${hours % 24} h` : `${days} d`;
}

/** "12 s ago" from an ISO time; "never" without one. */
export function ago(iso: string | null | undefined, now: number): string {
  if (!iso) return "never";
  const at = Date.parse(iso);
  if (Number.isNaN(at)) return "at an unreadable time";
  const seconds = (now - at) / 1000;
  return seconds < 2 ? "just now" : `${duration(seconds)} ago`;
}

/** A session's time in the market's own zone: "09:30 ET" on the same day,
 * "Mon 09:30 ET" on another -- whatever zone the reader is in. */
export function sessionTime(iso: string | null | undefined, now: number): string {
  if (!iso) return "the next session";
  const at = new Date(iso);
  const day = (d: Date) => d.toLocaleDateString("en-US", { timeZone: EASTERN });
  const clock = at.toLocaleTimeString("en-US", {
    timeZone: EASTERN,
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
  if (day(at) === day(new Date(now))) return `${clock} ET`;
  const weekday = at.toLocaleDateString("en-US", { timeZone: EASTERN, weekday: "short" });
  return `${weekday} ${clock} ET`;
}

/** "the trading loop (pid 4117)", "a connection check". */
export function attachedWords(attached: Pick<BridgeAttached, "process" | "pid">): string {
  const what =
    attached.process === "loop"
      ? "the trading loop"
      : attached.process === "check"
        ? "a connection check"
        : `a ${attached.process ?? "process"}`;
  return attached.pid ? `${what} (pid ${attached.pid})` : what;
}

/** The deployment's connection in one verdict: Trading, Ready for when, or
 * Not ready and the one thing to fix. */
export function verdict(d: DeploymentSummary, now: number): Verdict {
  const bridge = d.bridge;
  const status = d.status;
  if (!bridge) {
    const legacy = fidelityChip(status?.fidelity, Boolean(status && !status.stale));
    return { ...legacy, fix: null };
  }
  if (bridge.stale) {
    return {
      label: "Bridge host not reporting",
      tone: "loss",
      detail:
        `Its last report was ${ago(bridge.updated_at, now)}. Nothing may be listening for ` +
        "the extension, so no session can start.",
      fix: "docker compose --profile fidelity up -d fidelity-bridge",
    };
  }
  const readiness = bridge.readiness;
  if (!readiness.ready) {
    const item = readiness.items.find((i) => i.id === readiness.blocking);
    return {
      label: `Not ready: ${item?.label ?? "the connection"}`,
      tone: "loss",
      detail: readiness.summary,
      fix: readiness.fix,
    };
  }
  const warning = readiness.items.find((i) => i.state === "warn");
  if (status && !status.stale && status.process === "loop" && ACTIVE.has(status.state)) {
    return {
      label: "Connected · trading",
      tone: "profit",
      detail: warning
        ? `Trading. ${warning.label}: ${warning.detail}.`
        : "The extension is connected, Fidelity signed in and orders allowed.",
      fix: null,
    };
  }
  if (bridge.session_open) {
    return {
      label: "Ready · session open",
      tone: "profit",
      detail: bridge.attached
        ? `${capital(attachedWords(bridge.attached))} is attached and starting.`
        : "Everything is in place; the session's trading loop attaches when it starts.",
      fix: null,
    };
  }
  return {
    label: `Ready for ${sessionTime(bridge.next_open, now)}`,
    tone: "profit",
    detail: warning
      ? `${warning.label}: ${warning.detail}.`
      : "Everything the next session needs is in place.",
    fix: null,
  };
}

function capital(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function item(bridge: BridgeStatus, id: ReadinessItem["id"]): ReadinessItem | undefined {
  return bridge.readiness.items.find((i) => i.id === id);
}

/** Bridge -> Extension -> Fidelity tab -> Allow trading -> Trader ->
 * Account check, each with its state, detail and fix. The extension's
 * "last heard" is counted from `now`, so it moves between reports. */
export function chain(bridge: BridgeStatus, now: number): Step[] {
  const steps: Step[] = [];
  const add = (id: ReadinessItem["id"]) => {
    const found = item(bridge, id);
    if (found) steps.push({ ...found });
  };
  add("bridge");

  const extension = item(bridge, "extension");
  const version = item(bridge, "version");
  if (extension) {
    const connection = bridge.connection;
    let detail = extension.detail;
    let state = extension.state;
    if (connection.connected && extension.state === "ok") {
      detail =
        `from ${connection.client ?? "?"}` +
        (connection.version ? ` · v${connection.version}` : "") +
        ` · last heard ${ago(connection.last_heard, now)}`;
    }
    if (version?.state === "warn" && state === "ok") {
      state = "warn";
      detail += ` · ${version.detail}`;
    }
    steps.push({ ...extension, state, detail });
  }

  add("fidelity");
  add("trading");

  const attached = bridge.attached;
  if (attached) {
    steps.push({
      id: "trader",
      label: "Trader",
      state: "ok",
      detail: `${attachedWords(attached)} since ${attached.since ? ago(attached.since, now) : "?"}`,
      fix: null,
    });
  } else if (bridge.session_open) {
    steps.push({
      id: "trader",
      label: "Trader",
      state: "warn",
      detail: "a session is open and no trading loop is attached",
      fix: "the Fidelity trader starts one as soon as the connection is ready -- see its state above",
    });
  } else {
    steps.push({
      id: "trader",
      label: "Trader",
      state: "unknown",
      detail: `none until ${sessionTime(bridge.next_open, now)}`,
      fix: null,
    });
  }

  add("account");
  return steps;
}

const TONES: Record<string, Tone> = {
  started: "neutral",
  stopped: "stuck",
  listening: "profit",
  port_conflict: "loss",
  config: "neutral",
  connected: "profit",
  disconnected: "loss",
  refused: "loss",
  attached: "neutral",
  detached: "neutral",
  attach_refused: "stuck",
  ready: "profit",
  not_ready: "stuck",
};

function toneOf(event: BridgeEvent): Tone {
  if (event.kind === "fidelity") return event.state === "signed_in" ? "profit" : "loss";
  if (event.kind === "trading") return event.on ? "profit" : "stuck";
  if (event.kind === "check") return event.ok ? "profit" : "loss";
  return TONES[event.kind] ?? "neutral";
}

/** The journal, newest first, with each reconnect saying how long the
 * extension was gone. */
export function timeline(events: BridgeEvent[]): TimelineRow[] {
  const rows: TimelineRow[] = [];
  let goneAt: number | null = null;
  for (const event of [...events].sort((a, b) => a.t - b.t)) {
    let span: string | null = null;
    if (event.kind === "disconnected") goneAt = event.t;
    if (event.kind === "connected" && goneAt !== null) {
      span = `back after ${duration(event.t - goneAt)}`;
      goneAt = null;
    }
    rows.push({ t: event.t, kind: event.kind, text: event.detail, tone: toneOf(event), span });
  }
  return rows.reverse();
}

/** How long the extension has been gone, when it has: for the banner. */
export function goneFor(bridge: BridgeStatus, now: number): string | null {
  const connection = bridge.connection;
  if (connection.connected || !connection.disconnected_at) return null;
  return duration((now - Date.parse(connection.disconnected_at)) / 1000);
}
