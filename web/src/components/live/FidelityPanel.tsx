import { Loader2, PlugZap, RefreshCw } from "lucide-react";
import { useState, type ReactNode } from "react";

import { Badge, Button, Card, CardContent, CardHeader, CardTitle } from "@/components/ui/primitives";
import { useNow } from "@/hooks/useNow";
import { api } from "@/lib/api";
import {
  algorithmName,
  algorithmOrigin,
  algorithmWords,
  chip,
  fidelityChip,
  rememberedOperator,
} from "@/lib/control";
import { ago, attachedWords, chain, goneFor, verdict } from "@/lib/fidelity";
import { cn, usd } from "@/lib/utils";
import type { DeploymentDetail, DeploymentSummary } from "@/types/control";

import { ConnectionChain } from "./ConnectionChain";
import { ConnectionTimeline } from "./ConnectionTimeline";

/**
 * A Fidelity deployment's other half: the connection it trades through.
 * Every order goes from this server over the Fidelity Bridge extension into
 * the signed-in Fidelity tab, so the questions here are the ones that
 * decide whether anything can be placed at all -- is it connected, is
 * Fidelity signed in, is "Allow trading" on -- answered by the deployment's
 * bridge host (fidelity_gateway/bridge/host.py), which stays up between
 * sessions. So this reads the same at 2 a.m. as during a session: one
 * verdict, the chain of links with the first broken one and its fix, what
 * is running, the last account check (and a button for another), and the
 * timeline that explains any disconnect after the fact.
 *
 * This page never talks to the extension itself; the check is a command the
 * bridge host applies, read-only.
 */
const BANNER = {
  neutral: "border-border bg-secondary/30",
  profit: "border-profit/40 bg-profit/10",
  loss: "border-loss/50 bg-loss/10",
  stuck: "border-stuck/40 bg-stuck/10",
} as const;

const TITLE = {
  neutral: "",
  profit: "text-profit",
  loss: "text-loss",
  stuck: "text-stuck",
} as const;

export function FidelityPanel({
  deployment,
  onSent,
}: {
  deployment: DeploymentDetail;
  onSent?: (() => void) | undefined;
}) {
  const now = useNow(1000);
  const bridge = deployment.bridge;
  const summary = verdict(deployment, now);

  return (
    <Card className="border-loss/40">
      <CardHeader className="flex-row flex-wrap items-center justify-between gap-2">
        <CardTitle className="flex items-center gap-2">
          <PlugZap className="size-4" />
          Fidelity connection
        </CardTitle>
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="loss">real money</Badge>
          <Badge tone={summary.tone} title={summary.detail}>
            {summary.label}
          </Badge>
          {bridge && !deployment.setup ? (
            <CheckNow deployment={deployment} onSent={onSent} />
          ) : null}
        </div>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        {deployment.setup ? (
          <Setup deployment={deployment} />
        ) : bridge ? (
          <>
            <EngineLine deployment={deployment} />
            <div className={cn("rounded-md border p-3", BANNER[summary.tone])}>
              <p className={cn("font-medium", TITLE[summary.tone])}>{summary.label}</p>
              <p className="text-xs text-muted-foreground">{summary.detail}</p>
              {(() => {
                const gone = bridge.stale ? null : goneFor(bridge, now);
                const last = bridge.connection.last_disconnect;
                return gone ? (
                  <p className="mt-1 text-xs">
                    The extension has been gone {gone}
                    {last?.code ? ` (closed with ${last.code}${last.reason ? `: ${last.reason}` : ""})` : ""}.
                  </p>
                ) : null;
              })()}
              {summary.fix ? (
                <p className="mt-1 text-xs">
                  <span className="font-medium">To fix:</span> <code>{summary.fix}</code>
                </p>
              ) : null}
            </div>

            {bridge.stale ? null : <ConnectionChain steps={chain(bridge, now)} />}

            <Running deployment={deployment} now={now} />

            <ConnectionTimeline deploymentId={deployment.id} />

            <p className="text-xs text-muted-foreground">
              Turning "Allow trading" off in the extension pauses this engine's orders without
              stopping it -- every order is refused in the browser, and the engine keeps reading
              and applying fills. Turning it back on resumes them.
            </p>
          </>
        ) : (
          <Legacy deployment={deployment} />
        )}
      </CardContent>
    </Card>
  );
}

/** The ENGINE's own readiness -- its strategy built and history replayed --
 * apart from Fidelity's (the banner below): a deployment on its venue's
 * windows (live.sessions) starts its engine before the window opens, and
 * says it is ready before it asks Fidelity anything. Absent otherwise. */
function EngineLine({ deployment }: { deployment: DeploymentDetail }) {
  const engine = deployment.status?.stale ? null : deployment.status?.engine;
  if (!engine) return null;
  const tone = engine.state === "trading" || engine.state === "ready" ? "profit" : "neutral";
  const label = {
    starting: "Engine starting",
    warming_up: "Engine warming up",
    ready: "Engine ready",
    trading: "Engine trading",
  }[engine.state];
  return (
    <div className="flex flex-wrap items-center gap-2 text-xs">
      <Badge tone={tone}>{label}</Badge>
      <span className="text-muted-foreground">{engine.detail}</span>
      <span className="text-muted-foreground">· Fidelity's own readiness is below.</span>
    </div>
  );
}

/** The read-only account check, from the bridge host: queued, applied, and
 * its result shown in the Account step and the command log. */
function CheckNow({
  deployment,
  onSent,
}: {
  deployment: DeploymentDetail;
  onSent?: (() => void) | undefined;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pending = deployment.commands.some(
    (row) => row.type === "check_connection" && (row.status === "queued" || row.status === "applying"),
  );

  const send = async () => {
    setBusy(true);
    setError(null);
    try {
      await api.sendCommand(deployment.id, {
        type: "check_connection",
        reason: "checking the Fidelity connection from the Live page",
        operator: rememberedOperator() || "Live page",
      });
      onSent?.();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setBusy(false);
    }
  };

  return (
    <span className="flex items-center gap-2">
      {error ? <span className="text-xs text-loss">{error}</span> : null}
      <Button
        variant="outline"
        className="h-7 px-2 text-xs"
        onClick={send}
        disabled={busy || pending}
        title="A read-only look at the account through the extension: orders, positions, settled cash"
      >
        {busy || pending ? (
          <Loader2 className="size-3.5 animate-spin" aria-hidden />
        ) : (
          <RefreshCw className="size-3.5" aria-hidden />
        )}
        {pending ? "Checking..." : "Check connection"}
      </Button>
    </span>
  );
}

/** What is running: the algorithm in force, the trader, the mode, the
 * account and the extension's own facts. */
function Running({ deployment, now }: { deployment: DeploymentDetail; now: number }) {
  const bridge = deployment.bridge!;
  const algorithm = deployment.algorithm;
  const trader = chip(deployment);
  const status = deployment.status;
  const connection = bridge.connection;
  const check = bridge.last_check;
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <Fact label="Algorithm">
        {algorithm ? (
          <>
            <span className="font-medium">{algorithmName(algorithm)}</span>
            <span className="text-xs text-muted-foreground">{algorithmWords(algorithm)}</span>
            <span className="text-xs text-muted-foreground">
              {algorithmOrigin(algorithm)}
              {algorithm.changed_at ? `, ${new Date(algorithm.changed_at).toLocaleString()}` : ""}
              {algorithm.reported ? "" : " -- what the next session trades"}
            </span>
          </>
        ) : (
          <span className="text-xs text-muted-foreground">not reported</span>
        )}
      </Fact>
      <Fact label="Trader">
        <span>
          <Badge tone={trader.tone}>{trader.label}</Badge>
        </span>
        <span className="text-xs text-muted-foreground">
          {bridge.attached
            ? `${attachedWords(bridge.attached)} attached ${ago(bridge.attached.since, now)}`
            : "nothing attached to the bridge"}
        </span>
        {status?.ledger ? (
          <span className="text-xs text-muted-foreground">ledger {status.ledger}</span>
        ) : null}
        {status?.build?.commit || status?.build?.code ? (
          <span className="text-xs text-muted-foreground">
            build {status.build.commit ?? status.build.code}
          </span>
        ) : null}
      </Fact>
      <Fact label="Account">
        <span>{bridge.account_name ?? "--"}</span>
        <span className="text-xs text-muted-foreground">
          {bridge.mode === "live" ? "places real orders" : "preview only (dry_run)"}
          {bridge.max_order_value ? ` · buys capped at ${usd(bridge.max_order_value, 0)}` : ""}
        </span>
        <span className={cn("text-xs", check ? (check.ok ? "text-profit" : "text-loss") : "text-muted-foreground")}>
          {check
            ? `${check.ok ? "checked" : "check failed"} ${ago(check.at, now)}: ${check.detail}`
            : "not checked since the bridge host started"}
        </span>
      </Fact>
      <Fact label="Extension">
        <span>
          {connection.connected
            ? `connected ${connection.since ? ago(connection.since, now) : ""}`
            : connection.disconnected_at
              ? `gone ${ago(connection.disconnected_at, now)}`
              : "never connected"}
        </span>
        <span className="text-xs text-muted-foreground">
          {connection.version ? `v${connection.version}` : "version not said"}
          {connection.versions.latest ? ` · latest ${connection.versions.latest}` : ""}
          {connection.client ? ` · from ${connection.client}` : ""}
        </span>
        <span className="text-xs text-muted-foreground">
          Allow trading{" "}
          {connection.permissions ? (connection.permissions.place ? "on" : "off") : "--"} · previews{" "}
          {connection.permissions ? (connection.permissions.preview ? "on" : "off") : "--"}
        </span>
      </Fact>
      <Fact label="Fidelity tab">
        <span>
          {connection.fidelity_tab
            ? {
                signed_in: "signed in",
                signed_out: "signed out",
                no_tab: "no tab open",
                elsewhere: "not on the signed-in site",
              }[connection.fidelity_tab.state]
            : "--"}
        </span>
        <span className="text-xs text-muted-foreground">
          {connection.fidelity_tab?.since ? `since ${ago(connection.fidelity_tab.since, now)}` : ""}
        </span>
      </Fact>
      <Fact label="Bridge">
        <span className="font-mono text-xs">{connection.url ?? "--"}</span>
        <span className="text-xs text-muted-foreground">
          reported {ago(bridge.updated_at, now)}
          {bridge.build?.commit ? ` · build ${bridge.build.commit}` : ""}
        </span>
        {connection.last_refused ? (
          <span className="text-xs text-stuck">
            turned away {connection.last_refused.client} {ago(connection.last_refused.at, now)}:{" "}
            {connection.last_refused.reason}
          </span>
        ) : null}
      </Fact>
    </div>
  );
}

/** A deployment whose trading loop holds the bridge itself (no bridge
 * host): what its trader reports, which exists only while a loop runs. */
function Legacy({ deployment }: { deployment: DeploymentSummary }) {
  const status = deployment.status;
  const reporting = Boolean(status && !status.stale);
  const f = reporting ? status?.fidelity : null;
  const connection = fidelityChip(f, reporting);
  return (
    <>
      <p className="text-xs text-muted-foreground">{connection.detail}</p>
      {status && (status.state === "waiting_for_broker" || status.state === "recovery_required") ? (
        <p className="text-xs text-stuck">{status.detail}</p>
      ) : null}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Fact label="Extension">
          <span>
            {f?.connected ? "connected" : f?.disconnected_at ? "gone" : "not connected"}
          </span>
          <span className="text-xs text-muted-foreground">
            {f?.client ? `from ${f.client}` : ""}
            {f?.version ? ` · v${f.version}` : ""}
          </span>
        </Fact>
        <Fact label="Allow trading">
          <span>{f?.permissions ? (f.permissions.place ? "on" : "off") : "--"}</span>
        </Fact>
        <Fact label="Account">
          <span>{f?.account_name ?? "--"}</span>
        </Fact>
        <Fact label="Bridge">
          <span className="font-mono text-xs">{f?.url ?? "--"}</span>
        </Fact>
      </div>
      <p className="text-xs text-muted-foreground">
        This deployment's trading loop holds the bridge itself, so between sessions nothing
        reports the extension. Run the fidelity-bridge service to keep it connected and see it
        here all the time (docs/DEPLOY.md, "Fidelity").
      </p>
    </>
  );
}

function Setup({ deployment }: { deployment: DeploymentSummary }) {
  return (
    <div className="space-y-2">
      <p>Not set up: {deployment.setup}.</p>
      <ol className="list-decimal space-y-1 pl-5 text-xs text-muted-foreground">
        <li>
          <code>python -m fidelity_gateway.bridge keygen</code> -- the extension's API key, into{" "}
          <code>.env</code>.
        </li>
        <li>
          Copy <code>config/fidelity_live.yaml.example</code> to{" "}
          <code>config/fidelity_live.yaml</code>: the account, <code>bridge.host: 0.0.0.0</code> and
          your browser's machine in <code>allowed_clients</code>.
        </li>
        <li>
          Load the extension, paste the key, point it at this server, and sign into Fidelity in that
          browser. Leave "Allow trading" off for now.
        </li>
        <li>
          <code>docker compose --profile fidelity up -d fidelity-bridge fidelity</code>. The bridge
          stays up between sessions, so this section shows the extension connecting at once -- no
          need to wait for the open.
        </li>
        <li>Once the chain here reads connected and signed in, turn "Allow trading" on.</li>
      </ol>
    </div>
  );
}

function Fact({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs font-medium text-muted-foreground">{label}</span>
      {children}
    </div>
  );
}
