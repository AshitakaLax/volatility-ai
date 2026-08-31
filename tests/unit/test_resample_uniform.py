"""Tests for resample_uniform.py.

src/historical_data.resample_to_uniform_minutes has its own tests --
this covers the SCRIPT around it: the naming convention, the guards
that stop it destroying a raw download, the schema/tz validation that
turns opaque downstream errors into stated ones, and the provenance
sidecar (the whole reason this script exists, since the extuniform
dataset already on disk has none).
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from resample_uniform import (
    bars_per_session,
    default_output_path,
    load_minute_csv,
    main,
    parse_args,
    synthetic_fraction_by_year,
)
from src.exceptions import ConfigurationError, DataValidationError


def _write_source(path: Path, *, tz: str | None = "UTC", drop_col: str | None = None) -> Path:
    """Two sessions of sparse regular-hours bars, so resampling has real
    gaps to fill rather than being a no-op."""
    rows = []
    for day in ("2024-01-02", "2024-01-03"):
        # 14:30 UTC == 09:30 New York. Deliberately sparse: 4 bars in a
        # window that will be filled out to many more.
        for minute, price in ((30, 100.0), (31, 100.5), (45, 101.0), (59, 100.25)):
            rows.append(
                {
                    "timestamp": f"{day}T14:{minute:02d}:00+00:00",
                    "open": price,
                    "high": price + 0.1,
                    "low": price - 0.1,
                    "close": price,
                    "volume": 1000.0,
                }
            )
    df = pd.DataFrame(rows)
    if tz is None:
        df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.tz_localize(None)
    if drop_col:
        df = df.drop(columns=[drop_col])
    df.to_csv(path, index=False)
    return path


# --- output naming ---


@pytest.mark.parametrize(
    ("stem", "expected"),
    [
        ("RSP_1Min_sip_all_ext_2016-01-01_2026-08-30", "RSP_1Min_sip_all_extuniform_2016-01-01_2026-08-30"),
        ("TQQQ_1Min_sip_all_rth_2016-01-01_2026-08-21", "TQQQ_1Min_sip_all_rthuniform_2016-01-01_2026-08-21"),
        ("something_without_a_scope_tag", "something_without_a_scope_tag_uniform"),
    ],
)
def test_default_output_name_marks_the_file_uniform(stem, expected):
    """Mirrors the naming already on disk rather than inventing a second
    convention -- and never leaves a resampled file indistinguishable
    from a raw download."""
    assert default_output_path(Path(f"data/{stem}.csv")).name == f"{expected}.csv"


# --- guards ---


def test_refuses_to_resample_in_place(tmp_path):
    """data/ is git-ignored, so overwriting a raw download with its own
    resampled form is unrecoverable."""
    src = _write_source(tmp_path / "IN_1Min_ext_a_b.csv")
    with pytest.raises(ConfigurationError, match="resolves to the input file"):
        main(["--input", str(src), "--output", str(src)])


def test_missing_input_is_reported_not_crashed(tmp_path):
    with pytest.raises(ConfigurationError, match="Input file not found"):
        main(["--input", str(tmp_path / "nope.csv")])


def test_rejects_a_timezone_naive_source(tmp_path):
    """resample_to_uniform_minutes calls tz_convert immediately, which
    raises an opaque TypeError on a naive index. Say what is actually
    wrong instead."""
    src = _write_source(tmp_path / "naive.csv", tz=None)
    with pytest.raises(DataValidationError, match="timezone-naive"):
        load_minute_csv(src)


def test_rejects_a_source_missing_a_required_column(tmp_path):
    src = _write_source(tmp_path / "novol.csv", drop_col="volume")
    with pytest.raises(DataValidationError, match="missing required column"):
        load_minute_csv(src)


def test_will_not_clobber_an_existing_output_without_force(tmp_path):
    src = _write_source(tmp_path / "IN_1Min_ext_a_b.csv")
    out = tmp_path / "out.csv"
    out.write_text("existing\n")
    with pytest.raises(ConfigurationError, match="already exists"):
        main(["--input", str(src), "--output", str(out)])


# --- the transform, end to end ---


def _run(tmp_path, **kw):
    src = _write_source(tmp_path / "IN_1Min_ext_a_b.csv")
    out = tmp_path / "out.csv"
    argv = ["--input", str(src), "--output", str(out)]
    for k, v in kw.items():
        argv += [f"--{k.replace('_', '-')}", str(v)]
    assert main(argv) == 0
    return out


def test_every_session_gets_the_same_bar_count(tmp_path):
    out = _run(tmp_path, session_start="09:30", session_end="10:00")
    df = pd.read_csv(out, parse_dates=["timestamp"]).set_index("timestamp")
    counts = bars_per_session(df)
    assert counts.nunique() == 1
    assert counts.iloc[0] == 30  # 09:30-10:00 exclusive


def test_synthesized_bars_are_flat_zero_volume_and_carry_the_last_price(tmp_path):
    """The claim a synthetic bar makes is 'no trade occurred and the
    last price still stood' -- it must never look like a price move,
    because the intrabar fill model fills on touches."""
    out = _run(tmp_path, session_start="09:30", session_end="10:00")
    df = pd.read_csv(out, parse_dates=["timestamp"]).set_index("timestamp")
    synthetic = df[df["volume"] == 0.0]
    assert len(synthetic) > 0, "fixture is too dense to exercise synthesis"
    assert (synthetic["high"] == synthetic["low"]).all()
    assert (synthetic["open"] == synthetic["close"]).all()
    assert (synthetic["high"] == synthetic["close"]).all()


def test_real_bars_are_left_untouched(tmp_path):
    """Resampling must add bars, never alter the ones that traded."""
    src = _write_source(tmp_path / "IN_1Min_ext_a_b.csv")
    before = load_minute_csv(src)
    out = tmp_path / "out.csv"
    assert main(["--input", str(src), "--output", str(out), "--session-start", "09:30", "--session-end", "10:00"]) == 0
    after = pd.read_csv(out, parse_dates=["timestamp"]).set_index("timestamp")
    common = before.index.intersection(after.index)
    assert len(common) == len(before)
    for col in ("open", "high", "low", "close", "volume"):
        pd.testing.assert_series_equal(
            before.loc[common, col], after.loc[common, col], check_names=False
        )


def test_force_allows_a_deliberate_overwrite(tmp_path):
    src = _write_source(tmp_path / "IN_1Min_ext_a_b.csv")
    out = tmp_path / "out.csv"
    out.write_text("existing\n")
    assert main(["--input", str(src), "--output", str(out), "--force"]) == 0
    assert "existing" not in out.read_text()


# --- provenance sidecar: the reason this script exists ---


def test_writes_a_sidecar_tying_the_output_to_its_exact_source(tmp_path):
    """The extuniform dataset already on disk has no sidecar, so nothing
    records which download it came from. That is the gap being closed."""
    out = _run(tmp_path, session_start="09:30", session_end="10:00")
    meta = json.loads(out.with_suffix(".meta.json").read_text())

    assert meta["transform"] == "resample_to_uniform_minutes"
    assert meta["produced_by"] == "resample_uniform.py"
    assert meta["derived_from"].endswith("IN_1Min_ext_a_b.csv")
    assert len(meta["derived_from_sha256"]) == 64
    assert len(meta["sha256"]) == 64
    assert meta["session_start"] == "09:30"
    assert meta["session_end"] == "10:00"
    assert meta["bars_per_session"] == 30
    assert meta["bars_per_session_uniform"] is True
    assert meta["bars_synthesized"] > 0
    assert meta["rows"] == 60  # 2 sessions x 30


def test_the_sidecar_records_the_per_year_synthetic_gradient(tmp_path):
    """A single aggregate percentage hides the thing that actually
    biases a vol-scaled strategy: synthetic density drifting across
    eras. The by-year breakdown is what makes that visible."""
    out = _run(tmp_path, session_start="09:30", session_end="10:00")
    meta = json.loads(out.with_suffix(".meta.json").read_text())
    # JSON object keys are always strings -- that is the format's rule,
    # not a quirk of this writer, so a reader must index with "2024".
    by_year = meta["synthetic_pct_by_year"]
    assert set(by_year) == {"2024"}
    assert 0.0 < by_year["2024"] < 100.0


def test_sidecar_checksum_matches_the_file_actually_written(tmp_path):
    from src.historical_data import _sha256

    out = _run(tmp_path, session_start="09:30", session_end="10:00")
    meta = json.loads(out.with_suffix(".meta.json").read_text())
    assert meta["sha256"] == _sha256(out)


# --- helpers ---


def test_synthetic_fraction_by_year_counts_only_synthetic_bars():
    idx = pd.date_range("2024-01-02 14:30", periods=4, freq="1min", tz="UTC")
    df = pd.DataFrame(index=idx)
    mask = pd.Series([True, False, True, False], index=idx)
    result = synthetic_fraction_by_year(df, mask)
    assert result.loc[2024, "bars"] == 4
    assert result.loc[2024, "synthetic"] == 2
    assert result.loc[2024, "synthetic_pct"] == pytest.approx(50.0)


def test_session_bounds_are_configurable():
    args = parse_args(["--input", "x.csv", "--session-start", "09:30", "--session-end", "16:00"])
    assert (args.session_start, args.session_end) == ("09:30", "16:00")


def test_session_bounds_default_to_the_full_extended_session():
    """04:00-20:00 is 960 minutes, which is what this project's
    hf_local_reference configs set bars_per_day to."""
    args = parse_args(["--input", "x.csv"])
    assert (args.session_start, args.session_end) == ("04:00", "20:00")
