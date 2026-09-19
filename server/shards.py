"""Distributed sweeps: the routes remote shards and the UI use.

    cli.py serve --host 0.0.0.0                 # the main server
    cli.py shard --name fast-shard --main HOST  # each extra machine

--------------------------------------------------------------------
WHAT LIVES WHERE

The queue itself -- who runs what, ownership, timeouts, pauses -- is in
server/jobs.py, under the queue's one lock. This module is only the HTTP
face of it, plus the bar download a shard needs because it has no
warehouse of its own. The shard process is server/shard_client.py.

Every route is under /api/backtest/, on purpose: on the Raspberry Pi,
server/upstream.py forwards that whole prefix to the workstation, so the
UI's shard panel works through the Pi with no second origin -- the same
reason the run routes live there.

  for the UI
    GET  /api/backtest/shards                  every shard, and main's build
    POST /api/backtest/shards {paused}         pause / resume every shard
    POST /api/backtest/shards/{name} {op}      pause | resume | forget
    POST /api/backtest/shards/{name}/schedule  set/clear its daily lockout window

  for shards (server/shard_client.py)
    POST /api/backtest/shards/{name}/register
    POST /api/backtest/shards/{name}/claim
    POST /api/backtest/shards/{name}/sync
    POST /api/backtest/shards/{name}/runs/{run_id}/finish
    GET  /api/backtest/shard-data/tickers
    GET  /api/backtest/shard-data/bars/{ticker}/fingerprint
    GET  /api/backtest/shard-data/bars/{ticker}

--------------------------------------------------------------------
NO AUTHENTICATION, DELIBERATELY FOR NOW

Shards run on a trusted LAN, matching the rest of this server: anyone
who can reach the port can register a shard, claim a sweep, or post its
results. Binding the main server beyond loopback so shards can reach it
is the same deliberate act server/app.py's docstring describes.

--------------------------------------------------------------------
VERSION SKEW IS REFUSED

A shard on a different commit runs a different engine, and its rows
would be checkpointed next to this server's as if they were comparable.
Registration is refused (409 version_mismatch) unless the shard passes
--allow-version-mismatch. An unknown commit on either side (no git in a
container) is not a mismatch -- there is nothing to compare.

--------------------------------------------------------------------
BARS TRAVEL AS COMPRESSED NUMPY, NOT JSON

A decade of minute bars is a million rows; as JSON that is ~100 MB and
seconds of parsing on both ends. np.savez_compressed is ~20 MB, needs
nothing beyond numpy (already here for pandas), and loads with
allow_pickle=False, so a payload cannot execute anything. Shards cache
it on disk keyed by the fingerprint, and only download again when the
fingerprint changes.
"""

from __future__ import annotations

import hashlib
import io
import json
import threading
import time
from typing import Annotated, Any, Literal

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, Path, Request, Response
from pydantic import BaseModel, Field

from engine.warehouse import bars as warehouse_bars
from server import backtest, deployment
from server.jobs import (
    SHARD_NAME_PATTERN,
    SHARD_STALE_SECONDS,
    SHARD_TIMEOUT_SECONDS,
    NotOwner,
    QueueError,
    ShardSuperseded,
    UnknownShard,
)

router = APIRouter(prefix="/api/backtest", tags=["shards"])

# Upper bound on how long a claim may wait for work. Kept well under the
# stale threshold: a shard's heartbeat thread keeps running while its
# main thread waits here, but a long poll still holds a server thread.
CLAIM_WAIT_MAX = 10.0
REAP_INTERVAL_SECONDS = 5.0
BAR_COLUMNS = ("open", "high", "low", "close", "volume")
BARS_MEDIA_TYPE = "application/x-npz"
FINGERPRINT_HEADER = "X-Bars-Fingerprint"

ShardName = Annotated[str, Path(pattern=SHARD_NAME_PATTERN)]


# ---------------------------------------------------------------------
# Bars on the wire
# ---------------------------------------------------------------------


def encode_bars(frame: pd.DataFrame) -> bytes:
    """A load_frame()-shaped frame as compressed numpy arrays."""
    index = pd.DatetimeIndex(frame.index)
    aware = index.tz is not None
    utc = index.tz_convert("UTC").tz_localize(None) if aware else index
    arrays: dict[str, np.ndarray] = {
        "timestamp": utc.to_numpy(dtype="datetime64[ns]").astype("int64"),
        "aware": np.array([1 if aware else 0], dtype="int8"),
        # pandas 3 parses to microseconds, and the warehouse may differ;
        # the shard gets back the resolution the main server had.
        "unit": np.array([getattr(index, "unit", "ns")]),
    }
    for column in BAR_COLUMNS:
        values = frame[column].to_numpy()
        if values.dtype == object:
            values = values.astype("float64")
        arrays[column] = values
    buffer = io.BytesIO()
    np.savez_compressed(buffer, **arrays)
    return buffer.getvalue()


def decode_bars(payload: bytes) -> pd.DataFrame:
    """The inverse of encode_bars. Never unpickles; any malformed payload
    is a ValueError."""
    try:
        with np.load(io.BytesIO(payload), allow_pickle=False) as data:
            aware = bool(data["aware"][0])
            index = pd.DatetimeIndex(
                pd.to_datetime(data["timestamp"], unit="ns", utc=aware), name="timestamp"
            )
            if "unit" in data.files:
                index = index.as_unit(str(data["unit"][0]))
            columns = {column: data[column] for column in BAR_COLUMNS}
    except (KeyError, IndexError, EOFError, OSError) as exc:
        raise ValueError(f"not a bar payload: {exc}") from exc
    return pd.DataFrame(columns, index=index)


def bars_fingerprint(ticker: str) -> str | None:
    """The warehouse's cheap fingerprint, or -- where there is no
    warehouse row for it (tests, a patched load_frame) -- a hash of the
    bars themselves."""
    cheap = warehouse_bars.fingerprint(ticker)
    if cheap is not None:
        return cheap
    frame = backtest.load_frame(ticker)
    if frame.empty:
        return None
    return hashlib.sha256(encode_bars(frame)).hexdigest()[:32]


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------


def _json(payload: Any) -> Response:
    """JSON that tolerates NaN, which engine result rows can carry.

    FastAPI's default response refuses NaN (allow_nan=False); the rows a
    claim hands back were checkpointed with the stdlib encoder, which
    writes it. The shard reads them back with the stdlib decoder.
    """
    return Response(
        content=json.dumps(payload, default=_json_default),
        media_type="application/json",
    )


def _json_default(value: Any) -> Any:
    item = getattr(value, "item", None)
    if callable(item):
        return item()
    return str(value)


def _error(status: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status, detail={"code": code, "msg": message})


def _protocol(call):
    """Run a shard-protocol call, mapping queue refusals to HTTP."""
    try:
        return call()
    except UnknownShard as exc:
        raise _error(
            404, "unknown_shard", f"No shard {exc.args[0]!r} is registered; register again."
        ) from exc
    except ShardSuperseded as exc:
        raise _error(409, "superseded", str(exc)) from exc
    except NotOwner as exc:
        raise _error(409, "not_owner", str(exc)) from exc
    except QueueError as exc:
        raise _error(409, "refused", str(exc)) from exc


_main_commit: dict[str, str | None] = {}


def main_build() -> dict[str, Any]:
    """This server's commit and dirtiness, computed once per process."""
    if "commit" not in _main_commit:
        build = deployment.describe()["build"]
        _main_commit["commit"] = build.get("commit")
        _main_commit["dirty"] = build.get("dirty")
    return dict(_main_commit)


_reaper: threading.Thread | None = None
_reaper_lock = threading.Lock()


def _ensure_reaper() -> None:
    """Start the timeout sweeper on the first registration, not at import:
    importing a server module must not spawn a thread."""
    global _reaper
    with _reaper_lock:
        if _reaper is not None and _reaper.is_alive():
            return
        _reaper = threading.Thread(target=_reap_forever, name="shard-reaper", daemon=True)
        _reaper.start()


def _reap_forever() -> None:
    while True:
        time.sleep(REAP_INTERVAL_SECONDS)
        try:
            backtest.queue.reap()
        except Exception as exc:  # never let the sweeper die
            print(f"shard reaper: {type(exc).__name__}: {exc}", flush=True)


# ---------------------------------------------------------------------
# For the UI
# ---------------------------------------------------------------------


class ShardOp(BaseModel):
    """pause   stop taking work; the current sweep goes back to the queue
            after its in-flight configurations.
    resume  take work again.
    forget  drop an offline shard from the list."""

    op: Literal["pause", "resume", "forget"]


class ShardsPaused(BaseModel):
    paused: bool


class Schedule(BaseModel):
    """A daily lockout window, server-local wall-clock time.

    `start`/`end` are "HH:MM" (24-hour); required together when
    `enabled` is true. Posting `{"enabled": false}` with neither clears
    the window outright rather than merely disabling it -- see
    `JobQueue.set_shard_schedule`'s docstring for why those are made to
    look identical here on purpose.
    """

    enabled: bool
    start: str | None = None
    end: str | None = None


@router.get("/shards")
def list_shards() -> dict[str, Any]:
    backtest.queue.reap()
    shards = backtest.queue.shards()
    main = main_build()
    for shard in shards:
        if shard["local"]:
            shard["commit"], shard["dirty"] = main.get("commit"), main.get("dirty")
    return {
        "shards": shards,
        "paused": bool(shards) and all(shard["state"] in ("paused", "pausing") for shard in shards),
        "commit": main.get("commit"),
        "stale_s": SHARD_STALE_SECONDS,
        "timeout_s": SHARD_TIMEOUT_SECONDS,
    }


@router.post("/shards")
def set_shards_paused(body: ShardsPaused) -> dict[str, Any]:
    backtest.queue.set_shards_paused(body.paused)
    return {"paused": body.paused}


@router.post("/shards/{name}")
def control_shard(name: ShardName, body: ShardOp) -> dict[str, Any]:
    queue = backtest.queue
    try:
        if body.op == "pause":
            return queue.pause_shard(name)
        if body.op == "resume":
            return queue.resume_shard(name)
        queue.forget_shard(name)
        return {"name": name, "forgotten": True}
    except UnknownShard as exc:
        raise HTTPException(status_code=404, detail=f"No shard {name!r}.") from exc
    except QueueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/shards/{name}/schedule")
def set_shard_schedule(name: ShardName, body: Schedule) -> dict[str, Any]:
    """Not gated on `name` being a currently-registered shard -- see
    JobQueue.set_shard_schedule's docstring; the UI only ever calls this
    for a name it is already displaying."""
    try:
        schedule = backtest.queue.set_shard_schedule(name, body.enabled, body.start, body.end)
    except QueueError as exc:
        # A bad HH:MM or a missing start/end -- the request body itself
        # is invalid, not a conflict with the shard's current state
        # (control_shard's 409 for pause/resume/forget is that; this
        # never depends on what the shard happens to be doing).
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"name": name, "schedule": schedule}


# ---------------------------------------------------------------------
# For shards
# ---------------------------------------------------------------------


class Registration(BaseModel):
    instance: str = Field(min_length=1, max_length=64)
    commit: str | None = Field(default=None, max_length=64)
    dirty: bool | None = None
    cores: int | None = Field(default=None, ge=1)
    allow_version_mismatch: bool = False


class Claim(BaseModel):
    instance: str
    wait: float = Field(default=0.0, ge=0.0, le=CLAIM_WAIT_MAX)


class FinishedRow(BaseModel):
    ticker: str
    row: dict[str, Any]


class Sync(BaseModel):
    instance: str
    run: str | None = None
    progress: float | None = Field(default=None, ge=0.0, le=1.0)
    msg: str | None = None
    rows: list[FinishedRow] = Field(default_factory=list)


class Finish(BaseModel):
    instance: str
    outcome: Literal["complete", "failed", "stopped", "released"]
    report: dict[str, Any] | None = None
    error: str | None = None


@router.post("/shards/{name}/register")
def register(name: ShardName, body: Registration, request: Request) -> dict[str, Any]:
    main = main_build()
    ours, theirs = main.get("commit"), body.commit
    if ours and theirs and ours != theirs and not body.allow_version_mismatch:
        raise _error(
            409,
            "version_mismatch",
            f"Shard {name} is on commit {theirs} but the main server is on {ours}. "
            "Check out the same commit on both, or start the shard with "
            "--allow-version-mismatch to accept results from a different engine.",
        )
    host = request.client.host if request.client else None
    shard = _protocol(
        lambda: backtest.queue.register_shard(
            name,
            body.instance,
            host=host,
            commit=theirs,
            dirty=body.dirty,
            cores=body.cores,
        )
    )
    _ensure_reaper()
    return {
        "shard": shard,
        "main": main,
        "stale_s": SHARD_STALE_SECONDS,
        "timeout_s": SHARD_TIMEOUT_SECONDS,
    }


@router.post("/shards/{name}/claim")
def claim(name: ShardName, body: Claim) -> Response:
    claimed = _protocol(lambda: backtest.queue.claim(name, body.instance, wait=body.wait))
    if claimed is None:
        return _json({"run": None})
    job, rows = claimed
    return _json(
        {"run": {"id": job.run_id, "name": job.name, "request": job.request, "rows": rows}}
    )


@router.post("/shards/{name}/sync")
def sync(name: ShardName, body: Sync) -> dict[str, Any]:
    return _protocol(
        lambda: backtest.queue.shard_sync(
            name,
            body.instance,
            body.run,
            progress=body.progress,
            message=body.msg,
            rows=[(item.ticker, item.row) for item in body.rows],
        )
    )


@router.post("/shards/{name}/runs/{run_id}/finish")
def finish(name: ShardName, run_id: str, body: Finish) -> dict[str, Any]:
    _protocol(
        lambda: backtest.queue.shard_finish(
            name,
            body.instance,
            run_id,
            body.outcome,
            result=body.report,
            error=body.error,
        )
    )
    return {"ok": True}


@router.get("/shard-data/tickers")
def shard_tickers() -> dict[str, Any]:
    return {"tickers": sorted(backtest.available_tickers())}


@router.get("/shard-data/bars/{ticker}/fingerprint")
def shard_bars_fingerprint(ticker: str) -> dict[str, Any]:
    value = bars_fingerprint(ticker)
    if value is None:
        raise HTTPException(status_code=404, detail=f"No bars for {ticker!r}.")
    return {"ticker": ticker, "fingerprint": value}


@router.get("/shard-data/bars/{ticker}")
def shard_bars(ticker: str) -> Response:
    # Fingerprint first: if bars are ingested between the two reads, the
    # shard caches new bars under the old fingerprint and simply fetches
    # again next time -- never old bars under a new fingerprint.
    value = bars_fingerprint(ticker)
    frame = backtest.load_frame(ticker)
    if value is None or frame.empty:
        raise HTTPException(status_code=404, detail=f"No bars for {ticker!r}.")
    return Response(
        content=encode_bars(frame),
        media_type=BARS_MEDIA_TYPE,
        headers={FINGERPRINT_HEADER: value},
    )


__all__ = [
    "BARS_MEDIA_TYPE",
    "CLAIM_WAIT_MAX",
    "FINGERPRINT_HEADER",
    "bars_fingerprint",
    "decode_bars",
    "encode_bars",
    "main_build",
    "router",
]
