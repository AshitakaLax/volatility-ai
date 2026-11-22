"""
The forecast database's HTTP face (research/risk_overlay/forecasts.py): the
one server module that writes it, and the only thing it writes.

  POST /api/live/risk-forecasts   {report, operator?}: store a pasted report.
                                  The Live page's Check sends it before it
                                  previews the report against each
                                  deployment, so every report checked is
                                  kept, applied or not. 422 naming the audit's
                                  problems when it does not pass (it is not
                                  stored).
                                  Stored once by its SHA-256; each POST adds
                                  a receipt.
  GET  /api/live/risk-forecasts   ?symbol=&sessions=: the last sessions with
                                  a report, oldest first -- each session's
                                  newest forecast, and its actual
                                  close-to-close return and score once the
                                  tracking service has recorded them after
                                  the close (tools/score_risk_reports.py).
                                  Without a symbol: the one most recently
                                  received.

It reaches no ledger, no trader's inbox and no broker: a report stored here
changes nothing any deployment trades -- sending one to a trader is still
live_control.py's apply_risk_report. No route takes a path.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from research.risk_overlay.forecasts import ForecastRefused, ForecastStore
from server.live_control import same_origin

router = APIRouter(prefix="/api/live/risk-forecasts", tags=["forecasts"])


class ForecastRequest(BaseModel):
    """A pasted report, to keep."""

    report: dict[str, Any]
    operator: str | None = None


def _store() -> ForecastStore:
    # Resolved per request: VAI_FORECAST_DB / VAI_WAREHOUSE_DIR are read
    # when it is opened, so a test's monkeypatch holds.
    return ForecastStore()


@router.post("", status_code=201, dependencies=[Depends(same_origin)])
def record_forecast(body: ForecastRequest) -> dict[str, Any]:
    """Keep the report (module docstring); what it says is the same row
    GET serves for its session, beside whether it was new."""
    operator = (body.operator or "").strip()[:80] or None
    store = _store()
    try:
        stored = store.record(body.report, via="check", operator=operator)
    except ForecastRefused as exc:
        # A string, which the page shows as it is; the findings themselves
        # are the preview's to list.
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {**stored, "receipts": len(store.receipts(stored["sha256"]))}


@router.get("")
def forecasts(
    symbol: str | None = Query(None, max_length=12, pattern=r"^[A-Za-z0-9._-]+$"),
    sessions: int = Query(20, ge=1, le=250),
) -> dict[str, Any]:
    store = _store()
    symbols = store.symbols()
    chosen = symbol.upper() if symbol else (symbols[0] if symbols else None)
    return {
        "symbol": chosen,
        "symbols": symbols,
        "sessions": store.sessions(chosen, sessions) if chosen else [],
    }
