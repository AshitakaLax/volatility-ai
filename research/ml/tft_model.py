"""A trained Temporal Fusion Transformer, as the `ml_tft` sizer loads it.

research/ml/tft_training.py writes a directory:

    manifest.json   what was trained, on what, how it scored; file hashes
    model.ckpt      the Lightning checkpoint of the TemporalFusionTransformer
    dataset.pt      TimeSeriesDataSet.get_parameters(): the covariate groups,
                    the fitted scalers and the target normalizer

Both binary files are pickles (that is how pytorch-forecasting stores a
model and its dataset), so loading one runs code. Each is checked against
the SHA-256 recorded in the manifest before it is opened: load only models
you trained. This is unlike the meta-label artifact (research/ml/
meta_model.py), which is text and JSON throughout.

torch, lightning and pytorch-forecasting (requirements-dl.txt) are
imported here and only here, when a model is first loaded: the server,
the registry and the trading machine import the sizer without them.

A forecast is one TFT forward pass. The window is turned into a frame of
encoder_length + prediction_length rows and passed through the dataset's
own parameters (TimeSeriesDataSet.from_parameters), so every input is
scaled exactly as in training; the decoder's unknown inputs and target
are placeholders the network never reads.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from engine.core.exceptions import ConfigurationError
from research.ml.meta_model import sha256_of
from research.ml.tft_features import KNOWN, OBSERVED, ROW, SOURCES, TARGET

KIND = "tft"
FORMAT_VERSION = 1
MANIFEST = "manifest.json"
CHECKPOINT = "model.ckpt"
DATASET = "dataset.pt"


def read_manifest(directory: str | Path) -> dict:
    path = Path(directory) / MANIFEST
    if not path.exists():
        raise ConfigurationError(
            f"No TFT model at {directory} (no {MANIFEST}). Train one: "
            "python cli.py train --config config/ml/tft_tqqq.yaml"
        )
    manifest = json.loads(path.read_text())
    if manifest.get("kind") != KIND or manifest.get("format_version") != FORMAT_VERSION:
        raise ConfigurationError(f"{path} is not a format-{FORMAT_VERSION} {KIND} manifest")
    return manifest


def deep_learning():
    """(torch, TimeSeriesDataSet, TemporalFusionTransformer), or a clear error."""
    try:
        import torch
        from pytorch_forecasting import TemporalFusionTransformer, TimeSeriesDataSet
    except ImportError as exc:
        raise ConfigurationError(
            "The TFT needs torch, lightning and pytorch-forecasting, which are not installed. "
            "Run: pip install -r requirements-dl.txt"
        ) from exc
    return torch, TimeSeriesDataSet, TemporalFusionTransformer


class TftForecaster:
    """research/ml/tft_sizing.QuantileForecaster over a trained TFT."""

    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)
        manifest = read_manifest(self.directory)
        for name in (CHECKPOINT, DATASET):
            path = self.directory / name
            if not path.exists():
                raise ConfigurationError(f"{path} is missing from the model directory")
            if sha256_of(path) != manifest["files"][name]:
                raise ConfigurationError(
                    f"{path} does not match the SHA-256 in {MANIFEST}; refusing to unpickle it. "
                    "Retrain rather than edit a model."
                )
        torch, dataset_cls, model_cls = deep_learning()
        # One sample per forward pass gains nothing from intra-op threads
        # (measured: 34.0 ms on one thread, 34.5 ms on four), and a sweep runs
        # a process per core -- four threads each would oversubscribe them.
        torch.set_num_threads(1)
        self._torch = torch
        self._dataset_cls = dataset_cls
        self.manifest = manifest
        self.parameters = torch.load(self.directory / DATASET, weights_only=False)
        self.network = model_cls.load_from_checkpoint(
            str(self.directory / CHECKPOINT), map_location="cpu", weights_only=False
        )
        self.network.eval()
        self.levels = tuple(float(q) for q in manifest["quantiles"])
        self.encoder_length = int(manifest["encoder_length"])
        self.prediction_length = int(manifest["prediction_length"])
        self.bars_per_day = int(manifest["bars_per_day"])
        self.valid_from = pd.Timestamp(manifest["valid_from"])
        self.sources = {name: manifest["sources"].get(name) for name in SOURCES}
        self.group = manifest["symbol"]

    def frame(self, encoder: np.ndarray, decoder_known: np.ndarray) -> pd.DataFrame:
        """The encoder rows and the decoder's known inputs as one frame in the
        training layout (tft_features.build_frame's columns)."""
        L, H = self.encoder_length, self.prediction_length
        if encoder.shape != (L, len(ROW)) or decoder_known.shape != (H, len(KNOWN)):
            raise ConfigurationError(
                f"forecast needs a ({L}, {len(ROW)}) encoder and ({H}, {len(KNOWN)}) known "
                f"decoder inputs; got {encoder.shape} and {decoder_known.shape}"
            )
        rows = np.empty((L + H, len(ROW)), dtype=np.float64)
        rows[:L] = encoder
        unknown = 1 + len(OBSERVED)  # target and observed: placeholders in the decoder
        rows[L:, :unknown] = encoder[-1, :unknown]
        rows[L:, unknown:] = decoder_known
        frame = pd.DataFrame(rows, columns=list(ROW))
        frame.insert(0, "time_idx", np.arange(L + H, dtype=np.int64))
        frame.insert(1, "group", self.group)
        return frame

    def forecast(self, encoder: np.ndarray, decoder_known: np.ndarray) -> np.ndarray:
        """(prediction_length, len(levels)) quantiles of log_close."""
        frame = self.frame(encoder, decoder_known)
        dataset = self._dataset_cls.from_parameters(
            self.parameters, frame, predict=True, stop_randomization=True
        )
        x, _ = next(iter(dataset.to_dataloader(train=False, batch_size=1, num_workers=0)))
        with self._torch.no_grad():
            out = self.network(x)
        prediction = out["prediction"][0].detach().cpu().numpy()
        return np.asarray(prediction, dtype=np.float64).reshape(self.prediction_length, -1)


__all__ = [
    "CHECKPOINT",
    "DATASET",
    "FORMAT_VERSION",
    "KIND",
    "MANIFEST",
    "TARGET",
    "TftForecaster",
    "deep_learning",
    "read_manifest",
]
