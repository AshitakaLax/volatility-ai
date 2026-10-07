"""
What the browser extension says became of the orders it sent -- its
confirmation, pushed to the engine as each order changes.

The extension keeps a short log of every order it relays for the engine
(fidelity-bridge-chrome-extension/src/lib/order-log.js) and reads each
one's progress off the replies passing through it, with its own
transcription of broker.derive_order_state. Every change comes back as an
"order" event: Fidelity accepted it, it is working, partly filled,
FILLED, cancelled, rejected, refused by the extension, or of unknown
outcome. On every connect the extension also sends its whole log as an
"orders" event, so a report made while the engine was away -- the reply
to an order that arrived after the engine had stopped waiting for it --
is delivered rather than lost.

A report is a second witness, never an instruction. Nothing here places,
cancels or books anything:

  * OrderReports keeps the latest report for each order, logs each change
    of state, and, given a path, appends each change to a JSON-lines file
    so the extension's account outlives the process. After an ambiguous
    submission that file is where to look for what the browser saw.
  * FidelityBroker.get_order_by_client_id checks it against the engine's
    own reading of the same order: agreement on a fill is logged as
    "confirmed by the browser extension", a disagreement as an error.

The extension sends each report BEFORE the response to the request that
produced it, and the server handles one connection's frames in order, so
by the time a request returns, the report it caused is already here.
"""

from __future__ import annotations

import json
import math
import os
import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

#: Every state the extension's order log can hold.
STATES = frozenset(
    {
        "submitted",
        "working",
        "partially_filled",
        "filled",
        "cancel_requested",
        "cancelled",
        "expired",
        "rejected",
        "blocked",
        "unknown",
    }
)
#: Reports kept in memory: far more than the extension's log ever holds.
KEEP = 500
_MAX_TEXT = 500
# The file's (and this module's) field names, to the wire's.
_WIRE_NAMES = {
    "conf_num": "confNum",
    "limit_price": "limitPrice",
    "filled_qty": "filledQty",
    "avg_price": "avgPrice",
    "placed_at": "placedAt",
    "updated_at": "updatedAt",
}


def _text(value: Any, limit: int = _MAX_TEXT) -> str:
    """One line of printable text: reports end up in the log, so nothing
    in one may start a line of its own."""
    if not isinstance(value, str):
        return ""
    cleaned = "".join(ch if ch.isprintable() else " " for ch in value).strip()
    return cleaned[:limit]


def _number(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 0.0
    number = float(value)
    return number if math.isfinite(number) and number >= 0 else 0.0


def _shares(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else f"{value:.4f}".rstrip("0")


@dataclass(frozen=True)
class OrderReport:
    """The extension's account of one order. Field names follow the
    engine; the wire's are camelCase (PROTOCOL.md in the extension)."""

    id: str
    conf_num: str | None
    symbol: str
    side: str
    qty: float
    limit_price: float
    state: str
    filled_qty: float
    avg_price: float
    attempts: int
    placed_at: str
    updated_at: str
    detail: str

    @classmethod
    def parse(cls, data: Any) -> OrderReport | None:
        """A report from the wire, or None when it is not one. The sender
        is authenticated, but a report is still checked field by field:
        it is written to the log and to disk."""
        if not isinstance(data, dict):
            return None
        record_id = _text(data.get("id"), 100)
        state = data.get("state")
        side = data.get("side")
        symbol = _text(data.get("symbol"), 16).upper()
        if not record_id or state not in STATES or side not in ("buy", "sell") or not symbol:
            return None
        conf_num = _text(data.get("confNum"), 40) or None
        attempts = data.get("attempts")
        return cls(
            id=record_id,
            conf_num=conf_num,
            symbol=symbol,
            side=side,
            qty=_number(data.get("qty")),
            limit_price=_number(data.get("limitPrice")),
            state=state,
            filled_qty=_number(data.get("filledQty")),
            avg_price=_number(data.get("avgPrice")),
            attempts=attempts if isinstance(attempts, int) and attempts >= 1 else 1,
            placed_at=_text(data.get("placedAt"), 40),
            updated_at=_text(data.get("updatedAt"), 40),
            detail=_text(data.get("detail")),
        )

    @property
    def summary(self) -> str:
        """As the extension's popup shows it: BUY 3 TQQQ @ $70.10."""
        return f"{self.side.upper()} {_shares(self.qty)} {self.symbol} @ ${self.limit_price:,.2f}"

    def changed_from(self, other: OrderReport) -> bool:
        """Whether this says anything `other` did not. A refusal's attempt
        count does not count: the engine retries every tick."""
        return (self.state, self.filled_qty, self.avg_price, self.conf_num) != (
            other.state,
            other.filled_qty,
            other.avg_price,
            other.conf_num,
        )

    def describe(self) -> str | None:
        """The log line for reaching this state, or None for the routine
        middle of an order's life."""
        order = f"order {self.conf_num}" if self.conf_num else "an order"
        if self.state == "filled":
            return (
                f"the extension confirms {order} FILLED: {self.summary}, "
                f"{_shares(self.filled_qty)} at ${self.avg_price:,.2f}"
            )
        if self.state == "submitted":
            return f"the extension confirms Fidelity accepted {order}: {self.summary}"
        if self.state == "partially_filled":
            return (
                f"the extension reports {order} partly filled: {_shares(self.filled_qty)} of "
                f"{_shares(self.qty)} at ${self.avg_price:,.2f} ({self.summary})"
            )
        if self.state in ("cancelled", "expired"):
            return f"the extension reports {order} {self.state}: {self.summary}"
        if self.state == "rejected":
            return f"the extension reports Fidelity REJECTED {order}: {self.summary}"
        if self.state == "blocked":
            return f"the extension refused {self.summary}: {self.detail or 'no reason given'}"
        if self.state == "unknown":
            return (
                f"the extension could not confirm {self.summary} ({order}): "
                f"{self.detail or 'no reason given'}"
            )
        return None

    def to_dict(self) -> dict:
        return asdict(self)


class OrderReports:
    """The latest report for each order, as the extension last told it.

    Thread-safe: the bridge's connection thread writes, the engine's
    thread reads.
    """

    def __init__(
        self,
        *,
        path: str | Path | None = None,
        log: Callable[[str], None] | None = None,
        keep: int = KEEP,
    ) -> None:
        self._lock = threading.Lock()
        self._latest: OrderedDict[str, OrderReport] = OrderedDict()
        self._path = Path(path) if path is not None else None
        self._log = log or (lambda _message: None)
        self._keep = keep
        self._write_failed = False
        self._log_received = threading.Event()
        if self._path is not None:
            self._load()

    @property
    def path(self) -> Path | None:
        """The JSON-lines file each change is appended to, if any."""
        return self._path

    def note(self, data: Any, *, resent: bool = False) -> OrderReport | None:
        """Take one report. Returns it when it told the engine something
        new; None when it was malformed or nothing had changed."""
        report = OrderReport.parse(data)
        if report is None:
            self._log("[bridge] ignored an order report from the extension that is not one")
            return None
        with self._lock:
            previous = self._latest.pop(report.id, None)
            self._latest[report.id] = report
            while len(self._latest) > self._keep:
                self._latest.popitem(last=False)
        if previous is not None and not report.changed_from(previous):
            return None
        self._append(report)
        message = report.describe()
        if message and (previous is None or previous.state != report.state):
            prefix = "[bridge] (from the extension's log) " if resent else "[bridge] "
            self._log(prefix + message)
        return report

    def note_all(self, data: Any) -> int:
        """The extension's whole log, sent on connecting, newest first.
        Returns how many reports were new to the engine."""
        orders = data.get("orders") if isinstance(data, dict) else None
        if not isinstance(orders, list):
            self._log("[bridge] ignored an order log from the extension that is not one")
            return 0
        # Oldest first, so the newest ends up the most recent here too.
        new = sum(self.note(item, resent=True) is not None for item in reversed(orders))
        self._log_received.set()
        return new

    def wait_for_log(self, timeout: float) -> bool:
        """Wait for the extension's whole order log, which it sends on
        every connect. False if it has not come: an extension too old to
        send one, or one that has not finished connecting."""
        return self._log_received.wait(timeout)

    def for_conf_num(self, conf_num: str) -> OrderReport | None:
        """The latest report naming this confNum, or None."""
        conf_num = str(conf_num)
        with self._lock:
            for report in reversed(self._latest.values()):
                if report.conf_num == conf_num:
                    return report
        return None

    def recent(self, limit: int | None = None) -> list[OrderReport]:
        """Newest first: the order the extension last reported on leads."""
        with self._lock:
            reports = list(reversed(self._latest.values()))
        return reports if limit is None else reports[:limit]

    # -- the file -------------------------------------------------------

    def _load(self) -> None:
        """Seed from the file, so a report the engine already wrote down
        is not written, or logged, again when the extension resends its
        log on the next connect. A damaged line is skipped, not fatal:
        this file is a record, and nothing trades on it."""
        if self._path is None or not self._path.exists():
            return
        skipped = 0
        with open(self._path, encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                except ValueError:
                    entry = None
                # Checked exactly as a report off the wire is.
                report = OrderReport.parse(
                    {_WIRE_NAMES.get(k, k): v for k, v in entry.items()}
                    if isinstance(entry, dict)
                    else None
                )
                if report is None:
                    skipped += 1
                    continue
                self._latest.pop(report.id, None)
                self._latest[report.id] = report
        while len(self._latest) > self._keep:
            self._latest.popitem(last=False)
        if skipped:
            self._log(f"[bridge] skipped {skipped} unreadable line(s) in {self._path}")

    def _append(self, report: OrderReport) -> None:
        """One line per change, flushed and fsynced like the order journal:
        the case this file is for is a process that is about to stop."""
        if self._path is None:
            return
        line = json.dumps({"received": time.time(), **report.to_dict()}, sort_keys=True)
        try:
            with open(self._path, "a", encoding="utf-8") as handle:
                handle.write(line + "\n")
                handle.flush()
                os.fsync(handle.fileno())
        except OSError as exc:
            if not self._write_failed:
                self._log(f"[bridge] could not record order reports in {self._path}: {exc}")
            self._write_failed = True
