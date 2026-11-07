"""A trained TFT's forecasts, made once for every bar of a history and looked
up by the exact inputs they were made from.

A forecast at bar t is a pure function of the model and of what the sizer
hands it: the ring's encoder window and the calendar's known decoder inputs
(research/ml/tft_sizing.py). It does not depend on the strategy, so every
run over the same bars asks the same question at the same bar, and a sweep
of N runs makes the same ~34 ms forward passes N times. `precompute` makes
each once, spread over processes; `CachedForecaster` answers a window from
the table when it holds it, and runs the model when it does not.

THE KEY IS THE INPUT, NOT THE TIME. Each entry is keyed by a BLAKE2b digest
of the float64 bytes of the encoder window and of the decoder's known
inputs. A run whose windows differ in any bit -- other bars, a stressed
path, another source file, a ring that began on another first bar -- misses,
and a miss runs the model. So the table can make a run faster but never
different: a hit returns what the model returned for those exact inputs.
The ring's rows are build_frame's, bit for bit (test_tft_sizing), which is
why a table built from the frame is hit by a backtest over the same bars.

THE FILE (.npz): `keys` (n, 16) uint8, `values` (n, prediction_length,
levels) float64, and the SHA-256 of the model's checkpoint, checked on
load: a table made by another model is refused.
"""

from __future__ import annotations

import hashlib
import os
import time
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

from engine.core.exceptions import ConfigurationError
from research.ml.tft_features import ROW, build_frame, future_bar_times, known_at, load_sources
from research.ml.tft_model import CHECKPOINT, read_manifest

CHUNK = 2000


def window_key(encoder: np.ndarray, decoder_known: np.ndarray) -> bytes:
    """The digest a forecast is filed under."""
    digest = hashlib.blake2b(digest_size=16)
    digest.update(np.ascontiguousarray(encoder, dtype=np.float64).tobytes())
    digest.update(b"|")
    digest.update(np.ascontiguousarray(decoder_known, dtype=np.float64).tobytes())
    return digest.digest()


def decoder_known(ts, prediction_length: int, bars_per_day: int) -> np.ndarray:
    """The known inputs of bars t .. t+H-1, as TemporalFusionTransformerSizer
    builds them (_decoder_known)."""
    times = [ts, *future_bar_times(ts, prediction_length - 1, bars_per_day)]
    return np.array([known_at(t) for t in times], dtype=np.float64)


def frame_rows(bars: pd.DataFrame, manifest: dict) -> tuple[np.ndarray, pd.DatetimeIndex]:
    """The ring rows of every bar, and their stamps, with the model's own
    outside series."""
    sources = load_sources(manifest["sources"])
    frame = build_frame(bars, sources, manifest["symbol"])
    return frame[list(ROW)].to_numpy(dtype=np.float64), pd.DatetimeIndex(frame["timestamp"])


# -- the worker side: one model per process ------------------------------------

_WORKER: dict = {}


def _init_worker(model_dir: str, rows: np.ndarray, stamps: list, H: int, per_day: int) -> None:
    from research.ml.tft_model import TftForecaster

    _WORKER.update(
        forecaster=TftForecaster(model_dir), rows=rows, stamps=stamps, H=H, per_day=per_day
    )


def _forecast_range(bounds: tuple[int, int]) -> tuple[list[bytes], np.ndarray]:
    forecaster = _WORKER["forecaster"]
    rows, stamps, L = _WORKER["rows"], _WORKER["stamps"], forecaster.encoder_length
    keys, values = [], []
    for t in range(*bounds):
        encoder = rows[t - L : t]
        known = decoder_known(stamps[t], _WORKER["H"], _WORKER["per_day"])
        keys.append(window_key(encoder, known))
        values.append(forecaster.forecast(encoder, known))
    return keys, np.asarray(values, dtype=np.float64)


def precompute(
    model_dir: str | Path,
    bars: pd.DataFrame,
    out: str | Path,
    *,
    workers: int | None = None,
    log: Callable[[str], None] = print,
) -> Path:
    """Forecast every bar of `bars` that has a full encoder window, and write
    the table. `bars` must start where the runs that will read it start: the
    ring's first row is the first bar's."""
    manifest = read_manifest(model_dir)
    L, H = int(manifest["encoder_length"]), int(manifest["prediction_length"])
    rows, stamps = frame_rows(bars, manifest)
    if len(rows) <= L:
        raise ConfigurationError(f"{len(rows)} bars do not fill one {L}-bar encoder window")
    bounds = [(a, min(a + CHUNK, len(rows))) for a in range(L, len(rows), CHUNK)]
    workers = max(1, min(workers or (os.cpu_count() or 1), len(bounds)))
    started = time.monotonic()
    keys: list[bytes] = []
    values: list[np.ndarray] = []
    with ProcessPoolExecutor(
        max_workers=workers,
        initializer=_init_worker,
        initargs=(str(model_dir), rows, list(stamps), H, int(manifest["bars_per_day"])),
    ) as pool:
        for i, (k, v) in enumerate(pool.map(_forecast_range, bounds), 1):
            keys.extend(k)
            values.append(v)
            if i % max(1, len(bounds) // 10) == 0:
                log(f"  {i}/{len(bounds)} chunks ({time.monotonic() - started:.0f}s)")
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        out,
        keys=np.frombuffer(b"".join(keys), dtype=np.uint8).reshape(-1, 16),
        values=np.concatenate(values),
        checkpoint=np.array(manifest["files"][CHECKPOINT]),
        first_bar=np.array(stamps[0].isoformat()),
    )
    log(f"{len(keys):,} forecasts -> {out} ({time.monotonic() - started:.0f}s, {workers} workers)")
    return out


def load_table(path: str | Path, model_dir: str | Path) -> dict[bytes, np.ndarray]:
    """The table at `path`, refused unless the model in `model_dir` made it."""
    path = Path(path)
    if not path.exists():
        raise ConfigurationError(f"forecast cache not found: {path}")
    with np.load(path, allow_pickle=False) as data:
        made_by = str(data["checkpoint"])
        if made_by != read_manifest(model_dir)["files"][CHECKPOINT]:
            raise ConfigurationError(f"{path} was made by another model than {model_dir}")
        keys, values = data["keys"], data["values"]
        return {bytes(k): values[i] for i, k in enumerate(keys)}


class CachedForecaster:
    """tft_sizing.QuantileForecaster from a precomputed table, falling back
    to the model itself (loaded on the first miss) for any window the table
    does not hold."""

    def __init__(self, model_dir: str | Path, cache: str | Path) -> None:
        self.directory = Path(model_dir)
        manifest = read_manifest(self.directory)
        self.manifest = manifest
        self.levels = tuple(float(q) for q in manifest["quantiles"])
        self.encoder_length = int(manifest["encoder_length"])
        self.prediction_length = int(manifest["prediction_length"])
        self.bars_per_day = int(manifest["bars_per_day"])
        self.valid_from = pd.Timestamp(manifest["valid_from"])
        self.sources = dict(manifest["sources"])
        self._table = load_table(cache, self.directory)
        self._model = None
        self.hits = 0
        self.misses = 0

    def forecast(self, encoder: np.ndarray, decoder_known: np.ndarray) -> np.ndarray:
        found = self._table.get(window_key(encoder, decoder_known))
        if found is not None:
            self.hits += 1
            return found
        self.misses += 1
        if self._model is None:
            from research.ml.tft_model import TftForecaster

            self._model = TftForecaster(self.directory)
        return self._model.forecast(encoder, decoder_known)


def summary(path: str | Path) -> dict:
    with np.load(path, allow_pickle=False) as data:
        return {
            "forecasts": int(data["keys"].shape[0]),
            "first_bar": str(data["first_bar"]),
            "mb": round(Path(path).stat().st_size / 1e6, 1),
        }


__all__ = [
    "CachedForecaster",
    "decoder_known",
    "frame_rows",
    "load_table",
    "precompute",
    "summary",
    "window_key",
]
