"""engine/warehouse/bars.py: what the simulation and shards read bars through.

SKIPS WITHOUT DUCKDB, like the other warehouse tests: it is an optional
dependency (requirements-warehouse.txt) and a checkout without it must
still get a green suite.
"""

from __future__ import annotations

import pandas as pd
import pytest

duckdb = pytest.importorskip("duckdb")

from engine.warehouse import bars  # noqa: E402


def _write_warehouse(root, frame: pd.DataFrame, ticker: str = "TESTQ") -> None:
    """A minimal warehouse: the ohlcv table bars.py reads, nothing else.

    sim_results.duckdb is created empty because open_warehouse ATTACHes
    it, and a read-only attach of a file that does not exist fails -- at
    which point every read here answers "no data" rather than erroring,
    which is exactly the shape of a test that passes vacuously.
    """
    root.mkdir(parents=True, exist_ok=True)
    duckdb.connect(str(root / "sim_results.duckdb")).close()
    con = duckdb.connect(str(root / "market_data.duckdb"))
    # Registered by name rather than left to DuckDB's replacement scan of
    # local variables, which reads a frame the linter cannot see is used.
    con.register(
        "rows",
        frame.reset_index().assign(ticker=ticker)[
            ["ticker", "timestamp", "open", "high", "low", "close", "volume"]
        ],
    )
    con.execute(
        "CREATE TABLE ohlcv (ticker VARCHAR, timestamp TIMESTAMPTZ, open DOUBLE, "
        "high DOUBLE, low DOUBLE, close DOUBLE, volume BIGINT)"
    )
    con.execute("INSERT INTO ohlcv SELECT * FROM rows")
    con.close()


@pytest.fixture
def frame() -> pd.DataFrame:
    # Values chosen so the price columns do not sum exactly in binary:
    # the first version of fingerprint() summed them and was unstable.
    index = pd.date_range("2024-01-02 14:30:00+00:00", periods=5000, freq="1min", name="timestamp")
    close = [100.0 + (i % 7) * 0.1 for i in range(len(index))]
    return pd.DataFrame(
        {
            "open": close,
            "high": [value + 0.07 for value in close],
            "low": [value - 0.03 for value in close],
            "close": close,
            "volume": [1000 + i for i in range(len(index))],
        },
        index=index,
    )


@pytest.fixture
def warehouse(tmp_path, frame, monkeypatch):
    root = tmp_path / "warehouse"
    _write_warehouse(root, frame)
    monkeypatch.setenv("VAI_WAREHOUSE_DIR", str(root))
    return root


# BIG ENOUGH TO PARALLELISE, AND THAT IS THE WHOLE POINT. Measured on
# this machine: the float-summing fingerprint this replaced was stable at
# 5,000 and 50,000 rows and UNSTABLE at 300,000, because that is where
# DuckDB splits the aggregate across threads. A stability test on a small
# fixture passes against the very bug it is meant to catch.
PARALLEL_ROWS = 300_000


@pytest.fixture
def parallel_warehouse(tmp_path, monkeypatch):
    index = pd.date_range(
        "2016-01-04 14:30:00+00:00", periods=PARALLEL_ROWS, freq="1min", name="timestamp"
    )
    close = [100.0 + (i % 7) * 0.1 for i in range(PARALLEL_ROWS)]
    frame = pd.DataFrame(
        {
            "open": close,
            "high": [value + 0.07 for value in close],
            "low": [value - 0.03 for value in close],
            "close": close,
            "volume": list(range(1000, 1000 + PARALLEL_ROWS)),
        },
        index=index,
    )
    root = tmp_path / "big"
    _write_warehouse(root, frame)
    monkeypatch.setenv("VAI_WAREHOUSE_DIR", str(root))
    return root


class TestFingerprint:
    def test_it_is_the_same_answer_every_time(self, parallel_warehouse):
        """THE BUG THIS PINS: the first version summed the price columns,
        DuckDB sums floats in PARALLEL, and float addition is not
        associative -- so every call returned a different fingerprint. A
        shard concluded its cache was stale before every sweep and
        re-downloaded the whole bar history each time."""
        answers = {bars.fingerprint("TESTQ") for _ in range(8)}
        assert len(answers) == 1, f"fingerprint is not stable: {answers}"
        assert answers != {None}

    def test_it_changes_when_a_single_price_changes(self, tmp_path, frame, monkeypatch):
        before_root = tmp_path / "before"
        _write_warehouse(before_root, frame)
        monkeypatch.setenv("VAI_WAREHOUSE_DIR", str(before_root))
        before = bars.fingerprint("TESTQ")

        edited = frame.copy()
        edited.iloc[len(edited) // 2, edited.columns.get_loc("close")] += 0.01
        after_root = tmp_path / "after"
        _write_warehouse(after_root, edited)
        monkeypatch.setenv("VAI_WAREHOUSE_DIR", str(after_root))

        assert bars.fingerprint("TESTQ") != before

    def test_it_changes_when_a_bar_is_appended(self, tmp_path, frame, monkeypatch):
        root = tmp_path / "w"
        _write_warehouse(root, frame)
        monkeypatch.setenv("VAI_WAREHOUSE_DIR", str(root))
        before = bars.fingerprint("TESTQ")

        con = duckdb.connect(str(root / "market_data.duckdb"))
        con.execute(
            "INSERT INTO ohlcv VALUES ('TESTQ', TIMESTAMPTZ '2026-01-02 14:30:00+00', "
            "1.0, 2.0, 0.5, 1.5, 10)"
        )
        con.close()

        assert bars.fingerprint("TESTQ") != before

    def test_an_absent_ticker_or_warehouse_is_none(self, warehouse, tmp_path, monkeypatch):
        assert bars.fingerprint("NOPE") is None
        monkeypatch.setenv("VAI_WAREHOUSE_DIR", str(tmp_path / "nothing-here"))
        assert bars.fingerprint("TESTQ") is None


class TestLoadFrame:
    def test_it_loads_what_was_written(self, warehouse, frame):
        loaded = bars.load_frame("TESTQ")
        assert len(loaded) == len(frame)
        assert list(loaded.columns) == ["open", "high", "low", "close", "volume"]
        assert str(loaded.index.tz) == "UTC"
        assert loaded["close"].iloc[0] == pytest.approx(frame["close"].iloc[0])

    def test_available_tickers_and_row_count(self, warehouse, frame):
        assert bars.available_tickers() == {"TESTQ"}
        assert bars.row_count("TESTQ") == len(frame)
        assert bars.row_count("NOPE") is None
