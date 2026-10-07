"""
The trading algorithm of a running live deployment, as the Fidelity
Bridge extension shows it and -- when the deployment allows -- changes it.

--------------------------------------------------------------------
WHAT CAN CHANGE, AND WHAT CANNOT

The strategy (`strategy.strategy_id`), its parameters
(`strategy.strategy_params`), and the single grid the live loop trades
(`live.step`, `live.profit_target`). Nothing else: not the symbol, the
account, the order ceiling, the risk limits or the broker. Those decide
whose money moves and how much of it, and they stay in the deployment's
file.

--------------------------------------------------------------------
WHO DECIDES THAT IT CAN CHANGE AT ALL

The deployment's own file, `live.fidelity.bridge.allow_algorithm_changes`.
Without it the extension can look and every change is refused: what real
capital trades is decided in a reviewable file, and a browser may change
it only when that file says so.

--------------------------------------------------------------------
WHERE A CHANGE IS KEPT

In an override file beside the state database (`algorithm.json`), laid
over the YAML at every start. The YAML is never rewritten by a browser,
and "revert" is deleting the override. An override that does not
validate stops the engine from starting -- trading the YAML's algorithm
while the operator believes their change is live would be the worse
failure.

--------------------------------------------------------------------
HOW A CHANGE TAKES EFFECT

It is validated exactly as a start-up validates: BacktestConfig, the
registry, constructing the strategy with the parameters, and the
target_return cross-check. Only then is it written, and the running
process told. cli.py rebuilds the trading loop at the next tick boundary
from durable state -- the same state a restart loads -- so open lots,
orders in flight and cash carry over untouched.
"""

from __future__ import annotations

import copy
import json
import math
import os
import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from engine.core.config import BacktestConfig
from engine.core.exceptions import ConfigurationError
from research.strategies.param_schema import _HIDDEN_PARAMS, describe_params

OVERRIDE_FILENAME = "algorithm.json"
_MAX_PARAMS = 64
_MAX_TEXT = 200
_OMIT = object()


def override_path(state_db: str | Path) -> Path:
    """Beside the live state database, with the order journal."""
    return Path(state_db).with_name(OVERRIDE_FILENAME)


def check_target_return(config: BacktestConfig, strategy: Any) -> None:
    """A strategy's declared target_return must be the profit target the
    deployment actually trades, unless it says the mismatch is deliberate.

    Same cross-check optimization_controller._run_one_combination applies
    per sweep combination -- see BayesianDualScaleSizing's module
    docstring, "THE TARGET_RETURN / PROFIT_TARGET CROSS-CHECK" -- here
    against the single value the live loop trades: a posterior confidently
    estimating the probability of hitting a different price than the one
    being traded is a silent failure with real capital behind it.
    live.profit_target may be None (BacktestConfig.validate does not
    require it; LiveTradingLoop does, with its own clearer error), so a
    missing value is not misreported as a mismatch.
    """
    declared = getattr(strategy, "target_return", None)
    mismatch_allowed = getattr(strategy, "allow_target_return_mismatch", False)
    if (
        declared is not None
        and config.live.profit_target is not None
        and declared != config.live.profit_target
        and not mismatch_allowed
    ):
        raise ConfigurationError(
            f"{config.strategy.strategy_id}'s target_return={declared} does not match "
            f"live.profit_target={config.live.profit_target} -- the posterior would be "
            "confidently estimating the probability of hitting a different price than the one "
            "this deployment actually trades. Set target_return to match live.profit_target, "
            "or pass allow_target_return_mismatch=True in strategy_params to confirm the "
            "mismatch is deliberate."
        )


def build_strategy(config: BacktestConfig, registry: dict[str, type]) -> Any:
    """The strategy a config names, constructed and cross-checked -- or a
    ConfigurationError saying why not. What the live loop is built with,
    and what a proposed change must survive before it is accepted."""
    strategy_id = config.strategy.strategy_id
    strategy_class = registry.get(strategy_id)
    if strategy_class is None:
        known = ", ".join(sorted(registry))
        raise ConfigurationError(f"Unknown strategy_id {strategy_id!r}. Known: {known}")
    try:
        strategy = strategy_class(**config.strategy.strategy_params)
    except (TypeError, ValueError) as exc:
        raise ConfigurationError(f"{strategy_id} refused these parameters: {exc}") from exc
    check_target_return(config, strategy)
    return strategy


def _number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ConfigurationError(f"{name} must be a number, got {value!r}")
    return float(value)


def _fraction(value: Any, name: str) -> float:
    """A step or profit target: a fraction of the price, above 0 and below
    1. The upper bound catches a percentage typed as a fraction -- a 5%
    target sent as 5 -- which BacktestConfig, wanting only a positive
    number, would accept."""
    number = _number(value, name)
    if not 0 < number < 1:
        raise ConfigurationError(
            f"{name} must be a fraction of the price between 0 and 1 (0.01 is 1%), got {number}"
        )
    return number


def _param_value(spec: dict, value: Any) -> Any:
    """One parameter's value, checked against its schema entry
    (param_schema.describe_params): the type the constructor declares,
    one of its choices when it has them, and empty only where allowed."""
    name = f"strategy_params.{spec['name']}"
    kind = spec.get("type")
    if value is None:
        if spec.get("nullable"):
            return None
        if spec.get("required"):
            raise ConfigurationError(f"{name} is required.")
        return _OMIT  # left blank: the constructor's own default applies
    if kind == "bool":
        if not isinstance(value, bool):
            raise ConfigurationError(f"{name} must be true or false, got {value!r}")
        return value
    if kind == "int":
        number = _number(value, name)
        if not number.is_integer():
            raise ConfigurationError(f"{name} must be a whole number, got {value!r}")
        return int(number)
    if kind == "str":
        if not isinstance(value, str) or len(value) > _MAX_TEXT:
            raise ConfigurationError(f"{name} must be text of at most {_MAX_TEXT} characters.")
        if spec.get("enum") and value not in spec["enum"]:
            raise ConfigurationError(f"{name} must be one of {', '.join(spec['enum'])}.")
        return value
    return _number(value, name)


class AlgorithmControl:
    """The extension's view of the live algorithm, and the one way it changes.

    `base` is the deployment's YAML (as a validated BacktestConfig);
    `allowed` is its allow_algorithm_changes. `on_apply`, set by whatever
    runs the loop, is told when the algorithm to trade has changed; the
    runner then rebuilds from `effective_config()`.
    """

    def __init__(
        self,
        base: BacktestConfig,
        *,
        state_db: str | Path,
        registry: dict[str, type],
        allowed: bool,
        config_path: str | Path | None = None,
        log: Callable[[str], None] | None = None,
        now: Callable[[], float] = time.time,
    ) -> None:
        self._base = base.to_dict()
        self._path = override_path(state_db)
        self._registry = registry
        self._allowed = bool(allowed)
        self._config_path = (
            str(config_path) if config_path is not None else "the deployment's config"
        )
        self._log = log or (lambda _message: None)
        self._now = now
        self._lock = threading.Lock()
        self.on_apply: Callable[[], None] | None = None
        self._live: dict | None = None

    @property
    def allowed(self) -> bool:
        return self._allowed

    @property
    def path(self) -> Path:
        """The override file."""
        return self._path

    # -- what is in force ---------------------------------------------------

    def read_override(self) -> dict | None:
        """The override, or None. Unreadable is an error, not "none": an
        override that silently stopped applying would leave the operator
        believing their change is live."""
        if not self._path.exists():
            return None
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ConfigurationError(
                f"{self._path} is not readable JSON ({exc}). It holds the algorithm the "
                "extension set; fix it, or delete it to trade the config file's algorithm."
            ) from exc
        if not isinstance(data, dict):
            raise ConfigurationError(f"{self._path} must hold a JSON object.")
        return data

    def effective_config(self) -> BacktestConfig:
        """The config to trade: the YAML, with the override laid over it
        when this deployment allows changes. Validated, and its strategy
        constructed, before it is returned."""
        config = BacktestConfig.from_dict(self._effective_data())
        config.validate()
        build_strategy(config, self._registry)
        return config

    def _effective_data(self) -> dict:
        override = self.read_override() if self._allowed else None
        if override is None:
            return copy.deepcopy(self._base)
        # Held to exactly the rules a change from the extension is: the
        # file is plain JSON on disk, and a hand edit is still a change.
        try:
            checked = self._parse(override, from_file=True)
        except ConfigurationError as exc:
            raise ConfigurationError(f"{self._path}: {exc}") from exc
        return self._merged(checked)

    def ignored_override(self) -> bool:
        """An override on disk that this deployment does not allow, and so ignores."""
        return not self._allowed and self._path.exists()

    def mark_live(self, config: BacktestConfig) -> None:
        """Called by the runner once a loop trades `config`."""
        with self._lock:
            self._live = self._algorithm_of(config.to_dict())

    def pending(self) -> bool:
        """A change accepted but not yet traded: the loop picks it up at
        its next tick boundary."""
        with self._lock:
            live = self._live
        if live is None:
            return False
        try:
            return self._algorithm_of(self._effective_data()) != live
        except ConfigurationError:
            return False

    # -- the calls the extension makes ----------------------------------------

    def describe(self, _args: dict | None = None) -> dict:
        """algorithm.describe: what is traded, what may be picked, and
        whether it may be changed here."""
        override = self.read_override() if self._allowed else None
        effective = self._effective_data()
        strategies = []
        for strategy_id in sorted(self._registry):
            try:
                params = describe_params(strategy_id, self._registry[strategy_id])
            except Exception:
                params = []
            strategies.append({"id": strategy_id, "params": params})
        return {
            "editable": self._allowed,
            "reason": None
            if self._allowed
            else (
                "This deployment does not take algorithm changes from the browser. To allow "
                "them, set live.fidelity.bridge.allow_algorithm_changes: true in "
                f"{self._config_path} and restart the engine."
            ),
            "symbol": (effective.get("backtest") or {}).get("symbol"),
            "current": self._algorithm_of(effective),
            "configFile": self._algorithm_of(self._base),
            "source": "extension" if override is not None else "config",
            "changedAt": override.get("changedAt") if override is not None else None,
            "pending": self.pending(),
            "strategies": strategies,
        }

    def set(self, args: dict) -> dict:
        """algorithm.set: validate a new algorithm, keep it, and have the
        running loop switch to it at its next tick."""
        self._require_allowed()
        change = self._parse(args)
        with self._lock:
            config = self._validated(change)
            self._write(
                {**change, "changedAt": datetime.fromtimestamp(self._now(), UTC).isoformat()}
            )
        self._log(
            f"[algorithm] changed from the extension: {change['strategy_id']} "
            f"step={change['step']} profit_target={change['profit_target']} "
            f"params={json.dumps(change['strategy_params'], sort_keys=True)} -- "
            "the loop switches at its next tick"
        )
        self._notify()
        return {
            "applied": True,
            "current": self._algorithm_of(config.to_dict()),
            "source": "extension",
        }

    def reset(self, _args: dict | None = None) -> dict:
        """algorithm.reset: back to the config file's algorithm."""
        self._require_allowed()
        with self._lock:
            existed = self._path.exists()
            if existed:
                self._path.unlink()
        if existed:
            self._log(
                "[algorithm] the extension's change was reverted: back to the config "
                "file's algorithm at the next tick"
            )
            self._notify()
        return {"applied": existed, "current": self._algorithm_of(self._base), "source": "config"}

    # -- the pieces -------------------------------------------------------------

    def _require_allowed(self) -> None:
        if not self._allowed:
            raise PermissionError(
                "This deployment does not take algorithm changes from the browser "
                f"(live.fidelity.bridge.allow_algorithm_changes in {self._config_path})."
            )

    def _parse(self, args: Any, *, from_file: bool = False) -> dict:
        """A change, checked: from the extension, or as read back from the
        override file (which may also hold the wiring _parse itself
        carried over from the YAML -- never shown, so never sent)."""
        if not isinstance(args, dict):
            raise ConfigurationError("algorithm.set needs an object of arguments.")
        strategy_id = args.get("strategy_id")
        if not isinstance(strategy_id, str) or strategy_id not in self._registry:
            raise ConfigurationError(f"Unknown strategy {strategy_id!r}.")
        params = args.get("strategy_params", {})
        if not isinstance(params, dict) or len(params) > _MAX_PARAMS:
            raise ConfigurationError("strategy_params must be an object of at most 64 values.")
        step = _fraction(args.get("step"), "step")
        profit_target = _fraction(args.get("profit_target"), "profit_target")

        schema = {
            spec["name"]: spec for spec in describe_params(strategy_id, self._registry[strategy_id])
        }
        chosen: dict[str, Any] = {}
        for name, value in params.items():
            spec = schema.get(name)
            if spec is None and from_file and name in _HIDDEN_PARAMS:
                chosen[name] = value
                continue
            if spec is None:
                raise ConfigurationError(f"{strategy_id} has no parameter {name!r}.")
            if "locked" in spec and "mirrors" not in spec:
                raise ConfigurationError(f"{name} is not set here: {spec['locked']}.")
            checked = _param_value(spec, value)
            if checked is not _OMIT:
                chosen[name] = checked
        # A parameter that mirrors the profit target is set to it, as the
        # backtest form does: they must agree (check_target_return).
        for name, spec in schema.items():
            if spec.get("mirrors") == "profit_target":
                chosen[name] = profit_target
        # Never shown, so never sent: wiring the YAML supplies for the
        # same strategy is kept rather than silently dropped.
        base_strategy = self._base.get("strategy", {})
        if base_strategy.get("strategy_id") == strategy_id:
            for name, value in (base_strategy.get("strategy_params") or {}).items():
                if name in _HIDDEN_PARAMS and name not in chosen:
                    chosen[name] = value
        return {
            "strategy_id": strategy_id,
            "strategy_params": chosen,
            "step": step,
            "profit_target": profit_target,
        }

    def _merged(self, override: dict) -> dict:
        data = copy.deepcopy(self._base)
        data["strategy"] = {
            "strategy_id": override.get("strategy_id"),
            "strategy_params": dict(override.get("strategy_params") or {}),
        }
        live = data.setdefault("live", {})
        live["step"] = override.get("step")
        live["profit_target"] = override.get("profit_target")
        return data

    def _validated(self, change: dict) -> BacktestConfig:
        config = BacktestConfig.from_dict(self._merged(change))
        config.validate()
        build_strategy(config, self._registry)
        return config

    def _write(self, data: dict) -> None:
        """Atomically: a reader sees the old override or the new one,
        never half of either."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self._path.with_name(self._path.name + ".tmp")
        with open(temporary, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, self._path)

    def _notify(self) -> None:
        callback = self.on_apply
        if callback is not None:
            callback()

    @staticmethod
    def _algorithm_of(data: dict) -> dict:
        strategy = data.get("strategy") or {}
        live = data.get("live") or {}
        return {
            "strategy_id": strategy.get("strategy_id"),
            "strategy_params": dict(strategy.get("strategy_params") or {}),
            "step": live.get("step"),
            "profit_target": live.get("profit_target"),
        }
