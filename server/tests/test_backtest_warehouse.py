"""Every configuration a server run finishes is recorded in the warehouse
(server/backtest.py's _warehouse_writer): parameters and metrics in
sim.simulations under one sweep per run and ticker, and the best
configuration's trade log in the executions lake."""

from __future__ import annotations

import pytest

pytest.importorskip("duckdb")
pytest.importorskip("polars")

import server.backtest as backtest
from engine.tests.test_warehouse_schema import _bars
from engine.warehouse.connection import open_warehouse


@pytest.fixture
def warehouse(tmp_path, monkeypatch):
    frame = _bars(400)
    monkeypatch.setattr(backtest, "available_tickers", lambda: {"TESTQ"})
    monkeypatch.setattr(backtest, "load_frame", lambda ticker: frame)
    root = tmp_path / "warehouse"
    monkeypatch.setenv("VAI_WAREHOUSE_DIR", str(root))
    monkeypatch.setenv("VAI_RECORD_WAREHOUSE", "1")  # the root conftest turns it off
    return root


def _run(**overrides):
    request = {
        "name": "warehouse test",
        "tickers": ["TESTQ"],
        "grid_steps": [0.005, 0.01],
        "targets": [0.005, 0.01],
        "model": "fixed",
        "params": {"allocation_pct": 0.05},
        "jobs": 1,
        "limit": None,
    }
    request.update(overrides)
    return backtest.run_backtest(request, lambda *_: None)


def _query(root, sql):
    con = open_warehouse(root, read_only=True)
    try:
        return con.execute(sql).fetchall()
    finally:
        con.close()


def test_every_configuration_lands_in_the_warehouse(warehouse):
    report = _run()
    assert len(report["funds"]["TESTQ"]["cells"]) == 4
    assert _query(warehouse, "SELECT COUNT(*) FROM sim.simulations") == [(4,)]
    sweeps = _query(warehouse, "SELECT sweep_id FROM sim.sweeps")
    assert len(sweeps) == 1 and sweeps[0][0].startswith("server-")
    assert sweeps[0][0].endswith("-TESTQ")
    # The fund it ran on, not the request's default symbol.
    symbol = "SELECT json_extract_string(base_parameters, '$.backtest.symbol') FROM sim.sweeps"
    assert _query(warehouse, symbol) == [("TESTQ",)]


def test_only_the_best_configuration_keeps_its_trade_log(warehouse):
    report = _run()
    fills = _query(warehouse, "SELECT COUNT(DISTINCT simulation_id) FROM sim.trade_executions")
    assert fills == [(1,)]
    assert report["funds"]["TESTQ"]["fills"], "and Run History keeps the same one's fills"


def test_recording_can_be_turned_off(warehouse, monkeypatch):
    monkeypatch.setenv("VAI_RECORD_WAREHOUSE", "0")
    _run()
    assert not (warehouse / "sim_results.duckdb").exists()
