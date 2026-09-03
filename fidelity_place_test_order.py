#!/usr/bin/env python
"""
Place ONE real order at Fidelity, to prove the adapter works end to end.

THIS SCRIPT SPENDS REAL MONEY. Everything else in this project either
simulates, previews, or reads. This submits.

--------------------------------------------------------------------
WHAT IT DOES, IN ORDER

  1. Attaches to a browser YOU are already logged into, over CDP.
     Fidelity refuses a Playwright-launched browser, so there is no
     other path -- and this one reads no credentials at all.
  2. Quotes the symbol.
  3. Computes a limit price deliberately FAR FROM THE MARKET, so the
     order rests unfilled.
  4. Shows you exactly what it will send, and waits for you to type the
     confirmation phrase.
  5. Previews (mints a confNum), journals that confNum to disk, then
     places.
  6. Reads the order back out of the venue's own order list.

Default is a BUY LIMIT 20% BELOW the market on CWH. At roughly $20 a
share that is about $16 of exposure on one share, resting, with
effectively no chance of filling -- which is the point. Proving the
order LANDS is the objective; having it EXECUTE is a separate decision
and a separate risk.

--------------------------------------------------------------------
WHY A RESTING LIMIT AND NOT A MARKET ORDER

A market order would fill, and then you own something and have to sell
it -- two more real trades, in a cash account with T+1 settlement, to
learn nothing the resting order does not already tell you. The whole
question here is whether placeOrder round-trips a confNum that shows up
in transactions/pending. A resting order answers that and can be
cancelled at will.

--------------------------------------------------------------------
RECOVERY

Every confNum is journalled BEFORE the order is committed, so a timeout
is recoverable rather than ambiguous. If this script dies mid-place, run
it again with --check-only: it re-reads the journal, asks the venue what
it actually has, and names any order that never landed. Do not resubmit
before doing that.

Usage:
    # 1. start a debuggable browser and log into Fidelity BY HAND
    & "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe" \\
        --remote-debugging-port=9222 --user-data-dir="C:\\Users\\%USERNAME%\\edge-debug-profile"

    # 2. see what it would do -- places nothing
    python fidelity_place_test_order.py --account <number> --dry-run

    # 3. actually place it
    python fidelity_place_test_order.py --account <number> \\
        --i-understand-this-places-a-real-order

    # after any failure, before doing anything else
    python fidelity_place_test_order.py --account <number> --check-only
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.exceptions import ConfigurationError
from src.fidelity_broker import FidelityBroker
from src.fidelity_placing_broker import (
    FidelityPlacingBroker,
    FileConfNumJournal,
    unresolved_orders,
)
from src.fidelity_session import FidelitySession, FidelitySessionError

CONFIRM_PHRASE = "PLACE THE ORDER"
DEFAULT_JOURNAL = Path.home() / ".fidelity_recon" / "placed_orders.jsonl"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Place one real Fidelity order to validate the adapter.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--account", required=True, help="Full account number, exact.")
    parser.add_argument("--symbol", default="CWH", help="Ticker (default: CWH).")
    parser.add_argument(
        "--account-name",
        default="Traditional IRA",
        help="The account's display name, e.g. 'Traditional IRA'. Required by "
        "transactions/pending, which rejects an account filter missing it. "
        "Read it off your Fidelity account list if the default is wrong.",
    )
    parser.add_argument("--quantity", type=int, default=1, help="Shares (default: 1).")
    parser.add_argument(
        "--limit-discount",
        type=float,
        default=0.20,
        help="How far BELOW the quote to set the buy limit, as a fraction. "
        "Default 0.20 (20%% below), which rests unfilled. Lowering this "
        "toward 0 makes a fill more likely -- that is the risk dial.",
    )
    parser.add_argument(
        "--max-order-value",
        type=float,
        default=50.0,
        help="Hard per-order dollar ceiling (default: 50).",
    )
    parser.add_argument("--cdp-url", default="http://localhost:9222")
    parser.add_argument("--journal", default=str(DEFAULT_JOURNAL))
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Quote and show the ticket, then stop. Places nothing.",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Recovery path: reconcile the journal against the venue and exit.",
    )
    parser.add_argument(
        "--cancel",
        metavar="CONFNUM",
        help="Cancel a working order by confNum and exit. Needs the same "
        "acknowledgement flag as placing -- cancelling is state-changing and "
        "sits behind the same transport gate -- but NOT the typed phrase, "
        "which guards against placing an order you did not mean to place. "
        "There is no equivalent hazard in withdrawing one.",
    )
    parser.add_argument(
        "--i-understand-this-places-a-real-order",
        dest="confirmed",
        action="store_true",
        help="Required to place. Without it the script refuses.",
    )
    return parser.parse_args(argv)


def attach(cdp_url: str):
    """Attach to the user's own browser and find a Fidelity page."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise ConfigurationError(
            f"playwright is not installed: {exc}\n    pip install -r requirements-fidelity.txt"
        ) from exc

    playwright = sync_playwright().start()
    try:
        browser = playwright.chromium.connect_over_cdp(cdp_url)
    except Exception as exc:
        playwright.stop()
        raise ConfigurationError(
            f"Could not attach to a browser at {cdp_url}: {exc}\n\n"
            "Start Edge with remote debugging FIRST, on a SEPARATE profile:\n"
            '    & "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe" '
            '--remote-debugging-port=9222 --user-data-dir="C:\\Users\\%USERNAME%'
            '\\edge-debug-profile"\n\n'
            "--user-data-dir is required: current Edge and Chrome refuse to enable "
            "remote debugging on the default profile."
        ) from exc

    pages = [page for context in browser.contexts for page in context.pages]
    if not pages:
        playwright.stop()
        raise ConfigurationError("Attached, but the browser has no open tabs.")
    fidelity = [p for p in pages if "fidelity.com" in (p.url or "")]
    if not fidelity:
        playwright.stop()
        raise ConfigurationError(
            "No Fidelity tab is open. Log into Fidelity in that browser first -- "
            "this script never sees your credentials and cannot log in for you."
        )
    return playwright, fidelity[0]


def _report(broker: FidelityBroker, journal: FileConfNumJournal) -> int:
    """The recovery path, also run after every place."""
    entries = journal.read_all()
    orders = {str(o.get("orderNum")): o for o in broker._orders()}
    print(f"\njournal: {len(entries)} recorded intent(s); venue reports {len(orders)} order(s)")
    for entry in entries:
        found = orders.get(entry["conf_num"])
        state = "NOT AT VENUE" if found is None else str(found.get("status"))
        print(
            f"  {entry['conf_num']:>10}  {entry.get('side', '?'):>4} "
            f"{entry.get('qty', '?')} {entry.get('symbol', '?'):<6} -> {state}"
        )
    missing = unresolved_orders(journal, broker)
    if missing:
        print(
            f"\n  {len(missing)} journalled order(s) the venue does not report.\n"
            "  Those never landed. Anything NOT listed here DID land, whatever the\n"
            "  submitting call appeared to do."
        )
    return 0


def main(argv=None) -> int:
    args = parse_args(argv)
    journal = FileConfNumJournal(args.journal)
    Path(args.journal).parent.mkdir(parents=True, exist_ok=True)

    playwright, page = attach(args.cdp_url)
    try:
        # allow_order_endpoints is granted ONLY when a real place is
        # intended. In every other mode the transport itself refuses
        # /placeOrder, so a bug below cannot submit.
        # A cancel needs the ORDER endpoints too -- cancelPlaceOrder sits in
        # PLACE_ENDPOINTS deliberately -- so the transport is unlocked for
        # either act, and for neither without the acknowledgement.
        placing = bool(args.confirmed and not args.dry_run and not args.check_only)
        cancelling = bool(args.cancel and args.confirmed and not args.dry_run)
        session = FidelitySession(
            page,
            allow_order_endpoints=placing or cancelling,
            allow_preview_endpoints=True,
        )
        session.attach()
        session.prime()
        session.wait_for_credentials(timeout_seconds=60)
        session.assert_authenticated()

        if args.check_only:
            return _report(
                FidelityBroker(
                    session, args.account, (args.account,), account_name=args.account_name
                ),
                journal,
            )

        if args.cancel:
            if not args.confirmed:
                print(
                    "\nRefusing to cancel without "
                    "--i-understand-this-places-a-real-order. Cancelling reaches the "
                    "same order endpoints as placing and deserves the same "
                    "deliberateness.",
                    file=sys.stderr,
                )
                return 2
            if args.dry_run:
                print(f"\n--dry-run: would cancel {args.cancel}. Nothing was sent.")
                return 0
            canceller = FidelityPlacingBroker(
                session,
                args.account,
                (args.account,),
                account_name=args.account_name,
                confirm_live_orders=True,
                allowed_symbols=(args.symbol,),
                max_order_value=args.max_order_value,
                journal=journal,
            )
            print(f"\nCancelling {args.cancel} ...")
            canceller.cancel(args.cancel)
            print("Cancel accepted. Reading the venue's order list back ...")
            return _report(canceller, journal)

        quote_broker = FidelityBroker(
            session, args.account, (args.account,), account_name=args.account_name
        )
        price = quote_broker.get_quote(args.symbol)
        limit = round(price * (1.0 - args.limit_discount), 2)
        value = limit * args.quantity

        print(
            f"\n{'=' * 66}\n"
            f"  symbol        {args.symbol}\n"
            f"  last          ${price:,.2f}\n"
            f"  side          BUY, LIMIT ${limit:,.2f} "
            f"({args.limit_discount:.0%} below the market)\n"
            f"  quantity      {args.quantity}\n"
            f"  exposure      ${value:,.2f}  (ceiling ${args.max_order_value:,.2f})\n"
            f"  account       ...{args.account[-4:]}\n"
            f"  journal       {args.journal}\n"
            f"  time in force DAY -- it expires at the close if never filled\n"
            f"{'=' * 66}"
        )

        if args.dry_run:
            print("\n--dry-run: nothing was sent. No preview, no order.")
            return 0
        if not args.confirmed:
            print(
                "\nRefusing to place without --i-understand-this-places-a-real-order.",
                file=sys.stderr,
            )
            return 2

        print(f'\nType exactly "{CONFIRM_PHRASE}" to submit, or anything else to abort.')
        if input("> ").strip() != CONFIRM_PHRASE:
            print("Aborted. Nothing was sent.")
            return 1

        broker = FidelityPlacingBroker(
            session,
            args.account,
            (args.account,),
            account_name=args.account_name,
            confirm_live_orders=True,
            allowed_symbols=(args.symbol,),
            max_order_value=args.max_order_value,
            journal=journal,
        )
        decision_id = f"testorder-{args.symbol}-{int(price * 100)}"
        order = broker.place(args.symbol, "buy", args.quantity, limit, decision_id)

        print(f"\nPLACED. confNum {order.id}, state {order.state}.")
        print("Reading it back out of the venue's own order list ...")
        _report(broker, journal)
        print(
            "\nIt is a DAY order resting well below the market, so it should expire\n"
            "at the close. Cancel it in the browser if you would rather not wait."
        )
        return 0
    finally:
        playwright.stop()


def _cli(argv=None) -> int:
    """Turn an expected failure into advice, not a traceback.

    The person running this is about to spend real money and may be
    doing it after something already went wrong. A stack trace ending in
    wait_for_credentials tells them nothing they can act on; "log in
    first" does. Unexpected exceptions still propagate in full -- those
    are bugs, and hiding them would be worse than ugly.
    """
    try:
        return main(argv)
    except FidelitySessionError as exc:
        print(f"\nNot an authenticated Fidelity session: {exc}\n", file=sys.stderr)
        print(
            "  Log into Fidelity BY HAND in the debug browser, open a Fidelity\n"
            "  page, then re-run. This script never sees your credentials and\n"
            "  cannot log in for you.",
            file=sys.stderr,
        )
        return 3
    except ConfigurationError as exc:
        print(f"\n{exc}\n", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        # Ctrl-C before the confirmation prompt is the expected way to
        # back out, and must not look like a crash.
        print("\nInterrupted. Nothing was sent.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(_cli())
