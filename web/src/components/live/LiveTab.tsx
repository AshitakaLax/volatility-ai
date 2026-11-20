import { TriangleAlert } from "lucide-react";
import { useState } from "react";

import { Button, Card, CardContent, Skeleton } from "@/components/ui/primitives";
import { useDeploymentFills } from "@/hooks/useDeploymentFills";
import { useDeploymentOrders } from "@/hooks/useDeploymentOrders";
import { useNow } from "@/hooks/useNow";
import { usePolled } from "@/hooks/usePolled";
import { useLiveState } from "@/hooks/useLiveState";
import { api } from "@/lib/api";
import { attention, defaultDeployment, type Attention } from "@/lib/attention";
import { cn } from "@/lib/utils";
import type { DeploymentSummary } from "@/types/control";

import { ActivityCard } from "./ActivityCard";
import { AlgorithmPanel } from "./AlgorithmPanel";
import { CommandLog } from "./CommandLog";
import { ControlBar } from "./ControlBar";
import { DeploymentHealth } from "./DeploymentHealth";
import { DeploymentStrip } from "./DeploymentStrip";
import { FidelityPanel } from "./FidelityPanel";
import { LiveOrderLedger } from "./LiveOrderLedger";
import { LivePriceChart } from "./LivePriceChart";
import { OrdersCard } from "./OrdersCard";
import { OverviewCard } from "./OverviewCard";
import { PerformanceCard } from "./PerformanceCard";
import { RiskReportHistory } from "./RiskReportHistory";
import { RiskReportPanel } from "./RiskReportPanel";
import { TradesCard } from "./TradesCard";

/**
 * The Live tab: what needs attention first, whichever deployment is
 * selected; every deployment across the top, Alpaca's and Fidelity's in
 * their own sections; the selected one below -- what it trades and is doing,
 * for Fidelity the browser extension it trades through, its controls and
 * algorithm, its price as its trader saw it, its trades and book, how it
 * has done over time, its last commands, and (folded away) its build.
 *
 * The deployment shown before one is picked is real money that something
 * reports for (lib/attention.ts defaultDeployment); a picked one is kept in
 * the address by App.
 *
 * Mounted only while the tab is open (App renders it on selection), so the
 * polls and the socket stop when the reader leaves.
 */

const STRIP_POLL_MS = 5000;

interface Props {
  /** The deployment the address names, if any. */
  chosen: string | null;
  onChoose: (id: string) => void;
}

export function LiveTab({ chosen, onChoose }: Props) {
  const deployments = usePolled(api.deployments, STRIP_POLL_MS);
  const [sessions, setSessions] = useState(1);
  const now = useNow(5000);
  const listed = deployments.data ?? [];
  const named = chosen && listed.some((d) => d.id === chosen) ? chosen : null;
  const selected = named ?? defaultDeployment(listed);
  const needs = attention(listed, now);
  const live = useLiveState(selected);
  const trades = useDeploymentFills(selected, sessions);
  const orders = useDeploymentOrders(selected);
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
      {needs.length ? (
        <AttentionBanner items={needs} selected={selected} onShow={onChoose} />
      ) : null}
      {deployments.data === null && !deployments.error ? <Skeleton className="h-36" /> : null}
      <DeploymentStrip deployments={listed} selected={selected} onSelect={onChoose} />
      {deployments.error ? (
        <Card>
          <CardContent className="pt-5 text-sm text-loss">
            {deployments.error} — is the API running?
          </CardContent>
        </Card>
      ) : null}
      <RiskReportPanel deployments={listed} onSent={refreshAll} />
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
          <OrdersCard events={orders} lastWindow={status?.last_window} />
          <TradesCard fills={trades.fills} sessions={sessions} onSessions={setSessions} />
          <LiveOrderLedger lots={live.state?.lots ?? []} lastPrice={live.state?.last_px ?? null} />
          {selected ? <PerformanceCard deploymentId={selected} /> : null}
          {selected && detail?.risk_reports?.settings ? <RiskReportHistory deploymentId={selected} /> : null}
        </>
      ) : null}
      {detail && set ? (
        <CommandLog deploymentId={detail.id} commands={detail.commands} onChange={refreshAll} />
      ) : null}
      {set ? (
        // Which build runs and whether its process is alive: needed when
        // something is wrong, noise on a good day.
        <details className="group" data-testid="deployment-details">
          <summary className="cursor-pointer list-none rounded-lg border border-border bg-card px-5 py-3 text-sm font-semibold select-none">
            Build and process
            <span className="ml-2 font-normal text-muted-foreground group-open:hidden">
              {buildLine(detail)}
            </span>
          </summary>
          <div className="mt-4 space-y-4">
            <DeploymentHealth state={live.state} health={live.health} deployment={detail} />
          </div>
        </details>
      ) : null}
      {selected && set ? <ActivityCard deploymentId={selected} /> : null}
    </>
  );
}

function buildLine(deployment: DeploymentSummary | null): string {
  const status = deployment?.status;
  if (!status || status.stale) return "no report from the trader";
  const build = status.build;
  return [
    status.process ?? "trader",
    build ? `build ${build.commit ?? build.code ?? "unknown"}` : null,
    deployment?.service ? `service ${deployment.service}` : null,
  ]
    .filter(Boolean)
    .join(" · ");
}

/** What needs the reader, said once and first: the deployment, what is
 * wrong, and the one thing that fixes it. */
function AttentionBanner({
  items,
  selected,
  onShow,
}: {
  items: Attention[];
  selected: string | null;
  onShow: (id: string) => void;
}) {
  return (
    <div className="space-y-2" role="alert" data-testid="attention">
      {items.map((item) => (
        <div
          key={`${item.id}-${item.title}`}
          className={cn(
            "flex flex-wrap items-start gap-x-4 gap-y-2 rounded-lg border px-4 py-3",
            item.tone === "loss" ? "border-loss/50 bg-loss/10" : "border-stuck/50 bg-stuck/10",
          )}
        >
          <TriangleAlert
            className={cn("mt-0.5 size-4 shrink-0", item.tone === "loss" ? "text-loss" : "text-stuck")}
          />
          <div className="min-w-0 flex-1 basis-64 text-sm">
            <p className="font-semibold">
              {item.label}: {item.title}
            </p>
            <p className="text-muted-foreground">{item.detail}</p>
            {item.fix ? (
              <p className="mt-1">
                <span className="text-muted-foreground">Fix: </span>
                {item.fix}
              </p>
            ) : null}
          </div>
          {item.id !== selected ? (
            <Button variant="outline" onClick={() => onShow(item.id)}>
              Show it
            </Button>
          ) : null}
        </div>
      ))}
    </div>
  );
}
