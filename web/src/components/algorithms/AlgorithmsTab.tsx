import { useState } from "react";

import { Badge, Button, Card, CardContent, CardHeader, CardTitle, Input } from "@/components/ui/primitives";
import { usePolled } from "@/hooks/usePolled";
import { api } from "@/lib/api";
import {
  actionsFor,
  percent,
  promotionKind,
  STAGE_LABEL,
  STAGES,
  trialBlocker,
  type CandidateAction,
} from "@/lib/algorithms";
import { rememberedOperator, rememberOperator } from "@/lib/control";
import type { Candidate } from "@/types/algorithms";
import type { LegacyLots } from "@/types/control";

/**
 * Algorithm management: a backtest cell kept as a candidate, run on a paper
 * deployment, promoted, and published into config/live_profiles/ where the
 * Live page offers it (server/algorithms.py). Publishing writes a file for
 * the operator to review and commit; switching a deployment stays on the
 * Live page.
 */
export function AlgorithmsTab() {
  const { data, error, refresh } = usePolled(api.algorithms, 10000);
  const candidates = data?.candidates ?? [];

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Add a backtest from its result page (<em>Add as candidate</em>). A candidate runs on a paper
        deployment, is promoted by a passing trial or your own sign-off, and is then published as a
        live profile for you to review and commit. Real money switches only to a promoted profile,
        from the Live page.
      </p>
      {error ? <p className="text-sm text-loss">{error}</p> : null}
      {STAGES.map((stage) => {
        const rows = candidates.filter((candidate) => candidate.stage === stage);
        return (
          <Card key={stage}>
            <CardHeader>
              <CardTitle>
                {STAGE_LABEL[stage]} <span className="text-muted-foreground">· {rows.length}</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {rows.length === 0 ? (
                <p className="text-xs text-muted-foreground">None.</p>
              ) : (
                rows.map((candidate) => (
                  <CandidateRow key={candidate.id} candidate={candidate} onChanged={refresh} />
                ))
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

function CandidateRow({ candidate, onChanged }: { candidate: Candidate; onChanged: () => void }) {
  const [open, setOpen] = useState<CandidateAction | null>(null);
  const [operator, setOperator] = useState(rememberedOperator());
  const [reason, setReason] = useState("");
  const [confirm, setConfirm] = useState("");
  const [deployment, setDeployment] = useState(candidate.paper_deployments[0] ?? "");
  const [legacy, setLegacy] = useState<LegacyLots>("keep");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);

  const backtest = candidate.evidence.backtest ?? {};
  const kind = promotionKind(candidate);
  const verdict = candidate.trial?.evaluation ?? null;

  const run = async (action: CandidateAction) => {
    setBusy(true);
    setError(null);
    setNote(null);
    try {
      rememberOperator(operator.trim());
      if (action === "trial") {
        const started = await api.startTrial(candidate.id, {
          deployment,
          operator: operator.trim(),
          legacy_lots: legacy,
          timing: "next_session",
        });
        setNote(started.warning ?? "Queued: the paper deployment switches at the next session.");
      } else if (action === "evaluate") {
        await api.evaluateTrial(candidate.id);
      } else if (action === "override") {
        await api.signOff(candidate.id, { reason: reason.trim(), operator: operator.trim(), confirm });
      } else if (action === "publish") {
        await api.publishCandidate(candidate.id, { operator: operator.trim(), confirm });
        setNote("Written to config/live_profiles/. Review it and commit it.");
      } else if (action === "delete") {
        await api.deleteCandidate(candidate.id);
      }
      setOpen(null);
      setConfirm("");
      onChanged();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setBusy(false);
    }
  };

  const labels: Record<CandidateAction, string> = {
    trial: "Start paper trial",
    evaluate: "Evaluate trial",
    override: "Owner sign-off",
    publish: "Publish as live profile",
    delete: "Remove",
  };
  const needsId = open === "override" || open === "publish";
  const ready =
    operator.trim() !== "" &&
    (open !== "override" || reason.trim().length >= 3) &&
    (!needsId || confirm === candidate.id) &&
    (open !== "trial" || deployment !== "");

  return (
    <div className="space-y-2 rounded border border-border p-3 text-sm">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-medium">{candidate.label}</span>
        <Badge>{candidate.symbols.join(", ")}</Badge>
        {kind ? <Badge>{kind}</Badge> : null}
      </div>
      <p className="text-xs text-muted-foreground">
        {candidate.strategy_id} · step {candidate.step} · target {candidate.profit_target} · backtest
        yield {percent(backtest.net_yield_pct)}, CAGR {percent(backtest.cagr_pct)}, max drawdown{" "}
        {percent(backtest.max_drawdown_pct)}
      </p>
      {candidate.trial ? (
        <p className="text-xs">
          Trial on <code>{candidate.trial.deployment}</code> since {candidate.trial.started}
        </p>
      ) : trialBlocker(candidate) && candidate.stage === "candidate" ? (
        <p className="text-xs text-muted-foreground">{trialBlocker(candidate)}</p>
      ) : null}
      {verdict ? (
        <ul className="list-disc space-y-0.5 pl-5 text-xs">
          {verdict.passed ? <li>Passed.</li> : null}
          {verdict.failures.map((failure) => (
            <li key={failure}>{failure}</li>
          ))}
        </ul>
      ) : null}
      {candidate.promotion?.manual ? (
        <p className="text-xs">
          Signed off by {candidate.promotion.by}: {candidate.promotion.reason}
        </p>
      ) : null}
      <div className="flex flex-wrap gap-2">
        {actionsFor(candidate).map((action) => (
          <Button
            key={action}
            variant="outline"
            disabled={busy}
            onClick={() => (action === "evaluate" ? void run(action) : setOpen(action))}
          >
            {labels[action]}
          </Button>
        ))}
      </div>
      {open ? (
        <div className="space-y-2 rounded border border-border p-2 text-xs">
          {open === "trial" ? (
            <>
              <select
                className="rounded border border-border bg-background p-1"
                value={deployment}
                onChange={(event) => setDeployment(event.currentTarget.value)}
              >
                {candidate.paper_deployments.map((id) => (
                  <option key={id}>{id}</option>
                ))}
              </select>
              <p className="text-muted-foreground">
                The paper deployment switches at the next session. What happens to the lots it
                holds:
              </p>
              {(
                [
                  ["keep", "Keep selling them at their own targets"],
                  ["exit_at_cost", "Sell them as soon as they clear cost"],
                ] as [LegacyLots, string][]
              ).map(([id, label]) => (
                <label key={id} className="flex items-center gap-2">
                  <input type="radio" checked={legacy === id} onChange={() => setLegacy(id)} />
                  {label}
                </label>
              ))}
            </>
          ) : null}
          {open === "override" ? (
            <>
              <p className="text-muted-foreground">
                Promotes it without a passing paper trial. It is marked manual wherever it is shown,
                and no paper figures are invented.
              </p>
              <Input
                placeholder="Why -- recorded with the sign-off"
                value={reason}
                onChange={(event) => setReason(event.currentTarget.value)}
              />
            </>
          ) : null}
          {open === "delete" ? <p>Remove this candidate from the library?</p> : null}
          <Input
            placeholder="Your name"
            value={operator}
            onChange={(event) => setOperator(event.currentTarget.value)}
          />
          {needsId ? (
            <div className="space-y-1">
              <p className="text-loss">
                Type <code className="font-mono">{candidate.id}</code> to confirm.
              </p>
              <Input
                placeholder={candidate.id}
                value={confirm}
                onChange={(event) => setConfirm(event.currentTarget.value)}
              />
            </div>
          ) : null}
          <div className="flex gap-2">
            <Button disabled={!ready || busy} onClick={() => void run(open)}>
              {labels[open]}
            </Button>
            <Button variant="outline" onClick={() => setOpen(null)}>
              Cancel
            </Button>
          </div>
        </div>
      ) : null}
      {note ? <p className="text-xs text-muted-foreground">{note}</p> : null}
      {error ? <p className="text-xs text-loss">{error}</p> : null}
    </div>
  );
}
