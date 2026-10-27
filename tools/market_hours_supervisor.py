#!/usr/bin/env python
"""
Run the live loop for one trading session, then exit.

    python tools/market_hours_supervisor.py --config config/paper_aggressive.yaml

--------------------------------------------------------------------
WHY THIS ASKS THE BROKER RATHER THAN READING A CLOCK

The obvious design is a scheduled task at 09:30 and a stop at 16:00.
It is wrong roughly ten days a year and twice more on the DST
boundaries:

  * The market closes for holidays -- and half-days at 13:00 around
    Thanksgiving, Christmas and Independence Day. A fixed schedule
    trades on none of them correctly.
  * Market hours are EASTERN. This machine is not, so a local-time
    trigger drifts by an hour twice a year, in opposite directions,
    because US DST changes do not align with everywhere else's.

Alpaca's clock endpoint already knows all of that. So the schedule is
"start this early each weekday" and every real decision -- is today a
trading day, when does it open, when does it close -- is asked of the
broker at run time. A holiday simply produces "not a trading day" and
an immediate exit.

--------------------------------------------------------------------
WHY IT BOUNDS THE RUN WITH --max-ticks INSTEAD OF KILLING IT

cli.py handles SIGTERM/SIGINT by finishing the current tick and
shutting down through the ordinary path. Windows cannot deliver either
to a detached process: taskkill without /F does not reach a console
app, and terminate() is a hard kill that can land midway through
applying a confirmed fill.

So the session length is computed up front and passed as --max-ticks.
The loop then stops itself, gracefully, with no signal involved. The
CTRL_BREAK path exists as well (see _stop) for the case where this
supervisor is interrupted mid-session, but the normal exit needs it.

--------------------------------------------------------------------
RESTARTS ARE BOUNDED, AND A CRASH LOOP IS NOT HIDDEN

If the loop exits before the close it is restarted, because a transient
network failure at 10:03 should not cost the rest of the day. But a
process that keeps dying is a fault to surface, not to paper over, so
restarts are capped and the cap is reported.

A start that could not reach the broker is not a crash: cli.py exits with
EXIT_BROKER_UNAVAILABLE when startup stopped on something that clears by
itself -- the browser extension not connected yet, Fidelity signed out, the
bridge's port taken by a run started by hand. Those are retried every
BROKER_RETRY_SECONDS until the session ends, not counted, and the wait
reports the trader's own reason ("waiting_for_broker") -- on 10-22 and 10-23
five fast failures spent the cap, the page said "between sessions", and the
reason was only in the container's log.

--------------------------------------------------------------------
A FIDELITY SESSION STARTS ONLY WHEN THE BRIDGE SAYS IT IS READY

A Fidelity deployment's bridge runs as a host of its own
(fidelity_gateway/bridge/host.py, the fidelity-bridge service), up between
sessions, and writes whether the connection is ready -- the extension
connected, Fidelity signed in, "Allow trading" on -- into its control
directory (bridge/status.json). With VAI_BRIDGE_SOCKET set, this waits on that
verdict before launching the loop ("waiting_for_broker", detail: the one thing
to fix) and launches the moment it turns ready, rather than launching a loop
that can only fail.

--------------------------------------------------------------------
ON THE VENUE'S OWN WINDOWS (live.sessions)

A deployment that names its windows -- Fidelity's pre-market 07:00-09:28 ET,
the regular session, after-hours to 20:00 -- runs on them (_main_sessions,
engine/core/venue_sessions.py): the engine starts live.engine_lead_minutes
before the first window it trades and runs until the last one ends. It is
launched without the bridge gate above: the loop readies its engine first
(history replayed, said on the Live page) and waits for the broker itself,
in its own process (cli.py's engine-first start), so whether the engine is
ready and whether Fidelity is are two answers known before 07:00.

Each restart re-runs startup, which means reconciliation runs again --
which is the point. A loop that died and came back has more reason to
check its state against the broker, not less.
"""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
from datetime import UTC, datetime, timedelta
from functools import partial
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from engine.core.config import BacktestConfig
from engine.trading.control_inbox import ControlInbox
from engine.trading.operator_control import (
    STARTUP_ALLOWANCE_SECONDS,
    SupervisorControl,
    account_fingerprint,
    account_tag,
    reset_paper_ledger_handler,
)
from engine.trading.runtime_lifecycle import EXIT_BROKER_UNAVAILABLE

# Start trading a little after the bell. The first minutes of the
# session are the most volatile of the day (src/intraday_profile.py
# measures the open at 2.56x the session average), and a strategy whose
# grid is sized off recent volatility has no recent volatility yet.
DEFAULT_OPEN_DELAY = 60.0
# Stop before the close so the final tick completes inside the session
# rather than racing it.
DEFAULT_CLOSE_MARGIN = 120.0
MAX_RESTARTS = 5
# How long to wait before trying again after a start that could not reach the
# broker (EXIT_BROKER_UNAVAILABLE): the extension not connected yet, Fidelity
# signed out, the bridge's port taken. Not a crash, so not counted against
# MAX_RESTARTS -- it is tried until the session ends, and says why meanwhile.
BROKER_RETRY_SECONDS = 60.0


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Run the live loop for one session.")
    p.add_argument("--config", required=True)
    p.add_argument("--state-db", default="paper_ledger.db")
    p.add_argument("--open-delay", type=float, default=DEFAULT_OPEN_DELAY)
    p.add_argument("--close-margin", type=float, default=DEFAULT_CLOSE_MARGIN)
    p.add_argument(
        "--extended-hours",
        action="store_true",
        help="Run the pre-market and after-hours sessions too (04:00-20:00 ET). "
        "Implied by live.extended_hours in the config; this flag only forces it on.",
    )
    p.add_argument("--max-restarts", type=int, default=MAX_RESTARTS)
    p.add_argument(
        "--max-wait-hours",
        type=float,
        default=18.0,
        help="Give up waiting for an open rather than sleeping indefinitely.",
    )
    p.add_argument("--dry-run", action="store_true", help="Report the plan and exit.")
    p.add_argument(
        "--control-dir",
        default=os.environ.get("VAI_CONTROL_DIR"),
        help="This deployment's control directory: the Live page's commands "
        "(engine/trading/control_inbox.py). Defaults to $VAI_CONTROL_DIR; without "
        "one, nothing can pause, disable or switch this deployment from the page.",
    )
    p.add_argument(
        "--linger",
        type=float,
        default=0.0,
        help="Seconds to keep answering the Live page's commands after the session "
        "(or on a day with none) before exiting: the wait between sessions.",
    )
    return p.parse_args(argv)


def log(message: str) -> None:
    """Timestamped and flushed. A supervisor whose output is buffered
    tells you nothing while it is the thing you are debugging."""
    print(f"[{datetime.now(UTC):%Y-%m-%d %H:%M:%S}Z] {message}", flush=True)


def clock(paper: bool):
    from alpaca.trading.client import TradingClient

    key, secret = os.environ.get("APCA_API_KEY_ID"), os.environ.get("APCA_API_SECRET_KEY")
    if not (key and secret):
        raise SystemExit("APCA_API_KEY_ID / APCA_API_SECRET_KEY are not set.")
    return TradingClient(key, secret, paper=paper).get_clock()


def broker_book(paper: bool) -> dict:
    """The Alpaca account's open positions and orders and its cash -- what a
    fresh paper ledger must agree with (the Live page's reset)."""
    from alpaca.trading.client import TradingClient
    from alpaca.trading.enums import QueryOrderStatus
    from alpaca.trading.requests import GetOrdersRequest

    key, secret = os.environ.get("APCA_API_KEY_ID"), os.environ.get("APCA_API_SECRET_KEY")
    if not (key and secret):
        raise RuntimeError("APCA_API_KEY_ID / APCA_API_SECRET_KEY are not set.")
    client = TradingClient(key, secret, paper=paper)
    return {
        "positions": len(client.get_all_positions()),
        "open_orders": len(
            client.get_orders(filter=GetOrdersRequest(status=QueryOrderStatus.OPEN))
        ),
        "cash": float(client.get_account().cash),
    }


def extended_window(paper: bool):
    """(start, end) of today's EXTENDED session, in the clock's own tz.

    Alpaca's clock answers for the regular session only -- is_open,
    next_open and next_close all ignore pre- and post-market -- so a
    supervisor that trusts it sleeps through precisely the hours
    live.extended_hours was turned on for.

    The window is derived from the CALENDAR, which keeps holidays
    authoritative: a day the calendar does not list has no extended
    session either. [04:00 ET, close + 4h] is correct on normal and
    half days alike, because after-hours ends four hours after whatever
    close the calendar reports (16:00 -> 20:00, 13:00 -> 17:00).
    """
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import GetCalendarRequest

    key, secret = os.environ.get("APCA_API_KEY_ID"), os.environ.get("APCA_API_SECRET_KEY")
    if not (key and secret):
        raise SystemExit("APCA_API_KEY_ID / APCA_API_SECRET_KEY are not set.")
    client = TradingClient(key, secret, paper=paper)
    now = client.get_clock().timestamp
    today = now.date()
    for day in client.get_calendar(GetCalendarRequest(start=today, end=today)):
        day_date = day.date.date() if hasattr(day.date, "date") else day.date
        if day_date != today:
            continue
        start = now.replace(hour=4, minute=0, second=0, microsecond=0)
        end = now.replace(
            hour=day.close.hour, minute=day.close.minute, second=0, microsecond=0
        ) + timedelta(hours=4)
        return now, start, end
    return now, None, None


def _stop(process: subprocess.Popen) -> None:
    """Ask the loop to finish its tick, then insist.

    CTRL_BREAK_EVENT is the only graceful stop Windows can deliver to a
    detached process; cli.py handles it as SIGBREAK. Elsewhere SIGTERM
    does the same job. The kill is a backstop for a loop that has
    genuinely stopped responding, not the normal path.
    """
    if process.poll() is not None:
        return
    try:
        if os.name == "nt":
            process.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            process.terminate()
        process.wait(timeout=120)
        log("loop stopped cleanly")
    except (subprocess.TimeoutExpired, OSError, ValueError):
        log("loop did not stop within 120s -- killing it")
        process.kill()


def run_session(args, ticks: int, deadline: float, control=None) -> int:
    """Run the loop until it exits or the session deadline passes.

    While it runs, the LOOP answers the Live page's commands, between its
    ticks; this process does not touch the control directory meanwhile."""
    command = [
        sys.executable,
        "cli.py",
        "live",
        "--config",
        args.config,
        "--state-db",
        args.state_db,
        "--max-ticks",
        str(ticks),
    ]
    if args.control_dir:
        command += ["--control-dir", args.control_dir]
    if control is not None:
        control.report(
            "starting",
            "launching the trading loop",
            heartbeat_seconds=STARTUP_ALLOWANCE_SECONDS,
        )
    creation = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    log(f"starting: {' '.join(command[1:])}")
    process = subprocess.Popen(command, cwd=str(_REPO_ROOT), creationflags=creation)

    try:
        while process.poll() is None and time.time() < deadline:
            time.sleep(5.0)
        if process.poll() is None:
            log("session deadline reached")
            _stop(process)
            return 0
        return process.returncode or 0
    except KeyboardInterrupt:
        log("interrupted -- stopping the loop")
        _stop(process)
        raise


def _control_for(args) -> SupervisorControl | None:
    """The Live page's commands while no loop runs -- including algorithm
    switches, which write the override the next launch trades
    (research/strategies/live_algorithm.py), exactly as a loop would."""
    if not args.control_dir:
        return None
    inbox = ControlInbox(args.control_dir)
    extra = None
    account = account_fingerprint
    try:
        from research.strategies.live_algorithm import AlgorithmControl, algorithm_handlers
        from research.strategies.strategy_registry import STRATEGIES

        config = BacktestConfig.from_yaml(args.config)
        config.validate()
        # The account its status names, as the loop's does: a Fidelity
        # deployment's own, not the Alpaca key it reads prices with.
        account = partial(account_tag, config.live)
        grants = config.live.control.effective(config.live.paper_trading)
        algorithm = AlgorithmControl(
            config,
            state_db=args.state_db,
            registry=STRATEGIES,
            allowed=False,
            web_allowed=grants.algorithm_changes,
            profiles_only=grants.profiles_only,
            config_path=args.config,
            log=log,
        )
        extra = algorithm_handlers(
            algorithm, symbol=config.backtest.symbol, paper=config.live.paper_trading
        )
        extra["reset_paper_ledger"] = reset_paper_ledger_handler(
            inbox,
            state_db=args.state_db,
            paper=config.live.paper_trading,
            broker_book=lambda: broker_book(config.live.paper_trading),
        )
    except Exception as exc:
        # The session still runs; only the page's algorithm commands are
        # refused (as "cannot be applied by this trader") until it loads.
        log(f"algorithm commands unavailable: {type(exc).__name__}: {exc}")
    return SupervisorControl(inbox, state_db=args.state_db, extra=extra, account=account)


def _wait(control, seconds: float, *, state: str, detail: str = "", **fields) -> None:
    """Sleep -- answering the Live page's commands meanwhile, if there is a
    control directory, instead of being deaf for the whole wait."""
    if control is None:
        time.sleep(max(0.0, seconds))
        return
    control.serve(seconds, state=state, detail=detail, **fields)


def _hold_while_disabled(control, deadline: float) -> bool:
    """True to go ahead and trade; False if the deployment stayed disabled
    until `deadline` (the session's end)."""
    if control is None:
        return True
    control.poll()
    if control.enabled():
        return True
    log("disabled from the Live page -- holding until enabled or the session ends")
    return control.serve(
        deadline - time.time(),
        state="disabled",
        detail="no session starts until enabled",
        until=control.enabled,
    )


def _trader_detail(control) -> str | None:
    """What the trader that just exited said about why -- its status file's
    detail, written before it exited -- or None without a control directory."""
    if control is None:
        return None
    try:
        status = control.inbox.status() or {}
    except Exception:
        return None
    detail = status.get("detail")
    return detail if isinstance(detail, str) and detail else None


# A bridge host silent this long (and at least three of its own heartbeats)
# is called not running, as server/live.py calls a silent trader.
_BRIDGE_STALE_FLOOR_SECONDS = 90.0


def bridge_verdict(status: dict | None, now: float) -> tuple[bool, str]:
    """(ready, why) from a bridge host's status file: its readiness verdict
    (fidelity_gateway/bridge/readiness.py), or "not reporting"."""
    host_hint = (
        "the bridge host is not reporting -- is the fidelity-bridge service running? "
        "(docker compose --profile fidelity up -d fidelity-bridge)"
    )
    if not status:
        return False, host_hint
    try:
        age = now - datetime.fromisoformat(status["updated_at"]).timestamp()
    except (KeyError, TypeError, ValueError):
        return False, host_hint
    heartbeat = float(status.get("heartbeat_seconds") or 15.0)
    if age > max(3 * heartbeat, _BRIDGE_STALE_FLOOR_SECONDS) or status.get("state") == "stopped":
        return False, host_hint
    verdict = status.get("readiness") or {}
    if verdict.get("ready"):
        return True, "ready"
    summary = verdict.get("summary") or "not ready"
    fix = verdict.get("fix")
    return False, f"Fidelity is not ready: {summary}" + (f" -- {fix}" if fix else "")


def _broker_gate(args, config):
    """For a Fidelity deployment attached to a bridge host (VAI_BRIDGE_SOCKET),
    a callable answering bridge_verdict now; None otherwise -- a deployment
    that holds its own bridge, or an Alpaca one, starts when its session does."""
    if config.live.broker != "fidelity" or not os.environ.get("VAI_BRIDGE_SOCKET"):
        return None
    if not args.control_dir:
        return None
    inbox = ControlInbox(Path(args.control_dir) / "bridge")
    return lambda: bridge_verdict(inbox.status(), time.time())


def _hold_until_ready(control, deadline: float, gate) -> bool:
    """True once `gate` says ready (at once without one); False if it is
    still not ready at `deadline`, or the page disabled the deployment
    meanwhile (the caller holds for that). Answers the Live page as it waits,
    with the reason as the detail."""
    if gate is None:
        return True
    said = None
    while True:
        ready, why = gate()
        if ready:
            if said is not None:
                log("the broker is ready -- starting the session")
            return True
        if why != said:
            log(f"waiting to start: {why}")
            said = why
        left = deadline - time.time()
        if left <= 0:
            return False
        if control is None:
            time.sleep(min(15.0, left))
            continue
        control.serve(min(control.slice_seconds, left), state="waiting_for_broker", detail=why)
        if not control.enabled():
            return False


def _run_until(args, poll: float, deadline: float, control, label: str, gate=None) -> int:
    """Run the loop until `deadline`, restarting it if it dies -- but not
    counting a stop the Live page asked for as a crash: a disabled
    deployment waits to be enabled instead. With a `gate` (_broker_gate), a
    loop is launched only once the broker is ready."""
    attempts = 0
    while True:
        if not _hold_while_disabled(control, deadline):
            log(f"{label} over (disabled)")
            return 0
        if not _hold_until_ready(control, deadline, gate):
            if control is not None and not control.enabled():
                continue  # disabled while waiting: hold above
            log(f"{label} over (the broker was never ready)")
            return 0
        remaining = deadline - time.time()
        if remaining <= poll:
            log(f"{label} over")
            return 0
        code = run_session(args, max(1, int(remaining // poll)), deadline, control)
        remaining = deadline - time.time()
        if remaining <= poll:
            log(f"{label} over")
            return 0
        if control is not None and not control.enabled():
            continue  # the page disabled it (or it wound down): hold above
        if code == EXIT_BROKER_UNAVAILABLE:
            why = _trader_detail(control) or "the broker could not be reached"
            log(
                f"the broker could not be reached ({why}); trying again in "
                f"{BROKER_RETRY_SECONDS:.0f}s"
            )
            _wait(control, BROKER_RETRY_SECONDS, state="waiting_for_broker", detail=why)
            continue
        attempts += 1
        log(
            f"loop exited with {code} and {remaining / 60:.0f} min left "
            f"(attempt {attempts}/{args.max_restarts})"
        )
        if attempts >= args.max_restarts:
            log(
                f"{args.max_restarts} restarts in one session -- stopping rather than "
                "looping. Something is wrong that a restart is not fixing."
            )
            return 1
        _wait(control, 10.0, state="restarting", detail=f"the loop exited with {code}")


def _main_extended(args, config, poll: float) -> int:
    """Session control for the extended day, 04:00-20:00 ET.

    Deliberately a separate path rather than a few conditionals inside
    main(). The regular-hours logic reads the clock's own is_open /
    next_open / next_close, and none of those three mean anything here
    -- threading a flag through them would leave a function whose every
    line has to be read twice to know which session it is talking about.
    """
    now, start, end = extended_window(config.live.paper_trading)
    if start is None:
        log("not a trading day -- no extended session either. Exiting.")
        return 0

    if now < start:
        wait = (start - now).total_seconds()
        if wait > args.max_wait_hours * 3600:
            log(f"pre-market opens {start:%Y-%m-%d %H:%M} ET, too far off. Exiting.")
            return 0
        log(f"pre-market opens {start:%H:%M} ET ({wait / 60:.0f} min)")
        if args.dry_run:
            log("--dry-run: would wait, then trade the extended session.")
            return 0
        _wait(
            _control,
            wait + args.open_delay,
            state="waiting_for_open",
            detail=f"pre-market opens {start:%H:%M} ET",
            next_open=start.isoformat(),
        )
        now, start, end = extended_window(config.live.paper_trading)

    seconds_left = (end - now).total_seconds() - args.close_margin
    if seconds_left <= poll:
        log(f"only {seconds_left:.0f}s of extended session left. Exiting.")
        return 0

    ticks = max(1, int(seconds_left // poll))
    log(
        f"EXTENDED session {start:%H:%M}-{end:%H:%M} ET -- "
        f"{seconds_left / 60:.0f} min left, {ticks} ticks at {poll:.0f}s"
    )
    if args.dry_run:
        log("--dry-run: would run the loop now.")
        return 0

    return _run_until(
        args,
        poll,
        time.time() + seconds_left,
        _control,
        "extended session",
        gate=_broker_gate(args, config),
    )


def venue_calendar(config, trading_client=None):
    """The windows this deployment trades at its venue
    (engine/core/venue_sessions.py), with the real closes from Alpaca's
    calendar when there is a client to ask."""
    from engine.core.venue_sessions import VenueCalendar, default_close_for
    from engine.trading.session_clock import alpaca_close_for

    close_for = alpaca_close_for(trading_client) if trading_client is not None else None
    return VenueCalendar(
        config.live.broker, config.live.traded_sessions, close_for=close_for or default_close_for
    )


def _trading_client(paper: bool):
    from alpaca.trading.client import TradingClient

    key, secret = os.environ.get("APCA_API_KEY_ID"), os.environ.get("APCA_API_SECRET_KEY")
    if not (key and secret):
        raise SystemExit("APCA_API_KEY_ID / APCA_API_SECRET_KEY are not set.")
    return TradingClient(key, secret, paper=paper)


def _main_sessions(args, config, poll: float, calendar=None) -> int:
    """Session control on the venue's own windows (live.sessions).

    The engine starts live.engine_lead_minutes BEFORE the first window it
    trades -- 06:30 ET for Fidelity's 07:00 pre-market -- and runs until the
    last one ends. Starting early is the point: the engine replays its
    history and says it is ready on its own, before the broker is asked
    anything, so "is the engine ready" and "is Fidelity ready" are two
    answers known before the window opens, not one learned at it.

    No bridge gate here, unlike the other paths: the loop itself waits for
    the broker, ready and watching the market meanwhile (cli.py's engine-
    first start), rather than being launched only once the broker is ready.
    """
    calendar = calendar or venue_calendar(config, _trading_client(config.live.paper_trading))
    moment = datetime.fromtimestamp(time.time(), UTC)
    window = calendar.next_window(moment)
    if window is None:
        log(f"no {', '.join(calendar.sessions)} window in sight. Exiting.")
        return 0
    first, last = calendar.day_span(window.start.date())
    names = "+".join(calendar.sessions)
    launch = first - timedelta(minutes=float(config.live.engine_lead_minutes))
    if moment < launch:
        wait = (launch - moment).total_seconds()
        if wait > args.max_wait_hours * 3600:
            log(f"the next window opens {first:%Y-%m-%d %H:%M} ET, too far off. Exiting.")
            return 0
        log(
            f"the engine starts {launch:%H:%M} ET for {names} from {first:%H:%M} ET "
            f"({wait / 60:.0f} min)"
        )
        if args.dry_run:
            log("--dry-run: would wait, then start the engine.")
            return 0
        _wait(
            _control,
            wait,
            state="waiting_for_open",
            detail=f"the engine starts {launch:%H:%M} ET for the {first:%H:%M} ET {window.session}",
            next_open=first.isoformat(),
        )
        moment = datetime.fromtimestamp(time.time(), UTC)

    seconds_left = (last - moment).total_seconds() - args.close_margin
    if seconds_left <= poll:
        log(f"only {seconds_left:.0f}s of the trading day left. Exiting.")
        return 0
    ticks = max(1, int(seconds_left // poll))
    log(
        f"TRADING DAY on {config.live.broker}'s {names} windows, {first:%H:%M}-{last:%H:%M} ET -- "
        f"{seconds_left / 60:.0f} min left, {ticks} ticks at {poll:.0f}s"
    )
    if args.dry_run:
        log("--dry-run: would start the engine now.")
        return 0
    return _run_until(args, poll, time.time() + seconds_left, _control, "trading day")


def _interrupt(signum, _frame) -> None:
    """SIGTERM -- how `docker stop` (via tools/docker_session_loop.sh) and
    systemd ask for a stop -- takes the same path as Ctrl-C: run_session
    stops the trading loop gracefully, and a wait for the open just ends."""
    raise KeyboardInterrupt


# This run's control directory, if any: set by main() for the waits above.
_control: SupervisorControl | None = None


def main(argv=None) -> int:
    """One session (or none, on a day without one), then -- with --linger --
    the wait before the next, answering the Live page throughout."""
    global _control
    args = parse_args(argv)
    signal.signal(signal.SIGTERM, _interrupt)
    _control = _control_for(args)
    if _control is not None:
        _control.poll()  # commands queued while nothing was running
    code = _session(args)
    if args.linger > 0 and not args.dry_run:
        if _control is None:
            time.sleep(args.linger)
        else:
            _control.serve(
                args.linger,
                state="closed" if _control.enabled() else "disabled",
                detail="between sessions",
            )
    return code


def _session(args) -> int:
    config = BacktestConfig.from_yaml(args.config)
    config.validate()
    poll = float(config.live.poll_interval_seconds or 60.0)

    if config.live.venue_clock:
        return _main_sessions(args, config, poll)
    if args.extended_hours or getattr(config.live, "extended_hours", False):
        return _main_extended(args, config, poll)

    now = clock(config.live.paper_trading)
    if not now.is_open:
        wait = (now.next_open - now.timestamp).total_seconds()
        if wait > args.max_wait_hours * 3600:
            log(
                f"Next open is {now.next_open:%Y-%m-%d %H:%M} ET, more than "
                f"{args.max_wait_hours:.0f}h away -- not a trading day. Exiting; "
                "the scheduled task will try again tomorrow."
            )
            return 0
        log(f"market closed; opens {now.next_open:%Y-%m-%d %H:%M} ET ({wait / 60:.0f} min)")
        if args.dry_run:
            log("--dry-run: would wait, then trade until the close.")
            return 0
        _wait(
            _control,
            wait + args.open_delay,
            state="waiting_for_open",
            detail=f"opens {now.next_open:%Y-%m-%d %H:%M} ET",
            next_open=now.next_open.isoformat(),
        )
        now = clock(config.live.paper_trading)

    seconds_left = (now.next_close - now.timestamp).total_seconds() - args.close_margin
    if seconds_left <= poll:
        log(f"only {seconds_left:.0f}s of session left -- not worth starting. Exiting.")
        return 0

    ticks = max(1, int(seconds_left // poll))
    log(
        f"session open until {now.next_close:%H:%M} ET -- "
        f"{seconds_left / 60:.0f} min, {ticks} ticks at {poll:.0f}s"
    )
    if args.dry_run:
        log("--dry-run: would run the loop now.")
        return 0

    return _run_until(
        args, poll, time.time() + seconds_left, _control, "session", gate=_broker_gate(args, config)
    )


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        log("stopped")
        raise SystemExit(130) from None
