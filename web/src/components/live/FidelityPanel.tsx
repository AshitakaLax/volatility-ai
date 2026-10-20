import { PlugZap } from "lucide-react";
import type { ReactNode } from "react";

import { Badge, Card, CardContent, CardHeader, CardTitle } from "@/components/ui/primitives";
import { chip, fidelityChip } from "@/lib/control";
import { usd } from "@/lib/utils";
import type { DeploymentSummary } from "@/types/control";

/**
 * A Fidelity deployment's other half: the browser extension it trades
 * through. Fidelity has no paper mode and no order API of its own here --
 * every order goes from this engine over the Fidelity Bridge extension into
 * the user's signed-in Fidelity tab -- so whether the extension is connected
 * and whether its "Allow trading" switch is on decide whether anything can
 * be placed at all. Both are the bridge's own account
 * (fidelity_gateway/bridge/server.py connection_report), sent through the
 * engine's status file; this page never talks to the extension itself.
 */
export function FidelityPanel({ deployment }: { deployment: DeploymentSummary }) {
  const status = deployment.status;
  const reporting = Boolean(status && !status.stale);
  const f = reporting ? status?.fidelity : null;
  const connection = fidelityChip(f, reporting);
  const engine = chip(deployment);

  return (
    <Card className="border-loss/40">
      <CardHeader className="flex-row flex-wrap items-center justify-between gap-2">
        <CardTitle className="flex items-center gap-2">
          <PlugZap className="size-4" />
          Fidelity Bridge extension
        </CardTitle>
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="loss">real money</Badge>
          <Badge tone={connection.tone}>{connection.label}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        {deployment.setup ? (
          <div className="space-y-2">
            <p>Not set up: {deployment.setup}.</p>
            <ol className="list-decimal space-y-1 pl-5 text-xs text-muted-foreground">
              <li>
                <code>python -m fidelity_gateway.bridge keygen</code> -- the extension's API key,
                into <code>.env</code>.
              </li>
              <li>
                Copy <code>config/fidelity_live.yaml.example</code> to{" "}
                <code>config/fidelity_live.yaml</code>: the account, <code>bridge.host: 0.0.0.0</code>{" "}
                and your browser's machine in <code>allowed_clients</code>.
              </li>
              <li>
                Load the extension, paste the key, point it at this server, and sign into Fidelity
                in that browser. Leave "Allow trading" off for now.
              </li>
              <li>
                <code>docker compose --profile fidelity up -d fidelity</code>. The engine, and the
                bridge with it, runs from the open to the close; to check the setup sooner, run its{" "}
                <code>--check-only</code> between sessions (docs/DEPLOY.md, "Fidelity").
              </li>
              <li>Once this shows the extension connected, turn "Allow trading" on.</li>
            </ol>
          </div>
        ) : (
          <>
            <p className="text-xs text-muted-foreground">{connection.detail}</p>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <Fact label="Engine">
                <Badge tone={engine.tone}>{engine.label}</Badge>
                <span className="text-xs text-muted-foreground">
                  {f?.mode === "live"
                    ? "places real orders"
                    : f?.mode === "preview"
                      ? "preview only (dry_run)"
                      : "mode not reported"}
                </span>
              </Fact>
              <Fact label="Extension">
                <span>
                  {f?.connected
                    ? `connected${f.since ? ` since ${when(f.since)}` : ""}`
                    : f?.disconnected_at
                      ? `gone since ${when(f.disconnected_at)}`
                      : "not connected"}
                </span>
                <span className="text-xs text-muted-foreground">
                  {f?.last_heard ? `last heard ${when(f.last_heard)}` : "never heard from"}
                  {f?.client ? ` · from ${f.client}` : ""}
                </span>
              </Fact>
              <Fact label="Switches">
                <span>
                  Allow trading:{" "}
                  {f?.permissions ? (
                    <span className={f.permissions.place ? "text-profit" : "text-stuck"}>
                      {f.permissions.place ? "on" : "off"}
                    </span>
                  ) : (
                    "--"
                  )}
                </span>
                <span className="text-xs text-muted-foreground">
                  previews {f?.permissions ? (f.permissions.preview ? "on" : "off") : "--"}
                </span>
              </Fact>
              <Fact label="Version">
                <span>{f?.version ?? "--"}</span>
                <span className="text-xs text-muted-foreground">
                  {f?.versions.latest ? `latest ${f.versions.latest}` : ""}
                  {f?.versions.minimum ? ` · needs ${f.versions.minimum}+` : ""}
                </span>
              </Fact>
              <Fact label="Account">
                <span>{f?.account_name ?? "--"}</span>
                <span className="text-xs text-muted-foreground">
                  {f?.max_order_value ? `buys capped at ${usd(f.max_order_value, 0)}` : ""}
                </span>
              </Fact>
              <Fact label="Bridge">
                <span className="font-mono text-xs">{f?.url ?? "--"}</span>
              </Fact>
            </div>
            {f?.advice ? <p className="text-xs text-stuck">Extension: {f.advice}</p> : null}
            {status?.broker_unavailable ? (
              <p className="text-xs text-stuck">
                Waiting for Fidelity: {status.broker_unavailable}
              </p>
            ) : null}
            <p className="text-xs text-muted-foreground">
              Turning "Allow trading" off in the extension pauses this engine's orders without
              stopping it -- every order is refused in the browser and the engine keeps reading
              and applying fills. Turning it back on resumes them.
            </p>
          </>
        )}
      </CardContent>
    </Card>
  );
}

function when(iso: string): string {
  return new Date(iso).toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function Fact({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs font-medium text-muted-foreground">{label}</span>
      {children}
    </div>
  );
}
