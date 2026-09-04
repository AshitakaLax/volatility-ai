"""Verify a machine can actually run the live loop, BEFORE it trades.

Every check here exists because its failure mode is quiet. A fresh
deployment does not announce that it has no credentials, that its clock
source is unreachable, or that another host is already trading the same
account -- it starts, does nothing useful, and looks fine in a process
list. This turns each of those into a line of output before any money is
at risk.

Read-only and safe to run at any time: it places no orders, and every
broker call it makes is a GET.

    python tools/preflight.py --config config/paper_aggressive.yaml
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

PASS, FAIL, WARN = "PASS", "FAIL", "WARN"


class Report:
    def __init__(self) -> None:
        self.rows: list[tuple[str, str, str]] = []

    def add(self, status: str, name: str, detail: str = "") -> None:
        self.rows.append((status, name, detail))

    def render(self) -> int:
        width = max((len(n) for _, n, _ in self.rows), default=10)
        for status, name, detail in self.rows:
            mark = {PASS: "  ok  ", FAIL: " FAIL ", WARN: " warn "}[status]
            print(f"[{mark}] {name:<{width}}  {detail}")
        failures = sum(1 for s, _, _ in self.rows if s == FAIL)
        warnings = sum(1 for s, _, _ in self.rows if s == WARN)
        print()
        if failures:
            print(f"{failures} check(s) FAILED -- this machine is not ready to trade.")
        elif warnings:
            print(f"All checks passed, with {warnings} warning(s). Read them before starting.")
        else:
            print("All checks passed. This machine can run the loop.")
        return 1 if failures else 0


def check_python(report: Report) -> None:
    major, minor, patch = sys.version_info[:3]
    report.add(
        PASS if (major, minor) >= (3, 12) else FAIL,
        "python >= 3.12",
        f"{major}.{minor}.{patch}",
    )


def check_imports(report: Report) -> None:
    for module, why in (
        ("alpaca", "broker and market clock"),
        ("pandas", "bar handling"),
        ("yaml", "config loading"),
    ):
        try:
            __import__(module)
            report.add(PASS, f"import {module}", why)
        except ImportError as exc:
            report.add(FAIL, f"import {module}", f"{exc} -- pip install -r requirements.txt")


def check_config(report: Report, path: str):
    from src.config import BacktestConfig

    if not os.path.exists(path):
        report.add(FAIL, "config file", f"{path} does not exist")
        return None
    try:
        config = BacktestConfig.from_yaml(path)
        config.validate()
    except Exception as exc:
        report.add(FAIL, "config valid", f"{path}: {exc}")
        return None

    report.add(PASS, "config valid", path)
    live = config.live
    report.add(
        PASS if live.enabled else FAIL,
        "live.enabled",
        "true" if live.enabled else "false -- the loop refuses to construct",
    )
    report.add(
        PASS if live.paper_trading else WARN,
        "live.paper_trading",
        "paper" if live.paper_trading else "LIVE -- this trades real money",
    )
    report.add(PASS, "live grid", f"step={live.step} target={live.profit_target}")
    report.add(
        PASS,
        "live.extended_hours",
        "on, 04:00-20:00 ET" if getattr(live, "extended_hours", False) else "off, 09:30-16:00 ET",
    )
    return config


def check_credentials(report: Report) -> bool:
    """Presence and shape only. NEVER prints or logs a secret value."""
    from src.secrets import load_live_credentials

    try:
        creds = load_live_credentials()
    except Exception as exc:
        report.add(FAIL, "APCA credentials", f"{type(exc).__name__} -- set them in .env")
        return False
    key = creds.api_key_id
    report.add(
        PASS,
        "APCA credentials",
        f"key id ...{key[-4:]} ({len(key)} chars), secret present",
    )
    return True


def check_broker(report: Report, config) -> None:
    """One authenticated GET, proving the keys work and are the right kind."""
    from src.alpaca_broker import AlpacaBroker
    from src.secrets import load_live_credentials

    try:
        broker = AlpacaBroker(load_live_credentials(), paper=config.live.paper_trading)
        account = broker.trading_client.get_account()
    except Exception as exc:
        report.add(FAIL, "broker reachable", f"{type(exc).__name__}: {exc}")
        return

    report.add(
        PASS,
        "broker reachable",
        f"{account.status}, equity ${float(account.equity):,.2f}",
    )

    # PAPER AND LIVE ARE DIFFERENT KEYS AGAINST DIFFERENT HOSTS. Paper
    # keys in a live config authenticate perfectly well and then trade a
    # different account than the operator believes. Catching that here
    # beats discovering it from a fill.
    wants_paper = config.live.paper_trading
    number = str(getattr(account, "account_number", ""))
    looks_paper = number.startswith("PA")
    if wants_paper and not looks_paper:
        report.add(
            FAIL,
            "paper/live key match",
            "config says paper_trading=true but these keys are not a paper account",
        )
    elif not wants_paper and looks_paper:
        report.add(
            FAIL,
            "paper/live key match",
            "config says paper_trading=false but these are PAPER keys -- nothing "
            "you believe is happening would be",
        )
    else:
        report.add(PASS, "paper/live key match", "paper" if wants_paper else "live")

    try:
        clock = broker.trading_client.get_clock()
        report.add(
            PASS,
            "market clock",
            f"is_open={clock.is_open}, next open {clock.next_open:%Y-%m-%d %H:%M}",
        )
    except Exception as exc:
        report.add(FAIL, "market clock", f"{type(exc).__name__}: {exc}")


def check_extended_clock(report: Report, config) -> None:
    """The extended window reads the CALENDAR endpoint, not the clock,
    so it can fail independently of everything checked above."""
    if not getattr(config.live, "extended_hours", False):
        report.add(PASS, "extended clock", "not needed, extended_hours is off")
        return

    from alpaca.trading.client import TradingClient

    from src.alpaca_market_data import AlpacaMarketData
    from src.secrets import load_live_credentials

    creds = load_live_credentials()
    try:
        trading = TradingClient(
            creds.api_key_id, creds.api_secret_key, paper=config.live.paper_trading
        )
        market = AlpacaMarketData(creds, trading_client=trading)
        report.add(PASS, "extended clock", f"is_open_extended={market.is_open_extended()}")
    except Exception as exc:
        report.add(FAIL, "extended clock", f"{type(exc).__name__}: {exc}")


def check_market_data(report: Report, config) -> None:
    """The data feed is a SEPARATE entitlement from trading. sip without
    a subscription authenticates and then fails every bar request."""
    from alpaca.trading.client import TradingClient

    from src.alpaca_market_data import AlpacaMarketData
    from src.secrets import load_live_credentials

    creds = load_live_credentials()
    symbol = getattr(config.live, "symbol", None) or "TQQQ"
    try:
        trading = TradingClient(
            creds.api_key_id, creds.api_secret_key, paper=config.live.paper_trading
        )
        market = AlpacaMarketData(creds, trading_client=trading, feed=config.live.feed)
        bar = market.latest_bar(symbol)
        report.add(
            PASS,
            f"market data ({config.live.feed})",
            f"{symbol} last bar {bar.close:.2f} at {bar.timestamp:%Y-%m-%d %H:%M}",
        )
    except Exception as exc:
        report.add(
            FAIL,
            f"market data ({config.live.feed})",
            f"{type(exc).__name__}: {exc} -- sip needs a paid subscription; iex is free",
        )


def check_state_store(report: Report, db_path: str) -> None:
    parent = Path(db_path).resolve().parent
    if not parent.exists() or not os.access(parent, os.W_OK):
        report.add(FAIL, "state store", f"{parent} is missing or not writable")
        return
    if not os.path.exists(db_path):
        report.add(PASS, "state store", f"{db_path} not present yet -- will be created")
        return
    try:
        with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as conn:
            open_lots = conn.execute(
                "SELECT COUNT(*) FROM ledger_lots WHERE status = 'OPEN'"
            ).fetchone()[0]
        report.add(PASS, "state store", f"{db_path}, {open_lots} open lot(s)")
    except Exception as exc:
        report.add(WARN, "state store", f"{db_path} exists but did not read: {exc}")


def check_not_already_running(report: Report, db_path: str) -> None:
    """THE CHECK THAT MATTERS MOST ON A SECOND MACHINE.

    StateStoreLock is a FILE lock, so it only ever sees processes on THIS
    host. It cannot know that another machine is trading the same Alpaca
    account, and two loops on one account is not a degraded mode -- it is
    a ledger that diverges from the venue while both hosts believe they
    are authoritative.
    """
    from src.process_lock import LockHeldError, StateStoreLock

    try:
        StateStoreLock(db_path).acquire().release()
        report.add(PASS, "no local loop running", "the state-store lock is free")
    except LockHeldError as exc:
        report.add(FAIL, "no local loop running", str(exc))

    report.add(
        WARN,
        "no OTHER host trading",
        "NOT checkable from here -- the lock is per-machine. Confirm by hand that "
        "no other deployment points at this Alpaca account.",
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Check a machine before it trades.")
    parser.add_argument("--config", default="config/paper_aggressive.yaml")
    parser.add_argument("--state-db", default="paper_ledger.db")
    parser.add_argument(
        "--skip-network",
        action="store_true",
        help="Local checks only. Useful while provisioning, before keys exist.",
    )
    args = parser.parse_args(argv)

    report = Report()
    check_python(report)
    check_imports(report)
    config = check_config(report, args.config)
    if config is not None and not args.skip_network and check_credentials(report):
        check_broker(report, config)
        check_extended_clock(report, config)
        check_market_data(report, config)
    check_state_store(report, args.state_db)
    check_not_already_running(report, args.state_db)
    return report.render()


if __name__ == "__main__":
    sys.exit(main())
