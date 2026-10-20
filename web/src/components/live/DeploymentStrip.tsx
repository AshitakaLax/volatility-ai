import { Badge } from "@/components/ui/primitives";
import {
  algorithmName,
  byBroker,
  chip,
  fidelityChip,
  sharedAccounts,
  type BrokerSection,
} from "@/lib/control";
import { cn, usd } from "@/lib/utils";
import type { DeploymentSummary } from "@/types/control";

/**
 * Every deployment at a glance, by venue: Alpaca's API (paper and real
 * money) in one section, Fidelity through the browser extension in another
 * -- different engines with different failure modes, so they are never
 * mixed. Picking one shows it below.
 *
 * Paper or REAL MONEY comes from the deployment's own config
 * (live.paper_trading), not from what its ledger file is called. The state
 * chip is what the trader last reported, and a report that stopped arriving
 * reads "Not running", not as whatever it last said. The algorithm named is
 * the one IN FORCE -- the trader's own report while it reports -- not the
 * config file's, which a switch from this page replaces.
 */
interface Props {
  deployments: DeploymentSummary[];
  selected: string | null;
  onSelect: (id: string) => void;
}

export function DeploymentStrip({ deployments, selected, onSelect }: Props) {
  const shared = sharedAccounts(deployments);
  return (
    <div className="space-y-4">
      {byBroker(deployments).map((section) => (
        <Section
          key={section.broker}
          section={section}
          shared={shared}
          selected={selected}
          onSelect={onSelect}
        />
      ))}
    </div>
  );
}

function Section({
  section,
  shared,
  selected,
  onSelect,
}: {
  section: BrokerSection;
  shared: Record<string, string[]>;
  selected: string | null;
  onSelect: (id: string) => void;
}) {
  const fidelity = section.broker === "fidelity";
  return (
    <section
      className={cn(
        "rounded-lg border p-3",
        fidelity ? "border-loss/40 bg-loss/5" : "border-border bg-secondary/10",
      )}
    >
      <div className="mb-2 flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-sm font-semibold">{section.title}</h2>
        <span className="text-xs text-muted-foreground">{section.blurb}</span>
      </div>
      {section.deployments.length === 0 ? (
        <p className="text-xs text-muted-foreground">
          {fidelity
            ? "No Fidelity deployment is registered in config/deployments.yaml, so nothing here " +
              "reports the browser extension's connection yet."
            : "No Alpaca deployment is registered in config/deployments.yaml."}
        </p>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {section.deployments.map((deployment) => (
            <DeploymentCard
              key={deployment.id}
              deployment={deployment}
              shared={shared[deployment.id]}
              selected={selected === deployment.id}
              onSelect={() => onSelect(deployment.id)}
            />
          ))}
        </div>
      )}
    </section>
  );
}

function DeploymentCard({
  deployment,
  shared,
  selected,
  onSelect,
}: {
  deployment: DeploymentSummary;
  shared: string[] | undefined;
  selected: boolean;
  onSelect: () => void;
}) {
  const state = chip(deployment);
  const lots = deployment.ledger?.open_lots;
  const algorithm = deployment.algorithm;
  const status = deployment.status;
  const fidelity =
    deployment.broker === "fidelity"
      ? fidelityChip(status?.fidelity, Boolean(status && !status.stale))
      : null;
  return (
    <button
      type="button"
      onClick={onSelect}
      className={cn(
        "rounded-lg border bg-card p-3 text-left transition-colors",
        selected ? "border-primary ring-1 ring-primary/40" : "border-border hover:bg-secondary/30",
      )}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="truncate text-sm font-medium">{deployment.label}</span>
        {deployment.paper === false ? (
          <Badge tone="loss">real money</Badge>
        ) : deployment.paper ? (
          <Badge>paper</Badge>
        ) : null}
      </div>

      {deployment.setup ? (
        <p className="mt-2 text-xs text-muted-foreground">Not set up: {deployment.setup}.</p>
      ) : (
        <>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <Badge tone={state.tone}>{state.label}</Badge>
            {fidelity ? (
              <Badge tone={fidelity.tone} title={fidelity.detail}>
                {fidelity.label}
              </Badge>
            ) : null}
            {deployment.ledger?.halt && status?.state !== "buys_paused" ? (
              <Badge tone="stuck">buys halted</Badge>
            ) : null}
            {deployment.pending ? (
              <span className="text-xs text-stuck">{deployment.pending} queued</span>
            ) : null}
            {shared ? (
              <Badge tone="loss" title="Two loops on one account diverge both ledgers from the venue">
                same account as {shared.join(", ")}
              </Badge>
            ) : null}
          </div>
          {deployment.error ? null : (
            <>
              <div className="mt-1 text-xs">
                <span className="font-medium">{deployment.symbol}</span>
                {algorithm ? (
                  <span className="text-muted-foreground">
                    {" · "}
                    {algorithmName(algorithm)}
                    {algorithm.source !== "config" ? (
                      <span className="text-stuck"> (switched)</span>
                    ) : null}
                  </span>
                ) : null}
              </div>
              <div className="text-xs text-muted-foreground">
                {lots !== undefined ? `${lots} lot${lots === 1 ? "" : "s"}` : ""}
                {deployment.ledger?.cash !== undefined && deployment.ledger.cash !== null
                  ? ` · ${usd(deployment.ledger.cash, 0)} cash`
                  : ""}
              </div>
            </>
          )}
          {state.detail ? (
            <div className="mt-1 truncate text-xs text-muted-foreground" title={state.detail}>
              {state.detail}
            </div>
          ) : null}
        </>
      )}
    </button>
  );
}
