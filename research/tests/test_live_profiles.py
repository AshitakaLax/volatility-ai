"""research/strategies/live_profiles.py: the committed algorithm profiles a
live deployment can switch to from the Live page."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from engine.core.config import BacktestConfig
from engine.core.exceptions import ConfigurationError
from research.strategies import live_profiles
from research.strategies.live_algorithm import AlgorithmControl
from research.strategies.strategy_registry import STRATEGIES

DEPLOYMENTS = yaml.safe_load(Path("config/deployments.yaml").read_text(encoding="utf-8"))[
    "deployments"
]


def test_every_committed_profile_trades_on_a_deployment_it_fits(tmp_path):
    """A profile no deployment could trade is a file nobody can use: each
    must pass the trader's own validation on at least one deployment
    trading a fund it was researched on."""
    profiles = live_profiles.load_profiles()
    assert profiles, "no committed profiles"
    for profile in profiles.values():
        homes = []
        for entry in DEPLOYMENTS.values():
            if not Path(entry["config"]).exists():
                # Registered before its config is written: Fidelity's names the
                # account, so it is never committed, and trades nothing until then.
                continue
            config = BacktestConfig.from_yaml(entry["config"])
            if not profile.fits(config.backtest.symbol):
                continue
            control = AlgorithmControl(
                config,
                state_db=tmp_path / profile.id / "ledger.db",
                registry=STRATEGIES,
                allowed=False,
                web_allowed=True,
            )
            try:
                control.check(profile.change())
            except ConfigurationError:
                continue
            homes.append(entry["config"])
        assert homes, f"{profile.id} trades on no deployment"


def _write(directory, name, text):
    directory.mkdir(exist_ok=True)
    (directory / name).write_text(text)


def test_a_malformed_profile_is_an_error_not_a_skip(tmp_path, monkeypatch):
    monkeypatch.setenv("VAI_LIVE_PROFILES", str(tmp_path))
    _write(tmp_path, "a.yaml", "id: b\nsymbols: [TQQQ]\nstrategy_id: fixed\n")
    with pytest.raises(ConfigurationError, match="named after its id"):
        live_profiles.load_profiles()
    (tmp_path / "a.yaml").write_text("id: a\nsymbols: []\nstrategy_id: fixed\n")
    with pytest.raises(ConfigurationError, match="symbols"):
        live_profiles.load_profiles()


def test_promotion_must_be_a_passing_evaluation(tmp_path, monkeypatch):
    monkeypatch.setenv("VAI_LIVE_PROFILES", str(tmp_path))
    _write(
        tmp_path,
        "p.yaml",
        "id: p\nsymbols: [TQQQ]\nstrategy_id: fixed\nevidence: {promotion: e.json}\n",
    )
    assert not live_profiles.get("p").promoted(), "named file missing"
    (tmp_path / "e.json").write_text('{"passed": false}')
    assert not live_profiles.get("p").promoted()
    (tmp_path / "e.json").write_text('{"passed": true}')
    assert live_profiles.get("p").promoted()
    assert "promotion" not in live_profiles.get("p").to_wire()["evidence"]
