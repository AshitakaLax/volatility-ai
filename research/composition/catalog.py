"""
The buy and sell policies as the web describes them (Phase 7 of
docs/research/buy-sell-composition.md), and the check a composed change
must pass before a live deployment takes it.

`catalog()` is what /api/backtest/funds and the live algorithm editor serve
under `composition`: each policy's constructor schema in the same wire shape
a strategy's params use (research/strategies/param_schema.describe_params),
seeded from its committed defaults, less the parameters that belong to the
other side. A sell policy carries `loss: true` when it may sell below cost --
the web shows those by default, marked (owner, Oct 31) -- and `partial: true`
when it sells lots in parts.

`parse_change(params, check_value)` validates a composed strategy_params
mapping component by component, so the live loop's AlgorithmControl refuses
a bad nested value with its own name (buy.params.per_lot_pct) rather than as
an unknown parameter.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from engine.core.exceptions import ConfigurationError
from research.composition import entries, exits

PARTIAL_SELLS = frozenset({"scale_out", "scale_out_trail", "regime_exit_partial"})
MAX_COMPONENT_PARAMS = 64


def _buy_schema(entry_id: str) -> list[dict]:
    from research.strategies.param_schema import describe_params

    selling = entries.sell_params(entry_id)
    specs = describe_params(
        entry_id, entries.entry_class(entry_id), entries.entry_defaults(entry_id)
    )
    return [spec for spec in specs if spec["name"] not in selling]


def _sell_schema(exit_id: str) -> list[dict]:
    from research.strategies.param_schema import describe_params

    return describe_params(exit_id, exits.EXITS[exit_id], exits.EXIT_DEFAULTS.get(exit_id, {}))


def catalog() -> dict[str, Any]:
    buys = {}
    for entry_id in entries.entry_ids():
        try:
            buys[entry_id] = {"params": _buy_schema(entry_id)}
        except Exception:  # one broken policy never takes the catalog down
            continue
    sells = {}
    for exit_id, cls in sorted(exits.EXITS.items()):
        try:
            sells[exit_id] = {
                "label": getattr(cls, "label", exit_id),
                "params": _sell_schema(exit_id),
                **({"loss": True} if cls.can_realize_loss else {}),
                **({"partial": True} if exit_id in PARTIAL_SELLS else {}),
            }
        except Exception:
            continue
    return {"buys": buys, "sells": sells}


def defaults_for(side: str, policy_id: str) -> dict[str, Any]:
    """A policy's committed defaults (side "buy" or "sell")."""
    if side == "buy":
        return entries.entry_defaults(policy_id)
    return dict(exits.EXIT_DEFAULTS.get(policy_id, {}))


def with_defaults(params: dict, merge: bool = True) -> dict:
    """composed strategy_params with components' parameters taken from their
    committed defaults -- one component or a list of them per side, so a
    sweep's lists keep their shape. merge=True fills every parameter not
    given (the matrix); merge=False fills only a component given NO
    parameters, using any it was given exactly as given (the server's rule
    for a model's params, one level down)."""

    def fill(side: str, raw: Any) -> Any:
        if isinstance(raw, list):
            return [fill(side, item) for item in raw]
        if isinstance(raw, dict) and isinstance(raw.get("id"), str):
            given = raw.get("params") or {}
            if given and not merge:
                return {"id": raw["id"], "params": dict(given)}
            try:
                base = defaults_for(side, raw["id"])
            except ConfigurationError:
                base = {}  # an unknown id is refused where it is built, by name
            return {"id": raw["id"], "params": {**base, **given}}
        return raw

    return {k: fill(k, v) if k in ("buy", "sell") else v for k, v in params.items()}


def parse_change(
    params: Any,
    check_value: Callable[[dict, Any], Any],
    omit: object,
    profit_target: float | None = None,
) -> dict[str, Any]:
    """A composed strategy_params mapping, every value checked against its
    component's schema. `check_value(spec, value)` is the caller's per-value
    check (live_algorithm._param_value); it returns `omit` for a blank."""
    if not isinstance(params, dict) or set(params) != {"buy", "sell"}:
        raise ConfigurationError("composed strategy_params must be exactly {buy, sell}.")
    out: dict[str, Any] = {}
    total = 0
    for side, schema_for, known in (
        ("buy", _buy_schema, set(entries.entry_ids())),
        ("sell", _sell_schema, set(exits.EXITS)),
    ):
        raw = params[side]
        if not isinstance(raw, dict) or not isinstance(raw.get("id"), str):
            raise ConfigurationError(f"{side} must be {{id, params}}.")
        if set(raw) - {"id", "params"}:
            raise ConfigurationError(
                f"{side} has unknown keys {sorted(set(raw) - {'id', 'params'})}."
            )
        component_id = raw["id"]
        if component_id not in known:
            raise ConfigurationError(f"Unknown {side} policy {component_id!r}.")
        values = raw.get("params") or {}
        if not isinstance(values, dict):
            raise ConfigurationError(f"{side}.params must be an object.")
        total += len(values)
        schema = {spec["name"]: spec for spec in schema_for(component_id)}
        chosen: dict[str, Any] = {}
        for name, value in values.items():
            spec = schema.get(name)
            if spec is None:
                raise ConfigurationError(f"{side} policy {component_id} has no parameter {name!r}.")
            if "locked" in spec and "mirrors" not in spec:
                raise ConfigurationError(f"{side}.params.{name} is not set here: {spec['locked']}.")
            checked = check_value({**spec, "name": f"{side}.params.{name}"}, value)
            if checked is not omit:
                chosen[name] = checked
        # A parameter mirroring the profit target is set to it, as the flat
        # parser and the backtest form do (Bayesian's target_return).
        if profit_target is not None:
            for name, spec in schema.items():
                if spec.get("mirrors") == "profit_target":
                    chosen[name] = profit_target
        out[side] = {"id": component_id, "params": chosen}
    if total > MAX_COMPONENT_PARAMS:
        raise ConfigurationError(f"a composition may set at most {MAX_COMPONENT_PARAMS} values.")
    return out
