#!/usr/bin/env python
"""
Give every session in a downloaded minute dataset the same bar count.

WHY THIS SCRIPT EXISTS AT ALL. src/historical_data.py has had
resample_to_uniform_minutes since the extended-hours dataset was built,
but nothing in the repository ever called it: `cli.py fetch-data` does
not offer it, and no script wrapped it. The dataset every recorded
sweep result was produced against --
data/TQQQ_1Min_hf_splitdiv_extuniform_2016-01-01_2026-08-07.csv,
2,558,400 bars at 960/session -- was therefore made by an ad-hoc
invocation that was never committed. That file has no sidecar and no
recorded provenance: nothing on disk states which source file it came
from, what session window was used, or how many of its bars are
fabricated. This script closes that gap, so the next such dataset is
reproducible from a command rather than from memory.

WHAT UNIFORM RESAMPLING IS FOR. HighFrequencyLocalReferenceSizing takes
bars_per_day as a single constant for the whole backtest, and converts
every window it owns (lookback_days, vol_fast_days, vol_slow_days)
through it. On a raw extended-hours download that constant is a lie:
real bar density drifted 2.08x from 2016 to 2026 as pre/post-market
liquidity grew, so "0.25 days" silently means a different number of
observations in 2016 than in 2026. Filling every session out to the
same minute grid makes bars_per_day true by construction.

WHAT IT COSTS -- REPORTED, NOT BURIED. A synthesized bar is flat
(open==high==low==close of the last real print) with volume 0. It
cannot manufacture a fill, but it IS a genuine zero to any realized-
volatility measure, so volatility reads low exactly where synthetic
bars are dense. On the TQQQ dataset that density ran 52.2% of bars in
2016 against 0.6% in 2026 -- a strong year-correlated gradient, and
with this project's measured-negative vol_scale_exponent that means
sizing up more in the early years for a reason that is an artifact of
the fill pattern rather than a market signal.
HighFrequencyLocalReferenceSizing.record_tick carries a structural
detector to skip these bars for exactly that reason (see its module
docstring's "SYNTHETIC BARS" section). This script therefore prints the
per-year synthetic fraction every time it runs: the gradient is a
property of the dataset you are about to create, and it should be
looked at before that dataset is trusted, not discovered later.

Usage:

    python resample_uniform.py --input data/RSP_1Min_sip_all_ext_2016-01-01_2026-08-30.csv

    python resample_uniform.py \
        --input data/RSP_1Min_sip_all_ext_2016-01-01_2026-08-30.csv \
        --output data/RSP_1Min_extuniform.csv \
        --session-start 09:30 --session-end 16:00
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from src.exceptions import ConfigurationError, DataValidationError
from src.historical_data import (
    BACKTEST_COLUMNS,
    EXCHANGE_TZ,
    _sha256,
    resample_to_uniform_minutes,
    write_csv,
)


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Resample a minute-bar CSV so every session has the same bar count."
    )
    parser.add_argument("--input", required=True, help="Source minute-bar CSV")
    parser.add_argument(
        "--output",
        default=None,
        help=(
            "Destination CSV. Default: the input's name with its session-scope tag "
            "replaced by 'extuniform' (or '_extuniform' appended if it has none)."
        ),
    )
    parser.add_argument(
        "--session-start",
        default="04:00",
        help=(
            "First minute of the uniform grid, exchange-local (default: 04:00). "
            "The default spans the full extended-hours session; 04:00-20:00 is 960 "
            "bars, which is what this project's hf_local_reference configs set "
            "bars_per_day to."
        ),
    )
    parser.add_argument(
        "--session-end",
        default="20:00",
        help="End of the uniform grid, exclusive, exchange-local (default: 20:00).",
    )
    parser.add_argument(
        "--force", action="store_true", help="Overwrite an existing output file"
    )
    return parser.parse_args(argv)


def default_output_path(input_path: Path) -> Path:
    """Name the output after the input, marking it uniform.

    Mirrors the naming already on disk
    (TQQQ_1Min_hf_splitdiv_extuniform_...) rather than inventing a
    second convention: an '_ext' scope tag becomes '_extuniform', an
    '_rth' one becomes '_rthuniform', and anything else simply gains a
    '_uniform' suffix so the file can never be mistaken for a raw
    download.
    """
    stem = input_path.stem
    for tag, replacement in (("_ext_", "_extuniform_"), ("_rth_", "_rthuniform_")):
        if tag in stem:
            return input_path.with_name(stem.replace(tag, replacement) + input_path.suffix)
    return input_path.with_name(f"{stem}_uniform{input_path.suffix}")


def load_minute_csv(path: Path) -> pd.DataFrame:
    """Read a downloaded minute CSV the same way run_hf_sweep.py does.

    tz-awareness is asserted rather than assumed: resample_to_uniform_
    minutes calls tz_convert immediately, which raises an opaque
    TypeError on a naive index. Every file cli.py fetch-data writes is
    tz-aware, so a naive one means the file was produced by something
    else and its timestamps' meaning is unknown -- worth stopping for.
    """
    df = pd.read_csv(path, parse_dates=["timestamp"]).set_index("timestamp")
    missing = [c for c in BACKTEST_COLUMNS if c not in df.columns]
    if missing:
        raise DataValidationError(
            f"{path} is missing required column(s) {missing}. Expected the backtest schema "
            f"{BACKTEST_COLUMNS} written by `cli.py fetch-data`."
        )
    if df.index.tz is None:
        raise DataValidationError(
            f"{path} has timezone-naive timestamps. Every file `cli.py fetch-data` writes is "
            "UTC-aware; a naive index means this file came from somewhere else and what its "
            "timestamps mean is unknown. Refusing to guess."
        )
    if not df.index.is_monotonic_increasing:
        df = df.sort_index()
    return df[BACKTEST_COLUMNS]


def synthetic_fraction_by_year(df: pd.DataFrame, synthetic_mask: pd.Series) -> pd.DataFrame:
    """Per-year synthetic-bar share -- the gradient this script exists
    to surface. See the module docstring for why it matters."""
    years = df.index.tz_convert(EXCHANGE_TZ).year
    grouped = synthetic_mask.groupby(years)
    return pd.DataFrame(
        {
            "bars": grouped.size(),
            "synthetic": grouped.sum().astype(int),
            "synthetic_pct": (grouped.mean() * 100.0).round(2),
        }
    )


def bars_per_session(df: pd.DataFrame) -> pd.Series:
    """Bar count per exchange-local session, for the uniformity check."""
    dates = df.index.tz_convert(EXCHANGE_TZ).date
    return pd.Series(1, index=pd.Index(dates, name="session")).groupby(level=0).sum()


def main(argv=None) -> int:
    args = parse_args(argv)
    input_path = Path(args.input)
    if not input_path.exists():
        raise ConfigurationError(f"Input file not found: {input_path}")
    output_path = Path(args.output) if args.output else default_output_path(input_path)
    if output_path.resolve() == input_path.resolve():
        raise ConfigurationError(
            f"--output resolves to the input file ({input_path}). Resampling in place would "
            "destroy the raw download, which data/ being git-ignored makes unrecoverable."
        )

    print(f"Reading {input_path} ...", flush=True)
    source = load_minute_csv(input_path)
    source_sessions = len({ts.date() for ts in source.index.tz_convert(EXCHANGE_TZ)})
    print(
        f"  {len(source):,} bars over {source_sessions:,} sessions "
        f"({source.index[0]} -> {source.index[-1]})",
        flush=True,
    )

    print(
        f"Resampling to a uniform {args.session_start}-{args.session_end} grid "
        f"(exchange-local, {EXCHANGE_TZ}) ...",
        flush=True,
    )
    uniform, synthesized = resample_to_uniform_minutes(
        source, session_start=args.session_start, session_end=args.session_end
    )
    if uniform.empty:
        raise DataValidationError(
            "Resampling produced an empty frame. That means no source bar fell inside the "
            f"{args.session_start}-{args.session_end} window -- check the session bounds "
            "against the data's actual trading hours."
        )

    # A synthesized bar is flat AND carries volume 0; the second half is
    # what distinguishes it from a real bar that happened not to move,
    # which resample_to_uniform_minutes leaves untouched. Recomputing
    # the mask here rather than threading one out of that function keeps
    # this script a pure consumer of the existing helper.
    synthetic_mask = (
        (uniform["high"] == uniform["low"])
        & (uniform["open"] == uniform["close"])
        & (uniform["volume"] == 0.0)
    )

    per_session = bars_per_session(uniform)
    distinct_counts = sorted(per_session.unique())
    sessions = len(per_session)

    print(f"\nWrote-pending: {len(uniform):,} bars over {sessions:,} sessions", flush=True)
    if len(distinct_counts) == 1:
        print(f"  bars per session: {distinct_counts[0]} (UNIFORM)", flush=True)
        print(
            f"  -> set bars_per_day: {distinct_counts[0]} in any strategy config using this file",
            flush=True,
        )
    else:
        # Not fatal: a session that traded only outside the declared
        # window legitimately yields a short row group. Reported loudly
        # because bars_per_day is then not exactly true for every day.
        print(
            f"  bars per session: NOT uniform -- {len(distinct_counts)} distinct counts "
            f"(min {distinct_counts[0]}, max {distinct_counts[-1]})",
            flush=True,
        )

    print(
        f"\n  synthesized {synthesized:,} bars "
        f"({synthesized / len(uniform) * 100:.1f}% of the output)",
        flush=True,
    )
    by_year = synthetic_fraction_by_year(uniform, synthetic_mask)
    print("\n  synthetic share by year (see this script's docstring on why this matters):")
    print("    " + by_year.to_string().replace("\n", "\n    "), flush=True)
    spread = by_year["synthetic_pct"].max() - by_year["synthetic_pct"].min()
    if spread > 20.0:
        print(
            f"\n  WARNING: synthetic share spans {spread:.1f} percentage points across years.\n"
            "  Realized volatility reads low where synthetic bars are dense, so a\n"
            "  vol-scaled strategy will size differently across eras for a reason that is\n"
            "  an artifact of bar density, not a market signal. HighFrequencyLocalReference\n"
            "  Sizing.record_tick detects and skips these bars; a strategy WITHOUT that\n"
            "  guard should not be run against this file.",
            flush=True,
        )

    written = write_csv(uniform, output_path, force=args.force)
    size_mb = written.stat().st_size / (1 << 20)
    checksum = _sha256(written)

    # Provenance sidecar -- the thing the existing extuniform file
    # lacks. Deliberately records the SOURCE checksum too, so a
    # resampled dataset can be tied back to the exact download it came
    # from even after data/ has been refreshed.
    meta = {
        "derived_from": str(input_path),
        "derived_from_sha256": _sha256(input_path),
        "derived_from_rows": len(source),
        "derived_from_sessions": source_sessions,
        "transform": "resample_to_uniform_minutes",
        "produced_by": "resample_uniform.py",
        "session_start": args.session_start,
        "session_end": args.session_end,
        "exchange_tz": EXCHANGE_TZ,
        "resampled_at": datetime.now(UTC).isoformat(),
        "rows": len(uniform),
        "sessions": sessions,
        # int() is load-bearing, not decoration: per_session.unique()
        # yields numpy int64, which json.dumps cannot serialize, so
        # default=str would silently write "960" as a STRING and any
        # consumer comparing it numerically would quietly get False.
        "bars_per_session": int(distinct_counts[0]) if len(distinct_counts) == 1 else None,
        "bars_per_session_uniform": len(distinct_counts) == 1,
        "bars_synthesized": synthesized,
        "synthetic_pct": round(synthesized / len(uniform) * 100.0, 4),
        "synthetic_pct_by_year": {
            int(year): float(pct) for year, pct in by_year["synthetic_pct"].items()
        },
        "first_timestamp": str(uniform.index[0]),
        "last_timestamp": str(uniform.index[-1]),
        "sha256": checksum,
    }
    meta_path = written.with_suffix(".meta.json")
    meta_path.write_text(json.dumps(meta, indent=2, default=str) + "\n")

    print(f"\nWrote {written}  ({size_mb:.1f} MB)", flush=True)
    print(f"  sha256   : {checksum[:16]}...", flush=True)
    print(f"  provenance: {meta_path}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
