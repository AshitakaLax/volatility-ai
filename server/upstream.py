"""Forward backtest requests to a host that should run them.

--------------------------------------------------------------------
WHY THIS EXISTS

The deployment is split across two machines, and the split is forced by
where things physically live:

  Raspberry Pi   runs the paper trading loop, and the ledger it writes
                 lives in that host's Docker volume. NOTHING ELSE CAN
                 READ IT, so /api/live/* has to be served there.
  Workstation    has twelve cores and every historical bar file, so
                 /api/backtest/* belongs there -- and running a sweep on
                 the Pi would put it on the same four cores as the loop
                 that is actually trading.

Setting VAI_BACKTEST_UPSTREAM on the Pi forwards the backtest routes to
the workstation. The browser still talks to ONE origin, so there is no
CORS, no second base URL compiled into the bundle, and no way for the
two to disagree about which host to ask.

--------------------------------------------------------------------
WHY A PROXY RATHER THAN A SECOND BASE URL IN THE FRONTEND

A frontend that knew two hosts would need them configured at build time
(baking a LAN address into a bundle) or fetched at runtime (a config
endpoint, which is this file with extra steps). It would also reintroduce
CORS, since the browser would then be calling a second origin.

The cost is that the Pi relays bytes it does not read. A completed
report is a few hundred KB and a sweep takes seconds, so that is not the
constraint here.

--------------------------------------------------------------------
WHAT IT DOES NOT DO

No retries, no caching, no request rewriting beyond the path. If the
upstream is down the caller gets 502 with the reason, because a
backtesting UI that silently showed nothing would be worse than one that
says the engine host is unreachable.
"""

from __future__ import annotations

import os
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Request, Response, WebSocket, WebSocketDisconnect

router = APIRouter(prefix="/api/backtest", tags=["backtest"])


def upstream_base() -> str | None:
    """The host to forward to, or None to run backtests locally."""
    value = (os.environ.get("VAI_BACKTEST_UPSTREAM") or "").strip().rstrip("/")
    return value or None


def is_enabled() -> bool:
    return upstream_base() is not None


# Generous: a sweep over ten years of minute bars legitimately takes
# minutes, and a proxy that timed out mid-run would look exactly like a
# failed backtest. The job queue on the other side makes the HTTP calls
# themselves short -- this covers the outlier, not the norm.
TIMEOUT = httpx.Timeout(300.0, connect=10.0)


@router.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    include_in_schema=False,
)
async def forward(path: str, request: Request) -> Response:
    base = upstream_base()
    if base is None:  # pragma: no cover - router is only mounted when set
        raise HTTPException(status_code=500, detail="No upstream configured.")

    target = f"{base}/api/backtest/{path}"
    body = await request.body()
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.request(
                request.method,
                target,
                content=body or None,
                params=dict(request.query_params),
                headers={"content-type": request.headers.get("content-type", "application/json")},
            )
    except httpx.HTTPError as exc:
        # Named, not swallowed. "The engine host is unreachable" is
        # actionable; an empty page is not.
        raise HTTPException(
            status_code=502,
            detail=f"Backtest engine at {base} is unreachable: {exc}",
        ) from exc

    return Response(
        content=response.content,
        status_code=response.status_code,
        media_type=response.headers.get("content-type"),
    )


@router.websocket("/ws/{run_id}")
async def forward_socket(socket: WebSocket, run_id: str) -> None:
    """Relay a run's progress socket, frame for frame.

    Only upstream-to-client is relayed. The backtest socket is
    write-only from the server's side -- a client sends nothing after
    connecting -- so a bidirectional pump would be two tasks to
    supervise for a direction that carries no traffic.
    """
    base = upstream_base()
    if base is None:  # pragma: no cover
        await socket.close()
        return

    ws_base = base.replace("https://", "wss://").replace("http://", "ws://")
    await socket.accept()
    try:
        import websockets

        async with websockets.connect(f"{ws_base}/api/backtest/ws/{run_id}") as relay:
            async for message in relay:
                await socket.send_text(
                    message if isinstance(message, str) else message.decode("utf-8")
                )
    except WebSocketDisconnect:
        return
    except Exception as exc:
        # The client is already accepted, so an error has to be
        # delivered as a frame rather than a status code.
        try:
            await socket.send_json(
                {"type": "error", "detail": f"upstream {ws_base} unreachable: {exc}"}
            )
        finally:
            await socket.close()


def describe() -> dict[str, Any]:
    """For /api/health, so a reader can see where sweeps actually run."""
    base = upstream_base()
    return {"backtest_upstream": base, "backtest_local": base is None}


__all__ = ["describe", "forward", "is_enabled", "router", "upstream_base"]
