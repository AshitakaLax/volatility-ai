"""run_backtest when some configurations fail: the run completes with the
ones that ran, and the failed ones are left out of its report.

MLRegimeScaledSizing refuses, on a configuration's first bar, a threshold
its model never reaches. On 2026-10-21 that was half of two RSP sweeps,
and the report then crashed on their NaN metrics -- failing both runs
after every configuration had finished.
"""

from __future__ import annotations

import pytest

from engine.core.exceptions import ConfigurationError
from engine.warehouse.bars import available_tickers
from research.strategies.size_calculators import FixedPortfolioPercentage
from server.backtest import run_backtest

TICKER = "TQQQ"

pytestmark = pytest.mark.skipif(
    TICKER not in available_tickers(), reason=f"no {TICKER} bars in this machine's warehouse"
)


def test_a_run_with_failed_configurations_reports_the_ones_that_ran(monkeypatch):
    record_tick = FixedPortfolioPercentage.record_tick

    def refuse_some(self, context):
        if self.allocation_pct == 0.1:
            raise ConfigurationError("refused on its first bar, as a regime model's check is")
        return record_tick(self, context)

    monkeypatch.setattr(FixedPortfolioPercentage, "record_tick", refuse_some)
    report = run_backtest(
        {
            "tickers": [TICKER],
            "grid_steps": [0.005, 0.01],
            "targets": [0.005],
            "model": "fixed",
            "params": {"allocation_pct": [0.05, 0.1]},
            "limit": 4000,
            "jobs": 1,
        },
        lambda _fraction, _note: None,
    )

    cells = report["funds"][TICKER]["cells"]
    assert sorted(cell["grid"] for cell in cells) == [0.005, 0.01]
    assert all(cell["params"]["allocation_pct"] == 0.05 for cell in cells)
    assert cells[0]["m"]["final_equity"] > 0, "the best is one that ran"
