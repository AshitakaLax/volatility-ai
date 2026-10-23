"""engine/warehouse/lake.py: the refresh's direct reads and whole-partition
writes of the bar lake. Everything written is read back through the
warehouse's own `ohlcv` view (bars.load_frame), which is what every backtest
reads. Skips without duckdb, like the other warehouse tests."""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

duckdb = pytest.importorskip("duckdb")

from engine.core.exceptions import DataValidationError  # noqa: E402
from engine.warehouse import bars, ingest, lake  # noqa: E402
from engine.warehouse.connection import open_warehouse  # noqa: E402
from engine.warehouse.schema import initialize, refresh_views  # noqa: E402


def _session(day: str, minutes: int = 5, price: float = 100.0, start: str = "09:30"):
    """`minutes` one-minute bars from `start` Eastern on `day`."""
    index = (
        pd.date_range(f"{day} {start}", periods=minutes, freq="1min", tz="America/New_York")
        .tz_convert("UTC")
        .rename("timestamp")
    )
    close = [price + 0.01 * i for i in range(minutes)]
    return pd.DataFrame(
        {
            "open": close,
            "high": [c + 0.05 for c in close],
            "low": [c - 0.05 for c in close],
            "close": close,
            "volume": [1000 + i for i in range(minutes)],
        },
        index=index,
    )


def _bars(*days: str, **kwargs) -> pd.DataFrame:
    return pd.concat([_session(day, **kwargs) for day in days])


def _ingest(root, frame: pd.DataFrame, ticker: str = "TESTQ") -> None:
    """Load bars the way tools/build_warehouse.py --ingest does: a CSV
    through DuckDB's partitioned COPY, APPENDing uuid-named files."""
    path = root.parent / f"{ticker}-{len(list(root.parent.glob('*.csv')))}.csv"
    frame.reset_index().assign(
        timestamp=lambda f: f["timestamp"].map(lambda t: t.isoformat())
    ).to_csv(path, index=False)
    con = open_warehouse(root)
    try:
        initialize(con, root)
        ingest.ingest_ohlcv_csv(con, root, path, ticker)
        refresh_views(con, root)
    finally:
        con.close()


@pytest.fixture
def root(tmp_path, monkeypatch):
    path = tmp_path / "warehouse"
    path.mkdir()
    monkeypatch.setenv("VAI_WAREHOUSE_DIR", str(path))
    return path


def _files(root, ticker="TESTQ", year=None):
    base = lake.fund_dir(root, ticker)
    pattern = f"year={year}/*.parquet" if year else "year=*/*.parquet"
    return sorted(p.relative_to(base).as_posix() for p in base.glob(pattern))


def _same(a: pd.DataFrame, b: pd.DataFrame) -> None:
    a = a.set_axis(a.index.as_unit("ns"))
    b = b.set_axis(b.index.as_unit("ns"))
    pd.testing.assert_frame_equal(a, b, check_freq=False, check_index_type=False)


# --------------------------------------------------------------------
# Reading
# --------------------------------------------------------------------


def test_a_fund_with_no_files_reads_as_no_bars(root):
    assert lake.read_bars(root, "NOPE").empty
    assert lake.session_counts(root, "NOPE").empty
    assert lake.stored_years(root, "NOPE") == []


def test_it_reads_what_the_ingest_wrote_without_the_catalog(root):
    frame = _bars("2025-12-30", "2025-12-31", "2026-01-02")
    _ingest(root, frame)
    _same(lake.read_bars(root, "TESTQ"), frame)
    _same(lake.read_bars(root, "TESTQ", years=[2026]), _session("2026-01-02"))
    counts = lake.session_counts(root, "TESTQ")
    assert list(counts.index) == [date(2025, 12, 30), date(2025, 12, 31), date(2026, 1, 2)]
    assert list(counts) == [5, 5, 5]


# --------------------------------------------------------------------
# update_sessions
# --------------------------------------------------------------------


def test_new_sessions_are_added_and_the_view_reads_them(root):
    _ingest(root, _bars("2026-10-06", "2026-10-07"))
    fresh = _bars("2026-10-08", "2026-10-09")

    written = lake.update_sessions(root, "TESTQ", fresh)

    assert written.years == (2026,)
    expected = _bars("2026-10-06", "2026-10-07", "2026-10-08", "2026-10-09")
    _same(bars.load_frame("TESTQ"), expected)


def test_a_session_fetched_again_replaces_the_stored_one_whole(root):
    """A session stored while it traded (two bars) is completed, and one
    whose bars were corrected takes the new ones: never a mix of fetches."""
    stored = pd.concat([_session("2026-10-06"), _session("2026-10-07", minutes=2)])
    _ingest(root, stored)
    corrected = _session("2026-10-06", price=100.5)
    whole = _session("2026-10-07", minutes=5, price=101.0)

    lake.update_sessions(root, "TESTQ", pd.concat([corrected, whole]))

    _same(bars.load_frame("TESTQ"), pd.concat([corrected, whole]))


def test_sessions_it_was_not_given_are_left_alone(root):
    _ingest(root, _bars("2026-10-05", "2026-10-06", "2026-10-07"))
    lake.update_sessions(root, "TESTQ", _session("2026-10-06", price=99.0))

    loaded = bars.load_frame("TESTQ")
    _same(
        loaded,
        pd.concat(
            [_session("2026-10-05"), _session("2026-10-06", price=99.0), _session("2026-10-07")]
        ),
    )


def test_a_year_the_ingest_appended_to_becomes_one_file(root):
    """build_warehouse.py APPENDs a uuid-named file per ingest; a refreshed
    year is one data_0.parquet holding all of it, with nothing repeated."""
    _ingest(root, _bars("2026-10-05"))
    _ingest(root, _bars("2026-10-06"))
    assert len(_files(root, year=2026)) == 2

    lake.update_sessions(root, "TESTQ", _session("2026-10-07"))

    assert _files(root, year=2026) == ["year=2026/data_0.parquet"]
    _same(bars.load_frame("TESTQ"), _bars("2026-10-05", "2026-10-06", "2026-10-07"))


def test_only_the_years_it_touches_are_rewritten(root):
    _ingest(root, _bars("2025-06-02", "2026-10-05"))
    before = _files(root, year=2025)

    written = lake.update_sessions(root, "TESTQ", _session("2026-10-06"))

    assert written.years == (2026,)
    assert _files(root, year=2025) == before


def test_a_new_year_and_a_new_fund_appear(root):
    _ingest(root, _session("2026-12-31"))
    lake.update_sessions(root, "TESTQ", _session("2027-01-04"))
    lake.update_sessions(root, "NEWQ", _session("2027-01-04", price=50.0))

    assert lake.stored_years(root, "TESTQ") == [2026, 2027]
    _same(bars.load_frame("NEWQ"), _session("2027-01-04", price=50.0))


def test_the_written_file_keeps_the_ingests_schema(root):
    _ingest(root, _session("2026-10-05"))
    lake.update_sessions(root, "TESTQ", _session("2026-10-06"))
    ingested = lake.fund_dir(root, "TESTQ")
    con = duckdb.connect()
    try:
        schemas = {
            path.name: con.execute(
                "SELECT name, type, converted_type FROM parquet_schema(?)", [str(path)]
            ).fetchall()
            for path in ingested.glob("year=2026/*.parquet")
        }
    finally:
        con.close()
    (schema,) = schemas.values()
    assert [row[0] for row in schema] == [
        "duckdb_schema",
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]
    assert ("timestamp", "INT64", "TIMESTAMP_MICROS") in schema
    assert ("volume", "INT64", "INT_64") in schema


def test_bars_it_could_not_store_are_refused_and_nothing_is_written(root):
    _ingest(root, _session("2026-10-05"))
    before = _files(root)
    repeated = pd.concat([_session("2026-10-06"), _session("2026-10-06")])
    naive = _session("2026-10-06").tz_localize(None)
    negative = _session("2026-10-06").assign(low=-1.0)

    for frame in (repeated, naive, negative):
        with pytest.raises(DataValidationError):
            lake.update_sessions(root, "TESTQ", frame)
    assert _files(root) == before


# --------------------------------------------------------------------
# replace_fund
# --------------------------------------------------------------------


def test_a_replacement_takes_every_year_and_keeps_the_previous_copy(root):
    _ingest(root, _bars("2024-03-01", "2025-03-03", "2026-03-02"))
    new = _bars("2025-03-03", "2026-03-02", "2026-03-03", price=200.0)

    written = lake.replace_fund(root, "TESTQ", new)

    _same(bars.load_frame("TESTQ"), new)
    assert lake.stored_years(root, "TESTQ") == [2025, 2026]  # 2024 went with the old bars
    assert written.previous is not None
    assert sorted(p.name for p in written.previous.iterdir()) == [
        "year=2024",
        "year=2025",
        "year=2026",
    ]


def test_only_the_last_previous_copy_is_kept(root):
    _ingest(root, _session("2026-03-02", price=1.0))
    lake.replace_fund(root, "TESTQ", _session("2026-03-02", price=2.0))
    written = lake.replace_fund(root, "TESTQ", _session("2026-03-02", price=3.0))

    kept = next(written.previous.glob("year=2026/*.parquet"))
    con = duckdb.connect()
    try:
        assert con.execute("SELECT min(close) FROM read_parquet(?)", [str(kept)]).fetchone() == (
            2.0,
        )
    finally:
        con.close()


def test_replacing_a_fund_with_nothing_is_refused(root):
    _ingest(root, _session("2026-03-02"))
    with pytest.raises(DataValidationError, match="none"):
        lake.replace_fund(root, "TESTQ", lake.empty_bars())
    assert len(bars.load_frame("TESTQ")) == 5


# --------------------------------------------------------------------
# The swap
# --------------------------------------------------------------------


def test_the_exchange_swaps_two_directories_in_place(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    (a / "x").write_text("from a")
    (b / "x").write_text("from b")

    if not lake._exchange(a, b):
        pytest.skip("no renameat2 RENAME_EXCHANGE on this platform or filesystem")

    assert (a / "x").read_text() == "from b"
    assert (b / "x").read_text() == "from a"


def test_without_the_exchange_two_renames_do_the_same(root, monkeypatch):
    monkeypatch.setattr(lake, "_exchange", lambda a, b: False)
    _ingest(root, _bars("2026-10-05"))
    lake.update_sessions(root, "TESTQ", _session("2026-10-06"))
    lake.replace_fund(root, "TESTQ", _bars("2026-10-05", "2026-10-06", price=7.0))

    _same(bars.load_frame("TESTQ"), _bars("2026-10-05", "2026-10-06", price=7.0))
    assert not any(p.name.startswith("work-") for p in (root / lake.STAGING_DIR).iterdir())


def test_a_write_that_fails_leaves_the_lake_and_no_work_behind(root, monkeypatch):
    _ingest(root, _bars("2026-10-05"))
    before = _files(root)

    def broken(directory, frame):
        directory.mkdir(parents=True)
        raise OSError("disk full")

    monkeypatch.setattr(lake, "_write_year", broken)
    with pytest.raises(OSError):
        lake.update_sessions(root, "TESTQ", _session("2026-10-06"))

    assert _files(root) == before
    assert not any(p.name.startswith("work-") for p in (root / lake.STAGING_DIR).iterdir())


# --------------------------------------------------------------------
# One refresh at a time
# --------------------------------------------------------------------


def test_a_second_refresh_is_refused_while_one_holds_the_lock(root):
    pytest.importorskip("fcntl")
    with lake.refresh_lock(root), pytest.raises(lake.RefreshBusy), lake.refresh_lock(root):
        pass
    with lake.refresh_lock(root):  # released
        pass


def test_cleaning_removes_a_killed_runs_work_but_not_the_previous_copies(root):
    staging = root / lake.STAGING_DIR
    (staging / "work-1-2" / "year=2026").mkdir(parents=True)
    (staging / lake.PREVIOUS_DIR / "ticker=TESTQ").mkdir(parents=True)

    assert lake.clean_staging(root) == 1
    assert sorted(p.name for p in staging.iterdir()) == [lake.PREVIOUS_DIR]
