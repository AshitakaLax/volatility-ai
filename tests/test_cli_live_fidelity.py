"""`cli.py live` with live.broker: fidelity.

The seam between cli.py and fidelity_gateway/live.py, as peers: the
bridge connection is faked at connect_live, so these run with no
browser, no socket and no Alpaca account. What they pin: a preview-only
config cannot run the trading loop, the Fidelity broker is the one the
lifecycle reconciles and the loop trades, prices still come from Alpaca
(over a clock-only connection), and the bridge is closed on every way
out.
"""

from __future__ import annotations

import argparse
import importlib

import pytest
import yaml

from engine.execution.reconciliation import BrokerSnapshot
from engine.tests.test_live_trading_loop import FakeBroker, FakeMarketData

ACCOUNT = "999888777"


def _write_config(tmp_path, *, dry_run: bool):
    data = {
        "strategy": {"strategy_id": "fixed", "strategy_params": {"allocation_pct": 0.05}},
        "grid": {"steps": [0.01], "profit_targets": [0.005]},
        "backtest": {"symbol": "TQQQ", "initial_cash": 10_000.0},
        "live": {
            "enabled": True,
            "paper_trading": dry_run,
            "step": 0.01,
            "profit_target": 0.005,
            "poll_interval_seconds": 1.0,
            "broker": "fidelity",
            "fidelity": {
                "allowed_accounts": [ACCOUNT],
                "account": ACCOUNT,
                "account_name": "Traditional IRA",
                "dry_run": dry_run,
                "allowed_symbols": ["TQQQ"],
                "max_order_value": 2_000.0,
            },
        },
    }
    path = tmp_path / "fidelity_live.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def _args(config, tmp_path, *, check_only=False, max_ticks=None):
    return argparse.Namespace(
        config=str(config),
        state_db=str(tmp_path / "state" / "ledger.db"),
        check_only=check_only,
        max_ticks=max_ticks,
    )


class FidelityLikeBroker(FakeBroker):
    """A LiveBroker with a snapshot and, like the Fidelity adapter, no
    Alpaca trading_client."""

    def __init__(self, snapshot=None):
        super().__init__()
        self._snapshot = snapshot

    def snapshot(self):
        if isinstance(self._snapshot, Exception):
            raise self._snapshot
        return self._snapshot or BrokerSnapshot()


@pytest.fixture
def cli():
    return importlib.import_module("cli")


@pytest.fixture
def fake_connection(monkeypatch):
    """Replaces connect_live: records the call and whether close() ran."""
    calls = {"connected": 0, "closed": 0, "state_db": None}
    holder = {"broker": FidelityLikeBroker()}

    class Connection:
        def __init__(self, broker):
            self.broker = broker

        def close(self):
            calls["closed"] += 1

    def connect_live(config, *, state_db, **_kwargs):
        calls["connected"] += 1
        calls["state_db"] = state_db
        return Connection(holder["broker"])

    import fidelity_gateway.live

    monkeypatch.setattr(fidelity_gateway.live, "connect_live", connect_live)
    calls["holder"] = holder
    return calls


def test_a_preview_only_config_cannot_run_the_trading_loop(cli, tmp_path, capsys, fake_connection):
    """A preview never fills, so the loop would track phantom orders
    forever. Refused before anything is opened."""
    config = _write_config(tmp_path, dry_run=True)
    assert cli.cmd_live(_args(config, tmp_path)) == 2
    assert "--check-only" in capsys.readouterr().err
    assert fake_connection["connected"] == 0


def test_check_only_reaches_ready_through_the_bridge_and_closes_it(
    cli, tmp_path, capsys, fake_connection
):
    config = _write_config(tmp_path, dry_run=True)
    assert cli.cmd_live(_args(config, tmp_path, check_only=True)) == 0
    out = capsys.readouterr().out
    assert "READY" in out
    assert fake_connection["connected"] == 1
    assert fake_connection["closed"] == 1
    assert fake_connection["state_db"].endswith("ledger.db")


def test_a_failed_reconciliation_still_closes_the_bridge(cli, tmp_path, fake_connection):
    fake_connection["holder"]["broker"] = FidelityLikeBroker(snapshot=RuntimeError("no snapshot"))
    config = _write_config(tmp_path, dry_run=False)
    assert cli.cmd_live(_args(config, tmp_path, check_only=True)) == 1
    assert fake_connection["closed"] == 1


def test_the_loop_trades_the_fidelity_broker_with_alpaca_prices(
    cli, tmp_path, monkeypatch, fake_connection
):
    """Prices and the market clock still come from Alpaca; the Fidelity
    broker has no Alpaca connection to borrow, so a clock-only one is
    opened -- and the loop's orders go to the Fidelity broker."""
    monkeypatch.setenv("APCA_API_KEY_ID", "k")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "s")
    market = FakeMarketData()
    market.push(100.0)
    seen = {}

    def market_data(**kwargs):
        seen["trading_client"] = kwargs.get("trading_client")
        return market

    monkeypatch.setattr("engine.data.alpaca_market_data.AlpacaMarketData", market_data)
    clock = object()
    monkeypatch.setattr(cli, "_alpaca_clock_client", lambda: clock)

    config = _write_config(tmp_path, dry_run=False)
    assert cli.cmd_live(_args(config, tmp_path, max_ticks=1)) == 0
    assert seen["trading_client"] is clock
    assert fake_connection["closed"] == 1


def test_an_alpaca_broker_still_lends_its_own_clock(cli, tmp_path, monkeypatch):
    """Unchanged for Alpaca: the clock comes from the connection the
    broker already authenticated, and no second one is opened."""
    from engine.core.persistence import LedgerStore
    from engine.tests.test_live_trading_loop import make_config
    from engine.trading.risk_manager import CircuitBreaker
    from engine.trading.runtime_lifecycle import RuntimeLifecycle

    monkeypatch.setenv("APCA_API_KEY_ID", "k")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "s")
    market = FakeMarketData()
    market.push(100.0)
    seen = {}

    def market_data(**kwargs):
        seen["trading_client"] = kwargs.get("trading_client")
        return market

    monkeypatch.setattr("engine.data.alpaca_market_data.AlpacaMarketData", market_data)
    monkeypatch.setattr(cli, "_alpaca_clock_client", lambda: pytest.fail("opened a second client"))

    broker = FakeBroker()
    broker.trading_client = own = object()
    store = LedgerStore(str(tmp_path / "ledger.db"))
    breaker = CircuitBreaker(store=store)
    lifecycle = RuntimeLifecycle(store=store, circuit_breaker=breaker)

    class Args:
        max_ticks = 1

    assert cli._run_trading_loop(Args(), make_config(), broker, store, breaker, lifecycle) == 0
    assert seen["trading_client"] is own


def test_the_example_deployment_config_validates_and_trades_real_money():
    """config/fidelity_live.yaml.example is what an operator copies; it
    must load, validate, and say plainly that it places real orders."""
    from pathlib import Path

    from engine.core.config import BacktestConfig

    example = Path(__file__).resolve().parents[1] / "config" / "fidelity_live.yaml.example"
    config = BacktestConfig.from_yaml(str(example))
    config.validate()
    assert config.live.broker == "fidelity"
    assert config.live.paper_trading is False
    assert config.live.fidelity.dry_run is False
    assert config.backtest.symbol in config.live.fidelity.allowed_symbols
    assert config.live.fidelity.max_order_value > 0
    # allocation_pct of the budget must buy at least one whole share at a
    # plausible price, or the first buy would stop the loop.
    budget = config.backtest.initial_cash * config.strategy.strategy_params["allocation_pct"]
    assert budget >= 150, "the example's buys would be under one share of TQQQ"


def _lock_is_free(tmp_path) -> bool:
    from engine.core.process_lock import LockHeldError, StateStoreLock

    lock = StateStoreLock(str(tmp_path / "state" / "ledger.db"))
    try:
        lock.acquire()
    except LockHeldError:
        return False
    lock.release()
    return True


def test_every_way_out_releases_the_state_lock(cli, tmp_path, fake_connection):
    """By behaviour, alongside engine/tests/test_process_lock.py's check
    of the structure: READY, not-READY, each leaves the lock free."""
    config = _write_config(tmp_path, dry_run=True)
    assert cli.cmd_live(_args(config, tmp_path, check_only=True)) == 0
    assert _lock_is_free(tmp_path)
    fake_connection["holder"]["broker"] = FidelityLikeBroker(snapshot=RuntimeError("down"))
    assert cli.cmd_live(_args(config, tmp_path, check_only=True)) == 1
    assert _lock_is_free(tmp_path)
