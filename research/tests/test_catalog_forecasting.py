"""research/catalog/forecasting.py -- the huseinzol05 LSTM forecaster,
stacking, mlforecast-style lag regression, analogues and anomalies."""

from __future__ import annotations

import numpy as np
import pytest

from engine.core.exceptions import ConfigurationError
from research.catalog.forecasting import (
    LSTMCell,
    LSTMForecaster,
    MinMax,
    RecursiveLagForecaster,
    analog_forecast,
    anchor,
    calculate_accuracy,
    ewm_anomalies,
    lag_features,
    stack_forecasts,
)


def test_anchor_and_accuracy_follow_the_notebook():
    assert anchor([1.0, 3.0, 3.0], 0.5) == pytest.approx([1.0, 2.0, 2.5])
    assert calculate_accuracy([1.0, 2.0], [1.0, 2.0]) == 100.0
    assert calculate_accuracy([1.0], [3.0]) == pytest.approx(0.0)
    with pytest.raises(ConfigurationError):
        MinMax([2.0, 2.0])


def test_lstm_bptt_matches_finite_differences():
    rng = np.random.default_rng(0)
    cell = LSTMCell(2, 4, 1, rng)
    xs, ys = rng.normal(size=(5, 2)), rng.normal(size=(5, 1))
    h0, c0 = rng.normal(size=4) * 0.1, rng.normal(size=4) * 0.1

    def loss():
        out = cell.forward(xs, h0, c0)[0]
        return 0.5 * ((out - ys) ** 2).sum()

    out, _, _, cache = cell.forward(xs, h0, c0)
    grads = cell.backward(cache, out - ys)
    for k, p in cell.params.items():
        num = np.zeros_like(p)
        for idx in np.ndindex(p.shape):
            old = p[idx]
            p[idx] = old + 1e-6
            up = loss()
            p[idx] = old - 1e-6
            num[idx] = (up - loss()) / 2e-6
            p[idx] = old
        assert grads[k] == pytest.approx(num, abs=1e-6), k


def test_lstm_forecaster_trains_and_generates():
    t = np.arange(80)
    series = 100 + 5 * np.sin(t / 5)
    model = LSTMForecaster(
        size_layer=12, timestamp=5, epochs=40, seed=1, dropout_at_inference=False
    )
    losses = model.fit(series)
    assert losses[-1] < losses[0] / 3
    fc = model.forecast(10)
    assert fc.shape == (10,) and np.isfinite(fc).all()
    assert series.min() - 5 < fc.min() and fc.max() < series.max() + 5
    stochastic = LSTMForecaster(size_layer=12, timestamp=5, epochs=2, seed=2)
    stochastic.fit(series)
    assert not np.allclose(stochastic.forecast(5), stochastic.forecast(5))  # dropout left on


def test_stacking_recovers_the_meta_weights():
    rng = np.random.default_rng(3)
    preds = rng.normal(size=(200, 3))
    y = 0.5 + 0.7 * preds[:, 0] + 0.3 * preds[:, 2]
    st = stack_forecasts(preds, y)
    assert st["weights"] == pytest.approx([0.7, 0.0, 0.3], abs=1e-9)
    assert st["predict"]([[1.0, 5.0, 1.0]]) == pytest.approx([1.5])
    y2 = 0.7 * preds[:, 0] - 0.2 * preds[:, 1]
    assert stack_forecasts(preds, y2, nonneg=True)["weights"][1] == 0.0


def test_lag_features_do_not_leak():
    f = lag_features([1.0, 2.0, 3.0, 4.0, 5.0], lags=(1, 2), rolling=(2,))
    assert f.iloc[3].tolist() == [3.0, 2.0, 2.5]  # row t=3 sees 3, 2 and mean(2, 3)


def test_recursive_lag_forecaster_on_ar1_and_trend():
    trend = 2.0 * np.arange(30) + 1
    fc = RecursiveLagForecaster(lags=(1, 2), rolling=()).fit(trend).forecast(3)
    assert fc == pytest.approx([61.0, 63.0, 65.0], abs=1e-3)
    rng = np.random.default_rng(4)
    x = np.zeros(600)
    for i in range(1, 600):
        x[i] = 0.6 * x[i - 1] + rng.normal()
    model = RecursiveLagForecaster(lags=(1,), rolling=()).fit(x)
    assert model.coef[1] == pytest.approx(0.6, abs=0.06)
    path = model.forecast(4)
    assert abs(path[-1]) < abs(path[0]) or abs(path[0]) < 1e-9


def test_analog_forecast_finds_the_same_phase():
    t = np.arange(400)
    prices = 100 * np.exp(0.05 * np.sin(2 * np.pi * t / 40))
    out = analog_forecast(prices, window=20, horizon=5, k=3)
    r = np.diff(np.log(prices))
    assert all((len(r) - 20 - n) % 40 == 0 for n in out["neighbours"])
    nxt = 0.05 * (
        np.sin(2 * np.pi * np.arange(400, 405) / 40) - np.sin(2 * np.pi * np.arange(399, 404) / 40)
    )
    assert out["mean_path"] == pytest.approx(nxt, abs=1e-9)


def test_ewm_anomalies_flag_a_spike():
    s = np.r_[np.random.default_rng(5).normal(0, 1, 100), 15.0, np.zeros(5)]
    flags = ewm_anomalies(s, span=20, z=4)["anomaly"]
    assert flags.iloc[100] and flags.iloc[:100].sum() <= 1
