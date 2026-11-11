import { useEffect, useState } from "react";

import {
  Badge,
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Checkbox,
  Field,
  Input,
  Select,
} from "@/components/ui/primitives";
import { usePolled } from "@/hooks/usePolled";
import { api } from "@/lib/api";
import {
  actionsFor,
  percent,
  pickLabel,
  promotionKind,
  STAGE_LABEL,
  STAGES,
  trialBlocker,
  type CandidateAction,
} from "@/lib/algorithms";
import { rememberedOperator, rememberOperator } from "@/lib/control";
import type { Candidate, EnginePicks } from "@/types/algorithms";
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
      <EnginePickMenu onAdded={refresh} />
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

/**
 * Any stored run's engine pick (the cell it ranked first), filtered by fund,
 * algorithm and name, added as a candidate without opening the run. The
 * server reads the figures from the stored run, as for the result page's
 * button.
 */
function EnginePickMenu({ onAdded }: { onAdded: () => void }) {
  const [ticker, setTicker] = useState("");
  const [model, setModel] = useState("");
  const [name, setName] = useState("");
  const [tradedOnly, setTradedOnly] = useState(true);
  const [chosen, setChosen] = useState("");
  const [operator, setOperator] = useState(rememberedOperator());
  const [note, setNote] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [found, setFound] = useState<EnginePicks | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [version, setVersion] = useState(0);

  useEffect(() => {
    // Typing in the name box asks again after a pause, not per keystroke.
    const timer = window.setTimeout(() => {
      api
        .enginePicks({ ticker, model, name, traded_only: tradedOnly })
        .then((picks) => {
          setFound(picks);
          setError(null);
          setChosen((current) =>
            picks.picks.some((pick) => pick.candidate_id === current) ? current : "",
          );
        })
        .catch((cause) => setError(cause instanceof Error ? cause.message : String(cause)));
    }, 250);
    return () => window.clearTimeout(timer);
  }, [ticker, model, name, tradedOnly, version]);

  const picks = found?.picks ?? [];
  const pick = picks.find((candidate) => candidate.candidate_id === chosen);

  const add = async () => {
    if (!pick) return;
    setBusy(true);
    setNote(null);
    try {
      rememberOperator(operator.trim());
      const added = await api.addCandidate({
        run: pick.run,
        ticker: pick.ticker,
        cell: pick.rank,
        operator: operator.trim(),
      });
      setNote(`Added ${added.id}.`);
      setVersion((value) => value + 1);
      onAdded();
    } catch (cause) {
      setNote(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          Add an engine pick <span className="text-muted-foreground">· {found?.total ?? 0}</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex flex-wrap items-end gap-3">
          <Field label="Fund">
            <Select value={ticker} onChange={(event) => setTicker(event.target.value)}>
              <option value="">All funds</option>
              {(found?.funds ?? []).map((fund) => (
                <option key={fund}>{fund}</option>
              ))}
            </Select>
          </Field>
          <Field label="Algorithm">
            <Select value={model} onChange={(event) => setModel(event.target.value)}>
              <option value="">All algorithms</option>
              {(found?.models ?? []).map((id) => (
                <option key={id}>{id}</option>
              ))}
            </Select>
          </Field>
          <Field label="Run name contains">
            <Input value={name} onChange={(event) => setName(event.target.value)} />
          </Field>
          <label className="flex items-center gap-1.5 pb-2 text-xs">
            <Checkbox
              checked={tradedOnly}
              onChange={(event) => setTradedOnly(event.target.checked)}
            />
            Hide picks that never traded
          </label>
        </div>
        <Field label={`Engine pick, best return over drawdown first${found && found.total > picks.length ? ` (top ${picks.length} of ${found.total}: narrow the filters)` : ""}`}>
          <Select
            className="w-full"
            value={chosen}
            onChange={(event) => setChosen(event.target.value)}
          >
            <option value="">{picks.length === 0 ? "No engine picks match" : "Choose one…"}</option>
            {picks.map((candidate) => (
              <option key={candidate.candidate_id} value={candidate.candidate_id}>
                {pickLabel(candidate)}
              </option>
            ))}
          </Select>
        </Field>
        {pick ? (
          <p className="text-xs text-muted-foreground">
            Run {pick.run}
            {pick.name ? ` (${pick.name})` : ""}, {pick.start?.slice(0, 10) ?? "?"} to{" "}
            {pick.end?.slice(0, 10) ?? "?"} · {pick.m.total_trades ?? 0} trades · return/drawdown{" "}
            {pick.m.return_over_drawdown ?? "--"}. Web backtests are level-fill and zero-cost: a
            pick with very many trades will not hold up at a real broker.
          </p>
        ) : null}
        <div className="flex flex-wrap items-end gap-3">
          <Field label="Your name">
            <Input value={operator} onChange={(event) => setOperator(event.target.value)} />
          </Field>
          <Button
            disabled={busy || !pick || pick.added || operator.trim() === ""}
            onClick={() => void add()}
          >
            Add as candidate
          </Button>
          {pick?.added ? (
            <span className="pb-2 text-xs text-muted-foreground">Already a candidate.</span>
          ) : null}
          {note ? <span className="pb-2 text-xs text-muted-foreground">{note}</span> : null}
        </div>
        {error ? <p className="text-xs text-loss">{error}</p> : null}
      </CardContent>
    </Card>
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
        {candidate.composition ? (
          <Badge title="a composed algorithm: this buy and this sell">
            buy {candidate.composition.buy} · sell {candidate.composition.sell}
          </Badge>
        ) : null}
        {candidate.composition?.loss ? (
          <Badge tone="loss" title="its sell algorithm exits on a signal and can realise a loss">
            may sell below cost
          </Badge>
        ) : null}
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
      {candidate.paper_deployments.length > 0 && (candidate.paper_refused ?? []).length > 0 ? (
        <p className="text-xs text-muted-foreground">
          Not offered:{" "}
          {(candidate.paper_refused ?? []).map((entry) => `${entry.deployment} — ${entry.reason}`).join("; ")}
        </p>
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
