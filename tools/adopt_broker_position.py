#!/usr/bin/env python
"""
Write an existing broker position into the local ledger, so startup can
reconcile instead of halting.

--------------------------------------------------------------------
WHY THIS NEEDS A DELIBERATE ACT

RuntimeLifecycle halts at RECONCILIATION_REQUIRED when the broker holds
a position the local store has no lot for. That refusal is the point of
that layer: it will not run a strategy against a book it does not
understand, and it says "a human must resolve it" rather than importing
silently.

So importing is possible, and it is a decision -- not something startup
should ever do on its own. This script is that decision, written down.

--------------------------------------------------------------------
WHAT IS REAL HERE AND WHAT IS A CHOICE

REAL: the cost basis. Alpaca reports avg_entry_price for the position,
so the lot's buy_price is a fact about what was paid, not a guess. That
matters more than it sounds: enforce_no_loss evaluates every exit
against buy_price, so an invented basis would put the guard to work
defending a number nobody paid.

A CHOICE: the profit target. The position was not opened by this
strategy, so it has no target of its own. Taking it from the config
being adopted into is the only defensible option -- any other number
would be this script inventing a trading decision.

STATED CONSEQUENCE: with the champion config's 30% target and a $72.31
basis, the adopted lot's exit sits at $94.00. It will hold until then.
enforce_no_loss already floors any exit at the basis regardless, so the
target choice only decides how far ABOVE $72.31 the lot waits.

--------------------------------------------------------------------
IT ADOPTS, IT DOES NOT TRADE

No order is placed, cancelled or modified. The only mutation is a row
in the local ledger describing something the broker already holds.

Usage:
    python tools/adopt_broker_position.py --config config/paper_aggressive.yaml \\
        --state-db paper_ledger.db --i-understand-this-writes-a-local-lot
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.config import BacktestConfig
from src.ledger import AssetLotLedger
from src.persistence import LedgerStore


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Adopt a broker position into the ledger.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--state-db", required=True)
    parser.add_argument("--symbol", default=None, help="Defaults to backtest.symbol.")
    parser.add_argument(
        "--i-understand-this-writes-a-local-lot",
        dest="confirmed",
        action="store_true",
        help="Required. Without it this reports what it WOULD do and exits.",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    config = BacktestConfig.from_yaml(args.config)
    config.validate()
    symbol = args.symbol or config.backtest.symbol
    target = config.live.profit_target
    if target is None:
        print("config has no live.profit_target; nothing to adopt into.", file=sys.stderr)
        return 2

    try:
        from alpaca.trading.client import TradingClient
    except ImportError as exc:
        print(f"alpaca-py is required: {exc}", file=sys.stderr)
        return 2

    key, secret = os.environ.get("APCA_API_KEY_ID"), os.environ.get("APCA_API_SECRET_KEY")
    if not (key and secret):
        print("APCA_API_KEY_ID / APCA_API_SECRET_KEY are not set.", file=sys.stderr)
        return 2

    client = TradingClient(key, secret, paper=config.live.paper_trading)
    position = next((p for p in client.get_all_positions() if p.symbol == symbol), None)
    if position is None:
        print(f"The broker holds no {symbol} position. Nothing to adopt.")
        return 0

    shares = float(position.qty)
    basis = float(position.avg_entry_price)
    exit_price = basis * (1.0 + target)

    print(f"  symbol        {symbol}")
    print(f"  shares        {shares:,.6f}          (from the broker)")
    print(f"  cost basis    ${basis:,.4f}          (broker's avg_entry_price -- a FACT)")
    print(f"  profit target {target:.1%}              (from {args.config} -- a CHOICE)")
    print(f"  exits at      ${exit_price:,.4f}")
    print(f"  no-loss floor ${basis:,.4f}          (enforce_no_loss, regardless of target)")

    store = LedgerStore(args.state_db)
    try:
        existing = [lot for lot in store.load_ledger().open_lots if lot.symbol == symbol]
        if existing:
            print(
                f"\nThe ledger already has {len(existing)} open {symbol} lot(s). "
                "Refusing to adopt on top of them -- that would double-count the "
                "position against the broker's single holding.",
                file=sys.stderr,
            )
            return 1

        if not args.confirmed:
            print("\nDRY RUN. Pass --i-understand-this-writes-a-local-lot to write it.")
            return 0

        ledger = AssetLotLedger()
        lot = ledger.register_buy(
            f"adopted-{symbol}-{int(basis * 10000)}", symbol, basis, shares, target
        )
        store.record_open_lot(lot)
        print(f"\nAdopted as lot {lot.order_id!r} at revision {store.current_revision()}.")
        return 0
    finally:
        store.close()


if __name__ == "__main__":
    raise SystemExit(main())
