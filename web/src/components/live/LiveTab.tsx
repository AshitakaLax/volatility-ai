import { useState } from "react";

import { Card, CardContent } from "@/components/ui/primitives";
import { useDeploymentFills } from "@/hooks/useDeploymentFills";
import { usePolled } from "@/hooks/usePolled";
import { useLiveState } from "@/hooks/useLiveState";
import { api } from "@/lib/api";

import { ActivityCard } from "./ActivityCard";
import { AlgorithmPanel } from "./AlgorithmPanel";
import { CommandLog } from "./CommandLog";
import { ControlBar } from "./ControlBar";
import { DeploymentHealth } from "./DeploymentHealth";
import { DeploymentStrip } from "./DeploymentStrip";
import { FidelityPanel } from "./FidelityPanel";
import { LiveOrderLedger } from "./LiveOrderLedger";
import { LivePriceChart } from "./LivePriceChart";
import { OverviewCard } from "./OverviewCard";
import { TradesCard } from "./TradesCard";

/**
 * The Live tab: every deployment across the top, Alpaca's and Fidelity's in
 * their own sections; the selected one below -- what it trades and is doing,
 * for Fidelity the browser extension it trades through, its controls and
 * algorithm, its price as its trader saw it, its trades and book, its
 * commands, its build.
 *
 * Mounted only while the tab is open (App renders it on selection), so the
 * polls and the socket stop when the reader leaves.
 */

const STRIP_POLL_MS = 5000;

export function LiveTab() {
  const deployments = usePolled(api.deployments, STRIP_POLL_MS);
  const [chosen, setChosen] = useState<string | null>(null);
  const [sessions, setSessions] = useState(1);
  const listed = deployments.data ?? [];
  const selected = chosen ?? listed[0]?.id ?? null;
  const live = useLiveState(selected);
  const trades = useDeploymentFills(selected, sessions);
  const detail = live.detail;
  const set = Boolean(detail && !detail.setup);
  const status = detail?.status;
  const buyLevel =
    status && !status.stale && status.process === "loop" ? (status.now?.buy_level ?? null) : null;

  const refreshAll = () => {
    live.refresh();
    deployments.refresh();
  };

  return (
    <>
      <DeploymentStrip deployments={listed} selected={selected} onSelect={setChosen} />
      {deployments.error ? (
        <Card>
          <CardContent className="pt-5 text-sm text-loss">
            {deployments.error} — is the API running?
          </CardContent>
        </Card>
      ) : null}
      {deployments.data && listed.length === 0 ? (
        <Card>
          <CardContent className="pt-5 text-sm text-muted-foreground">
            No deployments are listed in <code>config/deployments.yaml</code>.
          </CardContent>
        </Card>
      ) : null}

      {detail && set ? <OverviewCard deployment={detail} state={live.state} fills={trades.today} /> : null}
      {detail?.broker === "fidelity" ? <FidelityPanel deployment={detail} onSent={refreshAll} /> : null}
      {detail && set ? <ControlBar deployment={detail} onSent={refreshAll} /> : null}
      {detail && set && detail.controllable ? (
        <AlgorithmPanel deployment={detail} onSent={refreshAll} />
      ) : null}
      {live.error && set ? (
        <Card>
          <CardContent className="pt-5 text-sm text-loss">{live.error}</CardContent>
        </Card>
      ) : null}
      {set ? (
        <>
          <LivePriceChart
            deploymentId={selected}
            symbol={detail?.symbol ?? null}
            lastPrice={live.state?.last_px ?? null}
            lastPriceAt={live.state?.last_tick ?? null}
            fills={trades.fills ?? []}
            buyLevel={buyLevel}
          />
          <TradesCard fills={trades.fills} sessions={sessions} onSessions={setSessions} />
          <LiveOrderLedger lots={live.state?.lots ?? []} lastPrice={live.state?.last_px ?? null} />
        </>
      ) : null}
      {detail && set ? (
        <CommandLog deploymentId={detail.id} commands={detail.commands} onChange={refreshAll} />
      ) : null}
      {set ? <DeploymentHealth state={live.state} health={live.health} deployment={detail} /> : null}
      {selected && set ? <ActivityCard deploymentId={selected} /> : null}
    </>
  );
}
