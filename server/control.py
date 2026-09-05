"""The one write this application performs: the halt.

--------------------------------------------------------------------
WHY THIS IS ITS OWN MODULE

server/live.py claims, in its docstring and in an AST test, that it
holds no writable connection and reaches no code that could change
anything. Putting the halt in there would make that claim false, and a
safety claim that is only mostly true is worse than none -- a reader
would stop checking.

So the write lives here, alone, and tests/unit/test_server_capability.py
asserts that this module reaches CircuitBreaker and NOTHING ELSE: no
broker, no session, no order type, no sell path.

--------------------------------------------------------------------
WHY HALT AND NOT LIQUIDATE

A halt is a change of MIND, not of POSITION. CircuitBreaker already
persists it, it already survives a restart, an operator can already
clear it, and the loop already honours it by blocking new buys while
continuing to track the market and exit open lots. Nothing new is
invented here; this endpoint reaches an existing, tested mechanism.

Liquidation is a different kind of thing and is deliberately absent.
src/live_trading_loop.py states it plainly:

    "NO FORCED LIQUIDATION, EVER. There is no code path in this module
    that sells a lot for any reason other than its profit target being
    met and the no-loss guard permitting it. Shutdown does not
    liquidate, a drawdown halt does not liquidate, and a reconciliation
    failure does not liquidate."

There is nothing to call. Building it would mean a forced-sell path that
realises losses -- the single largest change to this system's risk
posture available, and not one to make so a button could exist. The UI
renders it greyed WITH this reason rather than hiding it, because a
control a reader expects and cannot find reads as a bug, while one that
explains itself reads as a decision.

--------------------------------------------------------------------
THE ASYMMETRY WITH READS, STATED

Reads open the store `mode=ro` and are safe by construction. This
endpoint needs a WRITABLE connection, so it is safe by narrowness
instead: it opens the store, constructs a CircuitBreaker over it, calls
one method, closes it. The connection does not outlive the request, and
no other function in this module opens one.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.dashboard_data import load_state
from src.persistence import LedgerStore
from src.risk_manager import CircuitBreaker

router = APIRouter(prefix="/api/live", tags=["control"])


class HaltRequest(BaseModel):
    """A halt, with the reason that will be persisted alongside it."""

    path: str = Field(..., description="Path to the ledger store to halt.")
    reason: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description=(
            "Why. Stored verbatim and shown to the next operator, who may be "
            "the same person three weeks later with no memory of this moment."
        ),
    )


@router.post("/halt")
def halt(request: HaltRequest) -> dict[str, Any]:
    """Block new buys on one deployment. Idempotent.

    Re-halting an already-halted store is not an error and does not
    stack: CircuitBreaker holds one halt with one reason, so the call
    settles on the same state either way. An operator hitting the button
    twice under stress should not get an exception for it.

    Returns the halt state READ BACK through the read-only path rather
    than echoing the request. Two reasons: the caller sees what the
    store actually holds -- including a reason already there from an
    earlier halt -- and the write is verified rather than assumed. An
    endpoint that reports success from its own inputs cannot tell you it
    silently did nothing.
    """
    store = None
    try:
        store = LedgerStore(request.path)
        CircuitBreaker(store=store).halt_for_reconciliation(request.reason)
    except Exception as exc:
        # The path may not exist, may not be a ledger store, or may be
        # locked by the running loop. None of those should reach a
        # browser as a 500 with a stack trace.
        raise HTTPException(
            status_code=400, detail=f"Could not halt {request.path!r}: {exc}"
        ) from exc
    finally:
        if store is not None:
            store.close()

    state = load_state(request.path)
    return {
        "halted": state.halted,
        "halt_reason": state.halt_reason,
        "revision": state.revision,
    }


__all__ = ["HaltRequest", "router"]
