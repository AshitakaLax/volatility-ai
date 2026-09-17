"""run_backtest's pause/resume and bounded-memory contract, on real bars.

The claims under test, each of which the queue's UI is built on:

  - a run told to stop raises RunStopped having checkpointed exactly the
    configurations that finished, and no more;
  - a run resumed from that checkpoint produces the SAME report the
    uninterrupted run did -- every configuration's metrics, and the best
    configuration's trade log and equity curve;
  - a run whose every configuration was already checkpointed still
    returns a complete report, rebuilding the best trade log it never
    held in memory;
  - a resumed Bayesian run spends only the remaining trial budget;
  - the main sweep never asks run_sweep to retain every full result.
    That retention is what grew the server to 31.4 GB and bugchecked a
    15 GB machine on 2026-09-13; this pins it so it cannot return.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from server.backtest import KNOWN_DATA, run_backtest
from server.jobs import RunStopped, _json_default
from src.optimization.optimization_controller import OptimizationController

TICKER = "TQQQ"

pytestmark = pytest.mark.skipif(
    not Path(KNOWN_DATA.get(TICKER, "")).exists(), reason=f"no {TICKER} bar file on this machine"
)

# 2 x 2 x 2 = 8 configurations over the last 4,000 bars, serially, so the
# order configurations finish in -- and therefore where a stop lands -- is
# deterministic. "Final Equity" rather than the default ranking metric so
# the best configuration is not decided by a tie.
REQUEST = {
    "tickers": [TICKER],
    "grid_steps": [0.005, 0.01],
    "targets": [0.005, 0.01],
    "model": "fixed",
    "params": {"allocation_pct": [0.05, 0.1]},
    "limit": 4000,
    "jobs": 1,
    "rank_by": "Final Equity",
}


class FakeControl:
    """The RunControl protocol, with rows round-tripped through JSON exactly
    as server/jobs.py's QueueStore writes and reads them."""

    def __init__(self, completed=None, stop_after: int | None = None):
        self._completed = list(completed or [])
        self.recorded: list[dict] = []
        self._stop_after = stop_after

    def should_stop(self) -> bool:
        return self._stop_after is not None and len(self.recorded) >= self._stop_after

    def completed_rows(self, ticker: str) -> list[dict]:
        return list(self._completed) if ticker == TICKER else []

    def record_row(self, ticker: str, row: dict) -> None:
        self.recorded.append(json.loads(json.dumps(row, default=_json_default)))


def noop(_fraction: float, _note: str) -> None:
    pass


def _normalise(value):
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, dict):
        return {k: _normalise(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalise(v) for v in value]
    return value


def configurations(report) -> list:
    """Every configuration's metrics, keyed by what it ran -- order-free."""
    cells = report["funds"][TICKER]["cells"]
    return sorted(
        (_normalise(cell) for cell in cells),
        key=lambda c: (
            c["grid"],
            c["target"],
            json.dumps(c["params"], sort_keys=True),
        ),
    )


def best(report) -> dict:
    fund = report["funds"][TICKER]
    return _normalise(
        {
            "metrics": fund["cells"][0]["m"],
            "fills": fund["fills"],
            "equity": fund["equity"],
        }
    )


@pytest.fixture(scope="module")
def uninterrupted():
    return run_backtest(REQUEST, noop)


def test_a_stopped_run_checkpoints_exactly_what_finished():
    control = FakeControl(stop_after=3)
    with pytest.raises(RunStopped):
        run_backtest(REQUEST, noop, control)
    assert len(control.recorded) == 3


def test_a_resumed_run_reproduces_the_uninterrupted_report(uninterrupted):
    first = FakeControl(stop_after=3)
    with pytest.raises(RunStopped):
        run_backtest(REQUEST, noop, first)

    second = FakeControl(completed=first.recorded)
    resumed = run_backtest(REQUEST, noop, second)

    assert len(second.recorded) == 5  # only the remainder ran
    assert configurations(resumed) == configurations(uninterrupted)
    assert best(resumed) == best(uninterrupted)


def test_a_fully_checkpointed_run_rebuilds_the_best_trade_log(uninterrupted):
    everything = FakeControl()
    run_backtest(REQUEST, noop, everything)
    assert len(everything.recorded) == 8

    rebuilt_from = FakeControl(completed=everything.recorded)
    rebuilt = run_backtest(REQUEST, noop, rebuilt_from)

    assert rebuilt_from.recorded == []  # no configuration re-ran as a sweep
    assert configurations(rebuilt) == configurations(uninterrupted)
    assert best(rebuilt) == best(uninterrupted)


def test_a_stop_before_any_configuration_is_a_pause_not_a_failure():
    control = FakeControl(stop_after=0)
    with pytest.raises(RunStopped):
        run_backtest(REQUEST, noop, control)
    assert control.recorded == []


def test_a_resumed_bayesian_run_spends_only_the_remaining_budget():
    request = dict(REQUEST, bayes={"trials": 6, "seed": 11})
    first = FakeControl(stop_after=2)
    with pytest.raises(RunStopped):
        run_backtest(request, noop, first)
    second = FakeControl(completed=first.recorded)
    report = run_backtest(request, noop, second)
    assert len(second.recorded) == 4
    assert len(report["funds"][TICKER]["cells"]) == 6


def test_the_sweep_never_retains_every_full_result(monkeypatch):
    calls = []
    real = OptimizationController.run_sweep

    def spy(self, **kwargs):
        calls.append(
            {k: kwargs.get(k) for k in ("return_full_results", "result_sink", "grid_steps")}
        )
        return real(self, **kwargs)

    monkeypatch.setattr(OptimizationController, "run_sweep", spy)
    run_backtest(REQUEST, noop, FakeControl())

    sweep = calls[0]
    assert sweep["return_full_results"] is False
    assert sweep["result_sink"] is not None
    # Any further call is the single-configuration rebuild, which may
    # retain its one result.
    assert all(len(call["grid_steps"]) == 1 for call in calls[1:])


def test_the_ranking_is_the_engines_not_a_new_one(uninterrupted):
    """The equivalence tests above compare the new path against itself, so
    an inverted ranking would pass them. This anchors it to run_sweep's own
    order: descending by rank_by, with the report's best configuration the
    one run_sweep itself ranks first."""
    from server.backtest import RunRequest, build_config
    from src.trading.strategy_registry import resolve_strategy

    cells = uninterrupted["funds"][TICKER]["cells"]
    equities = [cell["m"]["final_equity"] for cell in cells]
    assert equities == sorted(equities, reverse=True)

    import pandas as pd

    from server.backtest import window

    parsed = RunRequest(**REQUEST)
    config = build_config(parsed)
    kwargs = config.to_run_sweep_kwargs(resolve_strategy(config.strategy.strategy_id))
    kwargs.update(symbol=TICKER, n_jobs=1)
    frame = pd.read_csv(KNOWN_DATA[TICKER], parse_dates=["timestamp"]).set_index("timestamp")
    engine = OptimizationController(historical_data=window(frame, None, None, 4000)).run_sweep(
        **kwargs
    )
    assert round(float(engine.iloc[0]["Final Equity"]), 2) == equities[0]
