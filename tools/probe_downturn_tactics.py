#!/usr/bin/env python
"""
TQQQ only: which tactic actually makes money THROUGH a drawdown?

--------------------------------------------------------------------
WHY THIS IS NOT ANOTHER 2022 STUDY

Every downturn result in this project so far rests on 2022, and that
n=1 has been the standing caveat on all of it. It turns out to be
avoidable. TQQQ put in FOURTEEN distinct peak-to-trough drawdowns of
20% or worse between 2016 and 2026, ranging from -21% to -81.7%:

    2016-01  -34.1%     2018-08  -58.8%     2021-04  -21.2%
    2016-04  -23.0%     2020-02  -69.9%     2021-09  -21.8%
    2018-01  -28.5%     2020-09  -35.4%     2021-11  -81.7%
    2018-03  -29.4%     2021-02  -30.5%     2024-12  -58.0%
                                            2025-10  -37.0%
                                            2026-06  -33.6% (open)

So a tactic can be scored on how it does across fourteen independent
episodes rather than on how it did in one year. That is the whole point
of this tool. A tactic that wins on the average of fourteen but loses
in nine of them is a tactic that got lucky in the deep ones, and the
per-episode table is printed for exactly that reason.

(It also settles a loose end: the "unexplained" 37.0% intra-year
drawdown in 2025 is the 2025-10-30 episode, which runs into 2026.)

--------------------------------------------------------------------
HOW AN EPISODE IS DEFINED

From each running peak in the daily closes, a drawdown reaching 20%
opens an episode. It ends when price regains the peak, or at the end of
the data if it never does. Episodes are non-overlapping: the scan
resumes at the recovery, so a wobble on the way back up is part of the
episode it belongs to rather than a new one.

Each episode is simulated INDEPENDENTLY, starting flat with the same
cash. That is the right shape for the question "if I am at a peak and
it falls apart, what should I be doing", and it deliberately does not
compound episodes together -- chaining them would smuggle in the
between-episode bull runs, which is what the whole rest of the project
already measures.

--------------------------------------------------------------------
WHAT IS COMPARED

  hold        buy the peak, hold to the end of the window.

              READ THIS COLUMN CAREFULLY. A closed episode ends WHEN
              PRICE REGAINS THE PEAK, so hold is close to 0% there by
              construction, not by merit -- the small positives are just
              the overshoot on the day of recovery. It is informative in
              exactly one row: the still-open 2026 episode, where it
              prints -16.6% because there has been no recovery to end
              the window. Do not read "hold median +1.5%" as a finding.

              Kept anyway, because it makes the actual question sharp:
              given that a round trip costs a holder nothing, how much
              can be EARNED crossing it? That is the volatility-harvest
              thesis stated as a measurement.

  grid        the ordinary grid, no escalation.
  dip         deep steps with log-linear escalation on the UNDERLYING's
              drawdown -- the "buy deep spikes, sell small rebounds"
              shape.
  noesc       the same step/target with escalation OFF (max_mult 1.0).
              The control that separates "the escalation is working"
              from "the step and target are working", which the first
              run of this tool could not distinguish.

Every run charges the config's cost model and honours enforce_no_loss.
No signal exits: this is a question about entries during a decline, and
adding a second new mechanism would confound it.

Usage:
    python tools/probe_downturn_tactics.py
    python tools/probe_downturn_tactics.py --min-depth 0.30
"""

from __future__ import annotations

import argparse
import os as _os
import sys as _sys

_REPO_ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _REPO_ROOT not in _sys.path:
    _sys.path.insert(0, _REPO_ROOT)

import logging

import pandas as pd

from optimization_controller import OptimizationController
from src.config import BacktestConfig
from src.risk_manager import RiskManager
from tools.harness import Escalating

DATA = "data/TQQQ_1Min_sip_all_2016-01-01_2026-08-21.csv"


# Escalating now lives in tools/harness.py -- ONE definition. Three
# independent copies of it lived in this directory, verified equivalent
# but each a chance to diverge silently, which would have made two
# probes' results look comparable while not being so.
def find_episodes(daily: pd.Series, min_depth: float) -> list[dict]:
    """Non-overlapping peak -> trough -> recovery drawdown episodes.

    Written as an explicit forward scan rather than anything clever with
    cummax masks. An episode is a stateful notion -- it has a start, an
    extreme, and an end condition -- and vectorising it is how off-by-one
    errors get in. The whole scan is ~2,700 daily points.
    """
    values = daily.values
    index = daily.index
    episodes: list[dict] = []
    i, n = 0, len(values)
    while i < n:
        peak_i = i
        peak = values[i]
        j = i + 1
        while j < n and values[j] < peak:
            j += 1
            if j < n and values[j] > peak:
                break
        # Walk forward from this peak until price regains it, tracking
        # the trough on the way.
        j = peak_i + 1
        trough_i = peak_i
        while j < n and values[j] < peak:
            if values[j] < values[trough_i]:
                trough_i = j
            j += 1
        depth = 1.0 - values[trough_i] / peak
        if depth >= min_depth:
            episodes.append(
                {
                    "peak_ts": index[peak_i],
                    "trough_ts": index[trough_i],
                    "end_ts": index[j] if j < n else index[-1],
                    "depth": depth,
                    "recovered": j < n,
                }
            )
            i = j if j < n else n
        else:
            i = peak_i + 1
    return episodes


def slice_minutes(frame: pd.DataFrame, start, end) -> pd.DataFrame:
    lo = pd.Timestamp(start).normalize()
    hi = pd.Timestamp(end).normalize() + pd.Timedelta(days=1)
    return frame.loc[(frame.index >= lo) & (frame.index < hi)]


def run_tactic(window: pd.DataFrame, cfg, *, step, target, per_lot, cap, max_mult) -> float:
    """Percent return over one episode window, starting flat."""
    controller = OptimizationController(historical_data=window)
    params = dict(cfg.strategy.strategy_params)
    params.update(per_lot_pct=per_lot, max_mult=max_mult, dd_ref=0.75)
    summary = controller.run_sweep(
        grid_steps=[step],
        profit_targets=[target],
        strategy_class=Escalating,
        strategy_params_grid=[params],
        cost_model=cfg.costs.build(),
        risk_manager=RiskManager(max_concurrent_lots=6000, max_total_exposure_pct=cap),
        fill_model="intrabar",
        intrabar_priority="sell_first",
        enforce_no_loss=True,
        on_flat_reentry="stale_reference",
    )
    return float(summary.iloc[0]["Total Return %"])


# The first run compared five shapes across all fourteen episodes and
# found dip .05/.02 alone at 14/14 positive with a median worth having
# (+3.3%); dip .10/.04 was also 14/14 but earned almost nothing outside
# the three deepest episodes. So this set probes the neighbourhood of
# .05/.02 and adds the escalation control.
# Step is settled: .05 beat both .03 (which went -2.5% in the open 2026
# episode, 13/14) and .07 (14/14 but only a +1.0% median) on the
# previous run. Target showed a clean monotone trend -- .01 -> .02 ->
# .03 gave medians of +1.7 -> +3.3 -> +4.6 -- so this run asks whether
# it keeps climbing or turns over. That is the difference between .03
# being an optimum and being merely the edge of the range I tried.
TACTICS = (
    # label,            step,  target, per_lot, cap,  max_mult
    ("dip .05/.02", 0.05, 0.020, 0.02, 0.50, 400.0),
    ("dip .05/.03", 0.05, 0.030, 0.02, 0.50, 400.0),
    ("dip .05/.04", 0.05, 0.040, 0.02, 0.50, 400.0),
    ("dip .05/.06", 0.05, 0.060, 0.02, 0.50, 400.0),
    ("noesc .05/.04", 0.05, 0.040, 0.02, 0.50, 1.0),
    ("dip .05/.04 c1.0", 0.05, 0.040, 0.02, 1.00, 400.0),
)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="TQQQ tactics across every drawdown episode.")
    parser.add_argument("--min-depth", type=float, default=0.20)
    parser.add_argument("--quiet", action="store_true", default=True)
    args = parser.parse_args(argv)
    if args.quiet:
        logging.disable(logging.WARNING)

    cfg = BacktestConfig.from_yaml("config/probe_dipbuy_full.yaml")
    frame = pd.read_csv(DATA, parse_dates=["timestamp"]).set_index("timestamp")
    daily = frame["close"].resample("D").last().dropna()
    episodes = find_episodes(daily, args.min_depth)

    print(f"TQQQ drawdown episodes of {args.min_depth:.0%} or worse: {len(episodes)}")
    print("Each simulated independently, starting flat. 'hold' buys the peak.\n")

    header = f"{'episode':>21} {'depth':>7} {'days':>5} {'hold':>9}"
    for label, *_ in TACTICS:
        header += f" {label:>16}"
    print(header)

    totals = {label: [] for label, *_ in TACTICS}
    hold_all = []
    spans: list[int] = []
    for ep in episodes:
        window = slice_minutes(frame, ep["peak_ts"], ep["end_ts"])
        if len(window) < 400:  # under about one session of bars
            continue
        first = float(window["close"].iloc[0])
        last = float(window["close"].iloc[-1])
        hold = (last / first - 1.0) * 100.0
        hold_all.append(hold)
        spans.append(max(1, (ep["end_ts"] - ep["peak_ts"]).days))

        row = (
            f"{ep['peak_ts'].date()!s:>11}->{ep['end_ts'].date()!s:>9} "
            f"{ep['depth'] * 100:6.1f}% {(ep['end_ts'] - ep['peak_ts']).days:5d} "
            f"{hold:+8.1f}%"
        )
        for label, step, target, per_lot, cap, max_mult in TACTICS:
            value = run_tactic(
                window, cfg, step=step, target=target, per_lot=per_lot, cap=cap, max_mult=max_mult
            )
            totals[label].append(value)
            row += f" {value:+15.1f}%"
        print(row + ("" if ep["recovered"] else "   (open)"))

    banner = f"{'':>21} {'':>7} {'':>5} {'hold':>9}" + "".join(
        f" {label:>16}" for label, *_ in TACTICS
    )
    print()
    print(banner)
    _summary("median", hold_all, totals, lambda v: pd.Series(v).median())
    _summary("worst", hold_all, totals, min)
    _summary("# positive", hold_all, totals, lambda v: sum(1 for x in v if x > 0))
    # Episode windows run from 42 to 1,111 days, so a median of raw
    # episode returns silently rewards the long ones. Annualising each
    # episode first removes that. It turns out to change the ranking in
    # exactly one place -- .05/.06 passes .05/.04 (+18.3% vs +16.3%)
    # because its wins come in shorter windows -- so both rows are
    # printed rather than picking whichever tells a better story. Note
    # .05/.06 is still the one that loses an episode.
    _summary("median ann.", hold_all, totals, lambda v: pd.Series(_annualize(v, spans)).median())

    # CHRONOLOGICAL SPLIT. Every parameter above was chosen by looking at
    # these same episodes, across three passes -- which is exactly how an
    # in-sample optimum gets mistaken for an edge. This project has paid
    # for that once already (config/search_hf_volume_sweep.yaml).
    #
    # Splitting the episodes in time is the cheapest guard available: a
    # tactic whose ranking survives 2016-2021 AND 2021-2026 separately is
    # at least not an artifact of one regime. It is NOT a true
    # out-of-sample test -- I had already seen both halves when choosing
    # the parameters -- so it is a consistency check, not a validation,
    # and it is labelled that way on purpose.
    half = len(hold_all) // 2
    for name, lo, hi in (
        (f"FIRST HALF (2016-2021), episodes 1-{half}", 0, half),
        (f"SECOND HALF (2021-2026), episodes {half + 1}-{len(hold_all)}", half, len(hold_all)),
    ):
        print()
        print(name)
        print(banner)
        sub = {k: v[lo:hi] for k, v in totals.items()}
        _summary("median", hold_all[lo:hi], sub, lambda v: pd.Series(v).median())
        _summary("worst", hold_all[lo:hi], sub, min)
        _summary("# positive", hold_all[lo:hi], sub, lambda v: sum(1 for x in v if x > 0))

    print("\nRead the '# positive' row before the median. A tactic that wins on")
    print("the median while losing in most episodes made its money in the deep")
    print("ones, and there are only three of those in eleven years.")
    return 0


def _annualize(values, spans):
    """Each episode's return restated as an annual rate.

    Not a claim that the tactic runs continuously at this rate -- these
    windows are drawdowns, which do not repeat back to back. It is the
    only way to compare a 42-day episode with a 1,111-day one without
    the long one winning purely on elapsed time.
    """
    return [
        ((1.0 + v / 100.0) ** (365.0 / d) - 1.0) * 100.0
        for v, d in zip(values, spans, strict=False)
    ]


def _summary(label, hold_all, totals, fn):
    line = f"{label:>21} {'':>7} {'':>5} {fn(hold_all):+8.1f}"
    line += "%" if label != "# positive" else f"/{len(hold_all)}"
    if label == "# positive":
        line = f"{label:>21} {'':>7} {'':>5} {fn(hold_all):>5}/{len(hold_all):<3}"
    for _name, values in totals.items():
        if label == "# positive":
            line += f" {fn(values):>12}/{len(values):<3}"
        else:
            line += f" {fn(values):+15.1f}%"
    print(line)


if __name__ == "__main__":
    raise SystemExit(main())
