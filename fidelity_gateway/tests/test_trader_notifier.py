"""bridge/trader_notifier.py: an Alpaca deployment's journals, told to apps.

The trader's files are written the way the trader writes them -- through
ControlInbox, with a clock the test holds -- and TraderWatch.poll is called
with the same clock, so nothing waits on time. The last part runs a
TraderNotifier over a real socket with bridge_support.FakeApp.
"""

from __future__ import annotations

import pytest

from engine.core.exceptions import ConfigurationError
from engine.trading.control_inbox import ControlInbox
from fidelity_gateway.bridge.ip_policy import AddressPolicy
from fidelity_gateway.bridge.keys import (
    API_KEY_ENV_VAR,
    NOTIFIER_KEY_ENV_VAR,
    NOTIFY_KEY_ENV_VAR,
    BridgeApiKey,
)
from fidelity_gateway.bridge.notifications import EVENT_KINDS, Notifications
from fidelity_gateway.bridge.trader_notifier import (
    JournalTail,
    TraderNotifier,
    TraderWatch,
    WatchedDeployment,
    engine_part,
    load_deployments,
    load_notifier_key,
    trader_report,
)
from fidelity_gateway.tests.bridge_support import NOTIFY_KEY

T0 = 1_763_478_000.0  # 2025-11-18 15:00 UTC: a weekday, mid-session in New York


class Clock:
    def __init__(self, t: float = T0) -> None:
        self.t = t

    def __call__(self) -> float:
        return self.t


def _deployment(tmp_path, **overrides) -> WatchedDeployment:
    fields = {
        "id": "paper-ultimate",
        "label": "Ultimate (paper)",
        "broker": "alpaca",
        "paper": True,
        "symbol": "TQQQ",
        "control_dir": tmp_path / "control",
        "state_db": None,
    }
    return WatchedDeployment(**{**fields, **overrides})


class Trader:
    """A trader's control directory, written as cli.py and operator_control do."""

    def __init__(self, root, clock: Clock) -> None:
        self.clock = clock
        self.inbox = ControlInbox(root, clock=clock)

    def status(self, state: str, *, process: str = "loop", **fields) -> None:
        self.inbox.write_status(state=state, process=process, heartbeat_seconds=60.0, **fields)

    def buy(self, qty=3.0, price=72.10, target_price=80.75) -> None:
        self.inbox.record_fill(
            {
                "t": self.clock(),
                "side": "buy",
                "lot": "lot-1",
                "qty": qty,
                "price": price,
                "value": qty * price,
                "target": 0.12,
                "target_price": target_price,
            }
        )

    def sell(self, qty=3.0, price=80.80, cost=216.30, pnl=25.95, reason="profit_target") -> None:
        self.inbox.record_fill(
            {
                "t": self.clock(),
                "side": "sell",
                "reason": reason,
                "lot": "lot-1",
                "qty": qty,
                "price": price,
                "proceeds": cost + pnl,
                "cost": cost,
                "pnl": pnl,
            }
        )

    def order(self, event: str, kind: str = "buy", **fields) -> None:
        self.inbox.record_order(
            {
                "t": self.clock(),
                "order": "d-1",
                "kind": kind,
                "event": event,
                "session": "regular",
                "limit": 72.10,
                "qty": 3.0,
                "filled_qty": 0.0,
                "avg_price": None,
                **fields,
            }
        )


@pytest.fixture
def setup(tmp_path):
    clock = Clock()
    trader = Trader(tmp_path / "control", clock)
    hub = Notifications(tuple(EVENT_KINDS), stream="s1", clock=clock)
    books: list[float] = []

    def book(state_db, inbox, *, symbol, now):
        books.append(now)
        return {"symbol": symbol, "asOf": "x", "open": [], "closed": [], "today": {}}

    watch = TraderWatch(_deployment(tmp_path), hub, book=book)
    return clock, trader, hub, watch, books


def _said(hub) -> list[tuple[str, str]]:
    return [(n.kind, n.title) for n in hub.recent()]


# -- which deployments --------------------------------------------------------------


def _registry(tmp_path) -> object:
    (tmp_path / "ultimate.yaml").write_text(
        "backtest:\n  symbol: TQQQ\nlive:\n  paper_trading: true\n", encoding="utf-8"
    )
    (tmp_path / "production.yaml").write_text(
        "backtest:\n  symbol: RSP\nlive:\n  paper_trading: false\n", encoding="utf-8"
    )
    (tmp_path / "fidelity.yaml").write_text(
        "backtest:\n  symbol: RSP\nlive:\n  broker: fidelity\n  paper_trading: false\n",
        encoding="utf-8",
    )
    path = tmp_path / "deployments.yaml"
    path.write_text(
        f"""deployments:
  paper-ultimate:
    label: Ultimate (paper)
    config: {tmp_path}/ultimate.yaml
    state_db: {tmp_path}/u.db
    control_dir: {tmp_path}/controls/u
  live:
    label: Production (real money)
    config: {tmp_path}/production.yaml
    state_db: {tmp_path}/p.db
    control_dir: {tmp_path}/controls/p
  no-journals:
    config: {tmp_path}/ultimate.yaml
    state_db: {tmp_path}/n.db
  fidelity:
    label: Fidelity (real money)
    broker: fidelity
    config: {tmp_path}/fidelity.yaml
    state_db: {tmp_path}/f.db
    control_dir: {tmp_path}/controls/f
""",
        encoding="utf-8",
    )
    return path


def test_every_alpaca_deployment_with_journals_is_followed_by_default(tmp_path):
    chosen = load_deployments(_registry(tmp_path))
    assert [d.id for d in chosen] == ["paper-ultimate", "live"]
    ultimate, live = chosen
    assert (ultimate.broker, ultimate.paper, ultimate.symbol) == ("alpaca", True, "TQQQ")
    assert (live.paper, live.mode, live.label) == (False, "live", "Production (real money)")
    assert ultimate.account == {
        "id": "paper-ultimate",
        "label": "Ultimate (paper)",
        "broker": "alpaca",
        "paper": True,
        "symbol": "TQQQ",
    }


def test_named_deployments_are_followed_in_the_registrys_order(tmp_path):
    chosen = load_deployments(_registry(tmp_path), only=("live", "paper-ultimate"))
    assert [d.id for d in chosen] == ["paper-ultimate", "live"]


def test_an_unknown_or_unreadable_deployment_is_refused(tmp_path):
    registry = _registry(tmp_path)
    with pytest.raises(ConfigurationError, match="no deployment champion"):
        load_deployments(registry, only=("champion",))
    with pytest.raises(ConfigurationError, match="no control_dir"):
        load_deployments(registry, only=("no-journals",))


def test_a_config_that_cannot_be_read_falls_back_to_the_registry(tmp_path):
    path = tmp_path / "deployments.yaml"
    path.write_text(
        f"deployments:\n  x:\n    config: {tmp_path}/missing.yaml\n    state_db: s.db\n"
        f"    control_dir: {tmp_path}/c\n",
        encoding="utf-8",
    )
    (only,) = load_deployments(path)
    assert (only.broker, only.paper, only.symbol, only.label) == ("alpaca", None, None, "x")


# -- the journals -----------------------------------------------------------------


def test_a_journal_is_read_from_where_it_was_left(tmp_path):
    folder = tmp_path / "fills"
    folder.mkdir()
    day = folder / "2025-11-18.jsonl"
    day.write_text('{"t": 1, "side": "buy"}\n', encoding="utf-8")
    tail = JournalTail(folder)
    tail.skip_to_end()
    assert tail.read() == []
    with open(day, "a", encoding="utf-8") as handle:
        handle.write('{"t": 2, "side": "sell"}\n{"t": 3, "si')  # the last still being written
    assert [row["t"] for row in tail.read()] == [2]
    with open(day, "a", encoding="utf-8") as handle:
        handle.write('de": "buy"}\n')
    assert [row["t"] for row in tail.read()] == [3]
    (folder / "2025-11-19.jsonl").write_text('{"t": 4}\nnot json\n{"no": "t"}\n')
    assert [row["t"] for row in tail.read()] == [4]


def test_a_rewritten_journal_is_followed_from_its_new_end(tmp_path):
    folder = tmp_path / "fills"
    folder.mkdir()
    day = folder / "2025-11-18.jsonl"
    day.write_text('{"t": 1}\n{"t": 2}\n', encoding="utf-8")
    tail = JournalTail(folder)
    tail.skip_to_end()
    day.write_text('{"t": 9}\n', encoding="utf-8")
    assert tail.read() == []
    with open(day, "a", encoding="utf-8") as handle:
        handle.write('{"t": 10}\n')
    assert [row["t"] for row in tail.read()] == [10]


# -- the trader's report ------------------------------------------------------------


def test_a_trader_is_stale_after_three_heartbeats_and_never_sooner_than_90s(tmp_path):
    clock = Clock()
    trader = Trader(tmp_path, clock)
    trader.status("trading", last_tick_at="2025-11-18T15:00:00+00:00")
    status = trader.inbox.status()
    fresh = trader_report(status, T0 + 179)
    assert fresh["stale"] is False and fresh["running"] is True
    assert fresh["lastTickAt"] == "2025-11-18T15:00:00+00:00"
    assert trader_report(status, T0 + 181)["stale"] is True
    trader.inbox.write_status(state="trading", process="loop", heartbeat_seconds=10.0)
    assert trader_report(trader.inbox.status(), T0 + 89)["stale"] is False
    assert trader_report(None, T0) is None


def test_the_loops_words_become_the_engines(tmp_path):
    deployment = _deployment(tmp_path)

    def engine(state, process="loop", stale=False, detail=None):
        report = {
            "state": state,
            "detail": detail,
            "process": process,
            "stale": stale,
            "lastTickAt": None,
            "updatedAt": None,
        }
        return engine_part(report, deployment)

    assert engine("trading") == {
        "mode": "paper",
        "state": "running",
        "detail": "trading",
        "symbol": "TQQQ",
        "lastTickAt": None,
        "updatedAt": None,
    }
    assert engine("buys_paused", detail="drawdown 18%")["state"] == "paused"
    assert engine("buys_paused", detail="drawdown 18%")["detail"] == "drawdown 18%"
    assert engine("winding_down")["detail"].startswith("winding down")
    assert engine("recovery_required")["state"] == "recovery_required"
    assert engine("waiting_for_open", process="supervisor") is None
    assert engine("trading", stale=True) is None


# -- what is said ---------------------------------------------------------------------


def test_what_was_there_when_it_started_is_history_not_news(setup):
    clock, trader, hub, watch, _ = setup
    trader.status("trading")
    trader.buy()
    trader.order("rejected")
    watch.poll(clock())
    assert hub.recent() == []
    assert hub.status["engine"]["state"] == "running"
    assert hub.status["trader"]["state"] == "trading"


def test_a_buy_says_where_its_lot_sells(setup):
    clock, trader, hub, watch, _ = setup
    trader.status("trading")
    watch.poll(clock())
    clock.t += 30
    trader.buy()
    watch.poll(clock())
    (notification,) = hub.recent()
    assert (notification.kind, notification.title) == ("buy", "Bought 3 TQQQ")
    # The app reads "Sells at $…" out of a buy's body (HomeScreen.sellsAt).
    assert notification.body == "3 at $72.10 ($216.30). Sells at $80.75."
    assert notification.data["targetSellPrice"] == 80.75
    assert notification.severity == "info"


def test_a_sale_says_what_it_made_and_a_loss_is_a_warning(setup):
    clock, trader, hub, watch, _ = setup
    watch.poll(clock())
    trader.sell()
    trader.sell(qty=2.0, price=70.0, cost=150.0, pnl=-10.25, reason="signal_exit")
    watch.poll(clock())
    first, second = hub.recent()
    assert (first.kind, first.title, first.severity) == ("sell", "Sold 3 TQQQ", "info")
    assert first.body == "3 at $80.80: +$25.95 after costs (profit target)."
    assert (second.title, second.severity) == ("Sold 2 TQQQ", "warning")
    assert second.body == "2 at $70.00: -$10.25 after costs (regime exit)."
    assert second.data["reason"] == "signal_exit"


def test_an_orders_life_is_told_but_not_its_fill(setup):
    clock, trader, hub, watch, _ = setup
    watch.poll(clock())
    trader.order("placed")
    trader.order("filled", filled_qty=3.0, avg_price=72.1)
    trader.order("cancel_requested")
    trader.order("cancelled", kind="sell", session="after_hours", filled_qty=1.0)
    trader.order("rejected", why="insufficient buying power")
    watch.poll(clock())
    assert _said(hub) == [
        ("order_update", "Order placed"),
        ("order_update", "Order cancelled"),
        ("order_problem", "Order rejected"),
    ]
    placed, cancelled, rejected = hub.recent()
    assert placed.body == "Buy 3 TQQQ at $72.10 limit, to Alpaca."
    assert cancelled.body == "Sell 3 TQQQ at $72.10 limit (after-hours), 1 filled first."
    assert rejected.body == (
        "Alpaca rejected the buy 3 TQQQ at $72.10 limit: insufficient buying power."
    )
    assert rejected.severity == "warning"


def test_the_engine_is_news_when_its_state_changes_and_not_between_sessions(setup):
    clock, trader, hub, watch, _ = setup
    trader.status("starting")
    watch.poll(clock())
    for state in ("trading", "trading", "buys_paused", "stopped"):
        clock.t += 10
        trader.status(state, detail="drawdown 18%" if state == "buys_paused" else None)
        watch.poll(clock())
    clock.t += 10
    trader.status("waiting_for_open", process="supervisor", next_open="2025-11-19T14:30:00+00:00")
    watch.poll(clock())
    assert hub.status["engine"] is None
    assert hub.status["trader"]["nextOpen"] == "2025-11-19T14:30:00+00:00"
    clock.t += 10
    trader.status("starting")
    watch.poll(clock())
    assert _said(hub) == [
        ("engine", "Engine running"),
        ("engine", "Engine paused"),
        ("engine", "Engine stopped"),
        ("engine", "Engine starting"),
    ]
    paused = hub.recent()[1]
    assert paused.severity == "warning"
    assert paused.body == "TQQQ · paper: drawdown 18%"


def test_a_trader_that_goes_quiet_is_said_once_and_again_when_it_is_back(setup):
    clock, trader, hub, watch, _ = setup
    trader.status("trading")
    watch.poll(clock())
    clock.t += 200
    watch.poll(clock())
    clock.t += 200
    watch.poll(clock())
    trader.status("trading")
    watch.poll(clock())
    assert _said(hub) == [
        ("session", "Trader not reporting"),
        ("session", "Trader reporting again"),
    ]
    quiet = hub.recent()[0]
    assert quiet.severity == "warning"
    assert quiet.body.startswith("Ultimate (paper) last reported 3m 20s ago (trading).")
    assert hub.status["engine"]["state"] == "running"


def test_a_trader_that_said_it_stopped_may_go_quiet(setup):
    clock, trader, hub, watch, _ = setup
    trader.status("trading")
    watch.poll(clock())
    trader.status("stopped")
    watch.poll(clock())
    clock.t += 3600
    watch.poll(clock())
    assert _said(hub) == [("engine", "Engine stopped")]
    assert hub.status["trader"]["stale"] is True


def test_a_window_that_closes_after_it_starts_is_summed_up_once(setup):
    clock, trader, hub, watch, _ = setup
    old = {"day": "2025-11-17", "session": "regular", "orders": 2}
    trader.status("trading", last_window=old)
    watch.poll(clock())
    watch.poll(clock())
    new = {
        "day": "2025-11-18",
        "session": "regular",
        "orders": 1,
        "filled_qty": 3.0,
        "avg_price": 72.1,
    }
    trader.status("trading", last_window=new)
    watch.poll(clock())
    watch.poll(clock())
    assert _said(hub) == [("window", "Regular window closed")]


def test_the_book_is_read_every_30s_and_at_once_after_a_fill(setup):
    clock, trader, hub, watch, books = setup
    watch.poll(clock())
    clock.t += 10
    watch.poll(clock())
    assert books == [T0]
    assert hub.status["book"]["symbol"] == "TQQQ"
    trader.buy()
    watch.poll(clock())
    assert books == [T0, T0 + 10]
    clock.t += 31
    watch.poll(clock())
    assert len(books) == 3


def test_the_status_apps_are_sent_changes_only_when_the_trader_writes(setup):
    clock, trader, hub, watch, _ = setup
    trader.status("trading")
    watch.poll(clock())
    sent: list[dict] = []
    hub.subscribe(lambda kind, payload: sent.append(payload) if kind == "status" else None)
    for _ in range(5):
        clock.t += 2
        watch.poll(clock())
    assert sent == []
    trader.status("trading", last_tick_at="2025-11-18T15:00:10+00:00")
    watch.poll(clock())
    assert len(sent) == 1


def test_a_deployment_that_never_reported_has_no_trader(setup):
    clock, _, hub, watch, _ = setup
    watch.poll(clock())
    assert hub.status["trader"] is None and hub.status["engine"] is None


# -- the key --------------------------------------------------------------------------


GOOD = "notifier-test-key-abcdefghijklmnopqrstuvwxyz0123"


def test_the_notifier_reads_a_key_of_its_own(tmp_path, monkeypatch):
    monkeypatch.setenv(NOTIFIER_KEY_ENV_VAR, GOOD)
    monkeypatch.delenv(API_KEY_ENV_VAR, raising=False)
    monkeypatch.delenv(NOTIFY_KEY_ENV_VAR, raising=False)
    assert load_notifier_key(env_file=tmp_path / ".env").value == GOOD


@pytest.mark.parametrize("other", [API_KEY_ENV_VAR, NOTIFY_KEY_ENV_VAR])
def test_the_notifier_refuses_either_of_the_bridges_keys(tmp_path, monkeypatch, other):
    monkeypatch.setenv(NOTIFIER_KEY_ENV_VAR, GOOD)
    monkeypatch.delenv(API_KEY_ENV_VAR, raising=False)
    monkeypatch.delenv(NOTIFY_KEY_ENV_VAR, raising=False)
    env = tmp_path / ".env"
    env.write_text(f"{other}={GOOD}\n", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="a key of its own"):
        load_notifier_key(env_file=env)


def test_without_a_key_it_says_how_to_make_one(tmp_path, monkeypatch):
    monkeypatch.delenv(NOTIFIER_KEY_ENV_VAR, raising=False)
    with pytest.raises(ConfigurationError, match="keygen --notifier"):
        load_notifier_key(env_file=tmp_path / ".env")


# -- over a socket ----------------------------------------------------------------------


@pytest.fixture
def served(tmp_path):
    pytest.importorskip("websockets")
    clock = Clock()
    ultimate = Trader(tmp_path / "u", clock)
    live = Trader(tmp_path / "l", clock)
    ultimate.status("trading")
    notifier = TraderNotifier(
        [
            _deployment(tmp_path, control_dir=tmp_path / "u"),
            _deployment(
                tmp_path, id="live", label="Production", paper=False, control_dir=tmp_path / "l"
            ),
        ],
        BridgeApiKey(NOTIFY_KEY),
        host="127.0.0.1",
        port=0,
        policy=AddressPolicy(["127.0.0.1"]),
        events=tuple(EVENT_KINDS),
        clock=clock,
        book=lambda *a, **k: None,
    )
    notifier.start()
    yield notifier, clock, ultimate, live
    notifier.server.stop()


def _connect(notifier, path):
    from fidelity_gateway.tests.bridge_support import FakeApp

    app = FakeApp(notifier.server.url_for(path))
    assert app.handshake()["type"] == "welcome"
    return app


def test_each_deployment_has_its_path_and_its_hello_names_the_account(served):
    notifier, _, _, _ = served
    first = _connect(notifier, "/notifications")
    named = _connect(notifier, "/notifications/paper-ultimate")
    live = _connect(notifier, "/notifications/live")
    assert first.hello["account"]["id"] == "paper-ultimate"
    assert first.hello["stream"] == named.hello["stream"] != live.hello["stream"]
    assert named.hello["account"] == {
        "id": "paper-ultimate",
        "label": "Ultimate (paper)",
        "broker": "alpaca",
        "paper": True,
        "symbol": "TQQQ",
    }
    assert named.hello["status"]["engine"]["state"] == "running"
    assert live.hello["account"]["paper"] is False
    assert live.hello["status"]["trader"] is None
    for app in (first, named, live):
        app.close()


def test_an_app_hears_its_own_deployments_fills_only(served):
    notifier, _, ultimate, live = served
    ultimate_app = _connect(notifier, "/notifications/paper-ultimate")
    live_app = _connect(notifier, "/notifications/live")
    live.sell()
    notifier.poll()
    assert live_app.notification()["title"] == "Sold 3 TQQQ"
    ultimate.buy()
    notifier.poll()
    heard = ultimate_app.notification()
    assert (heard["kind"], heard["title"]) == ("buy", "Bought 3 TQQQ")
    ultimate_app.send({"type": "test"})
    assert ultimate_app.notification()["kind"] == "test"
    ultimate_app.close()
    live_app.close()


def test_a_path_it_does_not_serve_is_not_found(served):
    from websockets.exceptions import InvalidStatus
    from websockets.sync.client import connect

    notifier, _, _, _ = served
    url = notifier.server.url_for("/notifications/champion")
    with pytest.raises(InvalidStatus) as refused, connect(url, proxy=None):
        pass
    assert refused.value.response.status_code == 404
