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

The deployment's own file, once per channel: the browser extension by
`live.fidelity.bridge.allow_algorithm_changes`, the Live page (its commands,
applied by the trader -- engine/trading/operator_control.py) by
`live.control.algorithm_changes`. Without the grant a channel can look and
every change is refused: what real capital trades is decided in a reviewable
file, and a browser may change it only when that file says so. A real-money
deployment takes only committed profiles from the page
(research/strategies/live_profiles.py; LiveControlConfig.effective).

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


# What a switch does with the lots held at the time: leave them selling at
# their own targets, sell them as soon as they clear cost, or (switching only
# when flat) nothing, as there are none.
LEGACY_MODES = ("keep", "exit_at_cost", "wait")


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


def check_live_support(config: BacktestConfig, strategy: Any) -> None:
    """Refuse a live deployment that would trade something other than what
    was researched, rather than discover it from the ledger.

      * A strategy whose design includes a signal exit (the Ultimate
        family's regime exit) without execution.allow_signal_exit: its
        calm lots would ride every downturn the exit exists to step out of.
        The flag stays this deployment file's decision -- the second key of
        the two-key gate -- so it is required here, never switched on.
      * A strategy with session-history state (warm_up) the live loop
        cannot rebuild (no live_history_sessions): it would start every
        session blind.
      * A regular-session strategy under live.extended_hours: pre-market
        ticks would widen its sessions' ranges, and after-hours crosses
        UTC midnight in winter. On its venue's windows (live.sessions) it
        may start early -- the loop feeds it the regular session's bars
        alone and places its orders only there -- but a window it cannot
        trade in is refused as a statement the file should not make.
      * A live.profit_target equal to the strategy's reversal_target: a
        restart tells reversal lots from calm lots by their target.
    """
    from research.strategies.strategy_registry import SIGNAL_EXIT_STRATEGIES

    strategy_id = config.strategy.strategy_id
    if strategy_id in SIGNAL_EXIT_STRATEGIES and not config.execution.allow_signal_exit:
        raise ConfigurationError(
            f"{strategy_id} was researched with its signal exit (for ultimate, the regime "
            "exit that sells the calm lots in the first turbulent session). Without it the "
            "lots ride the downturn -- a different, unresearched strategy. Set "
            "execution.allow_signal_exit: true in this deployment's config to trade it."
        )
    if callable(getattr(strategy, "warm_up", None)) and not callable(
        getattr(strategy, "live_history_sessions", None)
    ):
        raise ConfigurationError(
            f"{strategy_id} needs session history the live loop cannot rebuild for it yet; "
            "it would start every session blind. It is backtest-only."
        )
    if getattr(strategy, "regular_session_only", False):
        if config.live.extended_hours:
            raise ConfigurationError(
                f"{strategy_id} is built from regular-session bars; live.extended_hours would "
                "fold pre-market and after-hours ticks into its sessions. Set extended_hours: "
                "false (live.sessions can start the engine early without trading there)."
            )
        if config.live.sessions and "regular" not in config.live.sessions:
            raise ConfigurationError(
                f"{strategy_id} trades the regular session only, and live.sessions "
                f"{list(config.live.sessions)} does not include it."
            )
    reversal_target = getattr(strategy, "reversal_target", None)
    if (
        reversal_target is not None
        and config.live.profit_target is not None
        and math.isclose(reversal_target, config.live.profit_target)
    ):
        raise ConfigurationError(
            f"live.profit_target equals {strategy_id}'s reversal_target ({reversal_target}): "
            "after a restart its reversal lots could not be told from its calm lots, which "
            "the regime exit treats differently. Use different values."
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
    check_live_support(config, strategy)
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
    """The live algorithm as a browser sees it, and the one way it changes.

    `base` is the deployment's YAML (as a validated BacktestConfig);
    `allowed` is the extension's grant (live.fidelity.bridge.
    allow_algorithm_changes), `web_allowed` the Live page's
    (live.control.algorithm_changes), `profiles_only` whether the page may
    send only committed profiles. `on_apply`, set by whatever runs the loop,
    is told when the algorithm to trade has changed; the runner then
    rebuilds from `effective_config()`.
    """

    def __init__(
        self,
        base: BacktestConfig,
        *,
        state_db: str | Path,
        registry: dict[str, type],
        allowed: bool,
        web_allowed: bool = False,
        profiles_only: bool = False,
        config_path: str | Path | None = None,
        log: Callable[[str], None] | None = None,
        now: Callable[[], float] = time.time,
    ) -> None:
        self._base = base.to_dict()
        self._path = override_path(state_db)
        self._registry = registry
        self._allowed = bool(allowed)
        self._web_allowed = bool(web_allowed)
        self.profiles_only = bool(profiles_only)
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
        """The extension's grant."""
        return self._allowed

    @property
    def web_allowed(self) -> bool:
        """The Live page's grant."""
        return self._web_allowed

    @property
    def _applies_override(self) -> bool:
        """An override is traded when any channel that could write one may."""
        return self._allowed or self._web_allowed

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
        override = self.read_override() if self._applies_override else None
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
        return not self._applies_override and self._path.exists()

    def current(self) -> dict:
        """The algorithm traded now: the override when one applies, else the YAML's."""
        return self._algorithm_of(self._effective_data())

    def config_file_algorithm(self) -> dict:
        return self._algorithm_of(self._base)

    def config_file_config(self) -> BacktestConfig:
        """The deployment's YAML with no override laid over it: what a revert
        would trade. Validated."""
        config = BacktestConfig.from_dict(copy.deepcopy(self._base))
        config.validate()
        return config

    def transition(self) -> dict | None:
        """The override in force, for the loop to apply what the switch said
        to do with the lots then held; None when the YAML's algorithm trades."""
        return self.read_override() if self._applies_override else None

    def override_info(self) -> dict | None:
        """Who changed it, how and when -- None when the YAML's is traded."""
        override = self.read_override() if self._applies_override else None
        if override is None:
            return None
        return {
            "channel": override.get("channel", "extension"),
            "changedAt": override.get("changedAt"),
            "changedBy": override.get("changedBy"),
            "reason": override.get("reason"),
            "profile": override.get("profile"),
        }

    def check(self, args: dict) -> tuple[dict, BacktestConfig]:
        """A proposed change, parsed and validated exactly as set() would --
        but nothing written. Returns (the change as it would be kept, the
        config it would trade). Raises ConfigurationError."""
        change = self._parse(args)
        return change, self._validated(change)

    def live_capable(self, strategy_id: str) -> tuple[bool, str | None]:
        """Whether `strategy_id` could trade live on THIS deployment at all,
        and why not: its own live rules (check_live_support) against the
        deployment's settings, with its committed defaults. A strategy that
        only wants parameters filled in counts as capable."""
        from research.strategies.param_schema import STRATEGY_DEFAULTS

        strategy_class = self._registry.get(strategy_id)
        if strategy_class is None:
            return False, f"unknown strategy {strategy_id!r}"
        data = copy.deepcopy(self._base)
        data["strategy"] = {
            "strategy_id": strategy_id,
            "strategy_params": dict(STRATEGY_DEFAULTS.get(strategy_id, {})),
        }
        try:
            config = BacktestConfig.from_dict(data)
            strategy = strategy_class(**config.strategy.strategy_params)
        except Exception:
            return True, None  # it needs parameters chosen, not a different deployment
        try:
            check_live_support(config, strategy)
        except ConfigurationError as exc:
            return False, str(exc)
        return True, None

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

    def set(
        self, args: dict, *, channel: str = "extension", provenance: dict | None = None
    ) -> dict:
        """algorithm.set: validate a new algorithm, keep it, and have the
        running loop switch to it at its next tick. `provenance` (who, why,
        which profile) is kept beside it, for the page to show."""
        self._require_allowed(channel)
        change = self._parse(args)
        with self._lock:
            config = self._validated(change)
            self._write(
                {
                    **change,
                    **(provenance or {}),
                    "channel": channel,
                    "changedAt": datetime.fromtimestamp(self._now(), UTC).isoformat(),
                }
            )
        self._log(
            f"[algorithm] changed from the {channel}: {change['strategy_id']} "
            f"step={change['step']} profit_target={change['profit_target']} "
            f"params={json.dumps(change['strategy_params'], sort_keys=True)} -- "
            "the loop switches at its next tick"
        )
        self._notify()
        return {
            "applied": True,
            "current": self._algorithm_of(config.to_dict()),
            "source": channel,
        }

    def reset(self, _args: dict | None = None, *, channel: str = "extension") -> dict:
        """algorithm.reset: back to the config file's algorithm."""
        self._require_allowed(channel)
        with self._lock:
            existed = self._path.exists()
            if existed:
                self._path.unlink()
        if existed:
            who = "browser extension" if channel == "extension" else "Live page"
            self._log(
                f"[algorithm] reverted from the {who}: back to the config file's algorithm "
                "at the next tick"
            )
            self._notify()
        return {"applied": existed, "current": self._algorithm_of(self._base), "source": "config"}

    # -- the pieces -------------------------------------------------------------

    def _require_allowed(self, channel: str = "extension") -> None:
        if channel == "web":
            if not self._web_allowed:
                raise PermissionError(
                    "This deployment does not take algorithm changes from the Live page "
                    f"(live.control.algorithm_changes in {self._config_path})."
                )
            return
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
    def algorithm_of(data: dict) -> dict:
        return AlgorithmControl._algorithm_of(data)

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


def impact(current: dict, change: dict, lots: list[dict], legacy_lots: str = "keep") -> dict:
    """What a switch from `current` to `change` does to the open book.

    `lots` are the ledger's open lots ({"px", "qty", "target"} as server/
    live.py's state_payload serves them). A lot keeps the target it was
    bought at, and `legacy_lots` says whose it is afterwards: "keep" leaves
    them as the legacy book, exiting at those targets and out of the new
    algorithm's reach (so a regime exit does not apply to them);
    "exit_at_cost" also moves their targets to the smallest gain that clears
    cost; "wait" is a switch made when flat.
    """
    from engine.core.ledger import EXIT_AT_COST_TARGET
    from research.strategies.strategy_registry import SIGNAL_EXIT_STRATEGIES

    count = len(lots)
    target = change.get("profit_target")
    exit_before = current.get("strategy_id") in SIGNAL_EXIT_STRATEGIES
    exit_after = change.get("strategy_id") in SIGNAL_EXIT_STRATEGIES
    notes = []
    if count and legacy_lots == "keep":
        notes.append(
            f"{count} open lot{'' if count == 1 else 's'} become the legacy book: they exit at "
            "the targets they were bought at, and the new algorithm neither sees, retargets "
            "nor sells them. Its grid starts from the price at the switch."
        )
    elif count and legacy_lots == "exit_at_cost":
        notes.append(
            f"{count} open lot{'' if count == 1 else 's'} become the legacy book with their "
            f"target moved to {EXIT_AT_COST_TARGET:.2%}, so each sells as soon as it clears "
            "cost; a lot below cost waits. The new algorithm does not see them."
        )
    elif count:
        notes.append(
            f"{count} open lot{'' if count == 1 else 's'} carry over with the targets they were "
            "bought at; only new lots use the new step and target."
        )
    if exit_before and not exit_after and count:
        notes.append(
            f"The regime exit stops: lots opened under {current.get('strategy_id')} then exit "
            "only at their own targets, through any downturn."
        )
    if exit_after and not exit_before and count and legacy_lots == "wait":
        notes.append(
            f"{change.get('strategy_id')}'s regime exit will apply to the lots already open, "
            "including ones bought by the old algorithm."
        )
    if change.get("strategy_id") != current.get("strategy_id"):
        notes.append("The new strategy starts from replayed history, as every session does.")
    return {
        "open_lots": count,
        "cost": round(sum(float(lot["px"]) * float(lot["qty"]) for lot in lots), 2),
        "lots_at_new_target": sum(
            1
            for lot in lots
            if target is not None and math.isclose(float(lot["target"]), float(target))
        ),
        "signal_exit_before": exit_before,
        "signal_exit_after": exit_after,
        "legacy_lots": legacy_lots,
        "notes": notes,
    }


# A profit target this large is a placeholder the strategy never reaches: the
# Ultimate-RSP books hold, and exit by their regime vote.
_OUT_OF_REACH = 1.0


def _percent(fraction: Any) -> str:
    try:
        return f"{float(fraction) * 100:.4g}%"
    except (TypeError, ValueError):
        return "?"


def _param(strategy_id: str, params: dict, name: str) -> Any:
    """A parameter as the strategy will use it: the config's, else its default."""
    import inspect

    from research.strategies.strategy_registry import resolve_strategy

    if name in params:
        return params[name]
    try:
        parameter = inspect.signature(resolve_strategy(strategy_id).__init__).parameters.get(name)
    except Exception:
        return None
    return (
        None
        if parameter is None or parameter.default is inspect.Parameter.empty
        else parameter.default
    )


def algorithm_summary(algorithm: dict, symbol: str | None = None) -> str:
    """What an algorithm does, in one line, for whoever is watching it trade
    -- the Live page and the extension's popup say this rather than "step
    0.1%, target 1000%", which for a book that exits by regime is a
    placeholder, not a plan. `algorithm` is {strategy_id, strategy_params,
    step, profit_target}."""
    strategy_id = str(algorithm.get("strategy_id") or "?")
    params = dict(algorithm.get("strategy_params") or {})
    step, target = algorithm.get("step"), algorithm.get("profit_target")
    what = symbol or "the fund"
    if strategy_id in ("ultimate_rsp", "ultimate_ursp"):
        minute = _param(strategy_id, params, "execute_minute")
        band = _param(strategy_id, params, "rebalance_band")
        text = (
            f"holds a share of equity in {what} set by a daily regime vote, rebalanced once a "
            f"session at minute {minute} when more than {_percent(band)} off; it sells -- at a "
            "loss if need be -- only to cut exposure"
        )
        if isinstance(target, int | float) and target >= _OUT_OF_REACH:
            text += f" (the lots' +{_percent(target)} target is out of reach on purpose)"
        return text
    if strategy_id == "ultimate":
        minute = _param(strategy_id, params, "liquidate_minute")
        return (
            f"calm markets: buys each {_percent(step)} dip and sells each lot at "
            f"+{_percent(target)}; turbulent ones: no grid buys, only reversal lots, and its calm "
            f"lots are sold at minute {minute} of the first turbulent session"
        )
    return f"buys each {_percent(step)} dip, sells each lot at +{_percent(target)}"


def _describe_change(change: dict) -> str:
    return (
        f"{change['strategy_id']} (step {change['step']:.4%}, target {change['profit_target']:.4%})"
    )


def algorithm_handlers(
    control: AlgorithmControl,
    *,
    symbol: str,
    paper: bool,
    on_rewarm: Callable[[], None] | None = None,
) -> dict[str, Callable[[Any], str]]:
    """The Live page's algorithm commands, for the trader's ControlApplier
    (engine/trading/operator_control.py): switch, revert and -- where a loop
    runs -- re-warm.

    Applied through `control` exactly as the extension's changes are: the
    same validation, the same override file, the same rebuild at the next
    tick (`on_apply`). A switch names a committed profile
    (research/strategies/live_profiles.py) or, on paper only, the change
    itself; a real-money deployment takes only a profile with a passing
    paper promotion.
    """
    from engine.trading.operator_control import CommandRejected
    from research.strategies import live_profiles

    def switch(command) -> str:
        args = command.args
        provenance = {"changedBy": command.operator, "reason": command.reason}
        profile_id = args.get("profile_id")
        if profile_id:
            try:
                profile = live_profiles.get(str(profile_id))
            except ConfigurationError as exc:
                raise CommandRejected(str(exc)) from exc
            if not profile.fits(symbol):
                raise CommandRejected(
                    f"profile {profile.id} was researched on {', '.join(profile.symbols)}, "
                    f"not {symbol}"
                )
            if not paper and not profile.promoted():
                raise CommandRejected(
                    f"real money takes only a profile with a passing paper promotion, and "
                    f"{profile.id} names none"
                )
            change = profile.change()
            provenance["profile"] = profile.id
        elif control.profiles_only or not paper:
            raise CommandRejected("this deployment switches only to committed profiles")
        else:
            change = {
                key: args.get(key)
                for key in ("strategy_id", "strategy_params", "step", "profit_target")
            }
        # What to do with the lots held now (engine/trading/live_trading_loop.py
        # _apply_transition): the old algorithm's lots keep selling by default.
        mode = args.get("legacy_lots") or "keep"
        if mode not in LEGACY_MODES:
            raise CommandRejected(f"legacy_lots must be one of {', '.join(LEGACY_MODES)}")
        provenance["legacy_lots"] = mode
        try:
            result = control.set(change, channel="web", provenance=provenance)
        except (ConfigurationError, PermissionError) as exc:
            raise CommandRejected(str(exc)) from exc
        what = _describe_change(result["current"])
        return f"switching to {what}" + (
            f" (profile {provenance['profile']})" if "profile" in provenance else ""
        )

    def revert(_command) -> str:
        try:
            result = control.reset(channel="web")
        except PermissionError as exc:
            raise CommandRejected(str(exc)) from exc
        if not result["applied"]:
            return "already trading the config file's algorithm"
        return f"back to the config file's algorithm: {_describe_change(result['current'])}"

    handlers: dict[str, Callable[[Any], str]] = {
        "switch_algorithm": switch,
        "revert_algorithm": revert,
    }
    if on_rewarm is not None:

        def rewarm(_command) -> str:
            on_rewarm()
            return "rebuilding the strategy from replayed history after this tick"

        handlers["rewarm"] = rewarm
    return handlers
