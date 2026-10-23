"""
Committed algorithm profiles a live deployment can switch to from the Live
page: a strategy, its parameters and the grid, with the evidence behind them.

--------------------------------------------------------------------
WHY PROFILES

A paper deployment may take any validated parameters from the page
(live.control.algorithm_changes). Real money may not: what real capital
trades must be a reviewable decision, so a real-money deployment switches
only between files in config/live_profiles/ -- each in git, each naming the
backtest it came from, and each needing a passing paper promotion
(engine/promotion.py) before real money may use it.

A profile is the same four things an algorithm change is
(live_algorithm.AlgorithmControl): strategy_id, strategy_params, step and
profit_target. Nothing else -- not the symbol, the account, the risk limits
or the broker. `symbols` says which funds it was researched on; it is only
offered to deployments trading one of them.

  id: ultimate-tqqq
  label: Ultimate, TQQQ
  symbols: [TQQQ]
  strategy_id: ultimate
  strategy_params: {...}
  step: 0.00075
  profit_target: 0.3
  evidence:
    note: where it came from
    backtest: {run: ..., total_return_pct: ..., max_drawdown_pct: ...}
    promotion: promotions/ultimate-tqqq.json   # required for real money
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from engine.core.exceptions import ConfigurationError

_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DIR = _REPO_ROOT / "config" / "live_profiles"
_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,60}$")


@dataclass(frozen=True)
class Profile:
    id: str
    label: str
    symbols: tuple[str, ...]
    strategy_id: str
    strategy_params: dict = field(default_factory=dict)
    step: float = 0.0
    profit_target: float = 0.0
    evidence: dict = field(default_factory=dict)
    path: Path | None = None

    def change(self) -> dict:
        """The algorithm change this profile is (AlgorithmControl.set's args)."""
        return {
            "strategy_id": self.strategy_id,
            "strategy_params": dict(self.strategy_params),
            "step": self.step,
            "profit_target": self.profit_target,
        }

    def fits(self, symbol: str) -> bool:
        return symbol.upper() in self.symbols

    def promotion(self) -> dict | None:
        """The paper promotion evaluation it names, read -- None when it names
        none or the file is missing or unreadable."""
        named = self.evidence.get("promotion")
        if not named or self.path is None:
            return None
        path = Path(named)
        if not path.is_absolute():
            path = self.path.parent / path
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        return data if isinstance(data, dict) else None

    def promoted(self) -> bool:
        """Whether it carries a PASSING paper promotion -- what real money needs."""
        evaluation = self.promotion()
        return bool(evaluation and evaluation.get("passed") is True)

    def to_wire(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "symbols": list(self.symbols),
            **self.change(),
            "evidence": {key: value for key, value in self.evidence.items() if key != "promotion"},
            "promoted": self.promoted(),
        }


def profiles_dir() -> Path:
    configured = os.environ.get("VAI_LIVE_PROFILES")
    return Path(configured) if configured else DEFAULT_DIR


def _profile(path: Path) -> Profile:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ConfigurationError(f"{path}: a profile is a mapping")
    profile_id = str(data.get("id") or "")
    if not _ID.match(profile_id):
        raise ConfigurationError(f"{path}: id {profile_id!r} must be a-z, 0-9 and -")
    if path.stem != profile_id:
        raise ConfigurationError(f"{path}: the file must be named after its id ({profile_id}.yaml)")
    symbols = data.get("symbols") or []
    if not isinstance(symbols, list) or not symbols:
        raise ConfigurationError(f"{path}: symbols must list the funds it was researched on")
    params = data.get("strategy_params") or {}
    if not isinstance(params, dict):
        raise ConfigurationError(f"{path}: strategy_params must be a mapping")
    evidence = data.get("evidence") or {}
    if not isinstance(evidence, dict):
        raise ConfigurationError(f"{path}: evidence must be a mapping")
    return Profile(
        id=profile_id,
        label=str(data.get("label") or profile_id),
        symbols=tuple(str(symbol).upper() for symbol in symbols),
        strategy_id=str(data.get("strategy_id") or ""),
        strategy_params=dict(params),
        step=data.get("step"),
        profit_target=data.get("profit_target"),
        evidence=dict(evidence),
        path=path,
    )


def load_profiles() -> dict[str, Profile]:
    """Every profile, by id. A malformed file is an error, not a skip: a
    profile that silently vanished from the list would be a decision made
    by accident."""
    directory = profiles_dir()
    if not directory.is_dir():
        return {}
    profiles: dict[str, Profile] = {}
    for path in sorted(directory.glob("*.yaml")):
        profile = _profile(path)
        profiles[profile.id] = profile
    return profiles


def get(profile_id: str) -> Profile:
    profile = load_profiles().get(profile_id)
    if profile is None:
        raise ConfigurationError(f"No algorithm profile {profile_id!r} in {profiles_dir()}.")
    return profile


__all__ = ["DEFAULT_DIR", "Profile", "get", "load_profiles", "profiles_dir"]
