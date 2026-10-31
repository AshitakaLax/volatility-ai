"""
catalog_exposure: the research catalog's single-fund long-or-cash signals,
and the ledger's single-fund candidates that had no code (RK10, RK14, RK64,
RK290, RK314), traded through Ultimate-RSP's daily exposure book.

research/catalog/ holds every algorithm of docs/algorithm_ledger.md as
standalone research code, none of it a SizingStrategy. Most of the entries
that fit the platform's constraints (long-only, one fund, a loss only
through a signal exit) are the same shape: from the sessions before D, a
fraction of equity in [0, 1] to hold on D. That is exactly what
UltimateRspSizing executes -- a target reached once a session at
`execute_minute`, whole-lot buys for a shortfall, whole-lot signal exits
for an excess -- so this strategy is that book with the target taken from
one catalog signal instead of the PLUS_DM / ADOSC vote:

    strategy_id: catalog_exposure
    strategy_params:
      catalog_signal: kalman_trend
      catalog_params: "q_level=1e-5;q_slope=1e-7"
      execute_minute: 60
      rebalance_band: 0.05

`catalog_signal` names an entry of SIGNALS below; `catalog_params` overrides its
defaults ("name=value;name=value", a list value as "21/63/252"), so a
sweep varies one string per signal, as ultimate_rsp's pd_periods are.

--------------------------------------------------------------------
CAUSALITY

The target for session D is computed when D's first bar arrives, from
sessions strictly before D: the trailing `history` completed sessions
(open, high, low, close, volume of each, built here from the bars
record_tick sees) are handed to the catalog function and its LAST value is
the target. The catalog functions' value at t uses data through t only
(each one's docstring says so; the windowed ones are pinned by
research/tests/test_catalog_exposure_sizing.py against the full-history
call, and every one by a truncation test: changing later sessions never
changes an earlier target). Functions that fit a model on a training
slice are only ever handed the past, so their "training slice" is the
trailing window.

Recursive filters (Kalman, KAMA, Bayesian drift, MACD, PSAR, Heikin-Ashi,
Supertrend) are restarted on each trailing window rather than carried
forward; `history` is long enough for each to forget its seed.

The two signals that fit a model (random_forest, jump_stress) refit once
per `refit_days` calendar bucket, on sessions before the bucket only
(_before_bucket). Keyed by dates, so a live process -- which starts cold
every session -- rebuilds exactly the model a backtest through the same
dates holds; test_a_cold_start_holds_the_model_a_continuous_run_holds
pins it.

Left out: the catalog's Markov-state trend (concepts.hmm_trend) refits a
Gaussian HMM on every call -- ~3 s a session, hours a configuration -- and
the entries that need a training split with labels from the future
(kernel_trend_forecast, diffusion_trend) or a second instrument
(copula_momentum_positions, topology_filtered_trend).

A signal that is not yet defined (too few sessions, NaN) is 0: out.
Fractions above 1 (a volatility-scaled weight) are capped by
max_exposure; negative ones (a short) are 0 -- the platform is long-only.

--------------------------------------------------------------------
DEPENDENCIES

The catalog modules import scipy and scikit-learn, which the live loop
must be able to start without (the registry is imported there). Every
catalog import here is inside the function that needs it.

--------------------------------------------------------------------
NOT RESEARCHED

None of these signals has been measured on this platform's funds; the
ledger marks them 🧪/⏳. Registered so they can BE swept
(tools/sweep_brute_force.py) and, if one earns it, taken through the
Algorithms tab's candidate -> paper trial -> live profile path.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date

import numpy as np

from engine.core.exceptions import ConfigurationError
from research.strategies.ultimate_rsp_sizing import UltimateRspSizing

ParamValue = int | float | str | tuple


@dataclass(frozen=True)
class Window:
    """The trailing completed sessions, oldest first."""

    open: np.ndarray
    high: np.ndarray
    low: np.ndarray
    close: np.ndarray
    volume: np.ndarray
    # Each session's date as an ordinal (date.toordinal()).
    day: np.ndarray

    def returns(self) -> np.ndarray:
        return np.diff(np.log(self.close))

    def frame(self):
        import pandas as pd

        return pd.DataFrame(
            {
                "open": self.open,
                "high": self.high,
                "low": self.low,
                "close": self.close,
                "volume": self.volume,
            }
        )


@dataclass(frozen=True)
class Signal:
    """One catalog entry as a daily exposure target."""

    ledger: str
    summary: str
    compute: Callable[..., float]
    defaults: dict[str, ParamValue] = field(default_factory=dict)
    # Completed sessions the computation needs, from the resolved parameters.
    history: Callable[[dict], int] = lambda p: 260
    # A stateful signal's compute also takes a dict it keeps between
    # sessions (a fitted model and when it was fitted), always fed in
    # session order and only ever from completed sessions.
    stateful: bool = False
    # A string parameter's allowed values, checked when the strategy is built
    # rather than the first time the signal is computed.
    choices: dict[str, tuple[str, ...]] = field(default_factory=dict)


def _last(values) -> float:
    arr = np.asarray(values, float)
    return float(arr[-1]) if len(arr) else float("nan")


# ------------------------------------------------------------ the signals


def _tsmom(w: Window, p: dict) -> float:
    import pandas as pd

    from research.catalog.trend_following import tsmom_weights

    r = np.diff(w.close) / w.close[:-1]
    # tsmom_weights shifts by one (data through t-1 for day t's weight); a
    # trailing zero row makes its last row the weight for the NEXT session.
    frame = pd.DataFrame({"r": np.r_[r, 0.0]})
    out = tsmom_weights(frame, lookback=p["lookback"], vol_target=p["vol_target"], com=p["com"])
    return _last(out["r"])


def _multi_timeframe(w: Window, p: dict) -> float:
    from research.catalog.technical_ml import multi_timeframe_trend

    return _last(multi_timeframe_trend(w.close, tuple(p["horizons"]), p["mode"]))


def _supertrend(w: Window, p: dict) -> float:
    from research.catalog.technical_ml import supertrend

    return _last(supertrend(w.high, w.low, w.close, p["n"], p["mult"])["positions"])


def _trend_regime(method: str) -> Callable[[Window, dict], float]:
    def compute(w: Window, p: dict) -> float:
        from research.strategies.trend_regimes import risk_on_flags

        flags = risk_on_flags(w.frame(), method, **p)
        return float(bool(flags.iloc[-1])) if len(flags) else float("nan")

    return compute


def _kalman(w: Window, p: dict) -> float:
    from research.catalog.concepts import kalman_trend

    return _last(kalman_trend(w.close, p["q_level"], p["q_slope"], p["r"])["positions"])


def _l1(w: Window, p: dict) -> float:
    from research.catalog.concepts import l1_trend_positions

    n = p["window"]
    return _last(l1_trend_positions(w.close[-(n + 1) :], n, p["lam"]))


def _kama(w: Window, p: dict) -> float:
    from research.catalog.concepts import kama

    line = kama(w.close, p["n"], p["fast"], p["slow"])
    return float(w.close[-1] > line[-1]) if np.isfinite(line[-1]) else float("nan")


def _cycle(w: Window, p: dict) -> float:
    from research.catalog.concepts import cycle_blended_momentum

    return _last(cycle_blended_momentum(w.close, p["fast"], p["slow"])["positions"])


def _spectral(w: Window, p: dict) -> float:
    from research.catalog.concepts import spectral_trend_positions

    n = p["window"]
    return _last(spectral_trend_positions(w.close[-(n + 1) :], n, p["keep"]))


def _bayesian(w: Window, p: dict) -> float:
    from research.catalog.concepts import bayesian_drift

    out = bayesian_drift(
        w.returns(),
        prior_strength=p["prior_strength"],
        discount=p["discount"],
        threshold=p["threshold"],
    )
    return _last(out["positions"])


def _robust(w: Window, p: dict) -> float:
    from research.catalog.concepts import robust_momentum

    n = p["lookback"]
    return _last(robust_momentum(w.close[-(n + 1) :], n, p["method"]))


def _arfima(w: Window, p: dict) -> float:
    from research.catalog.concepts import arfima_forecast

    return _last(arfima_forecast(w.returns(), p["window"])["positions"])


def _tail_budget(w: Window, p: dict) -> float:
    from research.catalog.concepts import tail_budget_exposure

    n = p["window"]
    r = w.returns()[-(n + 1) :]
    # The catalog's value at t is fitted on r[t - window : t]: append a
    # placeholder so the last value is fitted on the window through D-1.
    return _last(tail_budget_exposure(np.r_[r[1:], 0.0], p["es_budget"], n, p["alpha"]))


def _wavelet(w: Window, p: dict) -> float:
    from research.catalog.concepts import var_exposure, wavelet_tail_risk

    r = np.r_[w.returns(), 0.0]  # value at t uses details through t-1
    var = wavelet_tail_risk(r, p["levels"], p["window"], p["alpha"])["var"]
    if not np.isfinite(var[-1]):
        return float("nan")
    return _last(var_exposure(var[-1:], p["var_budget"]))


def _early_warning(w: Window, p: dict) -> float:
    from research.catalog.concepts import early_warning_exposure

    n = p["window"] + p["trend_window"]
    series = np.r_[np.log(w.close[-(n + 1) :]), 0.0]  # value at t uses data through t-1
    out = early_warning_exposure(
        series, p["threshold"], window=p["window"], trend_window=p["trend_window"]
    )
    return _last(out)


def _momentum_ok(c: np.ndarray, lookback: int, skip: int) -> bool:
    """The fund's own lookback-session return, skipping the last `skip`."""
    return bool(c[-1 - skip] > c[-1 - lookback])


def _state_momentum(w: Window, p: dict) -> float:
    """RK10 (Cooper, Gutierrez & Hameed 2004; Daniel & Moskowitz 2016):
    momentum held only in a favourable state -- the market up over
    `state_lookback` sessions and its `vol_days` realised volatility not in
    the top of its own trailing year (`vol_quantile`), the panic state in
    which momentum crashes."""
    c = w.close
    if not _momentum_ok(c, p["lookback"], p["skip"]):
        return 0.0
    if c[-1] <= c[-1 - p["state_lookback"]]:
        return 0.0
    r = np.diff(np.log(c))
    n = p["vol_days"]
    vols = np.array([r[t - n : t].std() for t in range(n, len(r) + 1)][-252:])
    return float(vols[-1] <= np.quantile(vols, p["vol_quantile"]))


def _high_52w(w: Window, p: dict) -> float:
    """RK14 (George & Hwang 2004) for one fund: nearness = close / highest
    close of the trailing `window` sessions. `binary` holds above
    `threshold`; `graded` scales from 0 at `floor` to 1 at `threshold`."""
    near = w.close[-1] / w.close[-p["window"] :].max()
    if p["mode"] == "binary":
        return float(near >= p["threshold"])
    if p["mode"] != "graded":
        raise ConfigurationError("high_52w mode must be binary or graded")
    if not 0 < p["floor"] < p["threshold"] <= 1:
        raise ConfigurationError("high_52w needs 0 < floor < threshold <= 1")
    return float(np.clip((near - p["floor"]) / (p["threshold"] - p["floor"]), 0.0, 1.0))


def _ema(values: np.ndarray, span: int) -> np.ndarray:
    alpha, out = 2.0 / (span + 1), np.empty(len(values))
    out[0] = values[0]
    for t in range(1, len(values)):
        out[t] = alpha * values[t] + (1 - alpha) * out[t - 1]
    return out


def _ema_ribbon(w: Window, p: dict) -> float:
    """RK64: Guppy's ribbon as a regime -- held while every short EMA is
    above every long one (stacked); `average` holds the share of
    short/long pairs in order instead."""
    short = [_ema(w.close, int(n))[-1] for n in p["short"]]
    long_ = [_ema(w.close, int(n))[-1] for n in p["long"]]
    if p["mode"] == "stacked":
        return float(min(short) > max(long_))
    if p["mode"] != "average":
        raise ConfigurationError("ema_ribbon mode must be stacked or average")
    return float(np.mean([s > lo for s in short for lo in long_]))


def _before_bucket(w: Window, p: dict) -> int:
    """How many of the window's sessions precede the current refit bucket.

    A model is refitted once per `refit_days`-day calendar bucket, keyed
    by the latest completed session's date, on sessions BEFORE that
    bucket only. Keyed by dates rather than by a count of calls, so a live
    process that starts cold every session rebuilds exactly the model a
    backtest running through the same dates holds."""
    bucket = int(w.day[-1]) // p["refit_days"]
    return int(np.searchsorted(w.day // p["refit_days"], bucket))


def _jump_stress(w: Window, p: dict, state: dict) -> float:
    """RK314 (Ait-Sahalia, Cacho-Diaz & Laeven 2015) as a daily stress gauge
    on one fund: jumps are returns beyond k bipower sigmas
    (point_processes.detect_jumps), their self-exciting intensity is fitted
    on the window (fit_jump_excitation) and filtered
    (mutually_exciting_jump_intensity); the book drops to `floor` while
    the intensity is above `multiple` times its baseline mu. The fit is
    redone once per `refit_days` bucket on the `fit_sessions` sessions
    before it (_before_bucket); the filter runs every session."""
    from research.catalog.point_processes import (
        detect_jumps,
        fit_jump_excitation,
        mutually_exciting_jump_intensity,
    )

    r = w.returns()
    jumps = detect_jumps(r, p["jump_window"], p["k"]).astype(float)[:, None]
    end = _before_bucket(w, p) - 1  # returns end one before the sessions
    bucket = int(w.day[-1]) // p["refit_days"]
    if state.get("bucket") != bucket:
        train = jumps[max(0, end - p["fit_sessions"]) : end]
        if len(train) < p["fit_sessions"]:
            return float("nan")
        state["fit"] = fit_jump_excitation(train, p["beta"]) if train.sum() >= 3 else None
        state["bucket"] = bucket
    fit = state["fit"]
    if fit is None:
        return 1.0  # too few jumps to fit: no stress read
    # The intensity for the NEXT session: one filter step past the window.
    lam = mutually_exciting_jump_intensity(
        np.r_[jumps, [[0.0]]], fit["mu"], fit["alpha"], p["beta"]
    )
    stressed = lam[-1, 0] > p["multiple"] * fit["mu"][0]
    return float(p["floor"]) if stressed else 1.0


def _random_forest(w: Window, p: dict, state: dict) -> float:
    """RK290 (Krauss, Do & Huck 2017) for one fund: a random forest on
    lagged returns (technical_ml.lag_feature_matrix) classifies the next
    session up or down; long while P(up) > threshold. Refitted once per
    `refit_days` bucket on the `train` labelled sessions before it
    (_before_bucket; each label a session already closed), fixed seed."""
    from sklearn.ensemble import RandomForestClassifier

    from research.catalog.technical_ml import lag_feature_matrix

    lags = tuple(int(x) for x in p["lags"])
    c = w.close
    bucket = int(w.day[-1]) // p["refit_days"]
    if state.get("bucket") != bucket:
        end = _before_bucket(w, p)
        closes = c[max(0, end - p["train"] - max(lags) - 1) : end]
        if len(closes) < p["train"] + max(lags) + 1:
            return float("nan")
        x, y = lag_feature_matrix(closes, lags)
        state["model"], state["bucket"] = None, bucket
        if len(set(y)) == 2:
            model = RandomForestClassifier(
                n_estimators=p["trees"], min_samples_leaf=5, random_state=0, n_jobs=1
            )
            state["model"] = model.fit(x, y)
    if state["model"] is None:
        return float("nan")
    last = np.array([[c[-1] / c[-1 - lg] - 1 for lg in lags]])
    return float(state["model"].predict_proba(last)[0, 1] > p["threshold"])


SIGNALS: dict[str, Signal] = {
    "tsmom": Signal(
        "RK1, RK2",
        "time-series momentum (Moskowitz-Ooi-Pedersen), long at vol_target / sigma",
        _tsmom,
        {"lookback": 252, "vol_target": 0.4, "com": 60.0},
        lambda p: p["lookback"] + 250,
    ),
    "multi_timeframe": Signal(
        "RK78",
        "momentum signs over several horizons: all positive, or the share positive",
        _multi_timeframe,
        {"horizons": (21, 63, 252), "mode": "agree"},
        lambda p: max(p["horizons"]) + 2,
        choices={"mode": ("agree", "average")},
    ),
    "supertrend": Signal(
        "RK44",
        "Supertrend: ATR bands that ratchet, long while the close holds the lower one",
        _supertrend,
        {"n": 10, "mult": 3.0},
        lambda p: max(250, 10 * p["n"]),
    ),
    "macd": Signal(
        "Q1, RK62",
        "MACD line above its signal line",
        _trend_regime("macd"),
        {"fast": 12, "slow": 26, "signal": 9},
        lambda p: max(250, 8 * p["slow"]),
    ),
    "awesome": Signal(
        "Q5",
        "Awesome Oscillator above zero",
        _trend_regime("awesome"),
        {"fast": 5, "slow": 34},
        lambda p: p["slow"] + 2,
    ),
    "psar": Signal(
        "Q8",
        "Parabolic SAR in a rising trend",
        _trend_regime("psar"),
        {"step": 0.02, "max_step": 0.2},
        lambda p: 250,
    ),
    "heikin_ashi": Signal(
        "Q3",
        "Heikin-Ashi candles bullish, confirmed for `confirm` sessions",
        _trend_regime("heikin_ashi"),
        {"confirm": 1},
        lambda p: 250,
    ),
    "sma": Signal(
        "V16",
        "close above its `window`-session simple moving average",
        _trend_regime("sma"),
        {"window": 200},
        lambda p: p["window"] + 1,
    ),
    "state_momentum": Signal(
        "RK10",
        "momentum only when the fund is up over state_lookback and not in a high-volatility state",
        _state_momentum,
        {
            "lookback": 252,
            "skip": 21,
            "state_lookback": 756,
            "vol_days": 21,
            "vol_quantile": 0.8,
        },
        lambda p: max(p["state_lookback"], p["lookback"], 252 + p["vol_days"]) + 2,
    ),
    "high_52w": Signal(
        "RK14",
        "nearness to the 52-week high (George-Hwang): held above threshold, or graded",
        _high_52w,
        {"window": 252, "threshold": 0.9, "mode": "binary", "floor": 0.7},
        lambda p: p["window"] + 1,
        choices={"mode": ("binary", "graded")},
    ),
    "ema_ribbon": Signal(
        "RK64",
        "Guppy moving-average ribbon stacked (every short EMA above every long one)",
        _ema_ribbon,
        {"short": (3, 5, 8, 10, 12, 15), "long": (30, 35, 40, 45, 50, 60), "mode": "stacked"},
        lambda p: max(250, 5 * max(p["long"])),
        choices={"mode": ("stacked", "average")},
    ),
    "jump_stress": Signal(
        "RK314",
        "self-exciting jump intensity as a stress gauge: out while it is above its baseline",
        _jump_stress,
        {
            "jump_window": 60,
            "k": 4.0,
            "beta": 0.1,
            "multiple": 3.0,
            "floor": 0.0,
            "fit_sessions": 440,
            "refit_days": 28,
        },
        lambda p: p["fit_sessions"] + p["jump_window"] + p["refit_days"] + 2,
        stateful=True,
    ),
    "random_forest": Signal(
        "RK290",
        "random forest on lagged returns, refitted every refit_days; long when P(up) is high",
        _random_forest,
        {
            "lags": (1, 2, 3, 5, 10, 21),
            "trees": 100,
            "threshold": 0.55,
            "train": 500,
            "refit_days": 28,
        },
        lambda p: p["train"] + max(p["lags"]) + p["refit_days"] + 2,
        stateful=True,
    ),
    "kalman_trend": Signal(
        "concept: stochastic-process trend",
        "local linear trend Kalman filter on log prices, long while its slope is positive",
        _kalman,
        {"q_level": 1e-5, "q_slope": 1e-7, "r": 1e-4},
        lambda p: 500,
    ),
    "l1_trend": Signal(
        "concept: l1 trend filtering",
        "l1 trend filter (ADMM) on a trailing window, long while its last slope is positive",
        _l1,
        {"window": 120, "lam": 5.0},
        lambda p: p["window"] + 1,
    ),
    "kama": Signal(
        "concept: adaptive trend",
        "close above Kaufman's adaptive moving average",
        _kama,
        {"n": 10, "fast": 2, "slow": 30},
        lambda p: max(300, 10 * p["slow"]),
    ),
    "cycle_momentum": Signal(
        "concept: adaptive trend (Garg et al.)",
        "fast/slow momentum blended by cycle state, the blend fitted on the window's first half",
        _cycle,
        {"fast": 21, "slow": 252},
        lambda p: 3 * p["slow"],
    ),
    "spectral_trend": Signal(
        "concept: spectral trend",
        "low Fourier modes of the detrended window, long while the reconstruction rises",
        _spectral,
        {"window": 128, "keep": 3},
        lambda p: p["window"] + 1,
    ),
    "bayesian_drift": Signal(
        "concept: Bayesian trend",
        "P(drift > 0) from a discounted Normal-inverse-gamma posterior, long above threshold",
        _bayesian,
        {"prior_strength": 20.0, "discount": 0.99, "threshold": 0.6},
        # discount 0.99 forgets with a ~100-session memory; scipy's t cdf
        # per step makes each session's call ~75 ms at this length.
        lambda p: 250,
    ),
    "robust_momentum": Signal(
        "concept: robust trend",
        "Theil-Sen slope (or median return) of the trailing window, long while positive",
        _robust,
        {"lookback": 126, "method": "theil_sen"},
        lambda p: p["lookback"] + 1,
        choices={"method": ("theil_sen", "median")},
    ),
    "arfima": Signal(
        "concept: fractional-order trend",
        "ARFIMA(0,d,0) one-step forecast (d by GPH), long while positive",
        _arfima,
        {"window": 100},
        lambda p: max(500, 3 * p["window"]),
    ),
    "tail_budget": Signal(
        "concept: tail-risk model (POT)",
        "exposure min(1, es_budget / ES) from a peaks-over-threshold fit of the trailing window",
        _tail_budget,
        {"es_budget": 0.03, "window": 500, "alpha": 0.99},
        lambda p: p["window"] + 2,
    ),
    "wavelet_var": Signal(
        "concept: wavelet tail risk",
        "exposure min(1, var_budget / VaR) from Haar wavelet variances",
        _wavelet,
        {"var_budget": 0.03, "levels": 4, "window": 250, "alpha": 0.01},
        lambda p: p["window"] + 2 ** p["levels"] + 2,
    ),
    "early_warning": Signal(
        "concept: critical slowing down",
        "flat while lag-1 autocorrelation and variance are both trending up (Kendall tau)",
        _early_warning,
        {"threshold": 0.5, "window": 100, "trend_window": 50},
        lambda p: p["window"] + p["trend_window"] + 2,
    ),
}


# ------------------------------------------------------------ parameters


def _value(text: str) -> ParamValue:
    if "/" in text:
        return tuple(_value(part) for part in text.split("/") if part)
    for cast in (int, float):
        try:
            return cast(text)
        except ValueError:
            pass
    return text


def parse_signal_params(signal: str, text: str) -> dict[str, ParamValue]:
    """`signal`'s defaults with "name=value;..." laid over them; an unknown
    signal or parameter name, or a value of the wrong kind, is refused."""
    if signal not in SIGNALS:
        raise ConfigurationError(
            f"catalog_signal must be one of {', '.join(sorted(SIGNALS))}, got {signal!r}"
        )
    defaults = SIGNALS[signal].defaults
    params = dict(defaults)
    for part in (p.strip() for p in str(text or "").split(";")):
        if not part:
            continue
        name, sep, raw = part.partition("=")
        name, raw = name.strip(), raw.strip()
        if not sep or not raw:
            raise ConfigurationError(f"catalog_params entries look like name=value, got {part!r}")
        if name not in defaults:
            known = ", ".join(defaults) or "none"
            raise ConfigurationError(f"{signal} takes no parameter {name!r} (it takes: {known})")
        value, default = _value(raw), defaults[name]
        if isinstance(default, tuple) and not isinstance(value, tuple):
            value = (value,)
        if isinstance(default, float) and isinstance(value, int):
            value = float(value)
        if isinstance(default, str) != isinstance(value, str) or (
            isinstance(default, tuple) != isinstance(value, tuple)
        ):
            raise ConfigurationError(
                f"{signal}: {name}={raw!r} is not like its default {default!r}"
            )
        params[name] = value
    for name, allowed in SIGNALS[signal].choices.items():
        if params[name] not in allowed:
            raise ConfigurationError(
                f"{signal}: {name} must be one of {allowed}, got {params[name]!r}"
            )
    return params


# ------------------------------------------------------------ the signal object


class CatalogTimingSignal:
    """RspTimingSignal's interface (observe, warm_up, history_sessions,
    target, votes) over one catalog signal."""

    def __init__(self, signal: str, params: dict[str, ParamValue]) -> None:
        self.name = signal
        self.spec = SIGNALS[signal]
        self.params = params
        self._need = int(self.spec.history(params))
        if self._need < 2:
            raise ConfigurationError(f"{signal}: history must be at least 2 sessions")
        self._rows: deque[tuple[float, ...]] = deque(maxlen=self._need)
        self._day: date | None = None
        self._o = self._h = self._l = self._c = None
        self._v = 0.0
        self.next_open: float | None = None
        self._state: dict = {}
        self.target: float | None = None
        self.raw: float | None = None
        self.votes: dict[str, float | None] = {}

    @property
    def history_sessions(self) -> int:
        return self._need

    def observe(self, timestamp, high: float, low: float, close: float, volume: float, open_=None):
        """One bar. A new session's open is `open_`, else `next_open` (set
        by the strategy from the bar's open), else the bar's close."""
        day = timestamp.date()
        if day != self._day:
            if self._day is not None:
                self._close_session()
            self._day = day
            if open_ is None:
                open_ = self.next_open
            self._o = close if open_ is None else open_
            self._h, self._l, self._c, self._v = high, low, close, float(volume)
            return
        self._h = max(self._h, high)
        self._l = min(self._l, low)
        self._c = close
        self._v += float(volume)

    def warm_up(self, daily) -> int:
        """Seed from session OHLCV before the first bar, as RspTimingSignal."""
        missing = {"high", "low", "close", "volume"} - set(daily.columns)
        if missing:
            raise ConfigurationError(f"daily bars are missing {sorted(missing)}")
        opens = daily["open"] if "open" in daily.columns else daily["close"]
        days = [ts.date() for ts in daily.index]
        if days and self._day is not None and days[0] <= self._day:
            raise ConfigurationError(
                f"warm-up starts {days[0]}, not after the latest observed session {self._day}"
            )
        for ts, o, h, lo, c, v in zip(
            daily.index,
            opens.to_numpy(float),
            daily["high"].to_numpy(float),
            daily["low"].to_numpy(float),
            daily["close"].to_numpy(float),
            daily["volume"].to_numpy(float),
            strict=True,
        ):
            self.observe(ts, float(h), float(lo), float(c), float(v), open_=float(o))
        return len(days)

    def _close_session(self) -> None:
        self._rows.append((self._o, self._h, self._l, self._c, self._v, self._day.toordinal()))
        self.raw = self.evaluate(self._rows)
        value = 0.0 if not np.isfinite(self.raw) else max(0.0, self.raw)
        self.target = value
        self.votes = {self.name: self.raw}

    def evaluate(self, rows) -> float:
        """The signal's raw value from completed sessions `rows` (oldest
        first: open, high, low, close, volume, date ordinal); NaN while
        there are fewer than it needs."""
        if len(rows) < self._need:
            return float("nan")
        arr = np.asarray(rows, float)
        window = Window(
            arr[:, 0], arr[:, 1], arr[:, 2], arr[:, 3], arr[:, 4], arr[:, 5].astype(int)
        )
        with np.errstate(all="ignore"):
            if self.spec.stateful:
                return float(self.spec.compute(window, self.params, self._state))
            return float(self.spec.compute(window, self.params))


class CatalogExposureSizing(UltimateRspSizing):
    """Ultimate-RSP's exposure book on a research-catalog signal: see the
    module docstring."""

    # Each signal's `history` already includes the sessions its recursive
    # filters need to forget their seed, so a live replay adds none.
    _SIGNAL_SETTLE_SESSIONS = 0

    def __init__(
        self,
        catalog_signal: str = "kalman_trend",
        catalog_params: str = "",
        execute_minute: int = 60,
        rebalance_band: float = 0.05,
        max_exposure: float = 1.0,
        cash_buffer: float = 0.005,
    ) -> None:
        super().__init__(
            execute_minute=execute_minute,
            rebalance_band=rebalance_band,
            max_exposure=max_exposure,
            cash_buffer=cash_buffer,
        )
        self.signal = str(catalog_signal)
        self.signal_params = parse_signal_params(self.signal, catalog_params)
        self._signal = CatalogTimingSignal(self.signal, self.signal_params)

    def record_tick(self, context) -> None:
        # The parent's observe passes no open; a session's open is its
        # first bar's, handed over here before that call.
        self._signal.next_open = float(context.open)
        super().record_tick(context)

    def diagnostics(self) -> dict:
        out = super().diagnostics()
        out.update(catalog_signal=self.signal, catalog_raw=self._signal.raw)
        return out


__all__ = [
    "SIGNALS",
    "CatalogExposureSizing",
    "CatalogTimingSignal",
    "Signal",
    "Window",
    "parse_signal_params",
]
