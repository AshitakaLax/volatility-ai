"""fidelity_gateway/live.py -- how `cli.py live` gets a Fidelity broker.

The bridge is faked (a stub server behind a real BridgePage), so these
run without a browser or a socket. What they pin: the config decides the
session's permissions and the adapter, the bridge settings reach the
bridge, the journal lands beside the state database, and a failure never
leaves the bridge running.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import fidelity_gateway.live as live
from engine.core.config import BacktestConfig
from fidelity_gateway.bridge.page import BridgePage
from fidelity_gateway.broker import FidelityBroker
from fidelity_gateway.placing_broker import FidelityPlacingBroker
from fidelity_gateway.session import FidelitySessionError
from fidelity_gateway.tests.test_bridge_page import TRADE_URL, StubServer

ACCOUNT = "999888777"


def _config(dry_run=False, **fidelity):
    return BacktestConfig.from_dict(
        {
            "strategy": {"strategy_id": "fixed", "strategy_params": {"allocation_pct": 0.05}},
            "grid": {"steps": [0.01], "profit_targets": [0.005]},
            "backtest": {"symbol": "TQQQ", "initial_cash": 10_000.0},
            "live": {
                "enabled": True,
                "paper_trading": dry_run,
                "step": 0.01,
                "profit_target": 0.005,
                "broker": "fidelity",
                "fidelity": {
                    "allowed_accounts": [ACCOUNT],
                    "account": ACCOUNT,
                    "account_name": "Traditional IRA",
                    "dry_run": dry_run,
                    "allowed_symbols": ["TQQQ"],
                    "max_order_value": 2_000.0,
                    "bridge": {"host": "127.0.0.1", "port": 9123, "allowed_clients": ["127.0.0.1"]},
                    **fidelity,
                },
            },
        }
    )


class FakeBridge:
    """Stands in for open_bridge: records what it was asked for and hands
    back a stub server, with or without auth headers already seen."""

    def __init__(self, *, headers_now=True, headers_after_navigation=True):
        self.headers_now = headers_now
        self.headers_after_navigation = headers_after_navigation
        self.kwargs = None
        self.stopped = False

    def __call__(self, **kwargs):
        self.kwargs = kwargs
        bridge = self

        def answer(command, args):
            if command == "navigate" and bridge.headers_after_navigation:
                server.push("request", {"url": TRADE_URL, "headers": {"x-csrf-token": "T"}})
                return {"tabUrl": args["url"]}
            return {"status": 200, "url": "", "body": json.dumps({})}

        server = StubServer(answer)
        server.stop = self._stop
        if self.headers_now:
            server.push("request", {"url": TRADE_URL, "headers": {"x-csrf-token": "T"}})
        return server, BridgePage(server, settle_seconds=0)

    def _stop(self):
        self.stopped = True


@pytest.fixture(autouse=True)
def quick_waits(monkeypatch):
    monkeypatch.setattr(live, "CREDENTIALS_WAIT_SECONDS", 0.05)
    monkeypatch.setattr(live, "PRIMED_CREDENTIALS_WAIT_SECONDS", 0.2)


def test_real_orders_get_a_session_that_may_place_and_the_placing_broker(tmp_path):
    bridge = FakeBridge()
    connection = live.connect_live(
        _config(dry_run=False),
        state_db=tmp_path / "state" / "ledger.db",
        bridge_opener=bridge,
        log=lambda _m: None,
    )
    assert isinstance(connection.broker, FidelityPlacingBroker)
    assert connection.session.allows_orders is True
    assert connection.journal_path == tmp_path / "state" / "fidelity_orders.jsonl"
    assert connection.journal_path.parent.is_dir()
    connection.close()
    assert bridge.stopped


def test_previews_get_a_preview_only_session_and_no_journal(tmp_path):
    connection = live.connect_live(
        _config(dry_run=True),
        state_db=tmp_path / "ledger.db",
        bridge_opener=FakeBridge(),
        log=lambda _m: None,
    )
    assert type(connection.broker) is FidelityBroker
    assert connection.session.allows_orders is False
    assert connection.session.allows_previews is True
    assert connection.journal_path is None


def test_the_bridge_settings_reach_the_bridge(tmp_path):
    bridge = FakeBridge()
    live.connect_live(
        _config(), state_db=tmp_path / "ledger.db", bridge_opener=bridge, log=lambda _m: None
    )
    assert bridge.kwargs["host"] == "127.0.0.1"
    assert bridge.kwargs["port"] == 9123
    assert tuple(bridge.kwargs["allow"]) == ("127.0.0.1",)
    assert tuple(bridge.kwargs["block"]) == ()
    assert bridge.kwargs["wait_seconds"] == 120.0


def test_a_configured_journal_path_wins(tmp_path):
    connection = live.connect_live(
        _config(journal_path=str(tmp_path / "elsewhere" / "orders.jsonl")),
        state_db=tmp_path / "ledger.db",
        bridge_opener=FakeBridge(),
        log=lambda _m: None,
    )
    assert connection.journal_path == tmp_path / "elsewhere" / "orders.jsonl"


def test_a_quiet_page_is_primed_to_provoke_the_headers(tmp_path):
    lines: list[str] = []
    connection = live.connect_live(
        _config(),
        state_db=tmp_path / "ledger.db",
        bridge_opener=FakeBridge(headers_now=False),
        log=lines.append,
    )
    assert connection.session.has_credentials
    assert any("loading Trader+" in line for line in lines)


def test_a_session_that_never_authenticates_stops_the_bridge_and_says_so(tmp_path):
    bridge = FakeBridge(headers_now=False, headers_after_navigation=False)
    with pytest.raises(FidelitySessionError, match="x-csrf-token"):
        live.connect_live(
            _config(), state_db=tmp_path / "ledger.db", bridge_opener=bridge, log=lambda _m: None
        )
    assert bridge.stopped, "a failed start must not leave the bridge listening"


def test_a_config_the_broker_refuses_stops_the_bridge_too(tmp_path):
    from engine.core.exceptions import ConfigurationError

    bridge = FakeBridge()
    config = _config()
    object.__setattr__(config.live, "paper_trading", True)  # contradicts dry_run: false
    with pytest.raises(ConfigurationError, match="no paper mode"):
        live.connect_live(
            config, state_db=tmp_path / "ledger.db", bridge_opener=bridge, log=lambda _m: None
        )
    assert bridge.stopped


def test_the_default_journal_sits_beside_the_state_database():
    assert live.default_journal_path("state/ledger.db") == Path("state/fidelity_orders.jsonl")
