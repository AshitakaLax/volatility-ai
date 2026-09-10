"""
parameter_hash -- the identity of one simulation.

BUILT ON src/core/artifacts.py, NOT ALONGSIDE IT

This project already had two hashing schemes when this was written:
artifacts.canonical_hash (SHA-256 over canonical JSON, used for config
and dataset identity) and idempotency.compute_decision_id (SHA-256 over
a "|"-joined field list, used for broker client_order_ids). A third
would have been one too many, and the first is already exactly right
here -- lexical key ordering, compact separators, explicit UTF-8, and
NaN/Infinity rejected rather than silently hashed. So this module
composes the payload and delegates the hashing.

Two properties come along for free and are worth knowing about:

  * NaN/inf in a parameter raises ConfigurationError instead of
    hashing. Desirable -- a NaN parameter is a bug, and two NaNs are
    not equal anyway, so any hash of one would be a lie. It is also
    why METRICS are never hashed: "Return/Drawdown" is legitimately
    +/-inf on a zero-drawdown run.
  * _assert_no_secret_fields rejects key names that look like
    credentials. A strategy parameter named e.g. `auth_token` would be
    refused. That is the correct outcome for a permanent provenance
    record, but it is a surprising error message if you hit it.

WHAT GOES IN THE HASH, AND WHY THE BOUNDARY IS WHERE IT IS

parameter_hash carries a UNIQUE constraint, so it must cover
everything that changes what a run MEANS -- otherwise a legitimately
different experiment is rejected as a duplicate of one already stored.

IN, because changing it changes the numbers:
  strategy_id, strategy_params, grid_step, profit_target
  dataset_version -- the same parameters against 2016-2021 bars and
      against 2016-2026 bars are different experiments. Leaving this
      out was the single most tempting mistake: it makes the hash
      "purely about parameters", which reads clean and silently makes
      the warehouse refuse to re-measure a strategy on new data.
  broker_id -- the same parameters at zero cost and at 5bps slippage
      produce different equity curves. Same argument.
  execution flags -- fill_model, intrabar_priority, on_flat_reentry,
      enforce_no_loss, allow_signal_exit, settlement_days, symbol,
      initial_cash. Every one of these is an input to _simulate_single
      that moves the result.

OUT, because it does not:
  metrics and timings -- outputs, not inputs.
  sweep_id, created_at -- provenance of the batch, not identity of the
      work. Including either would make the hash unique per run, which
      defeats the entire purpose of the constraint.
  rank_by / tie_break_by -- these choose which row you LOOK at after
      the fact. Two sweeps ranking the same measurements differently
      did not do different work.
"""

from __future__ import annotations

from typing import Any

from src.core.artifacts import canonical_hash

# The ExecutionConfig fields that change simulated outcomes, plus the
# two BacktestSection fields that do. Named explicitly rather than
# taken as **kwargs so that adding a new execution flag to
# BacktestConfig is a deliberate decision here too: a flag that alters
# results but is missing from this tuple would make two genuinely
# different runs collide on one hash.
EXECUTION_FLAG_FIELDS = (
    "symbol",
    "initial_cash",
    "fill_model",
    "intrabar_priority",
    "on_flat_reentry",
    "enforce_no_loss",
    "allow_signal_exit",
    "settlement_days",
)


def execution_flags(source: Any) -> dict[str, Any]:
    """Pull EXECUTION_FLAG_FIELDS off a mapping or an object.

    Accepts either a dict (run_sweep's own kwargs) or something
    attribute-shaped (a BacktestConfig section), because both callers
    exist and neither should have to reshape itself first. A field
    that is genuinely absent is omitted rather than defaulted -- a
    wrong default here would be indistinguishable from a real value
    and would poison the hash silently.
    """
    out: dict[str, Any] = {}
    for field in EXECUTION_FLAG_FIELDS:
        if isinstance(source, dict):
            if field in source:
                out[field] = source[field]
        elif hasattr(source, field):
            out[field] = getattr(source, field)
    return out


def parameter_hash(
    *,
    strategy_id: str,
    strategy_params: dict[str, Any],
    grid_step: float,
    profit_target: float,
    dataset_version: str,
    broker_id: str,
    execution: dict[str, Any],
) -> str:
    """SHA-256 identity of one simulation. Keyword-only on purpose:
    seven same-typed arguments in a row is exactly the signature where
    a positional swap produces a valid-looking wrong hash."""
    return canonical_hash(
        {
            "strategy_id": strategy_id,
            "strategy_params": dict(strategy_params),
            "grid_step": grid_step,
            "profit_target": profit_target,
            "dataset_version": dataset_version,
            "broker_id": broker_id,
            "execution": dict(execution),
        }
    )


def broker_id_for(cost_config: Any) -> str:
    """Stable id for a cost model: its own content, hashed.

    Content-addressed rather than a label, so two configs that describe
    the same broker economics land on one row no matter what their YAML
    files were called, and a changed slippage number cannot quietly
    reuse the old broker's id.
    """
    fields = {
        "model_type": getattr(cost_config, "model_type", "zero"),
        "commission_per_trade": getattr(cost_config, "commission_per_trade", 0.0),
        "slippage_bps": getattr(cost_config, "slippage_bps", 0.0),
        "base_bps": getattr(cost_config, "base_bps", 0.0),
        "vol_multiplier": getattr(cost_config, "vol_multiplier", 1.0),
    }
    return f"{fields['model_type']}-{canonical_hash(fields)[:12]}"
