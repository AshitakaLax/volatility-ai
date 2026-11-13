"""tools/track_live.py -- live against backtest, session by session -- over
journal rows built here and control directories in a temp folder. No
network, no warehouse and no sleeping; the shadow backtest runs on the
composition fixture's bars."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from datetime import time as clock_time
from types import SimpleNamespace

import pytest

from engine.core.config import BacktestConfig
from engine.core.trading_calendar import EASTERN
from engine.trading.control_inbox import ControlInbox
from tests.fixtures import composition_baseline as fixture
from tools import track_live as T

DAY = date(2026, 11, 10)  # a Tuesday


def at(text: str, day: date = DAY) -> float:
    hour, minute = map(int, text.split(":"))
    return datetime.combine(day, clock_time(hour, minute), tzinfo=EASTERN).timestamp()


def bar(text: str, close: float = 100.0, day: date = DAY) -> dict:
    return {"t": int(at(text, day)), "o": close, "h": close, "l": close, "c": close, "v": 10.0}


def minutes(start: str, end: str, day: date = DAY) -> list[dict]:
    first, last = int(at(start, day)), int(at(end, day))
    return [
        {"t": t, "o": 100.0, "h": 100.0, "l": 100.0, "c": 100.0, "v": 1.0}
        for t in range(first, last + 1, 60)
    ]


def order(order_id, event, text, *, kind="buy", limit=100.0, price=None, qty=1.0, window="regular"):
    return {
        "t": at(text),
        "order": order_id,
        "event": event,
        "kind": kind,
        "session": window,
        "limit": limit,
        "qty": qty,
        "filled_qty": qty if price else 0.0,
        "avg_price": price,
    }


# -- availability ------------------------------------------------------------------


def test_a_session_watched_from_open_to_close_is_traded():
    found = T.availability(T.regular_bars(minutes("09:30", "15:59"), DAY), DAY)
    assert found == {
        "status": "traded",
        "bars": 390,
        "first": "09:30",
        "last": "15:59",
        "longest_gap_minutes": 1.0,
    }


def test_a_thin_feed_with_minutes_missing_is_still_traded():
    """A fund's feed has minutes with no print: fewer bars is not downtime."""
    thin = [b for i, b in enumerate(minutes("09:30", "15:59")) if i % 7 != 3]
    assert T.availability(T.regular_bars(thin, DAY), DAY)["status"] == "traded"


@pytest.mark.parametrize(
    ("bars", "why"),
    [
        (minutes("10:15", "15:59"), "first bar 45 min after the open"),
        (minutes("09:30", "14:59"), "last bar 60 min before the close"),
        ([*minutes("09:30", "11:00"), *minutes("12:00", "15:59")], "60 min without a bar"),
    ],
)
def test_a_late_start_an_early_stop_or_a_long_gap_is_partial(bars, why):
    found = T.availability(T.regular_bars(bars, DAY), DAY)
    assert found["status"] == "partial" and found["why"] == why


def test_no_regular_bars_is_missed_and_extended_hours_do_not_count():
    assert T.availability(T.regular_bars(minutes("07:00", "09:29"), DAY), DAY)["status"] == "missed"
    assert T.regular_bars([*minutes("16:00", "17:00"), bar("09:30")], DAY) == [bar("09:30")]


def test_a_bar_journaled_many_times_is_one_bar():
    repeated = minutes("09:30", "09:34") * 100
    assert len(T.regular_bars(repeated, DAY)) == 5


def test_a_session_older_than_the_bar_journal_is_unknown_not_missed():
    row = T.track_session(DAY, bars=[], fills=[], orders=[], bars_kept=False)
    assert row["availability"]["status"] == "unknown"
    assert T.track_session(DAY, bars=[], fills=[], orders=[])["availability"]["status"] == "missed"


# -- the bridge --------------------------------------------------------------------


def event(kind: str, text: str, detail: str = "") -> dict:
    return {"kind": kind, "t": at(text), "detail": detail}


def test_time_not_ready_is_counted_inside_the_day_it_trades_with_its_cause():
    events = [
        event("not_ready", "05:00", "Not ready: Fidelity tab: Fidelity signed you out -- sign in"),
        event("ready", "09:30", "Ready to trade."),
        event(
            "not_ready", "12:00", "Not ready: Account check: FidelitySessionExpired: on the page"
        ),
        event("ready", "12:30", "Ready to trade."),
        event("check", "12:31", "Account check passed"),  # not a readiness event
    ]
    found = T.not_ready(events, at("07:00"), at("20:00"))
    assert found["minutes"] == 180.0  # 07:00-09:30, then half an hour
    assert found["share"] == pytest.approx(180 / 780, abs=1e-4)
    assert [r["minutes"] for r in found["reasons"]] == [150.0, 30.0]
    assert found["reasons"][0]["why"].startswith("Fidelity tab: Fidelity signed you out")


def test_a_day_that_ends_not_ready_counts_to_its_end_and_a_silent_journal_says_nothing():
    down = [event("ready", "06:00"), event("not_ready", "19:00", "Not ready: Extension: gone")]
    assert T.not_ready(down, at("07:00"), at("20:00"))["minutes"] == 60.0
    assert T.not_ready([event("ready", "06:00")], at("07:00"), at("20:00"))["minutes"] == 0.0
    assert T.not_ready([], at("07:00"), at("20:00")) is None
    later = [event("not_ready", "21:00", "Not ready: x")]
    assert T.not_ready(later, at("07:00"), at("20:00")) is None


# -- activity and execution --------------------------------------------------------


def test_activity_counts_orders_and_what_was_realised():
    fills = [
        {"t": at("10:00"), "side": "buy", "qty": 2.0, "price": 100.0, "value": 200.0},
        {
            "t": at("11:00"),
            "side": "sell",
            "qty": 1.0,
            "proceeds": 101.0,
            "cost": 100.0,
            "pnl": 1.0,
        },
        {
            "t": at("12:00"),
            "side": "sell",
            "qty": 1.0,
            "proceeds": 98.0,
            "cost": 100.0,
            "pnl": -2.0,
        },
    ]
    orders = [
        order("a", "placed", "10:00"),
        order("a", "filled", "10:01", price=100.0),
        order("b", "placed", "10:05"),
        order("b", "expired", "10:10"),
    ]
    assert T.activity(fills, orders) == {
        "orders_placed": 2,
        "orders_filled": 1,
        "orders_cancelled": 0,
        "orders_expired": 1,
        "buys": 1,
        "buy_value": 200.0,
        "sells": 2,
        "proceeds": 199.0,
        "realized_pnl": -1.0,
        "loss_sales": 1,
    }


def test_slippage_is_against_the_limit_and_positive_is_worse_for_the_trader():
    bars = [bar("09:59", 100.0), bar("10:00", 100.5), bar("10:01", 100.5)]
    orders = [
        order("buy-better", "placed", "10:00", limit=100.0),
        order("buy-better", "filled", "10:01", price=99.9),
        order("sell-worse", "placed", "10:00", kind="sell", limit=100.0),
        order("sell-worse", "filled", "10:02", kind="sell", price=99.8),
        order("never", "placed", "10:00"),
        order("never", "cancelled", "10:05"),
    ]
    done = {row["kind"]: row for row in T.execution(orders, bars, base_bps=0.5, vol_multiplier=0.3)}
    assert done["buy"]["live_bps"] == -10.0  # bought below its limit
    assert done["sell"]["live_bps"] == 20.0  # sold below its limit
    assert done["buy"]["seconds_to_fill"] == 60.0
    # The model: 0.5 bp plus 0.3 x the 10:00 bar's 50 bp move.
    assert done["buy"]["model_bps"] == pytest.approx(0.5 + 0.3 * 50, abs=0.01)
    summary = T.execution_summary(list(done.values()), placed=3)
    assert summary["filled"] == 2 and summary["fill_share"] == pytest.approx(2 / 3, abs=1e-4)
    assert summary["live_bps"] == pytest.approx(5.0, abs=0.1)  # value-weighted
    assert T.execution_summary([], placed=4) == {"filled": 0, "placed": 4, "fill_share": 0.0}
    assert T.execution_summary([], placed=0)["fill_share"] is None


def test_the_model_cost_needs_the_bar_the_order_was_placed_in():
    bars = [bar("10:00", 100.0), bar("10:01", 101.0)]
    assert T.model_bps(bars, at("10:01"), 0.5, 0.3) == pytest.approx(0.5 + 0.3 * 100)
    assert T.model_bps(bars, at("10:00"), 0.5, 0.3) == 0.5  # no close before it: the floor
    assert T.model_bps(bars, at("12:00"), 0.5, 0.3) is None  # the bars do not reach it
    assert T.model_bps([], at("10:00"), 0.5, 0.3) is None


# -- a deployment ------------------------------------------------------------------


class Deployment:
    """What track_live needs of a server.live_registry.Deployment."""

    id, label = "paper-x", "Paper X"

    def __init__(self, root, config, *, bridge=False, override=None, grants=False):
        self._root, self._config, self._bridge = root, config, bridge
        self.state_db = root / "state" / "ledger.db"
        self.state_db.parent.mkdir(parents=True, exist_ok=True)
        if override is not None:
            (self.state_db.parent / "algorithm.json").write_text(json.dumps(override))
        self.caps = SimpleNamespace(algorithm_changes=grants)
        self.config_path = root / "config.yaml"

    def config(self):
        return self._config

    def inbox(self):
        return ControlInbox(self._root / "control")

    def bridge_inbox(self):
        return ControlInbox(self._root / "control" / "bridge") if self._bridge else None


def config(**live) -> BacktestConfig:
    return BacktestConfig.from_dict(
        {
            "strategy": {"strategy_id": "fixed", "strategy_params": {"per_lot_pct": 0.01}},
            "grid": {"steps": [0.01], "profit_targets": [0.02]},
            "backtest": {"symbol": "TQQQ", "initial_cash": 10_000.0},
            "costs": {"model_type": "dynamic_slippage", "base_bps": 0.5, "vol_multiplier": 0.3},
            "live": {
                "enabled": True,
                "paper_trading": True,
                "step": 0.004,
                "profit_target": 0.05,
                **live,
            },
        }
    )


NOW = datetime.combine(date(2026, 11, 12), clock_time(20, 40), tzinfo=EASTERN).astimezone(UTC)


def journaled(tmp_path, **kwargs) -> Deployment:
    """A trader that watched the 10th and the 12th and was down on the 11th."""
    deployment = Deployment(tmp_path, config(), **kwargs)
    inbox = deployment.inbox()
    for day in (date(2026, 11, 10), date(2026, 11, 12)):
        inbox.record_bars(minutes("09:30", "15:59", day), keep_past=True)
    inbox.record_fill({"t": at("10:01"), "side": "buy", "qty": 1.0, "price": 99.9, "value": 99.9})
    inbox.record_order(order("a", "placed", "10:00"))
    inbox.record_order(order("a", "filled", "10:01", price=99.9))
    return deployment


def test_a_day_inside_the_journals_with_nothing_journaled_is_a_missed_session(tmp_path):
    rows = T.track_deployment(journaled(tmp_path), NOW)
    assert [(r["session"], r["availability"]["status"]) for r in rows] == [
        ("2026-11-10", "traded"),
        ("2026-11-11", "missed"),
        ("2026-11-12", "traded"),
    ]
    assert rows[0]["activity"]["buys"] == 1 and rows[0]["execution"]["live_bps"] == -10.0
    assert "bridge_not_ready" not in rows[0]


def test_a_session_still_open_is_not_tracked_yet(tmp_path):
    midday = datetime.combine(date(2026, 11, 12), clock_time(12, 0), tzinfo=EASTERN).astimezone(UTC)
    rows = T.track_deployment(journaled(tmp_path), midday)
    assert [r["session"] for r in rows] == ["2026-11-10", "2026-11-11"]


def test_a_trader_that_has_journaled_nothing_has_no_rows(tmp_path):
    assert T.track_deployment(Deployment(tmp_path, config()), NOW) == []


# -- the algorithm in force --------------------------------------------------------

OVERRIDE = {
    "strategy_id": "hf_local_reference",
    "strategy_params": {"per_lot_pct": 0.002, "lookback_days": 0.02, "bars_per_day": 387},
    "step": 0.002,
    "profit_target": 0.04,
}


def test_the_override_beside_the_ledger_is_in_force_only_where_one_may_apply(tmp_path):
    granted = Deployment(tmp_path / "a", config(), override=OVERRIDE, grants=True)
    assert T.algorithm_in_force(granted) == (OVERRIDE, "override")
    ungranted = Deployment(tmp_path / "b", config(), override=OVERRIDE, grants=False)
    algorithm, source = T.algorithm_in_force(ungranted)
    assert source == "config" and algorithm["strategy_id"] == "fixed"
    assert (algorithm["step"], algorithm["profit_target"]) == (
        0.004,
        0.05,
    )  # live's, not the grid's
    plain = Deployment(tmp_path / "c", config(), grants=True)
    assert T.algorithm_in_force(plain)[1] == "config"


def test_the_shadow_is_the_deployments_own_config_at_the_live_step_and_target(tmp_path):
    base = config()
    shadow = T.shadow_config(base, OVERRIDE)
    assert shadow.strategy.strategy_id == "hf_local_reference"
    assert (list(shadow.grid.steps), list(shadow.grid.profit_targets)) == ([0.002], [0.04])
    assert shadow.costs == base.costs and shadow.backtest.initial_cash == 10_000.0
    assert shadow.live.enabled is False  # a backtest, never a deployment


def test_the_shadow_backtest_gives_each_session_its_trades_and_return():
    frame = fixture.load_ohlcv()
    case = next(c for c in fixture.CASES if c.name == "champion-close")
    algorithm = {
        "strategy_id": "hf_local_reference",
        "strategy_params": case.params(frame),
        "step": 0.002,
        "profit_target": 0.05,
    }
    since = frame.index[0].tz_convert(EASTERN).date()
    found = T.shadow_sessions(
        T.shadow_config(config(), algorithm), since, load=lambda _symbol: frame
    )
    sessions = sorted(found)
    assert sessions[0] == since.isoformat() and len(sessions) > 100
    assert sum(row["buys"] for row in found.values()) > 0
    assert sum(row["sells"] for row in found.values()) > 0
    assert all(
        set(row) == {"buys", "sells", "realized_pnl", "return_pct"} for row in found.values()
    )
    with pytest.raises(ValueError, match="no TQQQ bars"):
        T.shadow_sessions(
            T.shadow_config(config(), algorithm), date(2099, 1, 1), load=lambda _s: frame
        )


# -- the stored record -------------------------------------------------------------


def row(session: str, status: str = "traded", **over) -> dict:
    base = T.track_session(date.fromisoformat(session), bars=[], fills=[], orders=[])
    base["availability"] = {"status": status, "bars": 390}
    base.update(over)
    return base


def test_a_session_out_of_the_journals_is_kept_and_one_still_in_them_is_replaced(tmp_path):
    path = tmp_path / "x" / "sessions.jsonl"
    T.store(
        path, T.merge_rows({}, [row("2026-11-03", algorithm="A"), row("2026-11-04", "partial")])
    )
    stored = T.load_rows(path)
    merged = T.merge_rows(stored, [row("2026-11-04", "traded", algorithm="B"), row("2026-11-05")])
    assert list(merged) == ["2026-11-03", "2026-11-04", "2026-11-05"]
    assert merged["2026-11-04"]["availability"]["status"] == "traded"  # recomputed
    assert merged["2026-11-03"]["algorithm"] == "A"  # kept as first tracked
    assert merged["2026-11-04"]["algorithm"] == "B"  # it had none stored
    again = T.merge_rows(merged, [row("2026-11-04", algorithm="C")])
    assert again["2026-11-04"]["algorithm"] == "B"
    path.write_text(path.read_text() + "not json\n")
    assert list(T.load_rows(path)) == ["2026-11-03", "2026-11-04"]
    assert T.load_rows(tmp_path / "absent.jsonl") == {}


def test_a_run_writes_the_record_and_a_report_and_survives_a_shadow_that_cannot_run(tmp_path):
    deployment = journaled(tmp_path / "d")
    out = tmp_path / "out"

    def no_warehouse(_symbol):
        raise FileNotFoundError("no warehouse here")

    text = T.run_deployment(deployment, out, NOW, load=no_warehouse)
    assert "3: 2 traded, 0 partial, 1 missed" in text
    assert "Shadow backtest:** not run: FileNotFoundError" in text
    assert "1 of 1 orders filled (100%); against the limit -10.0 bp" in text
    assert "| 2026-11-11 | missed (no bars journaled in the regular session) |" in text
    stored = T.load_rows(out / "paper-x" / "sessions.jsonl")
    assert list(stored) == ["2026-11-10", "2026-11-11", "2026-11-12"]
    assert stored["2026-11-10"]["algorithm"] == "fixed step 0.004 target 0.05"
    assert (out / "paper-x" / "report.md").read_text() == text

    class Quiet(Deployment):
        id = "quiet"

    assert T.run_deployment(Quiet(tmp_path / "e", config()), out, NOW) is None


def test_the_report_says_when_the_algorithm_changed_and_totals_the_shadow():
    shadowed = {"buys": 3, "sells": 1, "realized_pnl": 5.0, "return_pct": 1.0}
    rows = [
        row("2026-11-03", algorithm="A", shadow=shadowed),
        row("2026-11-04", "missed", algorithm="B", shadow=shadowed),
    ]
    total = T.summarize(rows)
    assert (total["traded"], total["missed"]) == (1, 1)
    assert total["shadow"]["buys"] == 6 and total["shadow"]["return_pct"] == pytest.approx(2.01)
    text = T.report(
        "x", rows, {"label": "X", "symbol": "TQQQ", "algorithm": "B", "capital": 1000.0}
    )
    assert "The algorithm changed while tracked** (A; then B)" in text
    assert "6 buys, 2 sells, $10.00 realised, +2.01% return" in text


def test_one_deployment_failing_is_a_line_and_the_run_fails(tmp_path):
    class Broken(Deployment):
        id = "broken"

        def inbox(self):
            raise OSError("volume gone")

    lines: list[str] = []
    good = journaled(tmp_path / "good")
    ok = T.run_once(
        [Broken(tmp_path / "bad", config()), good],
        tmp_path / "out",
        NOW,
        shadow=False,
        report_to=lines.append,
    )
    assert not ok and any("broken: FAILED OSError" in line for line in lines)
    assert "## paper-x" in (tmp_path / "out" / "report.md").read_text()


# -- when --------------------------------------------------------------------------


def test_a_failed_run_is_tried_again_within_the_hour():
    from datetime import timedelta

    clock = [datetime(2026, 11, 12, 20, 40, tzinfo=EASTERN)]
    results = iter([False, True])
    slept: list[float] = []

    def sleep(seconds: float) -> None:
        slept.append(seconds)
        clock[0] += timedelta(seconds=seconds)

    T.run_daily(
        clock_time(20, 40),
        lambda: next(results),
        now=lambda: clock[0],
        sleep=sleep,
        report_to=lambda _line: None,
        rounds=2,
    )
    assert slept[0] == T.RETRY_SECONDS
    assert clock[0] == datetime(2026, 11, 13, 20, 40, tzinfo=EASTERN)


def test_the_command_line_takes_what_the_compose_service_passes():
    args = T.build_parser().parse_args(["--all", "--daily", "20:40"])
    assert args.all and args.daily == "20:40" and not args.no_shadow
    assert T.build_parser().parse_args([]).out == T.DEFAULT_OUT
