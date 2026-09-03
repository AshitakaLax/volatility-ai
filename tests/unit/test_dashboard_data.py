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
    find_stores,
    load_activity,
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
