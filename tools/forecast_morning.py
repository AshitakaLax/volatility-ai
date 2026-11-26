#!/usr/bin/env python
"""Each trading morning's risk report: made, kept and applied with nobody at
the page.

    python tools/forecast_morning.py                  # once, now: make, keep, apply
    python tools/forecast_morning.py --daily 07:45    # each session morning at 07:45 ET
    python tools/forecast_morning.py --dry-run        # make and audit; keep and apply nothing
    python tools/forecast_morning.py --no-apply       # make and keep only
    python tools/forecast_morning.py --engine bootstrap --symbols TQQQ

docker-compose.yml's `forecast` service runs the --daily form, on its own
image target (the Dockerfile's `forecast`: the app plus torch on CPU and
chronos-forecasting), so Chronos-2 runs here exactly as the Forecast tab's
chronos engine does.

--------------------------------------------------------------------
WHAT A RUN DOES, FOR EACH FUND (--symbols; VAI_FORECAST_SYMBOLS; else TQQQ)

1. MAKES the report for the session: research/forecast_generator's
   generate(), the Forecast tab's own run. It refuses inside regular hours,
   and whenever the source has not posted the previous session's close yet.
2. KEEPS it: POST /api/live/risk-forecasts, what the Live page's Check sends,
   so server/risk_forecasts.py stays the one writer of the forecast
   database. A forecast_harvest profile with forecast_from_db reads it there
   at the open, and the tracking service scores it after the close.
3. APPLIES it to every PAPER deployment that takes risk reports for that fund
   and whose trader is up (GET /api/live/deployments): POST
   /api/live/deployments/<id>/commands, apply_risk_report, what the Live
   page's Apply sends. The trader applies it between sessions, before the
   open, as it does a pasted one. Never to real money: the server asks for
   such a deployment's id typed back, and this never types it. Each apply
   carries an idempotency key made of the deployment and the report's hash,
   so the same report is never queued twice.

The report travels in the page's own JSON form (as_the_page_sends), so the
database, the command and the trader's archive all hash it alike.

The web server is the only thing this talks to besides the market-data
sources (--web; VAI_WEB_URL; else http://127.0.0.1:8000 -- http://web:8000
in compose). It mounts nothing it writes.

--------------------------------------------------------------------
WHEN (--daily)

On a session day only (engine/core/trading_calendar: weekends and NYSE
holidays are skipped), at each time given. A run that did not finish is
tried again every RETRY_MINUTES until LAST_TRY (09:15 ET), and only what
did not finish: a report already made is kept and applied as it is, never
made again. A start inside that window on a session morning (a restart, a
deploy) runs at once.

A fund whose session already has a report made THIS MORNING -- by the
Forecast tab, a paste, or this service before a restart -- is left as it is:
the service fills a gap, it never replaces the operator's report or applies
twice. An evening report does not count: the morning's carries the
pre-market move (its overnight_gap_risk), which the evening's cannot.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from datetime import time as clock_time
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from engine.core.risk_report import parse_report
from engine.core.trading_calendar import EASTERN, is_session
from research.forecast_generator import generator
from research.risk_overlay.forecasts import as_the_page_sends

DEFAULT_TIMES = ("07:45",)
DEFAULT_SYMBOLS = ("TQQQ",)
DEFAULT_WEB = "http://127.0.0.1:8000"
RETRY_MINUTES = 10
LAST_TRY = clock_time(9, 15)
# Before the open, the session's report made this morning (module docstring).
REGULAR_OPEN = clock_time(9, 30)
OPERATOR = "forecast service"
HTTP_TIMEOUT_SECONDS = 30.0

Report = Callable[[str], None]
Make = Callable[..., generator.Generated]


def _say(line: str) -> None:
    print(f"[forecast] {line}", flush=True)


# --------------------------------------------------------------------
# The web server


class WebError(RuntimeError):
    """A request the web server refused (status) or never answered (None)."""

    def __init__(self, status: int | None, detail: str) -> None:
        super().__init__(detail)
        self.status = status
        self.detail = detail

    @property
    def retryable(self) -> bool:
        """Worth trying again: no answer, a server error or a busy server. A
        4xx is the server's considered answer, and asking again changes
        nothing."""
        return self.status is None or self.status >= 500 or self.status in (408, 429)


Send = Callable[[str, str, dict[str, Any] | None], tuple[int, Any]]


def urllib_send(base: str, timeout: float = HTTP_TIMEOUT_SECONDS) -> Send:
    """(method, path, json body) -> (status, json) against `base`. No Origin
    and no Sec-Fetch-Site: a script, which the cross-site guard lets through."""

    def send(method: str, path: str, body: dict[str, Any] | None) -> tuple[int, Any]:
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            base.rstrip("/") + path,
            data=data,
            method=method,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read()
                return response.status, json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            try:
                payload = json.loads(raw) if raw else None
            except ValueError:
                payload = raw.decode("utf-8", "replace")[:300]
            return exc.code, payload

    return send


class Web:
    """The few routes this uses, each the Live page's own."""

    def __init__(self, send: Send) -> None:
        self._send = send

    def _call(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
        try:
            status, payload = self._send(method, path, body)
        except (OSError, TimeoutError, ValueError) as exc:  # URLError is an OSError
            raise WebError(None, f"{type(exc).__name__}: {exc}") from exc
        if status >= 400:
            detail = payload.get("detail") if isinstance(payload, dict) else payload
            raise WebError(status, f"{method} {path}: {status} {detail}")
        return payload

    def deployments(self) -> list[dict[str, Any]]:
        return self._call("GET", "/api/live/deployments")

    def sessions(self, symbol: str) -> list[dict[str, Any]]:
        return self._call("GET", f"/api/live/risk-forecasts?symbol={symbol}&sessions=5")["sessions"]

    def keep(self, report: dict[str, Any], inputs: dict[str, Any] | None = None) -> dict[str, Any]:
        """Keep the report, and what the generator read for it (shown beside
        it on the Forecast tab; research/risk_overlay/forecasts.py)."""
        body: dict[str, Any] = {"report": report, "operator": OPERATOR}
        if inputs is not None:
            body["inputs"] = inputs
        return self._call("POST", "/api/live/risk-forecasts", body)

    def apply(self, deployment: str, report: dict[str, Any], key: str, reason: str) -> Any:
        return self._call(
            "POST",
            f"/api/live/deployments/{deployment}/commands",
            {
                "type": "apply_risk_report",
                "args": {"report": report},
                "timing": "now",
                "reason": reason,
                "operator": OPERATOR,
                "idempotency_key": key,
            },
        )


def paper_takers(deployments: Iterable[dict[str, Any]], symbol: str) -> list[str]:
    """Paper deployments that take risk reports for `symbol` and whose trader
    is up: who an Apply reaches (module docstring). A trader that is down
    would let the command expire unapplied, so it is not sent one."""
    chosen = []
    for d in deployments:
        status = d.get("status") or {}
        if (
            d.get("paper") is True
            and str(d.get("symbol") or "").upper() == symbol
            and (d.get("risk_reports") or {}).get("takes") is True
            and not status.get("stale", True)
        ):
            chosen.append(str(d["id"]))
    return chosen


def made_this_morning(rows: Iterable[dict[str, Any]], session: date) -> dict[str, Any] | None:
    """The session's report if it was made on its own morning, before the
    open (module docstring), else None."""
    for row in rows:
        if row.get("session") != session.isoformat():
            continue
        try:
            stamped = datetime.fromisoformat(str(row.get("as_of")).replace("Z", "+00:00"))
        except ValueError:
            continue
        local = stamped.astimezone(EASTERN)
        if local.date() == session and local.time() < REGULAR_OPEN:
            return row
    return None


# --------------------------------------------------------------------
# One session's work


@dataclass
class Fund:
    """What a session's runs have done for one fund."""

    report: dict[str, Any] | None = None  # in the page's form
    inputs: dict[str, Any] | None = None  # what the generator read for it
    sha256: str | None = None
    kept: bool = False
    applied: set[str] = field(default_factory=set)
    done: bool = False


@dataclass
class Morning:
    """One session's work, carried from one try to the next."""

    session: date
    funds: dict[str, Fund] = field(default_factory=dict)

    def fund(self, symbol: str) -> Fund:
        return self.funds.setdefault(symbol, Fund())


def _summary(report: dict[str, Any]) -> str:
    tomorrow = (report.get("horizons") or {}).get("tomorrow") or {}
    summary = tomorrow.get("summary") or {}
    q = summary.get("quantiles_pct") or {}
    median, low, high = summary.get("median_pct"), q.get("p05"), q.get("p95")
    if None in (median, low, high):
        return ""
    return f"; 1-day median {median:+.2f}%, 90% band {low:+.2f}% to {high:+.2f}%"


def run_fund(
    morning: Morning,
    symbol: str,
    web: Web,
    *,
    engine: str,
    now: datetime,
    make: Make = generator.generate,
    apply: bool = True,
    dry_run: bool = False,
    skip_made: bool = True,
    report: Report = _say,
) -> bool:
    """One try for one fund. True when its morning is finished -- done, or
    given up for a reason another try would not change."""
    fund = morning.fund(symbol)
    if fund.done:
        return True
    session = morning.session

    if fund.report is None:
        if skip_made and not dry_run:
            try:
                earlier = made_this_morning(web.sessions(symbol), session)
            except WebError as exc:
                report(f"{symbol}: could not read the forecast database: {exc.detail}")
                return not exc.retryable
            if earlier is not None:
                report(
                    f"{symbol}: a report for {session} was already made this morning "
                    f"(as_of {earlier.get('as_of')}); left as it is"
                )
                fund.done = True
                return True
        try:
            made = make(symbol, engine, now=now, progress=lambda m: report(f"{symbol}: {m}"))
        except generator.ForecastRefused as exc:
            report(f"{symbol}: refused: {exc}")
            return False
        except Exception as exc:  # a provider outage, a model failure: tried again
            report(f"{symbol}: failed: {type(exc).__name__}: {str(exc)[:300]}")
            return False
        page = as_the_page_sends(made.report)
        audit = parse_report(page)
        if not audit.ok or audit.report is None:
            errors = "; ".join(f"{f.where}: {f.message}" for f in audit.errors[:5])
            report(f"{symbol}: the report fails the audit, so it is not kept: {errors}")
            return False
        if audit.report.session != session:
            report(f"{symbol}: the report is for {audit.report.session}, not {session}; not kept")
            fund.done = True
            return True
        fund.report, fund.sha256 = page, audit.report.sha256
        fund.inputs = {
            "snapshot": made.snapshot,
            "diagnostics": made.diagnostics,
            "sources": made.sources,
        }
        report(f"{symbol}: made {fund.sha256[:12]} for {session}{_summary(page)}")

    if dry_run:
        report(f"{symbol}: dry run: neither kept nor applied")
        fund.done = True
        return True

    if not fund.kept:
        try:
            try:
                kept = web.keep(fund.report, fund.inputs)
            except WebError as exc:
                # The report matters more than what is shown beside it.
                if exc.status != 422 or fund.inputs is None:
                    raise
                report(f"{symbol}: its inputs were refused ({exc.detail}); keeping it without")
                fund.inputs = None
                kept = web.keep(fund.report)
        except WebError as exc:
            report(f"{symbol}: could not keep the report: {exc.detail}")
            if not exc.retryable:
                fund.done = True
            return fund.done
        fund.kept = True
        report(
            f"{symbol}: kept {kept.get('sha256', fund.sha256)[:12]} in the forecast database"
            f"{'' if kept.get('new', True) else ' (already there)'}"
        )

    if not apply:
        fund.done = True
        return True
    try:
        targets = paper_takers(web.deployments(), symbol)
    except WebError as exc:
        report(f"{symbol}: could not list the deployments: {exc.detail}")
        if not exc.retryable:
            fund.done = True
        return fund.done
    if not targets:
        report(f"{symbol}: no paper deployment that takes its reports is up; applied nowhere")
    pending = False
    for deployment in targets:
        if deployment in fund.applied:
            continue
        key = f"forecast:{deployment}:{fund.sha256[:48]}"[:100]
        model = str(fund.report.get("model") or "").split(" (")[0] or "the generator"
        try:
            queued = web.apply(
                deployment, fund.report, key, f"This morning's risk report ({model})"
            )
        except WebError as exc:
            report(f"{symbol}: could not apply it to {deployment}: {exc.detail}")
            if exc.retryable:
                pending = True
            else:
                fund.applied.add(deployment)  # the server's answer: not asked again
            continue
        fund.applied.add(deployment)
        command = (queued or {}).get("command") or {}
        warning = (queued or {}).get("warning")
        report(
            f"{symbol}: applied to {deployment} (command {command.get('id')}, "
            f"{command.get('status', 'queued')}{'' if (queued or {}).get('new', True) else ', already queued'})"
            + (f"; {warning}" if warning else "")
        )
    if not pending:
        fund.done = True
    return fund.done


def run_morning(
    morning: Morning,
    symbols: Iterable[str],
    web: Web,
    *,
    engine: str,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
    make: Make = generator.generate,
    apply: bool = True,
    dry_run: bool = False,
    skip_made: bool = True,
    report: Report = _say,
) -> bool:
    """One try for every fund; True when every fund's morning is finished."""
    finished = True
    for symbol in symbols:
        finished &= run_fund(
            morning,
            symbol,
            web,
            engine=engine,
            now=now(),
            make=make,
            apply=apply,
            dry_run=dry_run,
            skip_made=skip_made,
            report=report,
        )
    return finished


# --------------------------------------------------------------------
# The schedule


def next_morning(now: datetime, times: Iterable[clock_time]) -> datetime:
    """The first of `times` (Eastern) after `now` on a session day."""
    local = now.astimezone(EASTERN)
    ordered = sorted(times)
    day = local.date()
    while True:
        if is_session(day):
            for at in ordered:
                candidate = datetime.combine(day, at, tzinfo=EASTERN)
                if candidate > local:
                    return candidate
        day += timedelta(days=1)


def in_window(now: datetime, times: Iterable[clock_time]) -> bool:
    """Whether `now` is inside a session morning's window: from the first
    run time to LAST_TRY. A start then runs at once."""
    local = now.astimezone(EASTERN)
    return is_session(local.date()) and min(times) <= local.time() <= LAST_TRY


def run_daily(
    times: list[clock_time],
    attempt: Callable[[Morning], bool],
    *,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
    sleep: Callable[[float], None] = time.sleep,
    report: Report = _say,
    rounds: int | None = None,
) -> None:
    """At each of `times` on every session day, and again every
    RETRY_MINUTES until LAST_TRY while the morning is unfinished (module
    docstring). `rounds` ends the loop after that many tries (tests)."""
    due = now() if in_window(now(), times) else next_morning(now(), times)
    mornings: dict[date, Morning] = {}
    tries = 0
    while rounds is None or tries < rounds:
        wait = (due - now()).total_seconds()
        if wait > 0:
            report(f"next run {due.astimezone(EASTERN):%a %Y-%m-%d %H:%M %Z}")
            sleep(wait)
        session = due.astimezone(EASTERN).date()
        morning = mornings.setdefault(session, Morning(session))
        for old in [day for day in mornings if day < session]:
            del mornings[old]
        report(f"{now().astimezone(EASTERN):%Y-%m-%d %H:%M %Z} -- the report for {session}")
        finished = attempt(morning)
        tries += 1
        # Every RETRY_MINUTES from when the try was due, however long it took.
        retry = max(due + timedelta(minutes=RETRY_MINUTES), now())
        last = datetime.combine(session, LAST_TRY, tzinfo=EASTERN)
        if finished:
            due = next_morning(now(), times)
        elif retry <= last:
            report(f"not finished; trying again at {retry.astimezone(EASTERN):%H:%M %Z}")
            due = retry
        else:
            report(
                f"not finished by {LAST_TRY:%H:%M} ET; the {session} session goes without "
                "this service's report -- make one on the Forecast tab"
            )
            due = next_morning(now(), times)


# --------------------------------------------------------------------
# The command line


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--daily",
        nargs="*",
        metavar="HH:MM",
        help=f"each session morning at these Eastern times (default: {' '.join(DEFAULT_TIMES)})",
    )
    parser.add_argument(
        "--symbols",
        nargs="+",
        help="the funds (default: VAI_FORECAST_SYMBOLS, else " + " ".join(DEFAULT_SYMBOLS) + ")",
    )
    parser.add_argument(
        "--engine",
        choices=generator.engines.ENGINES,
        default=None,
        help="chronos (Chronos-2) or bootstrap (the historical baseline); "
        "default VAI_FORECAST_ENGINE, else chronos",
    )
    parser.add_argument(
        "--web",
        default=None,
        help=f"the web server (default: VAI_WEB_URL, else {DEFAULT_WEB})",
    )
    parser.add_argument("--no-apply", action="store_true", help="keep the report, apply it nowhere")
    parser.add_argument(
        "--dry-run", action="store_true", help="make and audit the report; keep and apply nothing"
    )
    return parser


def _symbols(given: list[str] | None) -> list[str]:
    raw = given or os.environ.get("VAI_FORECAST_SYMBOLS", "").replace(",", " ").split()
    symbols = [s.strip().upper() for s in raw if s.strip()] or list(DEFAULT_SYMBOLS)
    bad = [s for s in symbols if not generator.SYMBOL.match(s)]
    if bad:
        raise SystemExit(f"not market symbols: {', '.join(bad)}")
    return symbols


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    symbols = _symbols(args.symbols)
    engine = args.engine or os.environ.get("VAI_FORECAST_ENGINE", "").strip() or "chronos"
    if engine not in generator.engines.ENGINES:
        parser.error(f"VAI_FORECAST_ENGINE must be one of {', '.join(generator.engines.ENGINES)}")
    base = args.web or os.environ.get("VAI_WEB_URL", "").strip() or DEFAULT_WEB
    web = Web(urllib_send(base))
    if engine == "chronos":
        available, detail = generator.engines.chronos_available()
        _say(f"Chronos-2: {detail}" if available else f"Chronos-2 is NOT available: {detail}")
    _say(
        f"{' '.join(symbols)} with {engine}, through {base}"
        + (" (dry run)" if args.dry_run else " (keep only)" if args.no_apply else "")
    )

    def attempt(morning: Morning, *, skip_made: bool = True) -> bool:
        return run_morning(
            morning,
            symbols,
            web,
            engine=engine,
            apply=not args.no_apply,
            dry_run=args.dry_run,
            skip_made=skip_made,
        )

    if args.daily is None:
        # Once, now, for whichever session a report made now is for: an
        # explicit run, so a report made earlier this morning does not stop it.
        session, why_not = generator.window_check(datetime.now(UTC))
        if session is None:
            _say(f"no report can be made now: {why_not}")
            return 1
        return 0 if attempt(Morning(session), skip_made=False) else 1

    try:
        times = [datetime.strptime(t, "%H:%M").time() for t in (args.daily or DEFAULT_TIMES)]
    except ValueError:
        parser.error(f"--daily wants HH:MM times, got {args.daily!r}")
    if any(t >= LAST_TRY for t in times):
        parser.error(f"--daily times must be before {LAST_TRY:%H:%M} ET, the last try")

    def stop(signum, frame):  # PID 1 in a container: SIGTERM has no default action
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, stop)
    run_daily(times, attempt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
