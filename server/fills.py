"""A run's executions, stored columnar and queried a page at a time.

WHY THIS EXISTS. A report used to carry every fill of its top
configuration inline. On a busy 3x-fund sweep that is ~850k fills and
~118 MB of JSON -- for a page whose trade log shows 50 rows and whose
chart can only draw markers for the window in view. The report now
carries `fills_count` per fund, and GET /api/backtest/runs/{id}/fills
serves exactly the slice a view asks for, filtered the way the browser
used to filter it.

THE FILTER SEMANTICS ARE A PORT, NOT A REDESIGN. Each rule below mirrors
web/src/lib/filters.ts as it stood (filterExecutions / openLotIds /
buildCycles), because the chart, the trade log and the CSV all used to
agree with one another by running that code on the same array:

  - the end of a date range covers the WHOLE day it names;
  - "open" ("stuck") is decided over ALL of the fund's fills, not the
    filtered ones -- a lot is open when it has a buy and no sell anywhere;
  - a fill with no RSI (inside the indicator warmup) is excluded as soon
    as either RSI bound is set -- unknown is not in range;
  - cycles are built from the FILTERED fills: the first buy of a lot
    opens it, later buys are ignored, sells with no buy are ignored, and
    `realized` sums the sells' pnl (None when no sell carries one).

STORAGE. Columns are numpy arrays saved with np.savez_compressed: lot
strings are dictionary-encoded, timestamps are epoch seconds (UTC), and
absent rsi/pnl are NaN. Queries are vectorised -- an 850k-fill fund
filters in milliseconds -- and a page is converted back to the wire
`Fill` shape only for the rows it returns.
"""

from __future__ import annotations

import csv
import io
import math
from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np

SIDES = ("BUY", "SELL")
MAX_LIMIT = 5000
CSV_HEADER = [
    "timestamp",
    "type",
    "lot_id",
    "ticker",
    "price",
    "shares",
    "rsi_at_entry",
    "profit_realized",
    "sell_reason",
]


def _epoch(ts: str) -> int:
    parsed = datetime.fromisoformat(ts)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return int(parsed.timestamp())


def _iso(epoch: int) -> str:
    return datetime.fromtimestamp(int(epoch), tz=UTC).isoformat()


def _start_bound(start: str) -> int:
    """`ts < start` excluded the fill: a bare date means its midnight."""
    if len(start) == 10:
        return int(
            datetime.combine(date.fromisoformat(start), datetime.min.time(), UTC).timestamp()
        )
    return _epoch(start)


def _end_bound(end: str) -> int:
    """Exclusive epoch bound: the whole of the day `end` names is kept,
    whether it arrives as a picker date or a full timestamp."""
    day = date.fromisoformat(end[:10]) + timedelta(days=1)
    return int(datetime.combine(day, datetime.min.time(), UTC).timestamp())


class FundFills:
    """One fund's fills as columns, in the order the engine recorded them."""

    def __init__(self, columns: dict[str, np.ndarray]):
        self.lots: np.ndarray = columns["lots"]
        self.lot_id: np.ndarray = columns["lot_id"]
        self.side: np.ndarray = columns["side"]
        self.bar: np.ndarray = columns["bar"]
        self.px: np.ndarray = columns["px"]
        self.qty: np.ndarray = columns["qty"]
        self.ts: np.ndarray = columns["ts"]
        self.rsi: np.ndarray = columns["rsi"]
        self.pnl: np.ndarray = columns["pnl"]
        self.why_values: np.ndarray = columns["why_values"]
        self.why: np.ndarray = columns["why"]
        n_lots = len(self.lots)
        has_buy = np.bincount(self.lot_id[self.side == 0], minlength=n_lots) > 0
        has_sell = np.bincount(self.lot_id[self.side == 1], minlength=n_lots) > 0
        # Decided over every fill of the fund, never the filtered subset.
        self.open_lot: np.ndarray = has_buy & ~has_sell

    def __len__(self) -> int:
        return len(self.side)

    # -- construction / persistence ------------------------------------

    @classmethod
    def from_fills(cls, fills: list[dict[str, Any]]) -> FundFills:
        lot_index: dict[str, int] = {}
        why_index: dict[str, int] = {}
        n = len(fills)
        lot_id = np.empty(n, dtype=np.int32)
        side = np.empty(n, dtype=np.int8)
        bar = np.empty(n, dtype=np.int64)
        px = np.empty(n, dtype=np.float64)
        qty = np.empty(n, dtype=np.float64)
        ts = np.empty(n, dtype=np.int64)
        rsi = np.full(n, np.nan, dtype=np.float64)
        pnl = np.full(n, np.nan, dtype=np.float64)
        why = np.full(n, -1, dtype=np.int16)
        for k, fill in enumerate(fills):
            lot_id[k] = lot_index.setdefault(str(fill["lot"]), len(lot_index))
            side[k] = 0 if str(fill["side"]).upper() == "BUY" else 1
            bar[k] = int(fill.get("i", 0))
            px[k] = float(fill["px"])
            qty[k] = float(fill["qty"])
            ts[k] = _epoch(fill["ts"])
            if fill.get("rsi") is not None:
                rsi[k] = float(fill["rsi"])
            if fill.get("pnl") is not None:
                pnl[k] = float(fill["pnl"])
            if fill.get("why"):
                why[k] = why_index.setdefault(str(fill["why"]), len(why_index))
        return cls(
            {
                "lots": np.array(list(lot_index), dtype=str),
                "lot_id": lot_id,
                "side": side,
                "bar": bar,
                "px": px,
                "qty": qty,
                "ts": ts,
                "rsi": rsi,
                "pnl": pnl,
                "why_values": np.array(list(why_index), dtype=str),
                "why": why,
            }
        )

    def save(self, path: Path) -> None:
        staging = path.with_name(path.name + ".tmp")
        with staging.open("wb") as handle:
            np.savez_compressed(
                handle,
                lots=self.lots,
                lot_id=self.lot_id,
                side=self.side,
                bar=self.bar,
                px=self.px,
                qty=self.qty,
                ts=self.ts,
                rsi=self.rsi,
                pnl=self.pnl,
                why_values=self.why_values,
                why=self.why,
            )
        staging.replace(path)

    @classmethod
    def load(cls, path: Path) -> FundFills:
        with np.load(path, allow_pickle=False) as data:
            return cls({key: data[key] for key in data.files})

    # -- wire shape ----------------------------------------------------

    def fill(self, k: int) -> dict[str, Any]:
        out: dict[str, Any] = {
            "lot": str(self.lots[self.lot_id[k]]),
            "side": SIDES[int(self.side[k])],
            "i": int(self.bar[k]),
            "px": float(self.px[k]),
            "qty": float(self.qty[k]),
            "ts": _iso(self.ts[k]),
        }
        if not math.isnan(self.rsi[k]):
            out["rsi"] = float(self.rsi[k])
        if not math.isnan(self.pnl[k]):
            out["pnl"] = float(self.pnl[k])
        if self.why[k] >= 0:
            out["why"] = str(self.why_values[self.why[k]])
        return out

    # -- querying ------------------------------------------------------

    def select(
        self,
        *,
        start: str | None = None,
        end: str | None = None,
        status: str = "all",
        rsi_min: float | None = None,
        rsi_max: float | None = None,
    ) -> np.ndarray:
        """Positions of the fills passing every filter, in recorded order."""
        mask = np.ones(len(self), dtype=bool)
        if start:
            mask &= self.ts >= _start_bound(start)
        if end:
            mask &= self.ts < _end_bound(end)
        if status == "stuck":
            mask &= self.open_lot[self.lot_id]
        elif status == "closed":
            mask &= ~self.open_lot[self.lot_id]
        if rsi_min is not None or rsi_max is not None:
            mask &= ~np.isnan(self.rsi)
            if rsi_min is not None:
                mask &= self.rsi >= rsi_min
            if rsi_max is not None:
                mask &= self.rsi <= rsi_max
        return np.flatnonzero(mask)

    def cycles(self, selected: np.ndarray) -> dict[str, np.ndarray]:
        """buildCycles over `selected`: one cycle per lot whose first buy is
        selected, ordered by that buy; sells joined from the same subset."""
        n_lots = len(self.lots)
        sides = self.side[selected]
        buys = selected[sides == 0]
        sells = selected[sides == 1]
        lots_of_buys = self.lot_id[buys]
        _, first = np.unique(lots_of_buys, return_index=True)
        buy_pos = np.sort(buys[first])
        cycle_lot = self.lot_id[buy_pos]

        sell_lots = self.lot_id[sells]
        sell_count = np.bincount(sell_lots, minlength=n_lots)
        valid = ~np.isnan(self.pnl[sells])
        realized_sum = np.bincount(
            sell_lots[valid], weights=self.pnl[sells][valid], minlength=n_lots
        )
        realized_has = np.bincount(sell_lots[valid], minlength=n_lots) > 0

        # Sells grouped by lot, recorded order kept within a lot.
        order = np.argsort(sell_lots, kind="stable")
        return {
            "buy": buy_pos,
            "lot": cycle_lot,
            "closed": sell_count[cycle_lot] > 0,
            "realized": realized_sum[cycle_lot],
            "realized_has": realized_has[cycle_lot],
            "sells_sorted": sells[order],
            "sells_sorted_lots": sell_lots[order],
        }

    def query(
        self,
        *,
        start: str | None = None,
        end: str | None = None,
        status: str = "all",
        rsi_min: float | None = None,
        rsi_max: float | None = None,
        view: str = "fills",
        cycles: str = "all",
        offset: int = 0,
        limit: int = 50,
    ) -> dict[str, Any]:
        limit = max(0, min(int(limit), MAX_LIMIT))
        offset = max(0, int(offset))
        selected = self.select(
            start=start, end=end, status=status, rsi_min=rsi_min, rsi_max=rsi_max
        )
        built = self.cycles(selected)
        closed = built["closed"]
        realized = float(np.sum(np.where(built["realized_has"] & closed, built["realized"], 0.0)))
        summary = {
            "fills": len(selected),
            "fills_unfiltered": len(self),
            "closed": int(np.count_nonzero(closed)),
            "open": int(np.count_nonzero(~closed)),
            "realized": realized,
        }

        if view == "cycles":
            keep = np.ones(len(built["buy"]), dtype=bool)
            if cycles == "closed":
                keep = closed
            elif cycles == "open":
                keep = ~closed
            chosen = np.flatnonzero(keep)
            page = chosen[offset : offset + limit]
            rows = [self._cycle_row(built, int(c)) for c in page]
            total = len(chosen)
        else:
            page = selected[offset : offset + limit]
            rows = [self.fill(int(k)) for k in page]
            total = len(selected)
        return {"total": total, "offset": offset, "summary": summary, "rows": rows}

    def _cycle_row(self, built: dict[str, np.ndarray], c: int) -> dict[str, Any]:
        lot = built["lot"][c]
        lo = np.searchsorted(built["sells_sorted_lots"], lot, side="left")
        hi = np.searchsorted(built["sells_sorted_lots"], lot, side="right")
        sells = [self.fill(int(k)) for k in built["sells_sorted"][lo:hi]]
        return {
            "lot": str(self.lots[lot]),
            "buy": self.fill(int(built["buy"][c])),
            "sells": sells,
            "realized": float(built["realized"][c]) if built["realized_has"][c] else None,
            "open": not bool(built["closed"][c]),
        }

    def csv_lines(self, ticker: str, selected: np.ndarray, chunk: int = 5000) -> Iterator[str]:
        """The browser's old CSV export, server-side and streamed."""
        buffer = io.StringIO()
        writer = csv.writer(buffer, lineterminator="\n")
        writer.writerow(CSV_HEADER)
        for start in range(0, len(selected), chunk):
            for k in selected[start : start + chunk]:
                fill = self.fill(int(k))
                writer.writerow(
                    [
                        fill["ts"],
                        fill["side"],
                        fill["lot"],
                        ticker,
                        fill["px"],
                        fill["qty"],
                        fill.get("rsi", ""),
                        fill.get("pnl", ""),
                        fill.get("why", ""),
                    ]
                )
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate()
        if buffer.tell():
            yield buffer.getvalue()


def strip_report(report: dict[str, Any] | None) -> dict[str, Any] | None:
    """A report as the API serves it: each fund's fills replaced by
    `fills_count`. A shallow copy -- the caller's report is untouched."""
    if not isinstance(report, dict) or not isinstance(report.get("funds"), dict):
        return report
    funds = {}
    for ticker, fund in report["funds"].items():
        if isinstance(fund, dict) and "fills" in fund:
            slim = {key: value for key, value in fund.items() if key != "fills"}
            slim["fills_count"] = len(fund.get("fills") or [])
            funds[ticker] = slim
        else:
            funds[ticker] = fund
    return {**report, "funds": funds}


__all__ = ["CSV_HEADER", "MAX_LIMIT", "FundFills", "strip_report"]
