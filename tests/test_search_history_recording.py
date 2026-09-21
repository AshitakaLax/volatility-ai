"""tools.export_ui_data.build_search_report/write_run_history producing
a run server/history.py can actually read back -- the seam between
`cli.py search --record-history` (needed because the server's job queue
never writes to the DuckDB warehouse, see engine/warehouse/duckdb_sink.py)
and the web UI's Run History, which reads output/runs/*.json.

Exercised end to end through server.history rather than just checking
the written dict's shape: contract.run()'s early return on a
current-format snapshot ("id", not "run_id") makes it easy to write
something that LOOKS right but that history.load_all() silently passes
through unexamined -- the only real check is that the actual read path
reports the actual fields.
"""

from __future__ import annotations

import pandas as pd

from engine.core.config import BacktestConfig
from tools.export_ui_data import build_search_report, write_run_history


def _config(fill_model="intrabar"):
    return BacktestConfig.from_dict(
        {
            "strategy": {"strategy_id": "fixed", "strategy_params": {"allocation_pct": 0.05}},
            "grid": {"steps": [0.01], "profit_targets": [0.03]},
            "backtest": {"symbol": "TEST"},
            "execution": {"fill_model": fill_model},
        }
    )


class _FakeSimResult:
    def __init__(self):
        self.trade_blotter = pd.DataFrame()
        self.equity_curve = pd.Series(dtype=float)


def _frame():
    index = pd.date_range("2024-01-02", periods=5, freq="1min", tz="UTC")
    return pd.DataFrame({"close": 100.0}, index=index)


def test_a_recorded_search_run_is_readable_by_the_run_history_store(monkeypatch, tmp_path):
    monkeypatch.setenv("VAI_RUN_HISTORY_DIR", str(tmp_path / "runs"))
    from server import history

    config = _config(fill_model="intrabar")
    results = pd.DataFrame(
        [
            {
                "Grid Step": 0.01,
                "Profit Target": 0.03,
                "allocation_pct": 0.05,
                "Total Return %": 12.5,
                "CAGR %": 6.1,
            },
            {
                "Grid Step": 0.01,
                "Profit Target": 0.03,
                "allocation_pct": 0.05,
                "error": "boom",
            },
        ]
    )
    report = build_search_report(
        config,
        "TEST",
        results,
        _FakeSimResult(),
        _frame(),
        "abc123def456",
        name="my understandable sweep name",
    )
    path = write_run_history("abc123def456", report)
    assert path.exists()

    rows = history.load_all()
    assert len(rows) == 1
    loaded = rows[0]
    assert loaded["id"] == "abc123def456"
    fund = loaded["report"]["funds"]["TEST"]
    # The failed combination (row 2) contributes no cell -- only the one
    # real result does.
    assert len(fund["cells"]) == 1
    assert fund["cells"][0]["m"]["cagr_pct"] == 6.1
    assert fund["cells"][0]["params"] == {"allocation_pct": 0.05}
    # The listing path strips fills/equity (server/history.py's own
    # load_all() contract) -- a single-run detail load would not.
    assert fund["fills"] == []


def test_the_run_name_survives_the_round_trip(monkeypatch, tmp_path):
    monkeypatch.setenv("VAI_RUN_HISTORY_DIR", str(tmp_path / "runs"))
    from server import history

    config = _config()
    results = pd.DataFrame(
        [{"Grid Step": 0.01, "Profit Target": 0.03, "allocation_pct": 0.05, "Total Return %": 1.0}]
    )
    report = build_search_report(
        config,
        "TEST",
        results,
        _FakeSimResult(),
        _frame(),
        "run2",
        name="my understandable sweep name",
    )
    write_run_history("run2", report)
    loaded = history.load("run2")
    assert loaded["report"]["name"] == "my understandable sweep name"


def test_every_combination_failing_still_writes_a_readable_run(monkeypatch, tmp_path):
    """No cells and no top_sim_result is a real, if useless, outcome --
    it must not crash the write path or the read path."""
    monkeypatch.setenv("VAI_RUN_HISTORY_DIR", str(tmp_path / "runs"))
    from server import history

    config = _config()
    results = pd.DataFrame(
        [{"Grid Step": 0.01, "Profit Target": 0.03, "allocation_pct": 0.05, "error": "boom"}]
    )
    report = build_search_report(config, "TEST", results, None, _frame(), "run3")
    write_run_history("run3", report)
    loaded = history.load("run3")
    assert loaded["report"]["funds"]["TEST"]["cells"] == []
    assert loaded["report"]["funds"]["TEST"]["fills"] == []
