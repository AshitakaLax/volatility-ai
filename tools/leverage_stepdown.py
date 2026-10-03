"""Leverage step-down: TQQQ while calm, QQQ while turbulent, one account.

    python -m tools.leverage_stepdown                      # causal (lag 1)
    python -m tools.leverage_stepdown --lag 0              # stage-harness reading, LOOKAHEAD
    python -m tools.leverage_stepdown --cash-yield 0       # no interest on idle cash

Three books on the same window, same costs, same champion parameters
(config/best_known_2026-08-24.yaml unless --config says otherwise):

  champion   hf_local_reference on TQQQ, always in.
  cash       the TQQQ sleeve alone: in while calm, liquidated to cash on
             the flip. plan.md's NATR policy, with the regime applied
             causally.
  stepdown   the TQQQ sleeve PLUS a QQQ sleeve that trades only while
             turbulent and liquidates on the flip back to calm.

stepdown minus cash is the question this tool exists to answer: is
holding one-times leverage through a correction worth more than holding
cash? Both are reported against TQQQ and QQQ buy-and-hold, by calendar
year, so 2018, 2020 and 2022 can be read directly.

--------------------------------------------------------------------
THE REGIME

research/strategies/natr_regime.calm_by_date on TQQQ's daily bars
(--regime-from qqq to use QQQ's), NATR period 10 / lookback 100 --
plan.md's best cell. lag 1 applies the flag computed at the close of D
to D+1. lag 0 reproduces how the stage harnesses applied it (same day,
lookahead -- see natr_regime's module docstring) and exists ONLY so the
gap between the two can be measured on your data. Do not select
parameters from a lag 0 run.

--------------------------------------------------------------------
THE QQQ SLEEVE'S GRID

"Step-down" here means the SAME grid in underlying terms at a third of
the exposure: step and target are divided by --qqq-scale (default 3, so
a QQQ lot triggers and exits on the same Nasdaq-100 move a TQQQ lot
would), and lots keep the SAME dollar size. --qqq-scale 1 keeps the raw
TQQQ step and target instead; --qqq-per-lot-pct changes lot size.

--------------------------------------------------------------------
THE STITCH, AND WHAT IT ASSUMES

The engine is single-symbol, so each sleeve runs alone with the full
initial cash, and the account is

    equity(t) = initial + PnL_tqqq_sleeve(t) + PnL_qqq_sleeve(t)

Additive is the right composition for THIS sizing: the champion buys a
fixed dollar lot (initial capital * per_lot_pct), not a fraction of
current equity, so a sleeve's trades do not depend on how much the
other sleeve made. The two books do not overlap in time -- they are
active on complementary sessions -- except for the one bar where one
liquidates and the other may begin buying.

What it does NOT capture: in one real account, the cash available to a
sleeve would be the account's, not that sleeve's own. Where a sleeve's
standalone run was cash- or lot-cap-constrained, the stitched account
could have been more or less constrained. Treat a result that depends
on that as unmeasured; a portfolio-level allocator in the engine is what
would remove the assumption.

--------------------------------------------------------------------
FILL MODEL

Defaults to fill_model=intrabar with execution.intrabar_fill=causal: a
resting limit fills at its price, or at the open when the bar opened
through it, and the level itself is computed from bars before the
current one (see ExecutionConfig.intrabar_fill).
The champion's recorded configuration is intrabar + "level", which books
at the order price even when the whole bar traded beyond it (measured:
125 of 183 champion buys booked above their bar's high on a synthetic
test). Pass --intrabar-fill level to reproduce that reading, or
--fill-model close for the close-fill model.

The window starts at the first session the regime covers (the warm-up
is ~250 sessions), and every curve is rebased there, the champion's
included, so all books are compared over the identical span.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.core.config import BacktestConfig
from research.optimization.optimization_controller import OptimizationController
from research.strategies.natr_regime import calm_by_date, count_flips, daily_bars
from research.strategies.regime_sleeve_sizing import RegimeSleeveSizing
from research.strategies.turbulence_regime import basket_closes
from research.strategies.turbulence_regime import calm_by_date as turbulence_calm_by_date

FOCUS_YEARS = (2018, 2020, 2022)


class SleeveFactory:
    """run_sweep takes "a callable that constructs a strategy" (see
    optimization_controller._strategy_name). Binding the regime here
    keeps a multi-thousand-entry dict out of strategy_params, which are
    copied into every result row."""

    def __init__(self, sleeve: str, regime: dict) -> None:
        self.sleeve = sleeve
        self.regime = regime
        self.__name__ = f"RegimeSleeve[{sleeve}]"

    def __call__(self, **params) -> RegimeSleeveSizing:
        return RegimeSleeveSizing(sleeve=self.sleeve, regime_by_date=self.regime, **params)


def run_book(
    frame,
    cfg,
    factory,
    symbol,
    step,
    target,
    params,
    cash_yield,
    fill_model=None,
    intrabar_fill=None,
):
    """One engine run; returns (equity curve, summary row)."""
    kwargs = cfg.to_run_sweep_kwargs(factory)
    kwargs.update(
        grid_steps=[step],
        profit_targets=[target],
        strategy_params_grid=[params],
        symbol=symbol,
        allow_signal_exit=True,
        return_full_results=True,
        search_strategy="grid",
    )
    if cash_yield is not None:
        kwargs["cash_yield_pct"] = cash_yield
    if fill_model is not None:
        kwargs["fill_model"] = fill_model
    if intrabar_fill is not None:
        kwargs["intrabar_fill"] = intrabar_fill
    summary, full = OptimizationController(historical_data=frame).run_sweep(**kwargs)
    if full[0] is None:
        raise SystemExit(f"{factory.__name__} on {symbol} failed: {summary.iloc[0].get('error')}")
    return full[0].equity_curve.astype(float), summary.iloc[0]


def stitch(initial: float, curves: list[pd.Series]) -> pd.Series:
    """initial + the sum of each curve's P&L, on the union of timestamps.
    Before a curve's first bar its P&L is zero; between its bars it
    holds its last value."""
    index = curves[0].index
    for curve in curves[1:]:
        index = index.union(curve.index)
    total = pd.Series(initial, index=index, dtype=float)
    for curve in curves:
        total += curve.reindex(index).ffill().fillna(initial) - initial
    return total


def summarize(curve: pd.Series, start) -> dict:
    """Metrics on `curve` from `start`, rebased to 1.0 there."""
    window = curve[curve.index >= start]
    rebased = window / window.iloc[0]
    years = (rebased.index[-1] - rebased.index[0]).days / 365.25
    final = float(rebased.iloc[-1])
    cagr = (final ** (1.0 / years) - 1.0) * 100.0 if years > 0 and final > 0 else float("nan")
    max_dd = float((1.0 - rebased / rebased.cummax()).max()) * 100.0
    year_end = rebased.groupby(rebased.index.year).last()
    annual = (year_end / year_end.shift(1, fill_value=1.0) - 1.0) * 100.0
    return {
        "total_return_pct": (final - 1.0) * 100.0,
        "cagr_pct": cagr,
        "max_dd_pct": max_dd,
        "cagr_over_dd": cagr / max_dd if max_dd > 0 else float("inf"),
        "worst_year_pct": float(annual.min()),
        "annual": annual,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--config", default="config/best_known_2026-08-24.yaml")
    p.add_argument("--tqqq", default="TQQQ", help="warehouse ticker for the leveraged sleeve")
    p.add_argument("--qqq", default="QQQ", help="warehouse ticker for the step-down sleeve")
    p.add_argument("--regime-from", choices=("tqqq", "qqq"), default="tqqq")
    p.add_argument("--period", type=int, default=10)
    p.add_argument("--lookback", type=int, default=100)
    p.add_argument("--lag", type=int, choices=(0, 1), default=1)
    p.add_argument(
        "--regime",
        choices=("natr", "turbulence"),
        default="natr",
        help="natr: NATR below its median (plan.md). turbulence: basket Mahalanobis "
        "distance below its trailing quantile (research/strategies/turbulence_regime.py)",
    )
    p.add_argument("--basket", nargs="+", default=["QQQ", "RSP", "TLT", "GLD"])
    p.add_argument("--turb-lookback", type=int, default=252)
    p.add_argument("--turb-quantile", type=float, default=0.9)
    p.add_argument("--turb-threshold-lookback", type=int, default=252)
    p.add_argument("--qqq-scale", type=float, default=3.0)
    p.add_argument("--qqq-per-lot-pct", type=float, default=None)
    p.add_argument(
        "--cash-yield",
        type=float,
        default=None,
        help="fixed annual cash yield (0 = none); default follows the config (None = historical)",
    )
    p.add_argument(
        "--fill-model",
        choices=("close", "intrabar"),
        default="intrabar",
        help="see module docstring",
    )
    p.add_argument(
        "--intrabar-fill",
        choices=("level", "open_or_level", "causal"),
        default="causal",
        help="level reproduces the champion's recorded booking; see module docstring",
    )
    p.add_argument("--out", default="output/stepdown")
    args = p.parse_args(argv)
    if args.qqq_scale <= 0:
        raise SystemExit("--qqq-scale must be > 0")

    from engine.warehouse.bars import load_frame

    cfg = BacktestConfig.from_yaml(args.config)
    if cfg.strategy.strategy_id != "hf_local_reference":
        raise SystemExit(f"{args.config} is not an hf_local_reference config")
    params = dict(cfg.strategy.strategy_params)
    if any(isinstance(v, list) for v in params.values()):
        raise SystemExit(f"{args.config} sweeps strategy params; pin one combination")
    step, target = cfg.grid.steps[0], cfg.grid.profit_targets[0]
    initial = cfg.backtest.initial_cash

    frames = {}
    for name in (args.tqqq, args.qqq):
        frames[name] = load_frame(name)
        if frames[name].empty:
            raise SystemExit(f"No warehouse data for {name!r}; ingest it first.")
    if args.regime == "natr":
        source = frames[args.tqqq if args.regime_from == "tqqq" else args.qqq]
        regime = calm_by_date(
            daily_bars(source), period=args.period, lookback=args.lookback, lag=args.lag
        )
        desc = f"NATR({args.period}) vs {args.lookback}-day median on {args.regime_from}"
    else:
        basket = {}
        for name in args.basket:
            basket[name] = frames[name] if name in frames else load_frame(name)
            if basket[name].empty:
                raise SystemExit(f"No warehouse data for basket member {name!r}; ingest it first.")
        regime = turbulence_calm_by_date(
            basket_closes(basket),
            lookback=args.turb_lookback,
            quantile=args.turb_quantile,
            threshold_lookback=args.turb_threshold_lookback,
            lag=args.lag,
        )
        source = frames[args.tqqq]
        desc = (
            f"turbulence({args.turb_lookback}d) below its {args.turb_quantile:g} quantile "
            f"over {args.turb_threshold_lookback}d, basket {'+'.join(args.basket)}"
        )
    start = pd.Timestamp(min(regime), tz=source.index.tz)
    calm_share = 100.0 * sum(regime.values()) / len(regime)
    label = "lag 1 (causal)" if args.lag == 1 else "lag 0 -- LOOKAHEAD, comparison only"
    print(f"Regime: {desc}, {label}")
    print(f"  {len(regime)} sessions from {start.date()}, {calm_share:.1f}% calm, ")
    print(f"  {count_flips(regime)} flips (each one liquidates whichever sleeve is leaving)")
    fill = args.fill_model + (f"/{args.intrabar_fill}" if args.fill_model == "intrabar" else "")
    print(f"  fill model: {fill}\n")

    qqq_params = dict(params)
    if args.qqq_per_lot_pct is not None:
        qqq_params["per_lot_pct"] = args.qqq_per_lot_pct

    runs = [
        ("champion", SleeveFactory("always", regime), args.tqqq, step, target, params),
        ("tqqq_calm", SleeveFactory("calm", regime), args.tqqq, step, target, params),
        (
            "qqq_turbulent",
            SleeveFactory("turbulent", regime),
            args.qqq,
            step / args.qqq_scale,
            target / args.qqq_scale,
            qqq_params,
        ),
    ]
    curves, rows = {}, {}
    for name, factory, symbol, s, t, prm in runs:
        print(f"[{name}] {symbol} step={s:.6g} target={t:.6g} ...", flush=True)
        curves[name], rows[name] = run_book(
            frames[symbol],
            cfg,
            factory,
            symbol,
            s,
            t,
            prm,
            args.cash_yield,
            args.fill_model,
            args.intrabar_fill,
        )

    books = {
        "champion": curves["champion"],
        "cash": curves["tqqq_calm"],
        "stepdown": stitch(initial, [curves["tqqq_calm"], curves["qqq_turbulent"]]),
        f"{args.tqqq} b&h": frames[args.tqqq]["close"].astype(float),
        f"{args.qqq} b&h": frames[args.qqq]["close"].astype(float),
    }
    stats = {name: summarize(curve, start) for name, curve in books.items()}

    print(
        f"\n{'=' * 78}\n{'book':<12} {'CAGR':>8} {'maxDD':>8} {'CAGR/DD':>8} {'worst yr':>9} {'total':>10}"
    )
    for name, st in stats.items():
        print(
            f"{name:<12} {st['cagr_pct']:>7.2f}% {st['max_dd_pct']:>7.2f}% "
            f"{st['cagr_over_dd']:>8.3f} {st['worst_year_pct']:>8.2f}% {st['total_return_pct']:>9.1f}%"
        )
    annual = pd.DataFrame({name: st["annual"] for name, st in stats.items()})
    print(f"\n{'=' * 78}\nCalendar-year returns (%), from {start.date()}:")
    print(annual.round(2).to_string())
    focus = [y for y in FOCUS_YEARS if y in annual.index]
    if focus:
        diff = annual.loc[focus, "stepdown"] - annual.loc[focus, "cash"]
        print(
            "\nstepdown minus cash in the correction years: "
            + ", ".join(f"{y} {d:+.2f}pp" for y, d in diff.items())
        )
    trades = {name: int(row.get("Trade Count", 0)) for name, row in rows.items()}
    print(f"\nTrade counts: {trades}")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    regime_tag = (
        f"natr_p{args.period}_lb{args.lookback}"
        if args.regime == "natr"
        else f"turb_lb{args.turb_lookback}_q{args.turb_quantile:g}"
    )
    tag = f"{regime_tag}_lag{args.lag}_s{args.qqq_scale:g}_{args.fill_model}"
    if args.fill_model == "intrabar":
        tag += f"_{args.intrabar_fill}"
    pd.DataFrame(
        {name: {k: v for k, v in st.items() if k != "annual"} for name, st in stats.items()}
    ).T.to_csv(out / f"summary_{tag}.csv")
    annual.to_csv(out / f"annual_{tag}.csv")
    print(f"Wrote {out}/summary_{tag}.csv and annual_{tag}.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
