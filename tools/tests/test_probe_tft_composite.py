"""tools/probe_tft_composite.py: the plan builds a composed configuration the
engine accepts for every buy x sell cell, opens the loss gate only for the
loss-capable sells, and the report sets each TFT buy against its null."""

from __future__ import annotations

import json

import pytest

from engine.core.config import BacktestConfig
from research.composition.composed_strategy import ComposedStrategy
from research.strategies.strategy_registry import resolve_strategy
from tools import probe_tft_composite as probe


def _models(tmp_path, null=True):
    tmp_path.mkdir(parents=True, exist_ok=True)
    for fund in ("tqqq", "rsp"):
        for suffix in ("", "_inputs"):
            directory = tmp_path / f"tft_{fund}{suffix}"
            directory.mkdir()
            (directory / "manifest.json").write_text(json.dumps({"kind": "tft"}))
            (directory / "forecasts.npz").write_bytes(b"")
            if null and not suffix:
                (directory / "forecasts_null.npz").write_bytes(b"")
    return tmp_path


def test_every_cell_builds_and_only_loss_capable_sells_may_lose(tmp_path):
    specs = probe.plan(_models(tmp_path))
    caps = len(probe.CAPS)
    buys = 1 + 3 * caps + 1  # base, tft, tft_inputs and null at each cap, the reference
    sells = len(probe.LIBRARY_SELLS) + 3 + 1  # the library, the TFT sells and their null, the exit
    assert len(specs) == len({s["name"] for s in specs}) == 2 * buys * sells
    for spec in specs:
        config = BacktestConfig.from_dict(spec["config"])
        config.to_run_sweep_kwargs(resolve_strategy(config.strategy.strategy_id))
        ComposedStrategy(**config.strategy.strategy_params)
        assert config.execution.allow_signal_exit is spec["loss_track"]
        assert config.execution.intrabar_fill == "causal"
    may_lose = {s["sell"] for s in specs if s["loss_track"]}
    assert may_lose == {"regime_exit", "ultimate_exit", "rsp_rebalance"}


def test_a_null_buy_is_the_tft_buy_on_the_null_table(tmp_path):
    specs = probe.plan(_models(tmp_path), ("RSP",))
    tft = next(s for s in specs if s["buy"] == "tft cap0.001")
    null = next(s for s in specs if s["buy"] == "null cap0.001")
    a = tft["config"]["strategy"]["strategy_params"]["buy"]["params"]
    b = null["config"]["strategy"]["strategy_params"]["buy"]["params"]
    assert b["forecast_cache"].endswith("forecasts_null.npz")
    assert {k: v for k, v in a.items() if k != "forecast_cache"} == {
        k: v for k, v in b.items() if k != "forecast_cache"
    }
    assert not any(s["buy"].startswith("null") for s in probe.plan(_models(tmp_path / "n", False)))


def _row(buy, sell, total, dd, cagr=None):
    return {
        "buy": buy,
        "sell": sell,
        "metrics": {"Total Return %": total, "Max Drawdown %": dd, "CAGR %": cagr or total / 3},
    }


def test_the_report_counts_where_the_tft_beats_its_null():
    rows = [
        _row("tft cap0.001", "fixed_target", 30, 10),
        _row("null cap0.001", "fixed_target", 30, 20),
        _row("tft cap0.005", "fixed_target", 30, 20),
        _row("null cap0.005", "fixed_target", 30, 10),
    ]
    lines = probe._against_null(rows)
    assert lines[-1].endswith("beats its null in 1 of 2 cells.")
    assert any(
        line.startswith("| fixed_target | 0.001 | 30.0 / 10.0 | - | 30.0 / 20.0 | yes")
        for line in lines
    )


@pytest.mark.parametrize(
    ("m", "expected"),
    [
        ({"CAGR %": 10.0, "Max Drawdown %": 20.0}, 0.5),
        ({"CAGR %": 5.0, "Max Drawdown %": 0.0}, None),
    ],
)
def test_calmar(m, expected):
    assert probe.calmar(m) == expected
