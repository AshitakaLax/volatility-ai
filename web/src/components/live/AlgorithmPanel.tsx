import { Cpu, TriangleAlert } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { ParamField } from "@/components/backtest/ParamField";
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Input,
  Select,
} from "@/components/ui/primitives";
import { api } from "@/lib/api";
import {
  algorithmLabel,
  algorithmName,
  defaultTiming,
  diffAlgorithms,
  gridWords,
  rememberedOperator,
  rememberOperator,
  shadowLine,
  sourceLabel,
} from "@/lib/control";
import { buildStrategyParams, paramSpec, seedOf } from "@/lib/strategyParams";
import { cn } from "@/lib/utils";
import type { ParamSpec } from "@/types/backtest";
import type {
  Algorithm,
  AlgorithmView,
  ChangeCheck,
  ChangeRequest,
  CommandType,
  DeploymentSummary,
  Timing,
} from "@/types/control";

/**
 * What the selected deployment trades, and switching it.
 *
 * A switch is a command like any other: queued here, applied by the
 * deployment's trader through the same validation, override file and
 * rebuild the browser extension's changes use (live_algorithm.py) -- at the
 * next tick, at the next session, or once the book is flat. Before it can
 * be sent it is CHECKED: the server dry-runs it exactly as the trader will,
 * and shows what it would do to the open lots (they keep the targets they
 * were bought at; a regime exit may stop or start applying to them).
 *
 * Paper takes a committed profile or any live-capable strategy with
 * schema-checked parameters; real money takes only a profile with a passing
 * paper promotion (the server enforces both).
 */

const POLL_MS = 15000;

interface Props {
  deployment: DeploymentSummary;
  onSent: () => void;
}

function newKey(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

export function AlgorithmPanel({ deployment, onSent }: Props) {
  const [view, setView] = useState<AlgorithmView | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<"switch" | "rewarm" | "revert" | null>(null);

  const load = useCallback(() => {
    api
      .algorithm(deployment.id)
      .then((next) => {
        setView(next);
        setError(null);
      })
      .catch((cause: unknown) => setError(cause instanceof Error ? cause.message : String(cause)));
  }, [deployment.id]);

  useEffect(() => {
    setView(null);
    setMode(null);
    load();
    const timer = window.setInterval(load, POLL_MS);
    return () => window.clearInterval(timer);
  }, [load]);

  const sent = () => {
    setMode(null);
    load();
    onSent();
  };

  const notEditable = "its config does not grant live.control.algorithm_changes";
  // The trader's shadow of the config file's algorithm: what a revert would
  // do to the book right now (an active regime exit sells at market).
  const revertWarning = shadowLine(deployment);

  return (
    <Card>
      <CardHeader className="flex-row flex-wrap items-center justify-between gap-2">
        <CardTitle className="flex items-center gap-2">
          <Cpu className="size-4" />
          Algorithm
        </CardTitle>
        {view ? (
          <Badge tone={view.source === "config" ? "neutral" : "stuck"}>
            from {sourceLabel(view)}
          </Badge>
        ) : null}
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        {error ? <p className="text-xs text-loss">{error}</p> : null}
        {view ? (
          <>
            <div className="space-y-0.5">
              <div className="font-medium">{nameOf(deployment, view)}</div>
              <div className="text-xs text-muted-foreground">
                {wordsOf(deployment, view)} ·{" "}
                <span className="font-mono">{algorithmLabel(view.current)}</span>
              </div>
              {view.override?.changedAt ? (
                <div className="text-xs text-muted-foreground">
                  changed {new Date(view.override.changedAt).toLocaleString()}
                  {view.override.reason ? ` -- ${view.override.reason}` : ""}
                </div>
              ) : null}
              {view.source !== "config" ? (
                <div className="text-xs text-muted-foreground">
                  config file: {algorithmLabel(view.config_file)}
                </div>
              ) : null}
              {view.pending ? (
                <div className="mt-1 text-xs text-stuck">
                  Written; the running loop switches to it after its current tick (it still
                  reports {view.live ? algorithmLabel(view.live) : "the old one"}).
                </div>
              ) : null}
              <TargetCheck current={view.current} configFile={view.config_file} />
            </div>
            <Parameters current={view.current} configFile={view.config_file} />

            <div className="flex flex-wrap gap-2">
              <Button
                variant="outline"
                disabled={!view.editable}
                title={view.editable ? "Switch to a profile or other parameters" : notEditable}
                onClick={() => setMode(mode === "switch" ? null : "switch")}
              >
                Switch…
              </Button>
              <Button
                variant="outline"
                disabled={!view.editable}
                title={
                  view.editable
                    ? "Rebuild the strategy from replayed history, same algorithm"
                    : notEditable
                }
                onClick={() => setMode(mode === "rewarm" ? null : "rewarm")}
              >
                Re-warm
              </Button>
              <Button
                variant="outline"
                disabled={!view.editable || view.source === "config"}
                title={
                  view.source === "config"
                    ? "Already trading the config file's algorithm"
                    : "Back to the config file's algorithm"
                }
                onClick={() => setMode(mode === "revert" ? null : "revert")}
              >
                Revert to config file
              </Button>
            </div>
            {view.profiles_only ? (
              <p className="text-xs text-muted-foreground">
                Real money: only committed profiles with a passing paper promotion.
              </p>
            ) : null}

            {mode === "switch" ? (
              <SwitchForm
                deployment={deployment}
                view={view}
                onCancel={() => setMode(null)}
                onSent={sent}
              />
            ) : mode === "rewarm" ? (
              <PlainCommand
                deployment={deployment}
                type="rewarm"
                label="Re-warm"
                effect={
                  "After the current tick the strategy is built again and its history " +
                  "replayed -- the same algorithm, its in-memory state rebuilt. Between " +
                  "sessions there is nothing to do: every session starts that way."
                }
                onCancel={() => setMode(null)}
                onSent={sent}
              />
            ) : mode === "revert" ? (
              <PlainCommand
                deployment={deployment}
                type="revert_algorithm"
                label="Revert"
                effect={`Back to the config file's algorithm: ${algorithmLabel(view.config_file)}.`}
                warning={revertWarning?.tone === "loss" ? revertWarning.text : null}
                onCancel={() => setMode(null)}
                onSent={sent}
              />
            ) : null}
          </>
        ) : !error ? (
          <p className="text-xs text-muted-foreground">loading…</p>
        ) : null}
      </CardContent>
    </Card>
  );
}

/** What the algorithm in force does: the server's line for it (the words the
 * extension shows), else its grid in words. */
function wordsOf(deployment: DeploymentSummary, view: AlgorithmView): string {
  const summary = deployment.algorithm;
  return summary?.summary &&
    summary.strategy_id === view.current.strategy_id &&
    summary.step === view.current.step &&
    summary.profit_target === view.current.profit_target
    ? summary.summary
    : gridWords(view.current.step, view.current.profit_target);
}

/** A profile's label when the algorithm in force is one, else its strategy. */
function nameOf(deployment: DeploymentSummary, view: AlgorithmView): string {
  const profile = view.override?.profile
    ? view.profiles.find((row) => row.id === view.override?.profile)
    : undefined;
  if (profile) return profile.label;
  const summary = deployment.algorithm;
  return summary && summary.strategy_id === view.current.strategy_id
    ? algorithmName(summary)
    : view.current.strategy_id;
}

// A target an order of magnitude wider than a grid's is worth a second
// look, unless the deployment's own config file states it: Ultimate's 30%
// calm-lot target is deliberate, the same 30% meant as 0.3% stranded 94 lots.
const IMPLAUSIBLE_TARGET = 0.05;

function TargetCheck({ current, configFile }: { current: Algorithm; configFile: Algorithm }) {
  const target = current.profit_target;
  if (
    target === null ||
    target <= IMPLAUSIBLE_TARGET ||
    (configFile.profit_target !== null && Math.abs(target - configFile.profit_target) <= 1e-9)
  ) {
    return null;
  }
  return (
    <p className="flex items-start gap-2 pt-1 text-xs text-loss">
      <TriangleAlert className="mt-0.5 size-3.5 shrink-0" />A {(target * 100).toFixed(2)}% profit
      target is far wider than a grid's and is not the config file's. Check it is not a decimal
      place: a target the market will not reach leaves capital committed indefinitely.
    </p>
  );
}

/** Every parameter in force, beside the config file's where they differ. */
function Parameters({ current, configFile }: { current: Algorithm; configFile: Algorithm }) {
  const sameStrategy = current.strategy_id === configFile.strategy_id;
  const names = Object.keys(current.strategy_params).sort();
  if (names.length === 0) return null;
  const changed = names.filter(
    (name) =>
      sameStrategy && String(current.strategy_params[name]) !== String(configFile.strategy_params[name]),
  );
  return (
    <details className="text-xs">
      <summary className="cursor-pointer text-muted-foreground">
        Parameters ({names.length}
        {changed.length ? `, ${changed.length} differ from the config file` : ""})
      </summary>
      <div className="mt-2 overflow-x-auto">
        <table className="w-full max-w-xl">
          <thead>
            <tr className="border-b border-border text-left text-muted-foreground">
              <th className="py-1 font-medium">Parameter</th>
              <th className="py-1 font-medium">In force</th>
              <th className="py-1 font-medium">
                {sameStrategy ? "Config file" : `Config file (${configFile.strategy_id})`}
              </th>
            </tr>
          </thead>
          <tbody>
            {names.map((name) => (
              <tr
                key={name}
                className={cn(
                  "border-b border-border/50 last:border-0",
                  changed.includes(name) && "text-stuck",
                )}
              >
                <td className="py-1 font-mono">{name}</td>
                <td className="py-1">{String(current.strategy_params[name])}</td>
                <td className="py-1 text-muted-foreground">
                  {sameStrategy && name in configFile.strategy_params
                    ? String(configFile.strategy_params[name])
                    : "--"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </details>
  );
}

/** Reason, operator and -- on real money -- the id typed back. */
function Confirm({
  deployment,
  typed,
  reason,
  operator,
  confirm,
  onReason,
  onOperator,
  onConfirm,
}: {
  deployment: DeploymentSummary;
  typed: string | null;
  reason: string;
  operator: string;
  confirm: string;
  onReason: (value: string) => void;
  onOperator: (value: string) => void;
  onConfirm: (value: string) => void;
}) {
  return (
    <div className="space-y-2">
      <div className="grid gap-2 sm:grid-cols-[1fr_12rem]">
        <Input
          placeholder="Why -- recorded with the command"
          value={reason}
          onChange={(event) => onReason(event.currentTarget.value)}
        />
        <Input
          placeholder="Your name"
          value={operator}
          onChange={(event) => onOperator(event.currentTarget.value)}
        />
      </div>
      {typed ? (
        <div className="space-y-1">
          <p className="text-xs text-loss">
            Type <code className="font-mono">{deployment.id}</code> to confirm: {typed}.
          </p>
          <Input
            placeholder={deployment.id}
            value={confirm}
            onChange={(event) => onConfirm(event.currentTarget.value)}
          />
        </div>
      ) : null}
    </div>
  );
}

function PlainCommand({
  deployment,
  type,
  label,
  effect,
  warning = null,
  onCancel,
  onSent,
}: {
  deployment: DeploymentSummary;
  type: CommandType;
  label: string;
  effect: string;
  /** What the trader says this would do that cannot be undone. */
  warning?: string | null;
  onCancel: () => void;
  onSent: () => void;
}) {
  const [reason, setReason] = useState("");
  const [operator, setOperator] = useState(rememberedOperator);
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [key] = useState(newKey);
  const typed = deployment.paper === false ? "this deployment trades real money" : null;
  const ready =
    reason.trim().length >= 3 && operator.trim() !== "" && (!typed || confirm === deployment.id);

  const send = async () => {
    setBusy(true);
    setError(null);
    try {
      await api.sendCommand(deployment.id, {
        type,
        reason: reason.trim(),
        operator: operator.trim(),
        idempotency_key: key,
        ...(typed ? { confirm } : {}),
      });
      rememberOperator(operator.trim());
      onSent();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-3 rounded-md border border-border p-3">
      <p className="text-xs text-muted-foreground">{effect}</p>
      {warning ? (
        <p className="flex items-start gap-2 text-xs text-loss">
          <TriangleAlert className="mt-0.5 size-3.5 shrink-0" />
          {warning}
        </p>
      ) : null}
      <Confirm
        deployment={deployment}
        typed={typed}
        reason={reason}
        operator={operator}
        confirm={confirm}
        onReason={setReason}
        onOperator={setOperator}
        onConfirm={setConfirm}
      />
      <div className="flex gap-2">
        <Button disabled={busy || !ready} onClick={() => void send()}>
          {busy ? "Sending…" : label}
        </Button>
        <Button variant="ghost" disabled={busy} onClick={onCancel}>
          Cancel
        </Button>
      </div>
      {error ? <p className="text-xs text-loss">{error}</p> : null}
    </div>
  );
}

function seedFor(specs: ParamSpec[], current: Algorithm | null): Record<string, string> {
  const out: Record<string, string> = {};
  for (const spec of specs) {
    if (spec.mirrors !== null) continue;
    const value = current?.strategy_params[spec.name];
    out[spec.name] = value === undefined || value === null ? seedOf(spec) : String(value);
  }
  return out;
}

const TIMINGS: { id: Timing; label: string; help: string }[] = [
  {
    id: "now",
    label: "Next tick",
    help: "The loop rebuilds after its current tick; between sessions it is written for the next.",
  },
  {
    id: "next_session",
    label: "Next session",
    help: "Applied before the next session starts; today's session finishes on the current one.",
  },
  {
    id: "when_flat",
    label: "When flat",
    help: "Pauses buys now and switches once no lots or orders are left; buys stay paused until resumed.",
  },
];

function SwitchForm({
  deployment,
  view,
  onCancel,
  onSent,
}: {
  deployment: DeploymentSummary;
  view: AlgorithmView;
  onCancel: () => void;
  onSent: () => void;
}) {
  const customAllowed = view.paper && !view.profiles_only;
  const usable = view.profiles.filter((profile) => profile.usable);
  const [source, setSource] = useState<"profile" | "custom">(
    usable.length > 0 || !customAllowed ? "profile" : "custom",
  );
  const [profileId, setProfileId] = useState(usable[0]?.id ?? "");
  const [strategyId, setStrategyId] = useState(view.current.strategy_id);
  const strategy = view.strategies.find((row) => row.id === strategyId);
  const specs = useMemo(() => (strategy?.params ?? []).map(paramSpec), [strategy]);
  const [values, setValues] = useState<Record<string, string>>(() =>
    seedFor((strategy?.params ?? []).map(paramSpec), view.current),
  );
  const [step, setStep] = useState(String(view.current.step ?? ""));
  const [target, setTarget] = useState(String(view.current.profit_target ?? ""));

  const [check, setCheck] = useState<ChangeCheck | null>(null);
  const [checking, setChecking] = useState(false);
  const [timing, setTiming] = useState<Timing>("now");
  const [reason, setReason] = useState("");
  const [operator, setOperator] = useState(rememberedOperator);
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [key] = useState(newKey);

  /** Any edit invalidates the last check: what is sent is what was checked. */
  const edit = (apply: () => void) => {
    apply();
    setCheck(null);
  };

  const chooseStrategy = (id: string) =>
    edit(() => {
      setStrategyId(id);
      const next = view.strategies.find((row) => row.id === id);
      setValues(
        seedFor((next?.params ?? []).map(paramSpec), id === view.current.strategy_id ? view.current : null),
      );
    });

  const request = (): ChangeRequest =>
    source === "profile"
      ? { profile_id: profileId }
      : {
          strategy_id: strategyId,
          strategy_params: buildStrategyParams(specs, values) as Record<string, string | number | boolean>,
          step: Number(step),
          profit_target: Number(target),
        };

  const runCheck = async () => {
    setChecking(true);
    setError(null);
    try {
      const result = await api.checkAlgorithm(deployment.id, request());
      setCheck(result);
      if (result.ok) setTiming(defaultTiming(result.impact));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setChecking(false);
    }
  };

  const ready =
    check?.ok === true &&
    reason.trim().length >= 3 &&
    operator.trim() !== "" &&
    (!check.typed || confirm === deployment.id);

  const send = async () => {
    if (!check?.ok || !check.change) return;
    setBusy(true);
    setError(null);
    try {
      await api.sendCommand(deployment.id, {
        type: "switch_algorithm",
        args:
          source === "profile"
            ? { profile_id: profileId }
            : (check.change as unknown as Record<string, unknown>),
        timing,
        reason: reason.trim(),
        operator: operator.trim(),
        idempotency_key: key,
        ...(check.typed ? { confirm } : {}),
      });
      rememberOperator(operator.trim());
      onSent();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-4 rounded-md border border-border p-3">
      <div className="flex gap-4 text-sm">
        <label className="flex items-center gap-2">
          <input
            type="radio"
            checked={source === "profile"}
            onChange={() => edit(() => setSource("profile"))}
          />
          A committed profile
        </label>
        <label
          className="flex items-center gap-2"
          title={customAllowed ? undefined : "Real money switches only to committed profiles"}
        >
          <input
            type="radio"
            disabled={!customAllowed}
            checked={source === "custom"}
            onChange={() => edit(() => setSource("custom"))}
          />
          Other parameters (paper)
        </label>
      </div>

      {source === "profile" ? (
        <div className="space-y-2">
          {view.profiles.length === 0 ? (
            <p className="text-xs text-muted-foreground">
              No profiles in config/live_profiles/ yet.
            </p>
          ) : null}
          {view.profiles.map((profile) => (
            <label
              key={profile.id}
              className={`flex items-start gap-2 rounded border p-2 ${
                profile.usable ? "border-border" : "border-border opacity-60"
              }`}
            >
              <input
                type="radio"
                disabled={!profile.usable}
                checked={profileId === profile.id}
                onChange={() => edit(() => setProfileId(profile.id))}
                className="mt-1"
              />
              <span>
                <span className="font-medium">{profile.label}</span>
                <span className="block text-xs text-muted-foreground">
                  {algorithmLabel(profile)} · {profile.symbols.join(", ")}
                  {profile.promoted ? " · promoted" : ""}
                </span>
                {typeof profile.evidence.note === "string" ? (
                  <span className="block text-xs text-muted-foreground">
                    {profile.evidence.note}
                  </span>
                ) : null}
                {profile.why ? <span className="block text-xs text-loss">{profile.why}</span> : null}
              </span>
            </label>
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          <div className="grid gap-2 sm:grid-cols-3">
            <label className="space-y-1 text-xs">
              <span className="text-muted-foreground">Strategy</span>
              <Select
                value={strategyId}
                onChange={(event) => chooseStrategy(event.currentTarget.value)}
              >
                {view.strategies.map((row) => (
                  <option key={row.id} value={row.id} disabled={!row.live_capable}>
                    {row.id}
                    {row.live_capable ? "" : " (cannot trade live here)"}
                  </option>
                ))}
              </Select>
            </label>
            <label className="space-y-1 text-xs">
              <span className="text-muted-foreground">Grid step (0.00075 = 0.075%)</span>
              <Input
                value={step}
                onChange={(event) => {
                  const value = event.currentTarget.value;
                  edit(() => setStep(value));
                }}
              />
            </label>
            <label className="space-y-1 text-xs">
              <span className="text-muted-foreground">Profit target (0.003 = 0.3%)</span>
              <Input
                value={target}
                onChange={(event) => {
                  const value = event.currentTarget.value;
                  edit(() => setTarget(value));
                }}
              />
            </label>
          </div>
          {strategy && !strategy.live_capable && strategy.why ? (
            <p className="text-xs text-loss">{strategy.why}</p>
          ) : null}
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {specs.map((spec) => (
              <ParamField
                key={spec.name}
                spec={spec}
                value={values[spec.name] ?? ""}
                onChange={(name, value) => edit(() => setValues((old) => ({ ...old, [name]: value })))}
                onReset={(name) =>
                  edit(() =>
                    setValues((old) => ({
                      ...old,
                      [name]: seedOf(specs.find((s) => s.name === name) ?? spec),
                    })),
                  )
                }
                errors={[]}
                disabled={busy}
                mirroredValue={spec.mirrors === "profit_target" ? target : undefined}
              />
            ))}
          </div>
        </div>
      )}

      <div className="space-y-2">
        <Button variant="outline" disabled={checking || busy} onClick={() => void runCheck()}>
          {checking ? "Checking…" : "Check"}
        </Button>
        {check && !check.ok ? (
          <ul className="list-disc space-y-1 pl-5 text-xs text-loss">
            {check.errors.map((message) => (
              <li key={message}>{message}</li>
            ))}
          </ul>
        ) : null}
        {check?.ok && check.change && check.current ? (
          <div className="space-y-2 text-xs">
            <table className="w-full max-w-xl">
              <tbody>
                {diffAlgorithms(check.current, check.change).map((row) => (
                  <tr key={row.field} className="border-b border-border/50 last:border-0">
                    <td className="py-1 text-muted-foreground">{row.field}</td>
                    <td className="py-1">{row.from}</td>
                    <td className="py-1">→ {row.to}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {diffAlgorithms(check.current, check.change).length === 0 ? (
              <p className="text-muted-foreground">This is the algorithm already in force.</p>
            ) : null}
            {check.impact?.notes.map((note) => (
              <p key={note}>{note}</p>
            ))}
          </div>
        ) : null}
      </div>

      {check?.ok ? (
        <div className="space-y-3">
          <div className="grid gap-2 sm:grid-cols-3">
            {TIMINGS.map((option) => (
              <label key={option.id} className="flex items-start gap-2 rounded border border-border p-2 text-xs">
                <input
                  type="radio"
                  checked={timing === option.id}
                  onChange={() => setTiming(option.id)}
                  className="mt-0.5"
                />
                <span>
                  <span className="font-medium">{option.label}</span>
                  <span className="block text-muted-foreground">{option.help}</span>
                </span>
              </label>
            ))}
          </div>
          <Confirm
            deployment={deployment}
            typed={check.typed ?? null}
            reason={reason}
            operator={operator}
            confirm={confirm}
            onReason={setReason}
            onOperator={setOperator}
            onConfirm={setConfirm}
          />
        </div>
      ) : null}

      <div className="flex gap-2">
        <Button disabled={busy || !ready} onClick={() => void send()}>
          {busy ? "Sending…" : "Switch"}
        </Button>
        <Button variant="ghost" disabled={busy} onClick={onCancel}>
          Cancel
        </Button>
      </div>
      {error ? <p className="text-xs text-loss">{error}</p> : null}
    </div>
  );
}
