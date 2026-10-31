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


def _with_symbol(section, symbol):
    """Every `allowed_symbols` list under `section`, re-pointed at `symbol`."""
    if isinstance(section, dict):
        for key, value in section.items():
            if key == "allowed_symbols":
                section[key] = [symbol]
            else:
                _with_symbol(value, symbol)


def _configs_for(entry, profile):
    """The configs a registered deployment could trade `profile` under.

    A committed config is the one it trades. A config that is registered but
    not committed (Fidelity's names the account, so it is git-ignored) is the
    operator's to write, fund included: it is checked as its committed
    `.example` re-pointed at each fund the profile fits, so the profile still
    has to pass the trader's validation there. With no example either there
    is nothing to check it against, and it counts as a home unchecked."""
    path = Path(entry["config"])
    if path.exists():
        config = BacktestConfig.from_yaml(path)
        return [config] if profile.fits(config.backtest.symbol) else []
    example = Path(f"{path}.example")
    if not example.exists():
        return None
    configs = []
    for symbol in profile.symbols:
        raw = yaml.safe_load(example.read_text(encoding="utf-8"))
        raw.setdefault("backtest", {})["symbol"] = symbol
        _with_symbol(raw.get("live"), symbol)
        configs.append(BacktestConfig.from_dict(raw))
    return configs


def _homes(profile, tmp_path):
    """The registered deployments `profile` passes the trader's validation on."""
    homes = []
    for entry in DEPLOYMENTS.values():
        configs = _configs_for(entry, profile)
        if configs is None:
            homes.append(entry["config"])
            continue
        for n, config in enumerate(configs):
            control = AlgorithmControl(
                config,
                state_db=tmp_path / profile.id / f"{n}" / "ledger.db",
                registry=STRATEGIES,
                allowed=False,
                web_allowed=True,
            )
            try:
                control.check(profile.change())
            except ConfigurationError:
                continue
            homes.append(entry["config"])
    return homes


def test_every_committed_profile_trades_on_a_deployment_it_fits(tmp_path):
    """A profile no deployment could trade is a file nobody can use: each
    must pass the trader's own validation on at least one registered
    deployment that does, or could, trade a fund it was researched on."""
    profiles = live_profiles.load_profiles()
    assert profiles, "no committed profiles"
    for profile in profiles.values():
        assert _homes(profile, tmp_path), f"{profile.id} trades on no deployment"


def test_an_uncommitted_deployment_still_checks_the_profile(tmp_path, monkeypatch):
    """The stand-in for an uncommitted config is its example, so a profile the
    trader would refuse finds no home there: an RSP profile naming an unknown
    strategy fits only Fidelity's (RSP is the operator's to choose) and fails it."""
    monkeypatch.setenv("VAI_LIVE_PROFILES", str(tmp_path))
    _write(tmp_path, "broken-rsp.yaml", "id: broken-rsp\nsymbols: [RSP]\nstrategy_id: no_such\n")
    (profile,) = live_profiles.load_profiles().values()
    assert _homes(profile, tmp_path) == []


def _write(directory, name, text):
    directory.mkdir(exist_ok=True)
    (directory / name).write_text(text)


def test_a_malformed_profile_is_skipped_and_the_rest_still_load(tmp_path, monkeypatch, caplog):
    monkeypatch.setenv("VAI_LIVE_PROFILES", str(tmp_path))
    _write(tmp_path, "a.yaml", "id: b\nsymbols: [TQQQ]\nstrategy_id: fixed\n")  # wrong name
    _write(tmp_path, "b.yaml", "id: b\nsymbols: []\nstrategy_id: fixed\n")  # no symbols
    _write(tmp_path, "c.yaml", "id: [unclosed\n")  # not YAML
    _write(tmp_path, "d.yaml", "id: d\nsymbols: [TQQQ]\nstrategy_id: fixed\n")
    with caplog.at_level("WARNING"):
        assert list(live_profiles.load_profiles()) == ["d"]
    for name in ("a.yaml", "b.yaml", "c.yaml"):
        assert f"Skipping malformed live profile {name}" in caplog.text
    with pytest.raises(ConfigurationError, match="No algorithm profile 'b'"):
        live_profiles.get("b")


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


def test_a_promotion_that_is_not_a_path_names_none_and_breaks_nothing(tmp_path, monkeypatch):
    monkeypatch.setenv("VAI_LIVE_PROFILES", str(tmp_path))
    for value in ("PASSING", {"passed": True}, ["x"], 3):
        profile = tmp_path / "p.yaml"
        profile.write_text(
            yaml.safe_dump(
                {
                    "id": "p",
                    "symbols": ["TQQQ"],
                    "strategy_id": "fixed",
                    "evidence": {"promotion": value},
                }
            )
        )
        assert live_profiles.get("p").promotion() is None
        assert not live_profiles.get("p").promoted()
