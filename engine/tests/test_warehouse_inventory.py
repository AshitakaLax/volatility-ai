"""engine/warehouse/inventory.py: what the Warehouse tab reports.

SKIPS WITHOUT DUCKDB/POLARS, like the other warehouse tests.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import pandas as pd
import pytest

duckdb = pytest.importorskip("duckdb")
pytest.importorskip("polars")

from engine.core.trading_calendar import EASTERN  # noqa: E402
from engine.tests.test_warehouse_schema import _write_csv  # noqa: E402
from engine.warehouse import bars, ingest, inventory, schema  # noqa: E402
from engine.warehouse.connection import open_warehouse  # noqa: E402
from engine.warehouse.result_writer import BatchedResultWriter  # noqa: E402

FULL_WEEKS = ["2026-10-05", "2026-10-06", "2026-10-07", "2026-10-08"]
LATER = ["2026-10-09", "2026-10-12", "2026-10-13", "2026-10-14", "2026-10-15", "2026-10-16"]
# Monday 2026-10-19, 21:30 Eastern: the 19th's session is over.
NOW = datetime(2026, 10, 19, 21, 30, tzinfo=EASTERN)


def _sessions(days: list[str], *, until: str = "15:30") -> pd.DataFrame:
    """Half-hourly bars, 09:30 to `until` Eastern: 13 a full session."""
    index = pd.DatetimeIndex([], tz="UTC")
    for day in days:
        index = index.append(
            pd.date_range(f"{day} 09:30", f"{day} {until}", freq="30min", tz="America/New_York")
        )
    index = index.tz_convert("UTC")
    index.name = "timestamp"
    return pd.DataFrame(
        {"open": 100.0, "high": 100.5, "low": 99.5, "close": 100.0, "volume": 1000},
        index=index,
    )


def _ingest(root, tmp_path, ticker: str, frame: pd.DataFrame) -> None:
    tmp_path.mkdir(parents=True, exist_ok=True)
    con = open_warehouse(root)
    try:
        schema.initialize(con, root)
        csv = _write_csv(frame, tmp_path / f"{ticker}-{len(frame)}.csv")
        ingest.ingest_ohlcv_csv(con, root, csv, ticker)
        schema.refresh_views(con, root)
    finally:
        con.close()


@pytest.fixture
def warehouse(tmp_path, monkeypatch):
    """FULL: four full sessions to Oct 8. PART: ten to Oct 16, the last one
    fetched at noon."""
    root = tmp_path / "warehouse"
    monkeypatch.setenv("VAI_WAREHOUSE_DIR", str(root))
    _ingest(root, tmp_path, "FULL", _sessions(FULL_WEEKS))
    part = pd.concat([_sessions(FULL_WEEKS + LATER[:-1]), _sessions(LATER[-1:], until="12:00")])
    _ingest(root, tmp_path, "PART", part)
    return root


def test_each_fund_has_its_span_sessions_and_density(warehouse):
    answer = inventory.fund_inventory()
    assert answer["available"] and not answer["busy"] and answer["error"] is None
    full = answer["funds"]["FULL"]
    assert full["bars"] == 52 and full["sessions"] == 4 and full["duplicates"] == 0
    assert full["bars_per_session"] == 13 and full["last_session_bars"] == 13
    assert datetime.fromisoformat(full["last"]) == datetime(2026, 10, 8, 15, 30, tzinfo=EASTERN)
    part = answer["funds"]["PART"]
    assert part["sessions"] == 10 and part["last_session_bars"] == 6


def test_the_fingerprint_is_the_dataset_version_a_sweep_records(warehouse):
    funds = inventory.fund_inventory()["funds"]
    assert funds["FULL"]["fingerprint"] == bars.fingerprint("FULL")
    assert funds["PART"]["fingerprint"] == bars.fingerprint("PART")


def test_a_fund_is_behind_by_the_sessions_since_its_last_one(warehouse):
    full = inventory.fund_inventory()["funds"]["FULL"]
    answer = inventory.freshness(
        full["last"], full["bars_per_session"], full["last_session_bars"], NOW
    )
    assert answer == {
        "through": "2026-10-19",
        "last_session": "2026-10-08",
        "partial": False,
        "sessions_behind": 7,
        "bars_to_add": 91,
    }


def test_a_session_fetched_mid_day_is_still_missing_its_afternoon(warehouse):
    part = inventory.fund_inventory()["funds"]["PART"]
    answer = inventory.freshness(
        part["last"], part["bars_per_session"], part["last_session_bars"], NOW
    )
    # The 16th (7 of its 13 bars missing) and the 19th.
    assert answer["partial"] and answer["sessions_behind"] == 2
    assert answer["bars_to_add"] == 2 * 13 - 6


def test_up_to_date_is_through_the_last_completed_session():
    last = datetime(2026, 10, 19, 15, 59, tzinfo=EASTERN).isoformat()
    trading = datetime(2026, 10, 19, 15, 0, tzinfo=EASTERN)
    assert inventory.freshness(last, 390, 390, NOW)["sessions_behind"] == 0
    before = datetime(2026, 10, 16, 15, 59, tzinfo=EASTERN).isoformat()
    assert inventory.freshness(before, 390, 390, trading)["sessions_behind"] == 0
    assert inventory.freshness(None, None, None, NOW)["sessions_behind"] is None


def test_an_overlapping_append_shows_as_duplicates(warehouse, tmp_path):
    _ingest(warehouse, tmp_path / "again", "FULL", _sessions(FULL_WEEKS))
    full = inventory.fund_inventory()["funds"]["FULL"]
    assert full["bars"] == 104 and full["duplicates"] == 52
    assert full["sessions"] == 4 and full["bars_per_session"] == 13


def test_the_signature_changes_only_with_the_lake(warehouse, tmp_path):
    first = inventory.ohlcv_signature()
    assert first is not None and inventory.ohlcv_signature() == first
    _ingest(warehouse, tmp_path / "more", "MORE", _sessions(FULL_WEEKS))
    assert inventory.ohlcv_signature() != first


class _Cost:
    model_type = "zero"
    commission_per_trade = 0.0
    slippage_bps = 0.0
    base_bps = 0.0
    vol_multiplier = 1.0


def _record(root, sweep_id: str, version: str, returns: list[float], **base) -> None:
    writer = BatchedResultWriter(
        root,
        sweep_id=sweep_id,
        algorithm="grid",
        base_parameters=base,
        cost_config=_Cost(),
        dataset_version=version,
    )
    for i, total_return in enumerate(returns):
        writer.add(
            {
                "Grid Step": 0.01 * (i + 1),
                "Profit Target": 0.02,
                "Strategy": "FixedPortfolioPercentage",
                "allocation_pct": 0.05,
                "Total Return %": total_return,
                "Max Drawdown %": 10.0 + i,
                "Return/Drawdown": float("inf") if i == 0 else total_return / (10.0 + i),
                "Trade Count": 5,
            }
        )
    assert writer.finish()["unwritten"] == 0


def test_results_are_grouped_per_sweep_with_the_fund_it_ran_on(warehouse):
    version = bars.fingerprint("FULL")
    _record(
        warehouse,
        "server-abc123-FULL",
        version,
        [4.0, 9.0, 6.5],
        backtest={"symbol": "TQQQ"},  # the request's default, as old sweeps recorded it
        strategy={"strategy_id": "fixed"},
        server_run={"run_id": "abc123", "ticker": "FULL", "name": "a test run"},
    )
    _record(warehouse, "cli-sweep", "an-older-version", [2.0], backtest={"symbol": "FULL"})

    answer = inventory.results_summary(datetime.now(UTC))
    assert answer["available"] and answer["sweeps"] == 2 and answer["simulations"] == 4
    assert answer["by_status"] == {"COMPLETED": 4} and answer["last_hour"] == 4
    assert sum(hour["n"] for hour in answer["hourly"]) == 4 and len(answer["hourly"]) == 48

    server = next(row for row in answer["sweep_rows"] if row["id"] == "server-abc123-FULL")
    assert server["fund"] == "FULL" and server["strategy"] == "fixed"
    assert server["run_id"] == "abc123" and server["run_name"] == "a test run"
    assert server["simulations"] == 3 and server["best_return"] == 9.0
    assert server["best_drawdown"] == 11.0
    assert server["best_calmar"] == pytest.approx(9.0 / 11.0)

    versions = {(v["fund"], v["dataset_version"]): v["simulations"] for v in answer["versions"]}
    assert versions == {("FULL", version): 3, ("FULL", "an-older-version"): 1}


def test_infinite_metrics_never_reach_the_response(warehouse):
    _record(warehouse, "server-inf-FULL", "v", [5.0], server_run={"ticker": "FULL"})
    row = inventory.results_summary(datetime.now(UTC))["sweep_rows"][0]
    assert row["best_calmar"] is None  # Return/Drawdown was inf


def test_storage_is_read_from_the_files(warehouse):
    answer = inventory.storage_summary()
    assert answer["available"] and answer["duckdb"].startswith("v")
    assert {c["name"] for c in answer["catalogs"]} >= {"market_data.duckdb", "sim_results.duckdb"}
    ohlcv = answer["lakes"]["ohlcv"]
    assert ohlcv["files"] > 0 and set(ohlcv["by_fund"]) == {"FULL", "PART"}
    assert answer["tables"]["broker_environments"] == 0
    assert answer["disk"]["free"] > 0


def test_no_warehouse_is_an_answer_not_an_error(tmp_path, monkeypatch):
    monkeypatch.setenv("VAI_WAREHOUSE_DIR", str(tmp_path / "none"))
    assert inventory.fund_inventory() == {"available": False, "busy": False, "error": None}
    assert inventory.results_summary(NOW)["available"] is False
    assert inventory.ohlcv_signature() is None
    storage = inventory.storage_summary()
    assert storage["available"] is False and storage["lakes"]["ohlcv"]["files"] == 0


def test_a_warehouse_another_process_holds_is_busy(warehouse, monkeypatch):
    import engine.warehouse.connection as connection

    def locked(*_args, **_kwargs):
        raise RuntimeError('IO Error: Could not set lock on file "market_data.duckdb"')

    monkeypatch.setattr(connection, "open_warehouse", locked)
    monkeypatch.setattr(bars, "_LOCK_RETRY_SECONDS", 0.0)  # no waiting it out here
    answer = inventory.fund_inventory()
    assert answer == {"available": True, "busy": True, "error": None}


def test_a_session_count_matches_the_calendar(warehouse):
    """The inventory's sessions are Eastern dates, as the calendar's are."""
    funds = inventory.fund_inventory()["funds"]
    assert funds["FULL"]["sessions"] == len(FULL_WEEKS)
    assert (
        date.fromisoformat(FULL_WEEKS[-1])
        == datetime.fromisoformat(funds["FULL"]["last"]).astimezone(EASTERN).date()
    )
