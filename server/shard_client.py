"""A remote shard: one machine working the main server's backtest queue.

    python cli.py shard --name fast-shard --main 1.2.3.4

--------------------------------------------------------------------
WHAT IT DOES

Registers with the main server (server/shards.py), then loops: claim one
queued run (a sweep), run it with the SAME run_backtest the main server
uses, and hand every finished configuration back as it lands. The main
server checkpoints those rows exactly as it checkpoints its own, which is
what lets any shard -- this one after a restart, or another machine --
continue the sweep at configuration granularity.

The engine runs on this machine's cores: server.backtest sizes its
process pool from os.cpu_count() here (or VAI_MAX_JOBS, which
`cli.py shard --max-jobs` sets), not from the main server's.

--------------------------------------------------------------------
TWO THREADS, ONE OUTBOX

  main thread    claim -> run -> finish, and the engine itself. The
                 engine's result sink calls record_row() once per
                 configuration, which only appends to the outbox --
                 never blocks on the network, never raises, as
                 run_sweep's sink contract requires.
  sender thread  drains the outbox IN ORDER (a run's rows before its
                 finish), and heartbeats every SYNC_INTERVAL_SECONDS
                 when there is nothing to send. Each sync answers
                 whether this shard is paused and whether its current
                 run has been asked to stop -- which is how pause and
                 cancel reach a remote engine.

A network failure keeps entries in the outbox and retries. If the main
server was gone long enough to reassign the run, it refuses the late
rows (owned=false / not_owner) and this shard drops the run: its work
up to the last delivered row is already in the main server's checkpoint.

--------------------------------------------------------------------
BARS ARE CACHED ON DISK

A decade of minute bars is fetched once per ticker and kept under
--cache-dir, keyed by the main server's fingerprint of that ticker, so
a sweep series over one fund downloads it once. An ingest on the main
server changes the fingerprint and the next sweep fetches again.

--------------------------------------------------------------------
STOPPING

Ctrl+C (SIGINT/SIGTERM/SIGBREAK) asks the engine to stop after the
configurations in flight, gives the run back to the queue, and waits a
bounded time for the outbox to drain. A second Ctrl+C exits at once;
the main server's timeout then reassigns the run.
"""

from __future__ import annotations

import collections
import contextlib
import json
import os
import re
import threading
import time
import traceback
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import httpx
import pandas as pd

from server.jobs import SHARD_NAME_PATTERN, RunStopped
from server.shards import BAR_COLUMNS, FINGERPRINT_HEADER, decode_bars

DEFAULT_PORT = 8000
CLAIM_WAIT_SECONDS = 5.0
SYNC_INTERVAL_SECONDS = 2.0
RETRY_SECONDS = 5.0
ROWS_PER_SYNC = 200
DRAIN_ON_EXIT_SECONDS = 30.0
PROGRESS_LOG_SECONDS = 30.0
MEMO_FRAMES = 2


class ShardRefused(Exception):
    """The main server will not accept this shard (version mismatch, bad name)."""


class Superseded(Exception):
    """Another process registered under this shard's name."""


class UnknownToMain(Exception):
    """The main server has no record of this shard -- it restarted."""


class NotOwned(Exception):
    """The main server no longer has this run assigned to this shard."""


def main_url(value: str, default_port: int = DEFAULT_PORT) -> str:
    """`1.2.3.4`, `1.2.3.4:9000`, `host`, or a full URL -> a base URL.

    A bare host gets `default_port`, the port `cli.py serve` binds.
    """
    text = value.strip().rstrip("/")
    if not text:
        raise ValueError("the main server address is empty")
    if "://" not in text:
        text = f"http://{text}"
    parts = urlsplit(text)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise ValueError(f"not a host or http(s) URL: {value!r}")
    host = f"[{parts.hostname}]" if ":" in parts.hostname else parts.hostname
    port = parts.port or (default_port if parts.scheme == "http" else None)
    return f"{parts.scheme}://{host}" + (f":{port}" if port else "")


def _json_default(value: Any) -> Any:
    item = getattr(value, "item", None)
    if callable(item):
        return item()
    return str(value)


def _dumps(payload: Any) -> bytes:
    # The stdlib encoder writes NaN, which result rows can carry and the
    # main server's request parser accepts; httpx's json= refuses it.
    return json.dumps(payload, default=_json_default).encode("utf-8")


def _empty_frame() -> pd.DataFrame:
    frame = pd.DataFrame(columns=list(BAR_COLUMNS))
    frame.index = pd.DatetimeIndex([], name="timestamp", tz="UTC")
    return frame


# ---------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------


class MainClient:
    """The shard protocol, one method per route. Raises the exceptions
    above for refusals and httpx.HTTPError for everything transient."""

    def __init__(self, base_url: str, name: str, instance: str, client: Any = None) -> None:
        self.base_url = base_url
        self.name = name
        self.instance = instance
        self._http = client or httpx.Client(
            base_url=base_url, timeout=httpx.Timeout(30.0, connect=5.0)
        )
        self._shard = f"/api/backtest/shards/{name}"

    def close(self) -> None:
        self._http.close()

    def _post(self, path: str, payload: dict[str, Any], timeout: float | None = None) -> Any:
        extra = {"timeout": timeout} if timeout is not None else {}
        response = self._http.post(
            path,
            content=_dumps({"instance": self.instance, **payload}),
            headers={"content-type": "application/json"},
            **extra,
        )
        return self._decode(response)

    def _get(self, path: str) -> Any:
        return self._decode(self._http.get(path))

    @staticmethod
    def _decode(response: httpx.Response) -> Any:
        if response.status_code in (404, 409, 422):
            try:
                detail = response.json().get("detail")
            except ValueError:
                detail = None
            code = detail.get("code") if isinstance(detail, dict) else None
            message = detail.get("msg") if isinstance(detail, dict) else str(detail)
            if code == "unknown_shard":
                raise UnknownToMain(message)
            if code == "superseded":
                raise Superseded(message)
            if code == "not_owner":
                raise NotOwned(message)
            if code in ("version_mismatch", "refused") or response.status_code == 422:
                raise ShardRefused(message or response.text)
        response.raise_for_status()
        return json.loads(response.content)

    def register(self, **fields: Any) -> dict[str, Any]:
        return self._post(f"{self._shard}/register", fields)

    def claim(self, wait: float) -> dict[str, Any] | None:
        body = self._post(f"{self._shard}/claim", {"wait": wait}, timeout=wait + 30.0)
        return body.get("run")

    def sync(
        self,
        run: str | None,
        progress: float | None,
        msg: str | None,
        rows: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return self._post(
            f"{self._shard}/sync",
            {"run": run, "progress": progress, "msg": msg, "rows": rows},
        )

    def finish(self, run_id: str, body: dict[str, Any]) -> None:
        self._post(f"{self._shard}/runs/{run_id}/finish", body, timeout=120.0)

    def tickers(self) -> set[str]:
        return set(self._get("/api/backtest/shard-data/tickers")["tickers"])

    def fingerprint(self, ticker: str) -> str | None:
        response = self._http.get(f"/api/backtest/shard-data/bars/{ticker}/fingerprint")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()["fingerprint"]

    def download_bars(self, ticker: str, dest: Path) -> str:
        """Stream one ticker's bars to `dest`; returns their fingerprint."""
        with self._http.stream(
            "GET", f"/api/backtest/shard-data/bars/{ticker}", timeout=600.0
        ) as response:
            response.raise_for_status()
            fingerprint = response.headers.get(FINGERPRINT_HEADER, "")
            with dest.open("wb") as handle:
                for chunk in response.iter_bytes():
                    handle.write(chunk)
        return fingerprint


# ---------------------------------------------------------------------
# The outbox and its sender
# ---------------------------------------------------------------------


class Link:
    """What this shard owes the main server, and what it last heard back."""

    def __init__(
        self,
        main: MainClient,
        *,
        sync_interval: float = SYNC_INTERVAL_SECONDS,
        retry_seconds: float = RETRY_SECONDS,
        log: Callable[[str], None] = print,
    ) -> None:
        self.main = main
        self._sync_interval = sync_interval
        self._retry = retry_seconds
        self._log = log
        self._cond = threading.Condition()
        # ("row", run_id, {"ticker", "row"}) | ("finish", run_id, body)
        self._outbox: collections.deque[tuple[str, str, dict[str, Any]]] = collections.deque()
        self._run: str | None = None
        self._progress: tuple[float, str] | None = None
        self._stop_asked = False
        self._lost = False
        self._closed = False
        self._failing = False
        self._thread: threading.Thread | None = None
        self.paused = False
        self.superseded = False
        self.unknown = False
        self.stopping = False

    # -- called from the main thread ------------------------------------

    def registered(self, paused: bool) -> None:
        with self._cond:
            self.paused = paused
            self.unknown = False
            self._cond.notify_all()

    def request_stop(self) -> None:
        with self._cond:
            self.stopping = True
            self._cond.notify_all()

    def begin(self, run_id: str) -> None:
        with self._cond:
            self._run = run_id
            self._progress = None
            self._stop_asked = False
            self._lost = False

    def end(self) -> None:
        with self._cond:
            self._run = None
            self._progress = None

    def owns(self, run_id: str) -> bool:
        with self._cond:
            return self._run == run_id and not self._lost and not self.superseded

    def should_stop(self, run_id: str) -> bool:
        with self._cond:
            return (
                self.stopping
                or self.superseded
                or self._lost
                or self._run != run_id
                or self._stop_asked
            )

    def report(self, fraction: float, note: str) -> None:
        with self._cond:
            self._progress = (max(0.0, min(1.0, float(fraction))), note)

    def record_row(self, run_id: str, ticker: str, row: dict[str, Any]) -> None:
        """Queue one finished configuration. Never blocks, never raises."""
        with self._cond:
            if self._run != run_id or self._lost:
                return
            self._outbox.append(("row", run_id, {"ticker": ticker, "row": row}))
            self._cond.notify_all()

    def finish(self, run_id: str, body: dict[str, Any]) -> None:
        with self._cond:
            self._outbox.append(("finish", run_id, body))
            self._cond.notify_all()

    def wait_drained(self, timeout: float | None = None, *, until_stopping: bool = False) -> bool:
        """Block until the outbox is empty. `until_stopping` also returns
        as soon as a stop is requested, so Ctrl+C is never stuck here."""
        with self._cond:
            return self._cond.wait_for(
                lambda: (
                    not self._outbox
                    or self.superseded
                    or self._closed
                    or (until_stopping and self.stopping)
                ),
                timeout=timeout,
            )

    def start(self) -> None:
        self._thread = threading.Thread(target=self._loop, name="shard-sender", daemon=True)
        self._thread.start()

    def close(self) -> None:
        with self._cond:
            self._closed = True
            self._cond.notify_all()
        if self._thread is not None:
            self._thread.join(timeout=self._sync_interval + 35.0)

    # -- the sender thread -----------------------------------------------

    def _loop(self) -> None:
        while True:
            with self._cond:
                self._cond.wait_for(
                    lambda: self._closed or bool(self._outbox), timeout=self._sync_interval
                )
                if self._closed or self.superseded:
                    return
                if self.unknown:
                    # The main thread re-registers; nothing is deliverable
                    # until it has.
                    continue
                entry = self._outbox[0] if self._outbox else None
                if entry is not None and entry[0] == "finish":
                    work: tuple[str, Any] = ("finish", entry)
                else:
                    work = ("sync", self._next_batch())
            try:
                if work[0] == "finish":
                    self._send_finish(work[1])
                else:
                    self._send_sync(*work[1])
                if self._failing:
                    self._failing = False
                    self._log(f"reconnected to main server at {self.main.base_url}")
            except Superseded:
                with self._cond:
                    self.superseded = True
                    self._outbox.clear()
                    self._cond.notify_all()
                return
            except ShardRefused as exc:
                # Malformed, not transient: retrying the same request would
                # be refused forever, so it is dropped rather than resent.
                self._log(f"main server rejected an update, dropping it: {exc}")
                with self._cond:
                    if work[0] == "finish":
                        if self._outbox and self._outbox[0] is work[1]:
                            self._outbox.popleft()
                    else:
                        for _ in range(work[1][2]):
                            if self._outbox:
                                self._outbox.popleft()
                    self._cond.notify_all()
            except UnknownToMain:
                with self._cond:
                    # A restarted main server restored every run as queued;
                    # nothing this shard still holds is its to deliver.
                    self.unknown = True
                    if self._run is not None:
                        self._lost = True
                    self._outbox.clear()
                    self._cond.notify_all()
            except (httpx.HTTPError, ValueError) as exc:
                if not self._failing:
                    self._failing = True
                    self._log(
                        f"main server at {self.main.base_url} unreachable "
                        f"({type(exc).__name__}: {exc}); retrying every {self._retry:g}s"
                    )
                with self._cond:
                    self._cond.wait_for(lambda: self._closed, timeout=self._retry)

    def _next_batch(self) -> tuple[str | None, list[dict[str, Any]], int]:
        """Leading rows of one run, up to ROWS_PER_SYNC. Caller holds the lock."""
        rows: list[dict[str, Any]] = []
        run = self._outbox[0][1] if self._outbox else self._run
        for kind, run_id, body in self._outbox:
            if kind != "row" or run_id != run or len(rows) >= ROWS_PER_SYNC:
                break
            rows.append(body)
        return run, rows, len(rows)

    def _send_sync(self, run: str | None, rows: list[dict[str, Any]], count: int) -> None:
        with self._cond:
            progress = self._progress if run is not None and run == self._run else None
        answer = self.main.sync(
            run,
            progress[0] if progress else None,
            progress[1] if progress else None,
            rows,
        )
        with self._cond:
            for _ in range(count):
                self._outbox.popleft()
            self.paused = bool(answer.get("paused"))
            if run is not None and run == self._run:
                self._stop_asked = bool(answer.get("stop"))
                if not answer.get("owned"):
                    self._lost = True
            if run is not None and not answer.get("owned"):
                # Refused rows stay refused; drop the rest of that run's.
                self._outbox = collections.deque(entry for entry in self._outbox if entry[1] != run)
            self._cond.notify_all()

    def _send_finish(self, entry: tuple[str, str, dict[str, Any]]) -> None:
        _, run_id, body = entry
        try:
            self.main.finish(run_id, body)
        except NotOwned:
            self._log(f"main server no longer assigns {run_id} to this shard; result dropped")
        with self._cond:
            if self._outbox and self._outbox[0] is entry:
                self._outbox.popleft()
            self._cond.notify_all()


class RemoteControl:
    """server.jobs.RunControl's protocol, backed by the Link."""

    def __init__(self, link: Link, run_id: str, rows: dict[str, list[dict[str, Any]]]) -> None:
        self._link = link
        self._run_id = run_id
        self._rows = rows

    def should_stop(self) -> bool:
        return self._link.should_stop(self._run_id)

    def completed_rows(self, ticker: str) -> list[dict[str, Any]]:
        return list(self._rows.get(ticker, []))

    def record_row(self, ticker: str, row: dict[str, Any]) -> None:
        self._link.record_row(self._run_id, ticker, row)


# ---------------------------------------------------------------------
# Bars
# ---------------------------------------------------------------------


class RemoteBars:
    """server.backtest.BarSource over the main server, cached on disk."""

    def __init__(
        self, main: MainClient, cache_dir: Path, log: Callable[[str], None] = print
    ) -> None:
        self._main = main
        self._dir = Path(cache_dir)
        self._log = log
        self._memo: collections.OrderedDict[tuple[str, str], pd.DataFrame] = (
            collections.OrderedDict()
        )

    def available_tickers(self) -> set[str]:
        return self._main.tickers()

    def load_frame(self, ticker: str) -> pd.DataFrame:
        fingerprint = self._main.fingerprint(ticker)
        if fingerprint is None:
            return _empty_frame()
        key = (ticker, fingerprint)
        if key in self._memo:
            self._memo.move_to_end(key)
            return self._memo[key].copy()

        safe = re.sub(r"[^A-Za-z0-9_.-]", "_", ticker)
        data_path = self._dir / f"{safe}.npz"
        meta_path = self._dir / f"{safe}.fingerprint"
        frame = None
        cached = (
            data_path.exists()
            and meta_path.exists()
            and meta_path.read_text(encoding="utf-8").strip() == fingerprint
        )
        if cached:
            try:
                frame = decode_bars(data_path.read_bytes())
            except (OSError, ValueError, KeyError) as exc:
                self._log(f"cached bars for {ticker} unreadable ({exc}); downloading again")
        if frame is None:
            self._dir.mkdir(parents=True, exist_ok=True)
            # PER PROCESS, AND A LOST RACE IS NOT A FAILED SWEEP. Two
            # shards sharing one --cache-dir both downloaded to
            # "<ticker>.npz.part"; on Windows the second one's replace()
            # raised PermissionError and failed a whole sweep over a
            # cache file. The download itself is what the run needs -- if
            # it cannot be installed as the shared cache, it is used
            # where it landed and removed after.
            partial = data_path.with_name(f"{data_path.name}.{os.getpid()}.part")
            started = time.monotonic()
            self._log(f"downloading {ticker} bars from the main server...")
            try:
                fingerprint = self._main.download_bars(ticker, partial) or fingerprint
                source, installed = partial, False
                try:
                    partial.replace(data_path)
                    source, installed = data_path, True
                except OSError as exc:
                    self._log(f"could not update the cached {ticker} bars ({exc}); using this copy")
                size = source.stat().st_size
                frame = decode_bars(source.read_bytes())
            finally:
                if partial.exists() and partial != data_path:
                    with contextlib.suppress(OSError):
                        partial.unlink()
            if installed:
                # Written after the data, so a fingerprint on disk always
                # describes bars that are already there.
                with contextlib.suppress(OSError):
                    meta_path.write_text(fingerprint, encoding="utf-8")
            self._log(
                f"cached {ticker}: {len(frame):,} bars, "
                f"{size / 1e6:.1f} MB in {time.monotonic() - started:.1f}s"
            )
            key = (ticker, fingerprint)

        self._memo[key] = frame
        while len(self._memo) > MEMO_FRAMES:
            self._memo.popitem(last=False)
        return frame.copy()


# ---------------------------------------------------------------------
# The process
# ---------------------------------------------------------------------


def _default_runner(request, report, control, bars):
    # Deferred: importing server.backtest pulls in the engine, and
    # cli.py sets VAI_MAX_JOBS before that import reads it.
    from server.backtest import run_backtest

    return run_backtest(request, report, control, bars=bars)


class ShardProcess:
    def __init__(
        self,
        name: str,
        main: str,
        *,
        cache_dir: Path,
        allow_version_mismatch: bool = False,
        client: Any = None,
        runner: Callable[..., dict[str, Any]] | None = None,
        claim_wait: float = CLAIM_WAIT_SECONDS,
        sync_interval: float = SYNC_INTERVAL_SECONDS,
        retry_seconds: float = RETRY_SECONDS,
        log: Callable[[str], None] | None = None,
    ) -> None:
        if not re.match(SHARD_NAME_PATTERN, name) or name == "local":
            raise ValueError(
                f"invalid shard name {name!r}: letters, digits, '.', '-', '_' "
                "(up to 64, starting with a letter or digit), and not 'local'"
            )
        self.name = name
        self.instance = uuid.uuid4().hex[:12]
        self._log = log or (lambda message: print(f"[shard {name}] {message}", flush=True))
        self.main = MainClient(main, name, self.instance, client)
        self.link = Link(
            self.main, sync_interval=sync_interval, retry_seconds=retry_seconds, log=self._log
        )
        self.bars = RemoteBars(self.main, cache_dir, log=self._log)
        self._runner = runner or _default_runner
        self._allow_mismatch = allow_version_mismatch
        self._claim_wait = claim_wait
        self._sync_interval = sync_interval
        self._retry = retry_seconds
        self._wake = threading.Event()
        self.completed = 0

    def request_stop(self) -> None:
        self.link.request_stop()
        self._wake.set()

    def _pause(self, seconds: float) -> None:
        self._wake.wait(seconds)

    def _register(self) -> None:
        from server.deployment import describe

        build = describe()["build"]
        failing = False
        while not self.link.stopping:
            try:
                answer = self.main.register(
                    commit=build.get("commit"),
                    dirty=build.get("dirty"),
                    cores=os.cpu_count(),
                    allow_version_mismatch=self._allow_mismatch,
                )
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code in (404, 405, 501):
                    raise ShardRefused(
                        f"{self.main.base_url} has no shard routes -- is it running this "
                        "project's server (`cli.py serve`), on a version with shard support?"
                    ) from exc
                if not failing:
                    failing = True
                    self._log(f"registration failed ({exc}); retrying every {self._retry:g}s")
                self._pause(self._retry)
                continue
            except httpx.HTTPError as exc:
                if not failing:
                    failing = True
                    self._log(
                        f"main server at {self.main.base_url} unreachable "
                        f"({type(exc).__name__}); retrying every {self._retry:g}s"
                    )
                self._pause(self._retry)
                continue
            shard = answer.get("shard") or {}
            self.link.registered(shard.get("state") == "paused")
            main_commit = (answer.get("main") or {}).get("commit")
            self._log(
                f"registered with {self.main.base_url} "
                f"(this shard: {build.get('commit') or 'unknown'}, "
                f"main: {main_commit or 'unknown'}, {os.cpu_count()} cores)"
                + (" -- PAUSED; resume it from the UI" if self.link.paused else "")
            )
            return

    def run_forever(self, max_runs: int | None = None) -> int:
        try:
            self._register()
        except ShardRefused as exc:
            self._log(f"refused by the main server: {exc}")
            return 2
        if self.link.stopping:
            return 0
        self.link.start()
        was_paused = self.link.paused
        try:
            while not self.link.stopping and not self.link.superseded:
                if max_runs is not None and self.completed >= max_runs:
                    break
                if self.link.unknown:
                    self._log("the main server restarted; registering again")
                    self._register()
                    continue
                if self.link.paused != was_paused:
                    was_paused = self.link.paused
                    self._log("paused from the UI" if was_paused else "resumed")
                if self.link.paused:
                    self._pause(self._sync_interval)
                    continue
                try:
                    run = self.main.claim(self._claim_wait)
                except UnknownToMain:
                    self.link.unknown = True
                    continue
                except Superseded:
                    self.link.superseded = True
                    break
                except (httpx.HTTPError, ShardRefused, ValueError) as exc:
                    self._log(f"claim failed ({type(exc).__name__}: {exc}); retrying")
                    self._pause(self._retry)
                    continue
                if run is not None:
                    self._run_one(run)
        finally:
            self.link.wait_drained(timeout=DRAIN_ON_EXIT_SECONDS)
            self.link.close()
            self.main.close()
        if self.link.superseded:
            self._log("another process registered with this name; exiting")
            return 1
        self._log(f"stopped after {self.completed} completed sweep(s)")
        return 0

    def _run_one(self, run: dict[str, Any]) -> None:
        run_id = run["id"]
        label = run.get("name") or run_id
        rows = run.get("rows") or {}
        done = sum(len(v) for v in rows.values())
        self._log(f"claimed {label}" + (f" (resuming after {done} configurations)" if done else ""))
        self.link.begin(run_id)
        control = RemoteControl(self.link, run_id, rows)
        last_log = [time.monotonic(), ""]

        def report(fraction: float, note: str) -> None:
            self.link.report(fraction, note)
            now = time.monotonic()
            if now - last_log[0] >= PROGRESS_LOG_SECONDS:
                last_log[0] = now
                self._log(f"{label}: {fraction:.0%} -- {note}")

        outcome, result, error, back_off = "complete", None, None, False
        try:
            result = self._runner(run["request"], report, control, self.bars)
        except RunStopped:
            outcome = "stopped"
        except Exception as exc:
            if self.link.should_stop(run_id):
                # A stop can break the engine on its way out (Ctrl+C
                # reaches the pool's workers too); that is not the run
                # failing.
                outcome = "stopped"
            elif isinstance(exc, (httpx.HTTPError, UnknownToMain, NotOwned)):
                outcome, error, back_off = "released", f"{type(exc).__name__}: {exc}", True
            else:
                traceback.print_exc()
                outcome, error = "failed", f"{type(exc).__name__}: {exc}"
        if self.link.stopping and outcome == "stopped":
            outcome, error = "released", "shard shutting down"

        if not self.link.owns(run_id):
            self._log(f"{label}: no longer assigned to this shard; its unsent work is dropped")
        else:
            self.link.finish(run_id, {"outcome": outcome, "report": result, "error": error})
            self.link.wait_drained(until_stopping=True)
            summary = {
                "complete": "complete",
                "failed": f"FAILED -- {error}",
                "stopped": "stopped; handed back to the queue",
                "released": f"handed back to the queue ({error})",
            }[outcome]
            self._log(f"{label}: {summary}")
        self.link.end()
        if outcome == "complete":
            self.completed += 1
        if back_off:
            self._pause(self._retry)


__all__ = [
    "Link",
    "MainClient",
    "RemoteBars",
    "RemoteControl",
    "ShardProcess",
    "ShardRefused",
    "Superseded",
    "UnknownToMain",
    "main_url",
]
