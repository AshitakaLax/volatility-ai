"""cli.py's `search`/`backtest` commands actually passing
config.execution.fill_model/intrabar_priority/enforce_no_loss into the
engine, not just reading them.

FOUND BY RUNNING A REAL SWEEP, NOT BY READING THE SCHEMA -- the same way
test_cli_backtest_window.py's bug was found. `cmd_search` calls
_run_one_combination() directly (its own inner loop, not run_sweep(),
so it can log trials in execution order) but the call omitted
fill_model/intrabar_priority/enforce_no_loss entirely, silently falling
back to _run_one_combination's own defaults -- fill_model="close" -- no
matter what a config's `execution.fill_model` said. Eleven configs
across a multi-hour sweep batch all named `execution.fill_model:
intrabar` in both their filename and their YAML, and every one of them
ran with close-only fills instead, because nothing forwarded the value.

A grid/target sweep or a metrics assertion would not have caught this:
both fill models produce valid, plausible-looking results, just
different ones (intrabar fills ~1.85x more often than close-only on
this project's own minute data). The only way to catch a forwarded
value that silently isn't forwarded is to check what was actually
passed to the engine -- hence the spy on _run_one_combination below,
not an assertion on simulated returns.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field

import pandas as pd
import pytest

import cli
from research.optimization import optimization_controller as occ


@dataclass
class _FakeSimResult:
    metrics: dict = field(default_factory=lambda: {"Total Return %": 5.0})
    trade_blotter: pd.DataFrame = field(default_factory=pd.DataFrame)
    equity_curve: pd.Series = field(default_factory=lambda: pd.Series(dtype=float))


def _make_bars() -> pd.DataFrame:
    index = pd.date_range("2024-01-02", periods=50, freq="1min", tz="UTC")
    return pd.DataFrame(
        {
            "open": 100.0,
            "high": 100.5,
            "low": 99.5,
            "close": 100.0,
            "volume": 1000,
        },
        index=index,
    )


def _write_config(tmp_path, fill_model: str) -> str:
    path = tmp_path / "config.yaml"
    path.write_text(
        f"""
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
  fill_model: {fill_model}
  intrabar_priority: sell_first
  enforce_no_loss: true
search:
  strategy: grid
  rank_by: Total Return %
  direction: maximize
  seed: 1
""",
        encoding="utf-8",
    )
    return str(path)


class _Capture:
    def __init__(self):
        self.calls: list[dict] = []


@pytest.fixture
def capture_combination_calls(monkeypatch):
    capture = _Capture()

    def fake_run_one_combination(*args, **kwargs):
        capture.calls.append(kwargs)
        return {"Grid Step": 0.01, "Profit Target": 0.03, "Total Return %": 5.0}, _FakeSimResult()

    monkeypatch.setattr(occ, "_run_one_combination", fake_run_one_combination)
    monkeypatch.setattr(cli, "_load_warehouse_bars", lambda symbol: (_make_bars(), "test-version"))
    return capture


class TestSearchForwardsExecutionSettings:
    def test_intrabar_fill_model_reaches_the_engine(self, tmp_path, capture_combination_calls):
        config_path = _write_config(tmp_path, "intrabar")
        args = argparse.Namespace(
            config=config_path,
            trials=1,
            output=None,
            trial_log=None,
            log_every=10,
            warehouse=None,
            record_history=False,
            name=None,
        )
        assert cli.cmd_search(args) == 0
        assert len(capture_combination_calls.calls) == 1
        assert capture_combination_calls.calls[0]["fill_model"] == "intrabar"
        assert capture_combination_calls.calls[0]["intrabar_priority"] == "sell_first"
        assert capture_combination_calls.calls[0]["enforce_no_loss"] is True

    def test_close_fill_model_also_reaches_the_engine(self, tmp_path, capture_combination_calls):
        """Not just "intrabar passes through" -- the forwarded value must
        actually vary with the config, or a hardcoded fill_model="intrabar"
        at the call site would pass the first test just as wrongly."""
        config_path = _write_config(tmp_path, "close")
        args = argparse.Namespace(
            config=config_path,
            trials=1,
            output=None,
            trial_log=None,
            log_every=10,
            warehouse=None,
            record_history=False,
            name=None,
        )
        assert cli.cmd_search(args) == 0
        assert capture_combination_calls.calls[0]["fill_model"] == "close"
