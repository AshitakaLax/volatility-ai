"""
The forecast database's HTTP face (research/risk_overlay/forecasts.py): the
one server module that writes it, and the only thing it writes.

  POST /api/live/risk-forecasts   {report, operator?, inputs?}: store a
                                  pasted report. The Live page's Check sends
                                  it before it previews the report against
                                  each deployment, so every report checked
                                  is kept, applied or not; the Forecast tab's
                                  Keep and the forecast service send what the
                                  generator read beside it (`inputs`:
                                  snapshot, diagnostics, sources). 422 naming
                                  the audit's problems when it does not pass,
                                  or saying why the inputs are not its own
                                  (neither is stored).
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
  GET  .../risk-forecasts/reports ?symbol=&limit=: every report, newest
                                  first -- a session's evening and morning
                                  reports both -- with who added each, its
                                  outcome, each longer horizon's score once
                                  its last session has closed, and the
                                  session a report sent now is for.
  GET  .../risk-forecasts/report  ?sha256=: one report whole, with every
                                  receipt and the inputs it was made from
                                  (null when none were kept). 404 when it is
                                  not stored.

It reaches no ledger, no trader's inbox and no broker: a report stored here
changes nothing any deployment trades -- sending one to a trader is still
live_control.py's apply_risk_report. No route takes a path.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from engine.core.trading_calendar import upcoming_session
from research.risk_overlay.forecasts import ForecastRefused, ForecastStore, InputsRefused
from server.live_control import same_origin

router = APIRouter(prefix="/api/live/risk-forecasts", tags=["forecasts"])


class ForecastRequest(BaseModel):
    """A pasted report, to keep."""

    report: dict[str, Any]
    operator: str | None = None
    # What the generator read (research/forecast_generator Generated:
    # snapshot, diagnostics, sources); display only.
    inputs: dict[str, Any] | None = None


SYMBOL = Query(None, max_length=12, pattern=r"^[A-Za-z0-9._-]+$")


def _now() -> datetime:
    return datetime.now(UTC)


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
        stored = store.record(body.report, via="check", operator=operator, inputs=body.inputs)
    except (ForecastRefused, InputsRefused) as exc:
        # A string, which the page shows as it is; the findings themselves
        # are the preview's to list.
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {**stored, "receipts": len(store.receipts(stored["sha256"]))}


@router.get("")
def forecasts(
    symbol: str | None = SYMBOL,
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


@router.get("/reports")
def listed(
    symbol: str | None = SYMBOL,
    limit: int = Query(60, ge=1, le=500),
) -> dict[str, Any]:
    """Every report for the symbol (module docstring), newest first."""
    store = _store()
    symbols = store.symbols()
    chosen = symbol.upper() if symbol else (symbols[0] if symbols else None)
    return {
        "symbol": chosen,
        "symbols": symbols,
        "upcoming_session": upcoming_session(_now()).isoformat(),
        "reports": store.reports(chosen, limit) if chosen else [],
    }


@router.get("/report")
def one(sha256: str = Query(..., pattern=r"^[0-9a-f]{64}$")) -> dict[str, Any]:
    """One report whole (module docstring)."""
    found = _store().report(sha256)
    if found is None:
        raise HTTPException(status_code=404, detail=f"No report {sha256[:12]} is kept.")
    return found
