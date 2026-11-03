"""fidelity_gateway/bridge/book.py: the trading book the phone app is shown,
read from the trader's ledger and fill journal -- and the host sending it."""

from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from engine.trading.control_inbox import ControlInbox
from fidelity_gateway.bridge.book import BOOK_SECONDS, CLOSED_SHOWN, read_book
from fidelity_gateway.bridge.host import BridgeHost
from fidelity_gateway.bridge.notifications import Notifications
from fidelity_gateway.tests.test_bridge_host import Clock, _fidelity, _make_server

ET = ZoneInfo("America/New_York")
NOW = datetime(2026, 11, 3, 14, 0, tzinfo=ET).timestamp()
YESTERDAY = datetime(2026, 11, 2, 11, 0, tzinfo=ET).timestamp()


@dataclass
class Lot:
    order_id: str
    buy_price: float
    shares: float
    target_sell_price: float


@dataclass
class State:
    lots: list = field(default_factory=list)
    last_price: float | None = None


class Inbox:
    def __init__(self, fills=(), bars=()):
        self._fills, self._bars = list(fills), list(bars)

    def fills(self, sessions=1):
        return list(self._fills)

    def bars(self, sessions=1):
        return list(self._bars)


@pytest.fixture
def ledger(tmp_path):
    path = tmp_path / "ledger.db"
    path.write_bytes(b"")  # read_book reads only a ledger that exists
    return path


def _book(ledger, state, inbox):
    return read_book(ledger, inbox, symbol="RSP", now=NOW, load_state=lambda _p: state)


def test_open_lots_carry_cost_target_and_when_they_were_bought(ledger):
    state = State(
        lots=[Lot("a", 218.0, 1.0, 220.18), Lot("b", 219.0, 2.0, 221.19)], last_price=219.5
    )
    inbox = Inbox(
        fills=[
            {"t": NOW - 600, "side": "buy", "lot": "a", "qty": 1.0, "price": 218.0},
            {"t": NOW - 60, "side": "buy", "lot": "b", "qty": 2.0, "price": 219.0},
        ]
    )
    book = _book(ledger, state, inbox)
    assert [lot["id"] for lot in book["open"]] == ["b", "a"]  # newest first
    assert book["open"][0] == {
        "id": "b",
        "qty": 2.0,
        "buyPrice": 219.0,
        "targetPrice": 221.19,
        "boughtAt": datetime.fromtimestamp(NOW - 60, UTC).isoformat(timespec="seconds"),
    }
    assert book["openCost"] == 656.0
    assert book["unrealized"] == pytest.approx(1.5 + 1.0)
    assert book["lastPrice"] == 219.5 and book["symbol"] == "RSP"
    assert book["today"] == {"realized": 0.0, "sales": 0, "buys": 2}


def test_today_counts_only_todays_sales_and_closed_lists_the_last_twenty(ledger):
    sales = [
        {
            "t": NOW - 60 * i,
            "side": "sell",
            "lot": f"s{i}",
            "qty": 1.0,
            "price": 220.0,
            "cost": 218.0,
            "pnl": 1.5,
            "reason": "profit_target",
        }
        for i in range(25)
    ]
    sales.append({**sales[0], "t": YESTERDAY, "lot": "old", "pnl": 9.0})
    book = _book(ledger, State(), Inbox(fills=sales))
    assert len(book["closed"]) == CLOSED_SHOWN
    first = book["closed"][0]
    assert (first["id"], first["buyPrice"], first["sellPrice"], first["pnl"]) == (
        "s0",
        218.0,
        220.0,
        1.5,
    )
    assert book["today"] == {"realized": 37.5, "sales": 25, "buys": 0}


def test_the_last_price_falls_back_to_the_journal_bars(ledger):
    state = State(lots=[Lot("a", 218.0, 1.0, 220.18)])
    book = _book(ledger, state, Inbox(bars=[{"t": NOW, "c": 219.0}]))
    assert book["lastPrice"] == 219.0 and book["unrealized"] == 1.0


def test_nothing_to_read_is_no_book(tmp_path):
    assert read_book(tmp_path / "missing.db", None, symbol="RSP", now=NOW) is None
    assert read_book(None, Inbox(), symbol="RSP", now=NOW) is None


def test_a_ledger_that_cannot_be_read_leaves_the_journal_s_part(ledger):
    def broken(_path):
        raise OSError("locked")

    sale = {
        "t": NOW,
        "side": "sell",
        "lot": "x",
        "qty": 1.0,
        "price": 220.0,
        "cost": 218.0,
        "pnl": 2.0,
    }
    book = read_book(ledger, Inbox(fills=[sale]), symbol="RSP", now=NOW, load_state=broken)
    assert book["open"] == [] and book["today"]["realized"] == 2.0


# -- the host sends it ---------------------------------------------------------


@pytest.fixture
def place():
    directory = Path(tempfile.mkdtemp(prefix="vai-book-", dir="/tmp"))
    yield directory
    shutil.rmtree(directory, ignore_errors=True)


def _host(place, clock, book):
    return BridgeHost(
        make_server=_make_server,
        settings=lambda: (_fidelity(), "RSP"),
        socket_path=place / "bridge.sock",
        inbox=ControlInbox(place / "control" / "bridge", clock=clock),
        deployment="fidelity",
        clock=clock,
        log=lambda _message: None,
        notifications=Notifications(clock=clock),
        book=book,
    )


def test_the_host_puts_the_book_in_the_app_status_and_resends_only_changes(place):
    clock = Clock()
    reads: list[float] = []
    figures = {"realized": 1.0}

    def book(now):
        reads.append(now)
        return {"asOf": str(now), "today": dict(figures)}

    host = _host(place, clock, book)
    host.open_socket()
    try:
        heard: list[dict] = []
        host.notifications.subscribe(
            lambda kind, payload: heard.append(payload) if kind == "status" else None
        )
        host.tick()
        assert host.notifications.status["book"]["today"] == {"realized": 1.0}
        sent = sum(1 for status in heard if "book" in status)

        clock.now += 1
        host.tick()  # not yet time to read again
        assert len(reads) == 1

        clock.now += BOOK_SECONDS
        host.tick()  # read again, but only the time stamp moved: not resent
        assert len(reads) == 2
        assert sum(1 for status in heard if "book" in status) == sent

        figures["realized"] = 3.0
        clock.now += BOOK_SECONDS
        host.tick()
        assert host.notifications.status["book"]["today"] == {"realized": 3.0}
    finally:
        host.close()


def test_a_book_that_fails_to_read_never_stops_the_host(place):
    clock = Clock()

    def book(_now):
        raise RuntimeError("ledger busy")

    host = _host(place, clock, book)
    host.open_socket()
    try:
        host.tick()
        assert "book" not in host.notifications.status
    finally:
        host.close()


def test_a_real_journal_reads_through(tmp_path):
    inbox = ControlInbox(tmp_path, clock=lambda: NOW)
    inbox.record_fill({"t": NOW, "side": "buy", "lot": "a", "qty": 1.0, "price": 218.0})
    book = read_book(None, inbox, symbol="RSP", now=NOW)
    assert book["today"]["buys"] == 1
