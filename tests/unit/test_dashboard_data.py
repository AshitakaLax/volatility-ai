"""
The dashboard's data layer.

Weighted toward the safety properties. A dashboard is exactly the kind
of thing that grows a "just one quick action" button later, so the
tests that matter are the ones asserting it CANNOT act -- and they are
written so that adding such a button breaks them.

No streamlit import anywhere in this file: the data layer is testable
without the UI framework, which is why it is a separate module.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from src.dashboard_data import (
    DashboardError,
    DeploymentState,
    Lot,
    find_bar_files,
    find_stores,
    load_activity,
    load_bars,
    load_order_journal,
    load_state,
)
from src.ledger import AssetLotLedger
from src.live_trading_loop import _META_CASH, _META_UNSETTLED
from src.persistence import LedgerStore
from src.risk_manager import HALT_REASON_KEY, HALT_STATE_KEY


@pytest.fixture
def store(tmp_path):
    s = LedgerStore(str(tmp_path / "live.db"))
    yield s
    s.close()


def _with_lots(store, n=2):
    ledger = AssetLotLedger()
    for i in range(n):
        lot = ledger.register_buy(f"lot-{i}", "TQQQ", 100.0 - i, 10.0, 0.05)
        store.record_open_lot(lot)
    return ledger


# ======================================================================
# It cannot write. This is the security model.
# ======================================================================


def test_the_connection_is_opened_read_only(store, tmp_path):
    """SQLite itself refuses the write -- not this module declining to
    call one. A dashboard is a second process against a live trading
    deployment's state; the failure to design against is a future
    button, not a bad chart."""
    _with_lots(store)
    path = Path(str(tmp_path / "live.db")).resolve()

    conn = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    try:
        with pytest.raises(sqlite3.OperationalError):
            conn.execute("DELETE FROM ledger_lots")
        with pytest.raises(sqlite3.OperationalError):
            conn.execute("INSERT INTO ledger_meta VALUES ('x', 'y')")
    finally:
        conn.close()


def test_no_broker_or_session_is_reachable_from_the_dashboard():
    """Property 2: there is no code path to an order to reach by
    accident, because nothing that can place one is imported."""
    import ast

    forbidden = (
        "fidelity_placing_broker",
        "fidelity_broker",
        "alpaca_broker",
        "fidelity_session",
        "broker_selection",
    )
    for module in ("src/dashboard_data.py", "dashboard.py"):
        tree = ast.parse(Path(module).read_text(encoding="utf-8"))
        imported = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported += [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                imported.append(node.module or "")
        hits = [m for m in imported if any(f in m for f in forbidden)]
        assert hits == [], f"{module} imports something that can trade: {hits}"


def test_the_dashboard_has_no_control_that_submits_anything():
    """Property 3. Every streamlit control on the page selects what to
    LOOK at; none of them act."""
    source = Path("dashboard.py").read_text(encoding="utf-8")
    for widget in ("st.button", "st.form_submit_button", "st.download_button", "st.form("):
        assert widget not in source, f"{widget} appeared in a read-only view"


def test_a_missing_store_is_an_error_not_a_silently_created_file(tmp_path):
    """uri=True is required for mode=ro to be honoured. Without it
    sqlite3 treats the whole string as a filename and CREATES
    `file:...?mode=ro`, which would render as an empty deployment."""
    missing = tmp_path / "nope.db"
    with pytest.raises(DashboardError, match="No ledger store"):
        load_state(str(missing))
    assert not missing.exists()
    assert list(tmp_path.iterdir()) == [], "nothing was created on disk"


# ======================================================================
# Reading real state
# ======================================================================


def test_an_empty_store_reads_as_empty_rather_than_failing(store, tmp_path):
    """A fresh deployment has no cash meta, no lots and no halt. That is
    a normal state the dashboard renders, not an error."""
    state = load_state(str(tmp_path / "live.db"))
    assert state.lots == []
    assert state.cash is None and state.buying_power is None
    assert state.halted is False
    assert state.open_shares == 0.0


def test_lots_cash_and_the_halt_all_come_back(store, tmp_path):
    _with_lots(store, n=3)
    store.set_meta(_META_CASH, "12345.67")
    store.set_meta(HALT_STATE_KEY, "HALTED")
    store.set_meta(HALT_REASON_KEY, "reconciliation mismatch")

    state = load_state(str(tmp_path / "live.db"))
    assert len(state.lots) == 3
    assert state.cash == pytest.approx(12345.67)
    assert state.halted is True
    assert "reconciliation" in state.halt_reason
    assert state.open_shares == pytest.approx(30.0)


def test_an_active_breaker_is_not_reported_as_halted(store, tmp_path):
    store.set_meta(HALT_STATE_KEY, "ACTIVE")
    assert load_state(str(tmp_path / "live.db")).halted is False


def test_settled_buying_power_is_cash_minus_unsettled(store, tmp_path):
    store.set_meta(_META_CASH, "1000.00")
    store.set_meta(
        _META_UNSETTLED,
        json.dumps({"session": 5, "unsettled": 400.0, "pending": [[6, 400.0]]}),
    )
    state = load_state(str(tmp_path / "live.db"))
    assert state.cash == 1000.0
    assert state.unsettled == 400.0
    assert state.buying_power == pytest.approx(600.0)
    assert state.pending_settlement == [(6, 400.0)]


def test_unreadable_settlement_state_overstates_rather_than_understates(store, tmp_path):
    """Matching the live loop's own recovery: corrupt settlement state
    means treat everything as unsettled. A viewer showing zero would
    UNDERSTATE what is tied up, which is the wrong direction to be wrong
    in when someone is deciding whether they can trade."""
    store.set_meta(_META_CASH, "900.00")
    store.set_meta(_META_UNSETTLED, "{not json")
    state = load_state(str(tmp_path / "live.db"))
    assert state.unsettled == pytest.approx(900.0)
    assert state.buying_power == 0.0


def test_a_file_that_is_not_a_ledger_store_says_so(tmp_path):
    other = tmp_path / "random.db"
    conn = sqlite3.connect(str(other))
    conn.execute("CREATE TABLE unrelated (x INTEGER)")
    conn.commit()
    conn.close()
    with pytest.raises(DashboardError, match="not a ledger store"):
        load_state(str(other))


# ======================================================================
# Derived figures
# ======================================================================


def test_distance_to_target_is_none_without_a_price():
    """None and 0.0 are different claims: 'unknown' versus 'already
    there'. Collapsing them would show every lot as marketable."""
    lot = Lot("a", "TQQQ", 100.0, 10.0, 0.05, 105.0)
    assert lot.distance_to_target(None) is None
    assert lot.distance_to_target(0.0) is None
    assert lot.distance_to_target(100.0) == pytest.approx(0.05)
    assert lot.distance_to_target(105.0) == pytest.approx(0.0)


def test_unsettled_proceeds_still_count_as_equity():
    """They are yours; they just cannot be spent. Excluding them would
    understate the account."""
    state = DeploymentState(
        path="x",
        cash=1000.0,
        unsettled=400.0,
        lots=[Lot("a", "TQQQ", 50.0, 10.0, 0.05, 52.5)],
    )
    assert state.equity(60.0) == pytest.approx(1600.0)
    assert state.buying_power == pytest.approx(600.0)


def test_buying_power_floors_at_zero():
    state = DeploymentState(path="x", cash=100.0, unsettled=900.0)
    assert state.buying_power == 0.0


def test_equity_is_none_when_cash_is_unknown():
    assert DeploymentState(path="x").equity(50.0) is None


# ======================================================================
# Activity and the order journal
# ======================================================================


def test_the_revision_log_comes_back_newest_first(store, tmp_path):
    _with_lots(store, n=3)
    rows = load_activity(str(tmp_path / "live.db"))
    assert len(rows) >= 3
    assert rows[0]["revision"] > rows[-1]["revision"]
    assert set(rows[0]) == {"revision", "operation", "order_id", "detail"}


def test_an_absent_order_journal_is_empty_not_an_error(tmp_path):
    assert load_order_journal(str(tmp_path / "none.jsonl")) == []


def test_a_torn_final_journal_line_is_surfaced_not_hidden(tmp_path):
    """Expected if the process died mid-write. Skipping it silently
    would hide exactly the event the journal exists to record."""
    path = tmp_path / "j.jsonl"
    path.write_text(
        json.dumps({"conf_num": "C1", "symbol": "CWH"}) + '\n{"conf_nu',
        encoding="utf-8",
    )
    entries = load_order_journal(str(path))
    assert entries[0]["conf_num"] == "C1"
    assert entries[1]["conf_num"] == "<unparseable>"


def test_find_stores_skips_virtualenvs(tmp_path):
    (tmp_path / "a.db").write_bytes(b"")
    venv = tmp_path / ".venv" / "lib"
    venv.mkdir(parents=True)
    (venv / "b.db").write_bytes(b"")
    found = find_stores(str(tmp_path))
    assert any(f.endswith("a.db") for f in found)
    assert not any("b.db" in f for f in found)


# ======================================================================
# The rendered app
# ======================================================================
#
# Streamlit's own AppTest actually EXECUTES dashboard.py, so these catch
# what a data-layer test cannot: a widget that raises, a column config
# naming a column that is not there, a metric fed the wrong type. Both
# UI bugs below were found this way and not by reading the code.

streamlit = pytest.importorskip("streamlit", reason="dashboard is an optional extra")
from streamlit.testing.v1 import AppTest  # noqa: E402


@pytest.fixture
def demo_db(tmp_path):
    from src.live_trading_loop import _META_CASH, _META_UNSETTLED

    path = tmp_path / "demo.db"
    s = LedgerStore(str(path))
    ledger = AssetLotLedger()
    for i, price in enumerate([68.40, 65.80, 61.90]):
        s.record_open_lot(ledger.register_buy(f"ord-{i}", "TQQQ", price, 10.0, 0.04))
    s.set_meta(_META_CASH, "48210.55")
    s.set_meta(
        _META_UNSETTLED,
        json.dumps({"session": 1, "unsettled": 3120.40, "pending": [[2, 3120.40]]}),
    )
    s.set_meta(HALT_STATE_KEY, "ACTIVE")
    s.close()
    return str(path)


APP = str(Path("dashboard.py").resolve())


def _app(db, price=None, monkeypatch=None):
    """Run the real app with `db` as the working directory's only store.

    chdir rather than driving the selectbox: the sidebar offers only
    stores found under `.`, so setting it to a path outside the tree
    raises "x not in list" -- which is how the FIRST version of this
    helper failed, and it is a fair description of the app's own
    constraint rather than a test artifact. Running from the store's
    directory is what an operator does anyway.
    """
    monkeypatch.chdir(Path(db).parent)
    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    if price is not None:
        at.number_input[0].set_value(price).run()
    return at


def test_the_app_renders_without_raising(demo_db, monkeypatch):
    at = _app(demo_db, monkeypatch=monkeypatch)
    assert at.exception == [], [str(e.value) for e in at.exception]
    assert at.title[0].value == "Live deployment"


def test_equity_is_blank_without_a_mark_price_not_silently_cash(demo_db, monkeypatch):
    """The bug the render exposed: equity showed a figure IDENTICAL to
    cash, because lots were valued at nothing. A real number that
    excludes every share held, presented as the account's worth."""
    at = _app(demo_db, monkeypatch=monkeypatch)
    equity = next(m for m in at.metric if m.label == "Equity")
    cash = next(m for m in at.metric if m.label == "Total cash")
    assert equity.value == "--"
    assert equity.value != cash.value


def test_equity_appears_once_a_mark_price_is_given(demo_db, monkeypatch):
    at = _app(demo_db, price=69.0, monkeypatch=monkeypatch)
    equity = next(m for m in at.metric if m.label == "Equity")
    assert equity.value.startswith("$")
    assert equity.value != next(m for m in at.metric if m.label == "Total cash").value


def test_lots_past_their_target_are_flagged_not_shown_as_a_negative_gap(demo_db, monkeypatch):
    """A lot already past its target read only as a NEGATIVE distance,
    which scans as a shortfall rather than as 'ready to sell'."""
    at = _app(demo_db, price=69.0, monkeypatch=monkeypatch)
    assert any("at or above their target" in w.value for w in at.warning)


def test_no_lots_are_flagged_when_the_market_is_below_every_target(demo_db, monkeypatch):
    at = _app(demo_db, price=50.0, monkeypatch=monkeypatch)
    assert not any("at or above their target" in w.value for w in at.warning)


def test_a_halt_is_shown_as_an_error_not_a_footnote(tmp_path, monkeypatch):
    from src.live_trading_loop import _META_CASH

    path = tmp_path / "halted.db"
    s = LedgerStore(str(path))
    s.set_meta(_META_CASH, "1000.0")
    s.set_meta(HALT_STATE_KEY, "HALTED")
    s.set_meta(HALT_REASON_KEY, "reconciliation mismatch on TQQQ")
    s.close()

    at = _app(str(path), monkeypatch=monkeypatch)
    assert at.exception == []
    assert any("HALTED" in e.value for e in at.error)
    assert any("reconciliation mismatch" in e.value for e in at.error)
    assert at.success == [], "a halted deployment must not also report ACTIVE"


# ======================================================================
# What the store held and the display was ignoring
# ======================================================================


def test_drawdown_uses_the_persisted_high_water_mark(store, tmp_path):
    """peak_equity was loaded and never displayed, so a deployment
    approaching its halt threshold looked exactly like one that was
    not -- and drawdown is the thing the circuit breaker acts on."""
    from src.live_trading_loop import _META_PEAK_EQUITY

    _with_lots(store, n=2)  # 20 shares at 100 and 99
    store.set_meta(_META_CASH, "1000.00")
    store.set_meta(_META_PEAK_EQUITY, "5000.00")
    state = load_state(str(tmp_path / "live.db"))
    # equity at 100 = 1000 cash + 20 shares * 100 = 3000
    assert state.equity(100.0) == pytest.approx(3000.0)
    assert state.drawdown(100.0) == pytest.approx(0.4)


def test_drawdown_is_none_without_a_peak_or_a_price():
    assert DeploymentState(path="x", cash=1.0).drawdown(10.0) is None
    assert DeploymentState(path="x", cash=1.0, peak_equity=5.0).drawdown(None) == 0.8


def test_drawdown_floors_at_zero_above_the_old_peak():
    """A new high is not a negative drawdown."""
    state = DeploymentState(path="x", cash=200.0, peak_equity=100.0)
    assert state.drawdown(None) == 0.0


def test_unrealized_is_market_value_less_cost_basis():
    state = DeploymentState(path="x", cash=0.0, lots=[Lot("a", "T", 50.0, 10.0, 0.04, 52.0)])
    assert state.unrealized(60.0) == pytest.approx(100.0)
    assert state.unrealized(40.0) == pytest.approx(-100.0)
    assert state.unrealized(None) is None


def test_closed_lots_are_surfaced(store, tmp_path):
    """They are retained in ledger_lots and nothing had ever read them
    back -- the deployment's whole trading history was invisible."""
    ledger = AssetLotLedger()
    lots = [ledger.register_buy(f"c{i}", "TQQQ", 100.0 - i, 10.0, 0.04) for i in range(4)]
    for lot in lots:
        store.record_open_lot(lot)
    for lot in lots[:3]:
        ledger.close_lot(lot)
        store.sync_lot(ledger, lot)

    state = load_state(str(tmp_path / "live.db"))
    assert len(state.lots) == 1
    assert len(state.closed_lots) == 3
    assert {lot.order_id for lot in state.closed_lots} == {"c0", "c1", "c2"}


def test_realized_pnl_is_deliberately_not_offered():
    """It is NOT derivable and must not be faked.

    record_lot_shares writes shares, status and revision -- never the
    execution price -- so the store genuinely cannot say what a closed
    lot sold for. Anything labelled 'realized P&L' here would be the
    target price wearing a different name, which is a floor for
    profit-target exits and meaningless for signal exits.
    """
    assert not hasattr(DeploymentState, "realized_pnl")
    assert not hasattr(DeploymentState, "realized")


# --- the price ladder ---


def _laddered():
    return DeploymentState(
        path="x",
        cash=0.0,
        lots=[
            Lot("a", "T", 100.0, 10.0, 0.04, 104.0),
            Lot("b", "T", 90.0, 10.0, 0.04, 93.6),
            Lot("c", "T", 80.0, 10.0, 0.04, 83.2),
        ],
    )


def test_the_ladder_counts_lots_released_by_each_move():
    rows = _laddered().ladder(95.0, moves=(0.0, 0.10))
    assert rows[0]["lots"] == 2, "at 95 the 83.2 and 93.6 targets are already passed"
    assert rows[1]["lots"] == 3, "a 10% move to 104.5 releases the last one"


def test_ladder_proceeds_use_the_lots_target_not_the_probe_price():
    """A resting limit sell fills AT ITS LIMIT. Valuing the release at
    the probe price would overstate proceeds on every lot whose target
    the move has passed."""
    rows = _laddered().ladder(200.0, moves=(0.0,))
    assert rows[0]["lots"] == 3
    expected = 10.0 * (104.0 + 93.6 + 83.2)
    assert rows[0]["proceeds"] == pytest.approx(expected)
    assert rows[0]["proceeds"] < 3 * 10.0 * 200.0


def test_the_ladder_is_empty_without_a_price():
    assert _laddered().ladder(None) == []
    assert _laddered().ladder(0.0) == []


# --- loop liveness ---


def test_the_write_age_is_reported_as_a_proxy_for_liveness(store, tmp_path):
    """Neither ledger_lots nor revisions carries a timestamp, so there
    is no in-band way to ask whether the loop is still running. The
    file's mtime is the only available answer."""
    _with_lots(store, n=1)
    state = load_state(str(tmp_path / "live.db"))
    assert state.last_write_age is not None
    assert 0.0 <= state.last_write_age < 60.0


def test_a_stale_store_warns_when_no_tick_was_ever_recorded(demo_db, monkeypatch):
    """The file-mtime fallback, which now applies ONLY when the loop has
    recorded no tick of its own.

    This previously asserted that stopped, wedged and market-closed were
    indistinguishable -- true when mtime was the only signal available.
    Persisting the loop's own tick made that obsolete: a tick moves only
    when a price was actually seen, so an old tick during the session
    means stopped, and an old tick outside it means closed. The old
    wording is gone because the limitation is.
    """
    import os
    import time

    stale = time.time() - 3600
    os.utime(demo_db, (stale, stale))
    at = _app(demo_db, monkeypatch=monkeypatch)
    assert at.exception == []
    assert any("no tick recorded" in c.value for c in at.caption)
    assert any("No tick for" in w.value for w in at.warning)


def test_a_fresh_store_does_not_warn_about_staleness(demo_db, monkeypatch):
    at = _app(demo_db, monkeypatch=monkeypatch)
    assert not any("wedged" in w.value for w in at.warning)


def test_the_new_sections_all_render(demo_db, monkeypatch):
    at = _app(demo_db, price=69.0, monkeypatch=monkeypatch)
    assert at.exception == []
    headings = [s.value for s in at.subheader]
    assert "If price moves" in headings
    labels = {m.label for m in at.metric}
    assert {"Peak equity", "Drawdown from peak", "Unrealized on open lots"} <= labels


# ======================================================================
# The loop's own mark, and the chart
# ======================================================================


def _tick(price=69.14, ago_seconds=0.0):
    import datetime as dt

    at = dt.datetime.now(dt.UTC) - dt.timedelta(seconds=ago_seconds)
    return json.dumps({"price": price, "at": at.isoformat(), "symbol": "TQQQ"})


def test_the_loops_own_tick_price_is_read_back(store, tmp_path):
    """The loop knew the price every tick and discarded it, leaving every
    reader with no mark to value the book at."""
    from src.live_trading_loop import _META_LAST_TICK

    store.set_meta(_META_CASH, "1000.0")
    store.set_meta(_META_LAST_TICK, _tick(69.14))
    state = load_state(str(tmp_path / "live.db"))
    assert state.last_price == pytest.approx(69.14)
    assert state.tick_age() is not None and state.tick_age() < 60


def test_tick_age_separates_a_stopped_loop_from_a_closed_market(store, tmp_path):
    """last_write_age moves on ANY write; this moves only when the loop
    actually saw a price. That is the distinction the file-mtime proxy
    could never make."""
    from src.live_trading_loop import _META_LAST_TICK

    store.set_meta(_META_LAST_TICK, _tick(69.14, ago_seconds=3600))
    state = load_state(str(tmp_path / "live.db"))
    assert state.tick_age() > 3500
    assert state.last_write_age < 60, "the file was just written; the TICK is old"


def test_an_unreadable_tick_is_no_mark_rather_than_zero(store, tmp_path):
    """A zero would render every lot as infinitely far from its target
    and equity as cash alone -- a wrong number that looks like data."""
    from src.live_trading_loop import _META_LAST_TICK

    store.set_meta(_META_CASH, "1000.0")
    store.set_meta(_META_LAST_TICK, "{ not json")
    state = load_state(str(tmp_path / "live.db"))
    assert state.last_price is None
    assert state.tick_age() is None


def test_bar_files_are_found_and_tailed(tmp_path):
    """The tail, not the whole file: these are 60 MB and a million rows,
    and a dashboard that takes seconds to redraw stops being looked at."""
    import pandas as pd

    folder = tmp_path / "data"
    folder.mkdir()
    frame = pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-01-01", periods=2000, freq="1min", tz="UTC"),
            "close": range(2000),
        }
    )
    frame.to_csv(folder / "TQQQ_1Min_x.csv", index=False)

    found = find_bar_files("TQQQ", root=str(folder))
    assert len(found) == 1
    bars = load_bars(found[0], limit=780)
    assert len(bars) == 780
    assert bars["close"].iloc[-1] == 1999, "the TAIL, so the newest bars"


def test_a_file_that_is_not_bars_is_refused(tmp_path):
    path = tmp_path / "nope.csv"
    path.write_text("a,b\n1,2\n", encoding="utf-8")
    with pytest.raises(DashboardError, match="not a minute-bar file"):
        load_bars(str(path))


def test_missing_bar_files_are_an_empty_list_not_an_error(tmp_path):
    assert find_bar_files("TQQQ", root=str(tmp_path / "absent")) == []


# --- the rendered page ---


@pytest.fixture
def demo_with_tick(tmp_path):
    import pandas as pd

    from src.live_trading_loop import _META_LAST_TICK, _META_PEAK_EQUITY

    path = tmp_path / "demo.db"
    s = LedgerStore(str(path))
    ledger = AssetLotLedger()
    for i, price in enumerate([68.40, 65.80, 61.90]):
        s.record_open_lot(ledger.register_buy(f"o{i}", "TQQQ", price, 12.0, 0.04))
    s.set_meta(_META_CASH, "48210.55")
    s.set_meta(_META_PEAK_EQUITY, "52000.00")
    s.set_meta(HALT_STATE_KEY, "ACTIVE")
    s.set_meta(_META_LAST_TICK, _tick(69.14))
    s.close()

    folder = tmp_path / "data"
    folder.mkdir()
    pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-08-21", periods=900, freq="1min", tz="UTC"),
            "close": [69.0 + (i % 20) * 0.01 for i in range(900)],
        }
    ).to_csv(folder / "TQQQ_1Min_demo.csv", index=False)
    return str(path)


def test_equity_populates_with_no_manual_price(demo_with_tick, monkeypatch):
    """THE POINT OF PERSISTING THE TICK. The page previously opened with
    equity blank and every lot at an unknown distance until someone
    typed a number the store already had."""
    at = _app(demo_with_tick, monkeypatch=monkeypatch)
    assert at.exception == []
    equity = next(m for m in at.metric if m.label == "Equity")
    assert equity.value != "--"
    assert equity.value != next(m for m in at.metric if m.label == "Total cash").value


def test_the_chart_renders(demo_with_tick, monkeypatch):
    at = _app(demo_with_tick, monkeypatch=monkeypatch)
    assert at.exception == []
    assert "Price and the lot grid" in [s.value for s in at.subheader]


def test_the_chart_says_it_is_history_not_a_quote(demo_with_tick, monkeypatch):
    """A stale close must not read as a live price."""
    at = _app(demo_with_tick, monkeypatch=monkeypatch)
    assert any("not a quote" in c.value for c in at.caption)


def test_the_header_reports_the_tick_not_the_file_write(demo_with_tick, monkeypatch):
    at = _app(demo_with_tick, monkeypatch=monkeypatch)
    assert any("last tick" in c.value for c in at.caption)
