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
backtest is something to run. tests/unit/test_server_capability.py walks
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

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from server import backtest, control, deployment, live

app = FastAPI(
    title="volatility-ai",
    version="0.1.0",
    description="Read-only live telemetry, and a backtest runner.",
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

app.include_router(live.router)
app.include_router(control.router)
app.include_router(backtest.router)
app.include_router(deployment.router)


@app.get("/api/health")
def health() -> dict[str, object]:
    """Liveness, plus what this server is allowed to do.

    The capability flags are reported rather than assumed so a client
    renders the Command Center from what the SERVER says it can do,
    instead of from a constant compiled into the bundle that could
    disagree with the deployment it is talking to.
    """
    return {
        "status": "ok",
        "capabilities": {
            "live_read": True,
            "halt": True,
            "liquidate": False,
            "parameter_override": False,
            "backtest_submit": True,
        },
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
