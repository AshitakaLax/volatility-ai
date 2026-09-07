"""Forward /api/ml/* to the workstation, the same way backtest is forwarded.

The ML research artifacts (data/external/, data/ml/) live on the
workstation, not the Pi -- they are gitignored and were never intended
to be synced there, and the Pi's image never installs
requirements-ml.txt (see server/ml_insights.py's docstring). So the Pi
relays the request rather than reading local files that do not exist.

A SEPARATE, SMALLER MODULE FROM upstream.py ON PURPOSE, even though the
logic mostly repeats it. /api/ml/* is entirely GET -- there is no
submitted job and no progress socket the way a backtest run has -- so
duplicating the handful of lines this needs keeps that module's
tested, production-critical POST-and-websocket forwarding for backtests
completely untouched rather than generalising it for a second caller
that does not need most of what it does.

Reuses upstream.upstream_base()/is_enabled() rather than a second env
var: this is the same workstation forwarding the same way, so it is one
decision ("is a backtest engine host configured"), not two that could
disagree.
"""

from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException, Request, Response

from server.upstream import is_enabled, upstream_base

router = APIRouter(prefix="/api/ml", tags=["ml"])

# Static JSON reads. A hung upstream should surface quickly rather than
# hold a browser tab for minutes, unlike a backtest run.
TIMEOUT = httpx.Timeout(15.0, connect=5.0)


@router.api_route("/{path:path}", methods=["GET"], include_in_schema=False)
async def forward(path: str, request: Request) -> Response:
    base = upstream_base()
    if base is None:  # pragma: no cover - router is only mounted when set
        raise HTTPException(status_code=500, detail="No upstream configured.")

    target = f"{base}/api/ml/{path}"
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(target, params=dict(request.query_params))
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"ML research host at {base} is unreachable: {exc}",
        ) from exc

    return Response(
        content=response.content,
        status_code=response.status_code,
        media_type=response.headers.get("content-type"),
    )


__all__ = ["forward", "is_enabled", "router"]
