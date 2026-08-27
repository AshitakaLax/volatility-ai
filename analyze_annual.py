"""Year-by-year performance of the best configurations, against TQQQ
buy-and-hold on the same data.

WHY THIS EXISTS. The headline comparison over the full 10.63-year
dataset is brutal and also misleading: the best configuration returns
10.64% CAGR against buy-and-hold's 39.15%, but that window contains the
strongest Nasdaq decade on record, which is the single worst regime for
a strategy that caps its upside at a fixed profit target. A grid/harvest
strategy is built for CHOP, and a whole-period CAGR cannot show whether
it delivers in the years it was designed for.

Annual returns separate the two. If the design works, it should beat
buy-and-hold in sideways and mildly-corrective years and lose badly in
strong trending ones. That is a testable claim, and the whole-period
number cannot test it.

Reads the top configuration out of each sweep's output CSV rather than
hardcoding parameters, so it cannot drift from what was actually
measured. Equity curves are extracted and the SimulationResult dropped
immediately -- a 430k-trade blotter is not needed here and is the
difference between this running comfortably and exhausting memory.
"""

import argparse
import glob
import inspect
import logging

import pandas as pd

from optimization_controller import OptimizationController, _run_one_combination
from src.cost_models import DynamicSlippageModel
from src.risk_manager import RiskManager
from src.strategy_registry import resolve_strategy

logging.disable(logging.WARNING)

# Two DIFFERENT questions, which must not share one constant.
#
# _METRIC_COLS is "what is an outcome rather than an input". Everything
# else identifies a configuration, so this is what deduplication uses.
#
# Grid Step and Profit Target are emphatically inputs -- they are axes
# of every sweep -- they simply are not STRATEGY CONSTRUCTOR arguments,
# because _run_one_combination takes them as separate positionals.
# Folding them into _METRIC_COLS made dedup blind to them, which
# collapsed configurations differing only in step/target into one row
# and silently discarded the best result ever measured (192.91%) in
# favour of a 174.71% one.
_METRIC_COLS = {
    "Strategy",
    "Final Equity",
    "Total Return %",
    "Realized PnL",
    "Trade Count",
    "Closed Trade Count",
    "Open Trade Count",
    "Capital Velocity Index",
    "Max Drawdown %",
    "Return/Drawdown",
    "error",
}

def _constructor_params(strategy_class, row):
    """Strategy kwargs for `row`, by ASKING the constructor what it takes.

    Deliberately not a denylist. This started as "everything except the
    metric columns", which failed twice for the same reason: adding
    "Grid Step"/"Profit Target" to that set made deduplication blind to
    them, and later a new "CAGR %" metric leaked straight through into
    the constructor. Every new metric was one more string somebody had
    to remember to add to a list.

    An allowlist taken from the signature cannot go stale. A new metric
    is excluded automatically because the constructor does not accept
    it, and a RENAMED strategy parameter shows up as a missing kwarg
    rather than being silently dropped.
    """
    accepted = set(inspect.signature(strategy_class.__init__).parameters) - {"self"}
    params = {k: row[k] for k in row.index if k in accepted and pd.notna(row[k])}
    for int_key in ("bars_per_day",):
        if int_key in params:
            params[int_key] = int(params[int_key])
    return params


def _top_configs(cap: float | None, limit: int):
    """Best rows across every sweep output, deduplicated by parameters."""
    frames = []
    for path in glob.glob("output/*.csv"):
        df = pd.read_csv(path)
        if "Total Return %" not in df.columns:
            continue
        frames.append(df[df["Total Return %"].notna()])
    if not frames:
        raise SystemExit("no sweep output found in output/")
    allrows = pd.concat(frames, ignore_index=True)
    if cap is not None:
        allrows = allrows[allrows["Max Drawdown %"] <= cap]
    axes = [c for c in allrows.columns if c not in _METRIC_COLS]
    allrows = allrows.drop_duplicates(subset=axes)
    return allrows.nlargest(limit, "Total Return %")


def _annual(series: pd.Series) -> pd.Series:
    """Calendar-year percentage returns from an equity or price series.

    The first year is measured from the series' own start rather than
    from a prior year that does not exist, so a partial first year is
    reported honestly instead of as NaN.

    Written plainly on purpose. The first version of this reindexed a
    concatenated shifted series and produced badly misaligned results --
    it reported TQQQ down 37% in 2023, a year it roughly tripled. A
    year-over-year return is one shift; anything more elaborate is a
    place for an off-by-one to hide.
    """
    yearly = series.resample("YE").last()
    prev = yearly.shift(1)
    prev.iloc[0] = series.iloc[0]
    return ((yearly / prev) - 1.0) * 100.0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/TQQQ_1Min_sip_all_2016-01-01_2026-08-21.csv")
    parser.add_argument("--cap", type=float, default=None, help="only consider maxDD <= this")
    parser.add_argument("--top", type=int, default=3)
    args = parser.parse_args()

    df = pd.read_csv(args.data, parse_dates=["timestamp"]).set_index("timestamp")
    controller = OptimizationController(historical_data=df)

    benchmark = _annual(df["close"])
    print(f"\n{'=' * 78}\nTQQQ BUY-AND-HOLD, annual\n{'=' * 78}")
    for year, value in benchmark.items():
        print(f"  {year.year}  {value:+9.2f}%")

    for rank, (_, row) in enumerate(_top_configs(args.cap, args.top).iterrows(), start=1):
        strategy_class = resolve_strategy("hf_local_reference")
        params = _constructor_params(strategy_class, row)
        result_row, sim = _run_one_combination(
            controller,
            float(row["Grid Step"]),
            float(row["Profit Target"]),
            strategy_class,
            params,
            "TQQQ",
            100_000.0,
            DynamicSlippageModel(base_bps=0.5, vol_multiplier=0.3, commission_per_trade=0.0),
            RiskManager(max_concurrent_lots=6000),
            "stale_reference",
            "intrabar",
            "sell_first",
            True,
        )
        if sim is None:
            print(f"\n#{rank} FAILED: {result_row.get('error')}")
            continue
        equity = sim.equity_curve.copy()
        metrics = dict(sim.metrics)
        del sim  # drop the blotter before the next iteration

        strat = _annual(equity)
        print(f"\n{'=' * 78}")
        print(
            f"#{rank}  total {metrics['Total Return %']:.2f}%  "
            f"maxDD {metrics['Max Drawdown %']:.2f}%  trades {metrics['Trade Count']:,.0f}"
        )
        print("     " + "  ".join(f"{k}={v}" for k, v in sorted(params.items())))
        print(f"{'=' * 78}")
        print(f"  {'year':<6} {'strategy':>10} {'TQQQ B&H':>10} {'diff':>10}")
        for year in strat.index:
            bench = benchmark.get(year, float("nan"))
            print(
                f"  {year.year:<6} {strat[year]:>9.2f}% {bench:>9.2f}% "
                f"{strat[year] - bench:>9.2f}%"
            )
        wins = sum(
            1 for y in strat.index if pd.notna(benchmark.get(y)) and strat[y] > benchmark[y]
        )
        print(f"  strategy beat buy-and-hold in {wins} of {len(strat)} calendar years")
        _by_regime(equity, df["close"])


def _by_regime(equity: pd.Series, price: pd.Series) -> None:
    """Strategy vs buy-and-hold bucketed by what the MARKET did.

    Calendar years are a crude proxy for regime. None of the eleven in
    this dataset is a clean flat-and-choppy market -- 2018, the closest,
    was three rising quarters followed by a Q4 crash -- so a year-by-year
    table cannot answer "does this design earn its keep in a sideways
    market with frequent small corrections", which is the actual claim a
    grid/harvest strategy makes for itself.

    Monthly buckets, keyed on the benchmark's own return, can. The
    SIDEWAYS bucket (-3% to +3%) is the one that matters: if the design
    works as intended, that is where it should beat holding. If it loses
    there too, the strategy is not a volatility harvester regardless of
    what the whole-period number says.
    """
    strat_m = equity.resample("ME").last().pct_change().dropna() * 100
    bench_m = price.resample("ME").last().pct_change().dropna() * 100
    joined = pd.DataFrame({"strategy": strat_m, "benchmark": bench_m}).dropna()

    buckets = [
        ("crash      (< -15%)", joined["benchmark"] < -15),
        ("down       (-15..-3%)", (joined["benchmark"] >= -15) & (joined["benchmark"] < -3)),
        ("SIDEWAYS   (-3..+3%)", (joined["benchmark"] >= -3) & (joined["benchmark"] <= 3)),
        ("up         (+3..+15%)", (joined["benchmark"] > 3) & (joined["benchmark"] <= 15)),
        ("rally      (> +15%)", joined["benchmark"] > 15),
    ]
    print()
    print("  --- monthly returns bucketed by what the MARKET did ---")
    print(f"  {'regime':<24}{'n':>4}{'strategy':>11}{'TQQQ B&H':>11}{'diff':>10}{'win rate':>10}")
    for label, mask in buckets:
        sub = joined[mask]
        if sub.empty:
            continue
        win = (sub["strategy"] > sub["benchmark"]).mean() * 100
        print(
            f"  {label:<24}{len(sub):>4}{sub['strategy'].mean():>10.2f}%"
            f"{sub['benchmark'].mean():>10.2f}%"
            f"{sub['strategy'].mean() - sub['benchmark'].mean():>9.2f}%{win:>9.0f}%"
        )


if __name__ == "__main__":
    main()
