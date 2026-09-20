"""The API this project's web UI talks to.

    pip install -r requirements-web.txt
    uvicorn server.app:app --host 127.0.0.1 --port 8000

--------------------------------------------------------------------
TWO ROUTERS, DELIBERATELY DIFFERENT POWERS

  live.py      READ-ONLY. Opens the ledger store `mode=ro`, so the
               SQLite driver refuses a write. Imports no broker.
  control.py   THE ONLY WRITE. One endpoint, reaching the existing
               CircuitBreaker and nothing else.
  backtest.py  BIDIRECTIONAL, because a simulation over a CSV cannot
               touch a position. Validated through BacktestConfig.

The split is the whole design: live state is something to look at, a
backtest is something to run. server/tests/test_server_capability.py walks
each module's AST and fails if the boundary moves.

--------------------------------------------------------------------
BINDS TO LOOPBACK, AND CORS IS NOT A WILDCARD

This server returns account balances, positions and cost bases. The
default host is 127.0.0.1 and CORS admits only the Vite dev origins;
exposing it on a network is a deliberate act (`--host 0.0.0.0`), not
something to inherit from a framework default.

There is no authentication. That is acceptable ONLY on loopback, and it
is the reason the default is loopback -- stated here rather than
discovered later by someone who bound it to a LAN.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from server import backtest, control, deployment, live, ml_insights, ml_upstream, shards, upstream


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Resume the backtest queue a previous process left behind.

    At startup rather than import, because importing server.backtest must
    not start a worker thread or read a directory -- every test imports
    it. Skipped when this host forwards backtests upstream: on the Pi the
    queue belongs to the workstation, and restoring one here would run
    sweeps on the trading loop's cores.
    """
    if not upstream.is_enabled():
        restored = backtest.queue.restore()
        if restored:
            logging.getLogger("Optimizer").info(f"Restored {restored} queued backtest run(s).")
    yield


app = FastAPI(
    title="volatility-ai",
    version="0.1.0",
    description="Read-only live telemetry, and a backtest runner.",
    lifespan=lifespan,
)

# Explicit origins, never ["*"]. A wildcard plus no authentication means
# any page the operator happens to visit can read their positions.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# /api/backtest/history flattens every stored run to one row per grid
# cell -- a brute-force sweep run this way pushed a single response past
# 120 MB and made it unreliable to deliver. The JSON is thousands of
# near-identical numeric records, so it compresses roughly 12x; gzip
# costs nothing on the (already lean) small responses everywhere else.
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.include_router(live.router)
app.include_router(control.router)
# THE BACKTEST ROUTES COME FROM ONE PLACE OR THE OTHER, NEVER BOTH.
#
# With VAI_BACKTEST_UPSTREAM set this host forwards them and never
# imports an engine run into its own process -- which is the point on
# the Raspberry Pi, where those cores belong to the trading loop.
# Without it, they are served locally, which is every other deployment.
#
# Mounting both would let registration order decide which one answers,
# and that is not a thing to leave to ordering.
if upstream.is_enabled():
    app.include_router(upstream.router)
else:
    app.include_router(backtest.router)
    # Remote shards (server/shards.py) work the same queue, so they belong
    # to whichever host runs it -- and are forwarded with it otherwise.
    app.include_router(shards.router)

# THE ML RESEARCH ROUTES FOLLOW THE SAME SPLIT, FOR THE SAME REASON.
#
# data/external/ and data/ml/ live on the workstation -- gitignored, and
# never synced to the Pi's image. With VAI_BACKTEST_UPSTREAM set this
# host forwards; without it, it reads those files itself.
if ml_upstream.is_enabled():
    app.include_router(ml_upstream.router)
else:
    app.include_router(ml_insights.router)


@app.get("/api/health")
def health() -> dict[str, object]:
    """Liveness, what this server is allowed to do, and which build it is.

    `caps` lists what the server CAN do, reported rather than assumed so
    a client renders the Command Center from what the SERVER says,
    instead of from a constant compiled into the bundle that could
    disagree with the deployment it is talking to. Liquidation and live
    parameter overrides are never listed -- by design, see control.py.
    `ml` is read-only research artifacts (server/ml_insights.py), not a
    trading capability.

    `upstream` is where sweeps actually run: the forwarding host, or
    None when this process runs them itself.
    """
    return {
        "caps": ["live", "halt", "backtest", "ml"],
        "upstream": upstream.upstream_base(),
        **deployment.describe(),
    }


# --------------------------------------------------------------------
# THE BUILT FRONTEND, WHEN THERE IS ONE.
#
# In development Vite serves the app on :5173 and proxies /api here, so
# there are two ports and CORS above covers the gap. In a deployment
# there is no Vite: the built bundle is served from THIS process, which
# means one origin, no CORS involved at all, and one port to expose.
#
# Mounted only if the build exists. A checkout that has never run
# `npm run build` still serves the API perfectly well, and failing to
# start because a frontend is missing would make the API hostage to a
# toolchain it does not need.
_DIST = Path(__file__).resolve().parent.parent / "web" / "dist"

if (_DIST / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=_DIST / "assets"), name="assets")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(_DIST / "index.html")

    @app.api_route(
        "/{path:path}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        include_in_schema=False,
    )
    def spa(path: str) -> FileResponse:
        """Serve a real file if there is one, else the app shell.

        Declared AFTER every /api route, so it can only catch what they
        did not -- a catch-all registered first would swallow the entire
        API.

        AND IT REFUSES /api ITSELF, on every method. Registration
        order alone is not enough. A GET-only catch-all still MATCHES
        the path for a POST, so Starlette answers 405 before this
        function runs -- and 405 on a nonexistent endpoint says "wrong
        verb" about a route that does not exist. A test caught exactly
        that, on the assertion that there is no /api/live/liquidate.
        Registering every method means this handler is reached and can
        say 404, which is what a fetch() expects.
        """
        if path == "api" or path.startswith("api/"):
            raise HTTPException(status_code=404, detail=f"No API route /{path}.")
        candidate = _DIST / path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_DIST / "index.html")
