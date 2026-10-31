"""tools/portfolio_book.py end to end, with the warehouse replaced by
synthetic minute bars."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

import engine.warehouse.bars as bars
from tools import portfolio_book


def _minutes(seed: int, drift: float) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    days = pd.bdate_range("2019-01-02", periods=400, tz="UTC") + pd.Timedelta(hours=15)
    close = 100 * np.exp(np.cumsum(drift + rng.normal(0, 0.01, len(days))))
    return pd.DataFrame(
        {"open": close, "high": close, "low": close, "close": close, "volume": 1000}, index=days
    )


@pytest.fixture
def warehouse(monkeypatch):
    frames = {"AAA": _minutes(1, 0.001), "BBB": _minutes(2, 0.0), "CCC": _minutes(3, -0.001)}
    monkeypatch.setattr(bars, "load_frame", lambda name: frames.get(name, pd.DataFrame()))


def test_runs_an_allocator_and_writes_its_outputs(warehouse, tmp_path, capsys):
    code = portfolio_book.main(
        [
            "--allocator",
            "cross_sectional_momentum",
            "--universe",
            "AAA",
            "BBB",
            "CCC",
            "--param",
            "k=1",
            "--param",
            "lookback=126",
            "--min-history",
            "130",
            "--out",
            str(tmp_path),
        ]
    )
    assert code == 0
    report = json.loads(capsys.readouterr().out)
    assert report["allocator"] == "cross_sectional_momentum" and "CAGR %" in report
    assert len(list(tmp_path.glob("*_equity.csv"))) == 1


def test_state_filtered_momentum_needs_a_market(warehouse):
    with pytest.raises(SystemExit):
        portfolio_book.main(["--allocator", "state_filtered_momentum", "--universe", "AAA", "BBB"])


def test_missing_data_is_reported(warehouse):
    with pytest.raises(SystemExit, match="No warehouse data"):
        portfolio_book.main(["--allocator", "equal_weight", "--universe", "AAA", "ZZZ"])
