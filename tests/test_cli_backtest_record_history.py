"""cli.py backtest --record-history end to end.

FOUND BY RUNNING IT, NOT BY READING THE SCHEMA -- the same way this
project keeps finding these. cmd_backtest's body referenced
args.record_history/args.name (added alongside cmd_search's own
--record-history support) but p_backtest's argparse subparser never
registered either flag, so `args.record_history` raised AttributeError
unconditionally on every invocation of `cli.py backtest`, whether or not
--record-history was actually passed -- the crash sat right after the
CSV-writing step, so even a plain `--warehouse`-only run hit it. This
test drives cmd_backtest exactly the way test_cli_search_execution_params.py
drives cmd_search, so the same class of "flag exists in the body but not
the parser" gap gets caught by running the function, not just by
`--help` listing the flag.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field

import pandas as pd

import cli
from server import history


@dataclass
class _FakeSimResult:
    metrics: dict = field(default_factory=lambda: {"Total Return %": 5.0})
    trade_blotter: pd.DataFrame = field(default_factory=pd.DataFrame)
    equity_curve: pd.Series = field(default_factory=lambda: pd.Series(dtype=float))


def _make_bars() -> pd.DataFrame:
    index = pd.date_range("2024-01-02", periods=50, freq="1min", tz="UTC")
    return pd.DataFrame(
        {"open": 100.0, "high": 100.5, "low": 99.5, "close": 100.0, "volume": 1000},
        index=index,
    )


def _write_config(tmp_path) -> str:
    path = tmp_path / "config.yaml"
    path.write_text(
        """
strategy:
  strategy_id: fixed
  strategy_params:
    allocation_pct: 0.05
grid:
  steps: [0.01]
  profit_targets: [0.03]
backtest:
  symbol: TEST
execution:
  fill_model: intrabar
search:
  strategy: grid
  rank_by: Total Return %
  direction: maximize
  seed: 1
""",
        encoding="utf-8",
    )
    return str(path)


def test_record_history_does_not_crash_and_produces_a_readable_run(monkeypatch, tmp_path):
    monkeypatch.setenv("VAI_RUN_HISTORY_DIR", str(tmp_path / "runs"))
    monkeypatch.setattr(cli, "_load_warehouse_bars", lambda symbol: (_make_bars(), "test-version"))

    def fake_run_sweep(self, **kwargs):
        row = {
            "Grid Step": kwargs["grid_steps"][0],
            "Profit Target": kwargs["profit_targets"][0],
            "Strategy": "FixedPortfolioPercentage",
            "allocation_pct": 0.05,
            "Total Return %": 5.0,
        }
        return pd.DataFrame([row])

    monkeypatch.setattr(
        "research.optimization.optimization_controller.OptimizationController.run_sweep",
        fake_run_sweep,
    )
    monkeypatch.setattr(
        "research.optimization.optimization_controller._run_one_combination",
        lambda *a, **k: (
            {
                "Grid Step": 0.01,
                "Profit Target": 0.03,
                "Strategy": "FixedPortfolioPercentage",
                "allocation_pct": 0.05,
                "Total Return %": 5.0,
            },
            _FakeSimResult(),
        ),
    )

    args = argparse.Namespace(
        config=_write_config(tmp_path),
        output=None,
        warehouse=None,
        record_history=True,
        name=None,
    )

    assert cli.cmd_backtest(args) == 0

    rows = history.load_all()
    assert len(rows) == 1
    loaded = rows[0]
    assert loaded["report"]["name"] == "config"
    assert loaded["report"]["fill"] == "intrabar"
    assert loaded["report"]["funds"]["TEST"]["cells"][0]["m"]["net_yield_pct"] == 5.0


def test_backtest_without_record_history_still_does_not_crash(monkeypatch, tmp_path):
    """The regression this whole file guards: the crash fired even when
    --record-history was never passed, since args.record_history simply
    didn't exist as an attribute at all."""
    monkeypatch.setattr(cli, "_load_warehouse_bars", lambda symbol: (_make_bars(), "test-version"))

    def fake_run_sweep(self, **kwargs):
        return pd.DataFrame(
            [
                {
                    "Grid Step": kwargs["grid_steps"][0],
                    "Profit Target": kwargs["profit_targets"][0],
                    "Strategy": "FixedPortfolioPercentage",
                    "allocation_pct": 0.05,
                    "Total Return %": 5.0,
                }
            ]
        )

    monkeypatch.setattr(
        "research.optimization.optimization_controller.OptimizationController.run_sweep",
        fake_run_sweep,
    )

    args = argparse.Namespace(
        config=_write_config(tmp_path),
        output=None,
        warehouse=None,
        record_history=False,
        name=None,
    )

    assert cli.cmd_backtest(args) == 0
