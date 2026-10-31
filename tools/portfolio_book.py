"""Run a multi-asset allocator over warehouse daily closes.

    python -m tools.portfolio_book --allocator inverse_volatility --universe QQQ RSP XLP USMV GLD
    python -m tools.portfolio_book --allocator cross_sectional_momentum --preset sectors \\
        --param k=3 --param lookback=252 --param skip=21          # RK19
    python -m tools.portfolio_book --allocator state_filtered_momentum --preset sectors \\
        --market SPY                                                # RK10
    python -m tools.portfolio_book --allocator dividend_yield --universe SPYD SCHD VYM DGRO \\
        --dividends data/dividends.csv                              # RK52

Allocators: research/strategies/allocators.py (ALLOCATORS). The book:
research/strategies/portfolio_book.py -- weights from closes before each
session, traded at its close, every sale through the no-loss guard
(--allow-loss makes rebalancing sales signal exits instead). A backtest
only: the engine trades one symbol per deployment (engine/roadmap.md).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.execution.cost_models import SlippageCommissionModel
from research.strategies.allocators import ALLOCATORS, SECTOR_ETFS
from research.strategies.natr_regime import daily_bars
from research.strategies.portfolio_book import run_portfolio

PRESETS = {"sectors": list(SECTOR_ETFS)}


def _value(text: str):
    for cast in (int, float):
        try:
            return cast(text)
        except ValueError:
            pass
    return {"true": True, "false": False}.get(text.lower(), text)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--allocator", choices=sorted(ALLOCATORS), required=True)
    p.add_argument("--universe", nargs="+", default=[])
    p.add_argument("--preset", choices=sorted(PRESETS))
    p.add_argument(
        "--market", help="market column for state_filtered_momentum (added to the universe)"
    )
    p.add_argument("--dividends", help="CSV of ticker, ex_date, amount (dividend_yield)")
    p.add_argument("--param", action="append", default=[], help="allocator keyword, name=value")
    p.add_argument("--rebalance", default="monthly", help="monthly | weekly | every N sessions")
    p.add_argument("--min-history", type=int, default=253)
    p.add_argument("--initial-cash", type=float, default=100_000.0)
    p.add_argument("--cash-yield", type=float, default=0.0)
    p.add_argument("--slippage-bps", type=float, default=2.0)
    p.add_argument("--allow-loss", action="store_true", help="rebalancing sales may realise a loss")
    p.add_argument("--out", default="output/portfolio_book")
    args = p.parse_args(argv)

    names = list(dict.fromkeys([*PRESETS.get(args.preset, []), *args.universe]))
    kwargs = dict(item.split("=", 1) for item in args.param)
    kwargs = {k: _value(v) for k, v in kwargs.items()}
    if args.allocator == "state_filtered_momentum":
        if not args.market:
            raise SystemExit("state_filtered_momentum needs --market")
        names.append(args.market)
        kwargs["market"] = args.market
    if args.allocator == "dividend_yield":
        if not args.dividends:
            raise SystemExit("dividend_yield needs --dividends")
        kwargs["dividends"] = pd.read_csv(args.dividends)
    if len(names) < 2:
        raise SystemExit("give two or more instruments (--universe or --preset)")

    from engine.warehouse.bars import load_frame

    closes = {}
    for name in dict.fromkeys(names):
        frame = load_frame(name)
        if frame.empty:
            raise SystemExit(f"No warehouse data for {name!r}; ingest it first.")
        closes[name] = daily_bars(frame)["close"]
    table = pd.DataFrame(closes).dropna(how="any")
    rebalance = int(args.rebalance) if args.rebalance.isdigit() else args.rebalance
    result = run_portfolio(
        table,
        ALLOCATORS[args.allocator],
        rebalance=rebalance,
        min_history=args.min_history,
        initial_cash=args.initial_cash,
        cost_model=SlippageCommissionModel(slippage_bps=args.slippage_bps),
        cash_yield=args.cash_yield,
        no_loss=not args.allow_loss,
        allocator_kwargs=kwargs,
    )
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    stem = f"{args.allocator}_{'-'.join(names)}"
    result.equity.to_csv(out / f"{stem}_equity.csv")
    result.weights.to_csv(out / f"{stem}_weights.csv")
    result.trades.to_csv(out / f"{stem}_trades.csv", index=False)
    print(json.dumps({"allocator": args.allocator, "universe": names, **result.metrics}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
