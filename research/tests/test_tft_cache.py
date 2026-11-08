"""research/ml/tft_cache.py: a precomputed forecast is found only for the
exact inputs it was made from, answers exactly what the model answered,
and a table made by another model is refused. The last test trains a small
real TFT where pytorch-forecasting is installed."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from engine.core.exceptions import ConfigurationError
from research.ml import tft_cache
from research.ml.tft_sizing import TemporalFusionTransformerSizer
from research.tests.test_tft_sizing import bars, ctx


def _model_dir(tmp_path, checkpoint="abc"):
    directory = tmp_path / "model"
    directory.mkdir()
    (directory / "manifest.json").write_text(
        json.dumps(
            {
                "kind": "tft",
                "format_version": 1,
                "symbol": "SYN",
                "quantiles": [0.1, 0.5, 0.9],
                "encoder_length": 2,
                "prediction_length": 1,
                "bars_per_day": 26,
                "valid_from": "2024-01-01T00:00:00+00:00",
                "sources": {"s_macro": None, "s_earnings": None, "s_news": None},
                "files": {"model.ckpt": checkpoint, "dataset.pt": "def"},
            }
        )
    )
    return directory


def _table(path, entries, checkpoint="abc"):
    keys = np.frombuffer(b"".join(k for k, _ in entries), dtype=np.uint8).reshape(-1, 16)
    np.savez(
        path,
        keys=keys,
        values=np.stack([v for _, v in entries]),
        checkpoint=np.array(checkpoint),
        first_bar=np.array("2024-01-02T14:30:00+00:00"),
    )
    return path


def test_the_key_is_every_bit_of_both_inputs():
    enc, dec = np.arange(18.0).reshape(2, 9), np.ones((1, 3))
    key = tft_cache.window_key(enc, dec)
    assert key == tft_cache.window_key(enc.copy(), dec.copy()) and len(key) == 16
    nudged = enc.copy()
    nudged[1, 4] = np.nextafter(nudged[1, 4], np.inf)  # one ulp
    assert tft_cache.window_key(nudged, dec) != key
    assert tft_cache.window_key(enc, dec * 2) != key
    assert tft_cache.window_key(enc[:, ::1], dec) == key  # layout is not content


def test_a_hit_is_the_table_and_a_miss_runs_the_model(tmp_path, monkeypatch):
    directory = _model_dir(tmp_path)
    enc, dec = np.zeros((2, 9)), np.zeros((1, 3))
    stored = np.array([[1.0, 2.0, 3.0]])
    table = _table(tmp_path / "f.npz", [(tft_cache.window_key(enc, dec), stored)])

    class Model:
        def __init__(self, path):
            self.calls = 0

        def forecast(self, encoder, decoder_known):
            self.calls += 1
            return np.full((1, 3), 9.0)

    monkeypatch.setattr("research.ml.tft_model.TftForecaster", Model)
    cached = tft_cache.CachedForecaster(directory, table)
    assert cached.levels == (0.1, 0.5, 0.9) and cached.encoder_length == 2
    np.testing.assert_array_equal(cached.forecast(enc, dec), stored)
    np.testing.assert_array_equal(cached.forecast(enc + 1, dec), np.full((1, 3), 9.0))
    assert (cached.hits, cached.misses) == (1, 1)


def test_a_table_from_another_model_is_refused(tmp_path):
    directory = _model_dir(tmp_path, checkpoint="abc")
    table = _table(tmp_path / "f.npz", [(b"0" * 16, np.zeros((1, 3)))], checkpoint="other")
    with pytest.raises(ConfigurationError, match="another model"):
        tft_cache.CachedForecaster(directory, table)
    with pytest.raises(ConfigurationError, match="not found"):
        tft_cache.CachedForecaster(directory, tmp_path / "missing.npz")


def test_a_real_tfts_table_is_what_the_live_sizer_asks_for(tmp_path):
    pytest.importorskip("pytorch_forecasting")
    import yaml

    from research.ml import tft_training as tt

    history = bars(days=80, per=26, seed=5)
    base = tmp_path / "base.yaml"
    base.write_text(
        yaml.safe_dump(
            {
                "strategy": {
                    "strategy_id": "hf_local_reference",
                    "strategy_params": {
                        "bars_per_day": 26,
                        "per_lot_pct": 0.002,
                        "lookback_days": 0.2,
                    },
                },
                "grid": {"steps": [0.003], "profit_targets": [0.004]},
                "backtest": {"symbol": "SYN", "initial_cash": 100000.0},
                "costs": {"model_type": "zero"},
            }
        )
    )
    cutoff = history.index[26 * 70]
    config = tt.TftTrainConfig.from_dict(
        {
            "kind": "tft",
            "name": "t",
            "base_config": str(base),
            "validation_start": str(cutoff.date()),
            "bars_per_day": 26,
            "encoder_length": 20,
            "prediction_length": 4,
            "trainer": {"max_epochs": 1, "batch_size": 32, "limit_train_batches": 3},
            "eval_samples": 50,
            "output": str(tmp_path / "tft"),
        }
    )
    tt.train(config, bars=history, log=lambda *_: None)
    run = history[history.index >= pd.Timestamp(cutoff.date(), tz="UTC")]
    table = tft_cache.precompute(config.output, run, tmp_path / "f.npz", workers=2, log=print)
    model = str(config.output)
    cached = TemporalFusionTransformerSizer(1.0, 26, model=model, forecast_cache=str(table))
    live = TemporalFusionTransformerSizer(1.0, 26, model=model)
    compared = 0
    for t in range(len(run)):
        c = ctx(t, frame=run)
        cached.record_tick(c)
        live.record_tick(c)
        a, b = cached.forecast_moments(c), live.forecast_moments(c)
        assert (a is None) == (b is None)
        if a is not None:
            assert a == b  # exactly: the table holds what the model returned
            compared += 1
    assert compared > 100 and cached._forecaster.misses == 0
