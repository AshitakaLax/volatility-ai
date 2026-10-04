"""
Price forecasters (ledger A4/C-RJ4 deep sequence models and stacked
ensembles, A8 forecasting and pattern libraries; ❌ for now -- `plan.md`
found direction forecasting the hardest problem, and these are daily, cost-
free and unvalidated). NumPy only.

Sources:

  * C-RJ4: huseinzol05/Stock-Prediction-Models deep-learning/1.lstm.ipynb
    -- MinMax-scaled closes, a 128-unit LSTM trained window by window
    (timestamp 5) with its state carried across windows, one-step-ahead
    targets at every step, Adam 0.01 for 300 epochs, output dropout (keep
    0.8, left ON at inference, which is why the notebook averages 10
    simulations), recursive 30-day generation, and `anchor` smoothing
    (0.3) of the inverse-scaled path. Its 17 siblings (GRU, bidirectional,
    seq2seq, attention, CNN) vary the cell, not the procedure.
  * C-RJ4 stacking: the same repo's stacking/ notebooks combine base
    forecasters through a meta-model -- stacked generalisation (Wolpert,
    "Stacked Generalization", Neural Networks 5, 1992); here the meta-model
    is least squares on out-of-sample base predictions.
  * A8 mlforecast (Nixtla): lag and rolling-window features of the target
    itself, one regression model, recursive multi-step forecasting.
  * A8 patternity / analog forecasting: Lorenz's method of analogues -- find
    the past windows most like the latest one and average what followed.
  * A8 Chaos Genius: anomaly flags outside an exponentially weighted band.

Quirk preserved: the notebook's `Model(..., forget_bias=dropout_rate)`
passes the dropout keep-probability through a parameter named forget_bias;
the LSTM cell itself uses TensorFlow's default forget bias of 1.0.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from engine.core.exceptions import ConfigurationError
from research.catalog.rl_agents import Adam

# ---------------------------------------------------------------- helpers from the notebook


def anchor(signal, weight: float) -> list[float]:
    """Exponential smoothing seeded with the first value:
    s_i = weight * s_{i-1} + (1 - weight) * x_i."""
    out, last = [], float(signal[0])
    for x in signal:
        last = last * weight + (1 - weight) * float(x)
        out.append(last)
    return out


def calculate_accuracy(real, predict) -> float:
    """The notebook's 'accuracy': 100 * (1 - RMS relative error) after adding
    1 to both series."""
    r, p = np.asarray(real, dtype=float) + 1, np.asarray(predict, dtype=float) + 1
    return float((1 - np.sqrt(np.mean(((r - p) / r) ** 2))) * 100)


class MinMax:
    def __init__(self, x) -> None:
        x = np.asarray(x, dtype=float)
        self.lo, self.hi = float(x.min()), float(x.max())
        if self.hi == self.lo:
            raise ConfigurationError("cannot min-max scale a constant series")

    def transform(self, x):
        return (np.asarray(x, dtype=float) - self.lo) / (self.hi - self.lo)

    def inverse(self, x):
        return np.asarray(x, dtype=float) * (self.hi - self.lo) + self.lo


# ---------------------------------------------------------------- C-RJ4 LSTM


class LSTMCell:
    """tf.nn.rnn_cell.LSTMCell gate layout: one matmul of [x, h] to
    (i, j, f, o); c' = sigmoid(f + forget_bias) c + sigmoid(i) tanh(j),
    h' = sigmoid(o) tanh(c'); then a dense layer to the output at every
    step."""

    def __init__(self, n_in: int, n_hidden: int, n_out: int, rng, forget_bias: float = 1.0):
        lim = np.sqrt(6.0 / (n_in + n_hidden + 4 * n_hidden))
        self.n_hidden, self.forget_bias = n_hidden, forget_bias
        lim_o = np.sqrt(6.0 / (n_hidden + n_out))
        self.params = {
            "w": rng.uniform(-lim, lim, (n_in + n_hidden, 4 * n_hidden)),
            "b": np.zeros(4 * n_hidden),
            "wy": rng.uniform(-lim_o, lim_o, (n_hidden, n_out)),
            "by": np.zeros(n_out),
        }

    @staticmethod
    def _sig(x):
        return 1.0 / (1.0 + np.exp(-x))

    def forward(self, xs, h0, c0, keep: float = 1.0, rng=None):
        """Run a window; returns (outputs per step, h, c, cache)."""
        p, n = self.params, self.n_hidden
        h, c = h0.copy(), c0.copy()
        cache, ys = [], []
        for x in np.atleast_2d(xs):
            z = np.r_[x, h] @ p["w"] + p["b"]
            i, j, f, o = (z[k * n : (k + 1) * n] for k in range(4))
            si, tj, sf, so = self._sig(i), np.tanh(j), self._sig(f + self.forget_bias), self._sig(o)
            c_new = sf * c + si * tj
            tc = np.tanh(c_new)
            h_new = so * tc
            mask = (rng.random(n) < keep) / keep if keep < 1.0 else np.ones(n)
            out = h_new * mask
            ys.append(out @ p["wy"] + p["by"])
            cache.append((x, h, c, si, tj, sf, so, tc, out, mask))
            h, c = h_new, c_new
        return np.array(ys), h, c, cache

    def backward(self, cache, dys) -> dict:
        p, n = self.params, self.n_hidden
        g = {k: np.zeros_like(v) for k, v in p.items()}
        dh_next, dc_next = np.zeros(n), np.zeros(n)
        for step in range(len(cache) - 1, -1, -1):
            x, h_prev, c_prev, si, tj, sf, so, tc, out, mask = cache[step]
            dy = dys[step]
            g["wy"] += np.outer(out, dy)
            g["by"] += dy
            dh = (dy @ p["wy"].T) * mask + dh_next
            dso = dh * tc
            dc = dh * so * (1 - tc**2) + dc_next
            dsf, dsi, dtj = dc * c_prev, dc * tj, dc * si
            dz = np.r_[
                dsi * si * (1 - si), dtj * (1 - tj**2), dsf * sf * (1 - sf), dso * so * (1 - so)
            ]
            g["w"] += np.outer(np.r_[x, h_prev], dz)
            g["b"] += dz
            dxh = dz @ p["w"].T
            dh_next, dc_next = dxh[len(x) :], dc * sf
        return g


class LSTMForecaster:
    """deep-learning/1.lstm.ipynb's `forecast()` on a single series."""

    def __init__(
        self,
        size_layer: int = 128,
        timestamp: int = 5,
        epochs: int = 300,
        learning_rate: float = 0.01,
        keep_prob: float = 0.8,
        dropout_at_inference: bool = True,
        anchor_weight: float = 0.3,
        seed=None,
    ) -> None:
        self.size, self.timestamp, self.epochs = size_layer, timestamp, epochs
        self.lr, self.keep, self.infer_dropout = learning_rate, keep_prob, dropout_at_inference
        self.anchor_weight = anchor_weight
        self.rng = np.random.default_rng(seed)

    def fit(self, series) -> list[float]:
        """Train on the scaled series, window by window, state carried and
        detached between windows; returns mean loss per epoch."""
        self.scaler = MinMax(series)
        self.train = self.scaler.transform(series)[:, None]
        self.cell = LSTMCell(1, self.size, 1, self.rng)
        opt, losses = Adam(self.lr), []
        n = len(self.train)
        for _ in range(self.epochs):
            h, c = np.zeros(self.size), np.zeros(self.size)
            epoch = []
            for k in range(0, n - 1, self.timestamp):
                idx = min(k + self.timestamp, n - 1)
                xs, ys = self.train[k:idx], self.train[k + 1 : idx + 1]
                out, h, c, cache = self.cell.forward(xs, h, c, self.keep, self.rng)
                diff = out - ys
                epoch.append(float((diff**2).mean()))
                opt.step(self.cell.params, self.cell.backward(cache, 2 * diff / diff.size))
            losses.append(float(np.mean(epoch)))
        return losses

    def forecast(self, horizon: int) -> np.ndarray:
        """Re-run the training data for state, then generate `horizon` steps
        recursively from the last `timestamp` values (predictions included),
        inverse-scale, anchor-smooth, and return the last `horizon` values."""
        keep = self.keep if self.infer_dropout else 1.0
        n, ts = len(self.train), self.timestamp
        pred = np.zeros(n + horizon)
        pred[0] = self.train[0, 0]
        h, c = np.zeros(self.size), np.zeros(self.size)
        upper = (n // ts) * ts
        for k in range(0, upper, ts):
            out, h, c, _ = self.cell.forward(self.train[k : k + ts], h, c, keep, self.rng)
            pred[k + 1 : k + ts + 1] = out[:, 0]
        future = horizon
        if upper != n:
            out, h, c, _ = self.cell.forward(self.train[upper:], h, c, keep, self.rng)
            pred[upper + 1 : n + 1] = out[:, 0]
            future -= 1
        for i in range(future):
            lo = len(pred) - future - ts + i
            window = pred[lo : lo + ts][:, None]
            out, h, c, _ = self.cell.forward(window, h, c, keep, self.rng)
            pred[len(pred) - future + i] = out[-1, 0]
        smoothed = anchor(self.scaler.inverse(pred), self.anchor_weight)
        return np.array(smoothed[-horizon:])


# ---------------------------------------------------------------- C-RJ4 stacking


def stack_forecasts(base_predictions, target, nonneg: bool = False) -> dict:
    """Stacked generalisation: fit the meta-model target ~ const + sum_k
    b_k pred_k on OUT-OF-SAMPLE base predictions (columns). Returns the
    weights, intercept and a predictor for new base predictions."""
    x = np.asarray(base_predictions, dtype=float)
    y = np.asarray(target, dtype=float)
    if x.ndim != 2 or len(x) != len(y):
        raise ConfigurationError("base_predictions must be (n, k) aligned with target")
    design = np.column_stack([np.ones(len(y)), x])
    if nonneg:
        from research.catalog.je_suis_tm_projects import nnls

        xc, yc = x - x.mean(0), y - y.mean()
        w = nnls(xc, yc)
        coef = np.r_[y.mean() - x.mean(0) @ w, w]
    else:
        coef = np.linalg.lstsq(design, y, rcond=None)[0]

    def predict(p):
        return np.column_stack([np.ones(len(np.atleast_2d(p))), np.atleast_2d(p)]) @ coef

    return {"intercept": float(coef[0]), "weights": coef[1:], "predict": predict}


# ---------------------------------------------------------------- A8 mlforecast-style


def lag_features(series, lags=(1, 2, 3, 7), rolling=(7,)) -> pd.DataFrame:
    """Target features in mlforecast's style: lag_k = y_{t-k}; rolling means
    over the window ending at lag 1 (so nothing from t leaks in)."""
    s = pd.Series(series, dtype=float).reset_index(drop=True)
    cols = {f"lag{k}": s.shift(k) for k in lags}
    cols.update({f"rolling_mean_{w}": s.shift(1).rolling(w).mean() for w in rolling})
    return pd.DataFrame(cols)


class RecursiveLagForecaster:
    """One ridge regression on lag features, forecast recursively: each
    prediction is appended to the history and feeds the next step's lags
    (mlforecast's default multi-step strategy)."""

    def __init__(self, lags=(1, 2, 3, 7), rolling=(7,), ridge: float = 1e-6) -> None:
        self.lags, self.rolling, self.ridge = tuple(lags), tuple(rolling), ridge

    def fit(self, series) -> RecursiveLagForecaster:
        self.history = [float(v) for v in series]
        f = lag_features(self.history, self.lags, self.rolling)
        y = pd.Series(self.history)
        ok = f.notna().all(axis=1)
        x = np.column_stack([np.ones(ok.sum()), f[ok].to_numpy()])
        a = x.T @ x + self.ridge * np.eye(x.shape[1])
        self.coef = np.linalg.solve(a, x.T @ y[ok].to_numpy())
        return self

    def forecast(self, horizon: int) -> np.ndarray:
        hist = list(self.history)
        out = []
        for _ in range(horizon):
            row = lag_features([*hist, np.nan], self.lags, self.rolling).iloc[-1].to_numpy()
            yhat = float(np.r_[1.0, row] @ self.coef)
            out.append(yhat)
            hist.append(yhat)
        return np.array(out)


# ---------------------------------------------------------------- A8 analogues and anomalies


def analog_forecast(series, window: int = 20, horizon: int = 5, k: int = 5) -> dict:
    """Method of analogues on returns: z-normalise every past window of
    `window` returns, take the k nearest (Euclidean) to the latest one among
    windows whose following `horizon` returns are fully observed, and
    average those following returns."""
    p = np.asarray(series, dtype=float)
    r = np.diff(np.log(p))
    if len(r) < window + horizon + k:
        raise ConfigurationError("series too short for the window, horizon and k")

    def z(v):
        sd = v.std()
        return (v - v.mean()) / sd if sd > 0 else v - v.mean()

    query = z(r[-window:])
    starts = np.arange(0, len(r) - window - horizon + 1)
    dists = np.array([np.linalg.norm(z(r[s : s + window]) - query) for s in starts])
    nearest = starts[np.argsort(dists, kind="stable")[:k]]
    paths = np.array([r[s + window : s + window + horizon] for s in nearest])
    return {
        "neighbours": nearest,
        "mean_path": paths.mean(axis=0),
        "expected": float(paths.sum(1).mean()),
    }


def ewm_anomalies(series, span: int = 20, z: float = 3.0) -> pd.DataFrame:
    """Flag points outside EWMA +/- z * EW standard deviation, both computed
    through t-1 (so a spike cannot widen its own band)."""
    s = pd.Series(series, dtype=float)
    mean = s.ewm(span=span).mean().shift(1)
    sd = s.ewm(span=span).std().shift(1)
    upper, lower = mean + z * sd, mean - z * sd
    return pd.DataFrame(
        {"mean": mean, "upper": upper, "lower": lower, "anomaly": (s > upper) | (s < lower)}
    )
