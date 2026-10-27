"""live.sessions, live.orders and live.secondary_feed (engine/core/config.py)."""

from __future__ import annotations

import pytest

from engine.core.config import BacktestConfig, LiveOrdersConfig
from engine.core.exceptions import ConfigurationError


def _config(live: dict | None = None, broker: str = "alpaca") -> BacktestConfig:
    data = {
        "strategy": {"strategy_id": "fixed", "strategy_params": {"allocation_pct": 0.05}},
        "grid": {"steps": [0.01], "profit_targets": [0.005]},
        "backtest": {"symbol": "RSP", "initial_cash": 10_000.0},
        "live": {"enabled": True, "step": 0.01, "profit_target": 0.005, "broker": broker},
    }
    if broker == "fidelity":
        data["live"]["fidelity"] = {"allowed_accounts": ["X1"], "allowed_symbols": ["RSP"]}
    data["live"].update(live or {})
    return BacktestConfig.from_dict(data)


def test_a_config_without_windows_keeps_the_old_clock_and_its_hash():
    plain = _config()
    plain.validate()
    assert not plain.live.venue_clock
    assert plain.live.traded_sessions == ("regular",)
    assert _config({"extended_hours": True}).live.traded_sessions == (
        "pre_market",
        "regular",
        "after_hours",
    )
    emitted = plain.to_dict()["live"]
    for key in ("sessions", "engine_lead_minutes", "orders", "secondary_feed"):
        assert key not in emitted, f"{key} at its default changes every existing config's hash"


def test_named_windows_round_trip():
    config = _config(
        {
            "sessions": ["pre_market", "regular"],
            "engine_lead_minutes": 45,
            "orders": {"ttl_seconds": 120},
            "secondary_feed": {"enabled": True},
        },
        broker="fidelity",
    )
    config.validate()
    assert config.live.venue_clock and config.live.traded_sessions == ("pre_market", "regular")
    assert config.live.orders == LiveOrdersConfig(ttl_seconds=120)
    assert BacktestConfig.from_dict(config.to_dict()) == config


@pytest.mark.parametrize(
    "live,message",
    [
        ({"sessions": "regular"}, "LIST"),
        ({"sessions": ["overnight"]}, "unknown session"),
        ({"sessions": ["regular", "pre_market"]}, "day's order"),
        ({"sessions": ["regular"], "extended_hours": True}, "regular session only"),
        ({"engine_lead_minutes": -5}, "engine_lead_minutes"),
        ({"orders": {"ttl_seconds": 0}}, "ttl_seconds"),
        ({"orders": {"max_spread": 0.5}}, "max_spread"),
        ({"orders": {"ttl": 5}}, "no setting"),
        ({"secondary_feed": {"enabled": True}}, "only a Fidelity"),
        ({"secondary_feed": {"enabled": "yes"}}, "true or false"),
    ],
)
def test_bad_window_settings_are_named(live, message):
    with pytest.raises(ConfigurationError, match=message):
        _config(live).validate()
