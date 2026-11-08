"""A trained meta-label model, as research/ml/meta_label_sizing.py loads it.

--------------------------------------------------------------------
THE ARTIFACT: ONE MODEL PER WALK-FORWARD PERIOD

research/ml/meta_training.py writes a directory:

    manifest.json        what was trained, on what, how it scored, and
                         each segment's file, hash and calibration
    segment_00.txt ...   LightGBM boosters in their native TEXT format

Segment k was fitted only on labels resolved before its `valid_from`, and
answers for bars from its `valid_from` up to the next segment's. So a
backtest over the whole history is out of sample everywhere a model
speaks: before the first `valid_from` there is no model (the strategy
then sizes exactly as hf_local_reference), and the last segment, trained
on everything, is the one a live session uses.

No pickle: a text booster and JSON are read, never executed. Each file's
SHA-256 is checked against the manifest on load, so a model swapped
under a deployment fails loudly instead of trading.

--------------------------------------------------------------------
CALIBRATION IS PART OF THE MODEL

The booster's raw score is mapped through an isotonic curve fitted on
that segment's own held-out tail (stored as knots, applied with
numpy.interp). The strategy's thresholds are probabilities, so a model
that says 0.6 must be right about 60% of the time for them to mean what
they say (Meyer, Barziy & Joubert 2023 on calibration for sizing).

lightgbm is imported when a model is first loaded, never at import time:
strategy_registry imports this module's consumer unconditionally, and the
server and the Pi must start without requirements-ml.txt.
"""

from __future__ import annotations

import bisect
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from engine.core.exceptions import ConfigurationError

FORMAT_VERSION = 1
MANIFEST = "manifest.json"
KIND = "meta_label"


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _lightgbm():
    try:
        import lightgbm
    except ImportError as exc:
        raise ConfigurationError(
            "The meta-label model needs lightgbm, which is not installed. Run: "
            "pip install -r requirements-ml.txt"
        ) from exc
    return lightgbm


@dataclass
class Segment:
    valid_from: pd.Timestamp
    booster: Any
    knots_x: np.ndarray
    knots_y: np.ndarray

    def probability(self, row: np.ndarray) -> float:
        raw = float(self.booster.predict(row, num_threads=1, validate_features=False)[0])
        if self.knots_x.size == 0:
            return raw
        return float(np.interp(raw, self.knots_x, self.knots_y))


def read_manifest(directory: str | Path) -> dict:
    """The artifact's manifest, checked for kind and format; reads no
    booster and needs no lightgbm (a run's preflight uses it)."""
    manifest_path = Path(directory) / MANIFEST
    if not manifest_path.exists():
        raise ConfigurationError(
            f"No meta-label model at {directory} (no {MANIFEST}). Train one: "
            "python cli.py train --config config/ml/meta_label_tqqq.yaml"
        )
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("kind") != KIND or manifest.get("format_version") != FORMAT_VERSION:
        raise ConfigurationError(
            f"{manifest_path} is not a format-{FORMAT_VERSION} {KIND} manifest"
        )
    return manifest


class MetaLabelModel:
    """Every segment of one artifact, and the lookup by bar time."""

    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)
        manifest = read_manifest(self.directory)
        self.manifest = manifest
        self.feature_names: list[str] = list(manifest["features"]["names"])
        lgb = _lightgbm()
        self.segments: list[Segment] = []
        for entry in manifest["segments"]:
            path = self.directory / entry["file"]
            if not path.exists():
                raise ConfigurationError(f"{path} is missing from the model directory")
            if sha256_of(path) != entry["sha256"]:
                raise ConfigurationError(
                    f"{path} does not match the SHA-256 in {MANIFEST}: the model was changed "
                    "after training. Retrain rather than edit it."
                )
            self.segments.append(
                Segment(
                    valid_from=pd.Timestamp(entry["valid_from"]),
                    booster=lgb.Booster(model_file=str(path)),
                    knots_x=np.asarray(entry["calibration"]["x"], dtype=float),
                    knots_y=np.asarray(entry["calibration"]["y"], dtype=float),
                )
            )
        if not self.segments:
            raise ConfigurationError(f"{self.directory / MANIFEST} lists no segments")
        self._starts = [s.valid_from.value for s in self.segments]
        self.fingerprint = hashlib.sha256(
            "".join(e["sha256"] for e in manifest["segments"]).encode()
        ).hexdigest()[:16]

    @property
    def primary(self) -> dict:
        return self.manifest["primary"]

    @property
    def label(self) -> dict:
        return self.manifest["label"]

    def segment_for(self, timestamp) -> Segment | None:
        """The segment that answers for `timestamp`, or None before the
        first one (no model had been trained by then)."""
        ts = pd.Timestamp(timestamp)
        if ts.tzinfo is None:
            ts = ts.tz_localize("UTC")
        k = bisect.bisect_right(self._starts, ts.value) - 1
        return self.segments[k] if k >= 0 else None

    def probability(self, timestamp, features: np.ndarray) -> float | None:
        segment = self.segment_for(timestamp)
        if segment is None:
            return None
        return segment.probability(features.reshape(1, -1))


__all__ = [
    "FORMAT_VERSION",
    "KIND",
    "MANIFEST",
    "MetaLabelModel",
    "Segment",
    "read_manifest",
    "sha256_of",
]
