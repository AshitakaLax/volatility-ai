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


class TestAMovedWarehouse:
    """Views used to store an ABSOLUTE read_parquet path, fixed when created.
    A warehouse copied elsewhere (it moved from C:/workspace on Windows to
    Linux) read as empty -- every query failed and load_frame, which never
    raises, answered "no data". They are relative now, resolved through
    the connection's file_search_path, so one catalog also serves the host
    and a container that mounts it at /app/warehouse."""

    @staticmethod
    def _lake_warehouse(root, frame):
        from engine.warehouse.connection import open_warehouse
        from engine.warehouse.schema import refresh_views

        part = root / "ohlcv" / "ticker=TESTQ" / "year=2024"
        part.mkdir(parents=True)
        frame.reset_index().to_parquet(part / "part-0.parquet", index=False)
        con = open_warehouse(root)
        refresh_views(con, root)
        con.close()

    @staticmethod
    def _view_sql(root):
        con = duckdb.connect(str(root / "market_data.duckdb"), read_only=True)
        try:
            return con.execute(
                "SELECT sql FROM duckdb_views() WHERE view_name = 'ohlcv'"
            ).fetchone()[0]
        finally:
            con.close()

    def test_reads_survive_moving_the_directory(self, tmp_path, frame, monkeypatch):
        import shutil

        old, new = tmp_path / "old" / "warehouse", tmp_path / "new" / "warehouse"
        self._lake_warehouse(old, frame)
        shutil.move(str(old), str(new))
        monkeypatch.setenv("VAI_WAREHOUSE_DIR", str(new))

        assert bars.available_tickers() == {"TESTQ"}
        assert len(bars.load_frame("TESTQ")) == len(frame)

    def test_two_mount_points_share_one_catalog_without_rewriting_it(
        self, tmp_path, frame, monkeypatch
    ):
        """The host and a container read the same files from different
        paths. A catalog that had to be rewritten for each would flip on
        every switch -- and fail whenever the other side held it open."""
        import shutil

        host, app = tmp_path / "host" / "warehouse", tmp_path / "app" / "warehouse"
        self._lake_warehouse(host, frame)
        before = self._view_sql(host)
        assert str(tmp_path) not in before, "the view must not name where it lives"

        def read_from(root):
            monkeypatch.setenv("VAI_WAREHOUSE_DIR", str(root))
            assert len(bars.load_frame("TESTQ")) == len(frame)
            assert self._view_sql(root) == before

        read_from(host)
        shutil.move(str(host), str(app))
        read_from(app)
        shutil.move(str(app), str(host))
        read_from(host)

    def test_an_older_absolute_view_is_rewritten_once(self, tmp_path, frame, monkeypatch):
        import shutil

        from engine.warehouse.connection import _has_absolute_views, open_warehouse

        old, new = tmp_path / "old" / "warehouse", tmp_path / "new" / "warehouse"
        self._lake_warehouse(old, frame)
        con = duckdb.connect(str(old / "market_data.duckdb"))
        con.execute(
            f"CREATE OR REPLACE VIEW ohlcv AS SELECT * FROM read_parquet("
            f"'{(old / 'ohlcv').as_posix()}/**/*.parquet', hive_partitioning = true)"
        )
        con.close()
        shutil.move(str(old), str(new))

        monkeypatch.setenv("VAI_WAREHOUSE_DIR", str(new))
        assert len(bars.load_frame("TESTQ")) == len(frame)
        con = open_warehouse(new, read_only=True)
        try:
            assert not _has_absolute_views(con)
        finally:
            con.close()


class TestAWarehouseBeingWritten:
    """Another process writing the warehouse holds DuckDB's file lock; a
    read waits a write out instead of answering "no data"."""

    def test_a_locked_warehouse_is_retried_until_it_opens(self, tmp_path, frame, monkeypatch):
        import engine.warehouse.connection as connection

        _write_warehouse(tmp_path, frame)
        real = connection.open_warehouse
        refusals = [RuntimeError("IO Error: Could not set lock on file")] * 2
        naps = []

        def locked_twice(root, **kwargs):
            if refusals:
                raise refusals.pop()
            return real(root, **kwargs)

        monkeypatch.setattr(connection, "open_warehouse", locked_twice)
        con = bars._connect(tmp_path, sleep=naps.append, clock=lambda: 0.0)
        assert con is not None and len(naps) == 2
        con.close()

    def test_anything_else_is_no_data_at_once(self, tmp_path, frame, monkeypatch):
        import engine.warehouse.connection as connection

        _write_warehouse(tmp_path, frame)

        def corrupt(root, **kwargs):
            raise RuntimeError("not a DuckDB file")

        monkeypatch.setattr(connection, "open_warehouse", corrupt)
        naps = []
        assert bars._connect(tmp_path, sleep=naps.append) is None and naps == []

    def test_a_lock_that_outlasts_the_wait_is_no_data(self, tmp_path, frame, monkeypatch):
        import engine.warehouse.connection as connection

        _write_warehouse(tmp_path, frame)

        def always_locked(root, **kwargs):
            raise RuntimeError("Could not set lock on file")

        monkeypatch.setattr(connection, "open_warehouse", always_locked)
        now = iter([0.0, 5.0, 11.0])
        naps = []
        assert bars._connect(tmp_path, sleep=naps.append, clock=lambda: next(now)) is None
        assert len(naps) == 1
