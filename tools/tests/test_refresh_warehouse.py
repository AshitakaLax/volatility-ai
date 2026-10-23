"""tools/refresh_warehouse.py -- keeping the warehouse's funds current --
against a fake Alpaca that serves adjusted minute bars for any session, and
a real lake in a temp directory. No network; no sleeping."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pandas as pd
import pytest

pytest.importorskip("duckdb")

from engine.core.exceptions import DataValidationError
from engine.core.trading_calendar import EASTERN, sessions_between
from engine.warehouse import lake
from tools import refresh_warehouse as R

# 21:00 Eastern on a Thursday: every session through today is complete.
NOW = datetime(2026, 10, 22, 21, 0, tzinfo=EASTERN)


def _session(day: date, minutes: int = 5, factor: float = 1.0, skip: int = 0) -> pd.DataFrame:
    """A session's bars, priced by its date so each day differs; the first
    `skip` minutes did not print."""
    base = 100.0 + day.toordinal() % 17
    index = (
        pd.date_range(f"{day} 09:30", periods=minutes, freq="1min", tz=EASTERN)
        .tz_convert("UTC")
        .rename("timestamp")
    )[skip:]
    close = [round((base + 0.25 * i) * factor, 6) for i in range(skip, minutes)]
    return pd.DataFrame(
        {
            "open": close,
            "high": [c + 0.1 for c in close],
            "low": [c - 0.1 for c in close],
            "close": close,
            "volume": [500 + i for i in range(skip, minutes)],
        },
        index=index,
    )


class FakeAlpaca:
    """fetch_bars over a fund that trades every session from `first`;
    bars before `ex_date` are scaled by `factor`, as an adjusted feed
    rescales them after a dividend. `lacks` are sessions it has no bars for."""

    def __init__(self, first=date(2026, 8, 3), ex_date=None, factor=1.0, lacks=(), skip=None):
        self.first, self.ex_date, self.factor = first, ex_date, factor
        self.lacks, self.skip = set(lacks), skip or {}
        self.specs = []

    def bars(self, first, last):
        days = [d for d in sessions_between(first - pd.Timedelta(days=1), last) if d >= self.first]
        frames = [
            _session(
                d,
                factor=self.factor if self.ex_date and d < self.ex_date else 1.0,
                skip=self.skip.get(d, 0),
            )
            for d in days
            if d not in self.lacks
        ]
        return pd.concat(frames) if frames else lake.empty_bars()

    def fetch_bars(self, spec):
        self.specs.append(spec)
        first = spec.start.astimezone(EASTERN).date()
        last = spec.end.astimezone(EASTERN).date()
        frame = self.bars(first, last)
        if frame.empty:
            raise DataValidationError("no bars: does not exist, no trading days, or not entitled")
        return frame, 0, 0


FUND = R.Fund("TESTQ", date(2026, 8, 3))


@pytest.fixture
def root(tmp_path):
    return tmp_path / "warehouse"


def _fetch(alpaca, pauses=None):
    return R.AlpacaBars(
        alpaca, pause=1.0, sleep=(pauses.append if pauses is not None else lambda s: None)
    )


def _store(root, frame, ticker="TESTQ"):
    lake.replace_fund(root, ticker, frame)


def _same(a, b):
    a = a.set_axis(a.index.as_unit("ns"))
    b = b.set_axis(b.index.as_unit("ns"))
    pd.testing.assert_frame_equal(a, b, check_freq=False)


def _refresh(root, alpaca, fund=FUND, **kwargs):
    return R.refresh_fund(fund, root=root, fetch=_fetch(alpaca), now=NOW, **kwargs)


# --------------------------------------------------------------------
# The registry and the calendar
# --------------------------------------------------------------------


def test_every_fund_the_ui_knows_is_kept_current():
    from tools.export_ui_data import KNOWN_DATA

    assert set(R.FUNDS) | set(R.DERIVED) == set(KNOWN_DATA)


def test_the_new_index_funds_are_kept_with_extended_hours():
    for ticker in ("SPY", "IWM", "EEM"):
        assert R.FUNDS[ticker].extended_hours
        assert R.FUNDS[ticker].start == date(2016, 1, 1)


@pytest.mark.parametrize(
    ("at", "extended", "expected"),
    [
        ("2026-10-22 16:15", False, date(2026, 10, 21)),  # SIP's delay not yet past
        ("2026-10-22 16:16", False, date(2026, 10, 22)),
        ("2026-10-22 16:16", True, date(2026, 10, 21)),  # after-hours still trading
        ("2026-10-22 20:16", True, date(2026, 10, 22)),
        ("2026-10-24 12:00", False, date(2026, 10, 23)),  # a Saturday
        ("2026-11-26 21:00", False, date(2026, 11, 25)),  # Thanksgiving
    ],
)
def test_a_session_is_complete_once_its_last_bar_is_past_sips_delay(at, extended, expected):
    now = pd.Timestamp(at, tz=EASTERN).to_pydatetime()
    assert R.complete_through(now, extended) == expected


# --------------------------------------------------------------------
# A fund from Alpaca
# --------------------------------------------------------------------


def test_a_fund_the_warehouse_lacks_is_downloaded_from_its_start_a_month_at_a_time(root):
    alpaca, pauses = FakeAlpaca(), []
    outcome = R.refresh_fund(FUND, root=root, fetch=_fetch(alpaca, pauses), now=NOW)

    assert outcome.status == "new"
    _same(lake.read_bars(root, "TESTQ"), alpaca.bars(date(2026, 8, 3), date(2026, 10, 22)))
    assert len(alpaca.specs) == 3  # Aug 3 - Sep 2, Sep 3 - Oct 3, Oct 4 - 22
    assert pauses == [1.0, 1.0]
    spec = alpaca.specs[0]
    assert (spec.feed, spec.adjustment, spec.timeframe) == ("sip", "all", "1Min")
    assert spec.regular_hours_only


def test_new_sessions_are_appended_and_the_last_three_checked(root):
    alpaca = FakeAlpaca()
    _store(root, alpaca.bars(date(2026, 8, 3), date(2026, 10, 16)))

    outcome = _refresh(root, alpaca)

    assert outcome.status == "updated"
    assert outcome.added == (
        date(2026, 10, 19),
        date(2026, 10, 20),
        date(2026, 10, 21),
        date(2026, 10, 22),
    )
    _same(lake.read_bars(root, "TESTQ"), alpaca.bars(date(2026, 8, 3), date(2026, 10, 22)))
    anchor, window = alpaca.specs
    assert anchor.start.astimezone(EASTERN).date() == date(2026, 8, 3)  # the oldest session
    assert window.start.astimezone(EASTERN).date() == date(
        2026, 10, 14
    )  # three stored sessions back


def test_a_fund_with_nothing_new_is_current_and_not_rewritten(root):
    alpaca = FakeAlpaca()
    _store(root, alpaca.bars(date(2026, 8, 3), date(2026, 10, 22)))
    before = sorted((p.name, p.stat().st_mtime_ns) for p in lake.fund_dir(root, "TESTQ").rglob("*"))

    outcome = _refresh(root, alpaca)

    assert outcome.status == "current"
    assert (
        sorted((p.name, p.stat().st_mtime_ns) for p in lake.fund_dir(root, "TESTQ").rglob("*"))
        == before
    )


def test_a_late_volume_correction_is_picked_up(root):
    alpaca = FakeAlpaca()
    stored = alpaca.bars(date(2026, 8, 3), date(2026, 10, 22))
    stored.iloc[-1, stored.columns.get_loc("volume")] += 7
    _store(root, stored)

    outcome = _refresh(root, alpaca)

    assert outcome.status == "updated" and "1 stored bars corrected" in outcome.detail
    _same(lake.read_bars(root, "TESTQ"), alpaca.bars(date(2026, 8, 3), date(2026, 10, 22)))


def test_a_dividend_since_the_bars_were_stored_downloads_the_whole_history_again(root):
    """Appending to bars adjusted before the dividend would leave a fake
    drop where they meet the new ones."""
    _store(root, FakeAlpaca().bars(date(2026, 8, 3), date(2026, 10, 16)))
    alpaca = FakeAlpaca(ex_date=date(2026, 10, 19), factor=0.99)

    outcome = _refresh(root, alpaca)

    assert outcome.status == "redownloaded"
    assert "x0.9900" in outcome.detail and "2026-08-03..2026-10-16 x0.9900" in outcome.detail
    _same(lake.read_bars(root, "TESTQ"), alpaca.bars(date(2026, 8, 3), date(2026, 10, 22)))
    assert outcome.added[-1] == date(2026, 10, 22)


def test_a_redownload_missing_a_stored_session_keeps_the_stored_bars(root):
    stored = FakeAlpaca().bars(date(2026, 8, 3), date(2026, 10, 16))
    _store(root, stored)
    alpaca = FakeAlpaca(ex_date=date(2026, 10, 19), factor=0.99, lacks={date(2026, 9, 9)})

    with pytest.raises(R.RefreshError, match="lacks 1 of the"):
        _refresh(root, alpaca)
    _same(lake.read_bars(root, "TESTQ"), stored)


def test_a_recent_session_the_fund_is_missing_is_fetched_again(root):
    alpaca = FakeAlpaca()
    stored = alpaca.bars(date(2026, 8, 3), date(2026, 10, 22))
    hole = lake.sessions_of(stored.index) == pd.Timestamp("2026-10-07")
    _store(root, stored[~hole])

    outcome = _refresh(root, alpaca)

    assert outcome.added == (date(2026, 10, 7),)
    _same(lake.read_bars(root, "TESTQ"), stored)


def test_a_dry_run_writes_nothing(root):
    alpaca = FakeAlpaca()
    stored = alpaca.bars(date(2026, 8, 3), date(2026, 10, 16))
    _store(root, stored)

    outcome = _refresh(root, alpaca, dry_run=True)

    assert outcome.status == "updated" and outcome.line(dry_run=True).split()[1:3] == [
        "would",
        "be",
    ]
    _same(lake.read_bars(root, "TESTQ"), stored)


def test_an_extended_hours_fund_asks_for_the_whole_day(root):
    alpaca = FakeAlpaca()
    fund = R.Fund("TESTQ", date(2026, 10, 19), extended_hours=True)
    R.refresh_fund(fund, root=root, fetch=_fetch(alpaca), now=NOW)

    (spec,) = alpaca.specs
    assert not spec.regular_hours_only
    assert spec.end.astimezone(EASTERN).hour == 20


def test_a_uniform_fund_fills_every_minute_and_a_late_open_carries_the_previous_close(root):
    """RSP is kept with all 390 regular-hours minutes. Its stored history
    was resampled whole, so a session that opened late carries the close
    before it -- and an update must do the same, not back-fill."""
    fund = R.Fund("TESTQ", date(2026, 8, 3), uniform=True)
    late = date(2026, 10, 20)
    alpaca = FakeAlpaca(skip={late: 2})
    _store(root, R.uniform(alpaca.bars(date(2026, 8, 3), date(2026, 10, 16))))

    R.refresh_fund(fund, root=root, fetch=_fetch(alpaca), now=NOW)

    stored = lake.read_bars(root, "TESTQ")
    assert set(lake.session_counts(root, "TESTQ")) == {390}
    _same(stored, R.uniform(alpaca.bars(date(2026, 8, 3), date(2026, 10, 22))))
    day = stored[lake.sessions_of(stored.index) == pd.Timestamp(late)]
    previous_close = stored[lake.sessions_of(stored.index) == pd.Timestamp("2026-10-19")][
        "close"
    ].iloc[-1]
    assert list(day["close"].iloc[:2]) == [previous_close, previous_close]
    assert list(day["volume"].iloc[:2]) == [0, 0]


# --------------------------------------------------------------------
# URSP_SIM
# --------------------------------------------------------------------


def _daily(days, factor=1.0):
    """URSP's daily bars as simulate_ursp.fetch_yahoo_daily returns them."""
    rows = []
    for day in days:
        base = 30.0 + day.toordinal() % 11
        rows.append(
            {
                "open": base * factor,
                "high": (base + 1) * factor,
                "low": (base - 1) * factor,
                "close": (base + 0.5) * factor,
                "volume": 1000.0,
                "adjclose": (base + 0.5) * factor,
            }
        )
    return pd.DataFrame(rows, index=pd.DatetimeIndex([pd.Timestamp(d) for d in days], name="date"))


def _ursp_world(root, rsp_through=date(2026, 10, 21)):
    from tools import simulate_ursp as S

    rsp = R.uniform(FakeAlpaca().bars(date(2026, 8, 3), rsp_through))
    _store(root, rsp, "RSP")
    days = sessions_between(date(2026, 9, 30), date(2026, 10, 22))
    stored_days = [d for d in days if d <= date(2026, 10, 16)]
    library = S.rsp_minute_library(rsp)
    real = S.adjusted(_daily(stored_days), clean=False)
    _store(root, S.minute_bars(real, library), "URSP_SIM")
    return days


def test_ursp_sim_gains_the_sessions_rsp_holds_drawn_on_rsps_minutes(root):
    from tools import simulate_ursp as S

    days = _ursp_world(root, rsp_through=date(2026, 10, 21))
    outcome = R.refresh_ursp_sim(root=root, now=NOW, yahoo=lambda symbol: _daily(days), rates=None)

    # The 22nd waits for RSP's own bars of it.
    assert outcome.added == (date(2026, 10, 19), date(2026, 10, 20), date(2026, 10, 21))
    stored = lake.read_bars(root, "URSP_SIM")
    daily = stored.groupby(lake.sessions_of(stored.index)).agg(
        open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last")
    )
    expected = S.adjusted(_daily(days), clean=False).loc[
        daily.index, ["open", "high", "low", "close"]
    ]
    pd.testing.assert_frame_equal(
        daily, expected, check_names=False, check_freq=False, check_index_type=False
    )


def test_ursp_sim_is_rebuilt_when_ursps_adjusted_prices_moved(root, monkeypatch):
    days = _ursp_world(root)
    calls = []
    monkeypatch.setattr(
        R,
        "rebuild_ursp_sim",
        lambda **kwargs: calls.append(kwargs["reason"]) or R.Outcome("URSP_SIM", "redownloaded"),
    )

    R.refresh_ursp_sim(
        root=root, now=NOW, yahoo=lambda symbol: _daily(days, factor=0.98), rates=None
    )

    assert calls == ["URSP's adjusted daily bars moved (a dividend?)"]


# --------------------------------------------------------------------
# A run, and the daily schedule
# --------------------------------------------------------------------


def test_one_funds_failure_does_not_stop_the_others(root, monkeypatch):
    monkeypatch.setattr(R, "FUNDS", {"TESTQ": FUND, "BADQ": R.Fund("BADQ", date(2026, 8, 3))})

    class Broken(FakeAlpaca):
        def fetch_bars(self, spec):
            if spec.symbol == "BADQ":
                raise ConnectionError("reset by peer")
            return super().fetch_bars(spec)

    lines = []
    outcomes = R.refresh_all(
        ["BADQ", "TESTQ"],
        root=root,
        fetch=_fetch(Broken()),
        now=NOW,
        yahoo=object(),
        rates=object(),
        report=lines.append,
    )

    # In the registry's order, whatever order they were asked for in.
    assert [(o.ticker, o.status) for o in outcomes] == [("TESTQ", "new"), ("BADQ", "failed")]
    assert "ConnectionError: reset by peer" in lines[1]


def test_a_second_run_while_one_holds_the_lake_is_refused(root):
    pytest.importorskip("fcntl")
    with lake.refresh_lock(root), pytest.raises(lake.RefreshBusy):
        R.refresh_all(
            ["TESTQ"],
            root=root,
            fetch=_fetch(FakeAlpaca()),
            now=NOW,
            yahoo=object(),
            rates=object(),
        )


def test_the_next_run_is_the_next_time_of_day_in_eastern():
    at = datetime.strptime("20:30", "%H:%M").time()
    assert R.next_run(datetime(2026, 10, 22, 20, 29, tzinfo=EASTERN), at) == datetime(
        2026, 10, 22, 20, 30, tzinfo=EASTERN
    )
    assert R.next_run(datetime(2026, 10, 22, 20, 30, tzinfo=EASTERN), at) == datetime(
        2026, 10, 23, 20, 30, tzinfo=EASTERN
    )
    # 23:00 on the last evening of daylight saving: still 20:30 on the wall
    # clock the next day, which is 01:30 UTC rather than 00:30.
    after = R.next_run(datetime(2026, 11, 1, 3, 0, tzinfo=UTC), at)
    assert after == datetime(2026, 11, 1, 20, 30, tzinfo=EASTERN)
    assert after.astimezone(UTC).hour == 1


def test_daily_runs_now_then_at_the_hour_and_retries_a_failure_within_the_hour():
    clock = [datetime(2026, 10, 22, 10, 0, tzinfo=EASTERN)]
    results = iter([False, True])
    slept = []

    class Done(Exception):
        pass

    def sleep(seconds):
        slept.append(seconds)
        clock[0] = clock[0] + pd.Timedelta(seconds=seconds)
        if len(slept) == 2:
            raise Done

    with pytest.raises(Done):
        R.run_daily(
            datetime.strptime("20:30", "%H:%M").time(),
            lambda: next(results),
            now=lambda: clock[0],
            sleep=sleep,
            report=lambda line: None,
        )

    assert slept == [3600.0, 9.5 * 3600]  # failed at 10:00, retried 11:00, then 20:30


def test_unknown_funds_are_refused_before_anything_runs(capsys):
    with pytest.raises(SystemExit):
        R.main(["--fund", "NOPE"])
    assert "not a tracked fund: NOPE" in capsys.readouterr().err


def test_a_new_warehouse_gets_the_view_backtests_read_through(root, monkeypatch):
    from engine.warehouse import bars

    monkeypatch.setenv("VAI_WAREHOUSE_DIR", str(root))
    monkeypatch.setattr(R, "FUNDS", {"TESTQ": FUND})
    R.refresh_all(
        ["TESTQ"],
        root=root,
        fetch=_fetch(FakeAlpaca()),
        now=NOW,
        yahoo=object(),
        rates=object(),
        report=lambda line: None,
    )

    _same(bars.load_frame("TESTQ"), FakeAlpaca().bars(date(2026, 8, 3), date(2026, 10, 22)))
