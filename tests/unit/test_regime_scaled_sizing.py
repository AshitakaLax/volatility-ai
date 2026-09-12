"""MLRegimeScaledSizing: the latch, the widened grid, and the sizing terms.

NO MODEL FILE IS LOADED BY ANY OF THESE, and that is the point of the
context-injection seam. MarketContext carries qlib_regime_score, so a
regime response can be tested by CONSTRUCTING the regime -- which means
these tests state the behavior directly instead of depending on a
trained artifact that is gitignored, ticker-specific, and absent on any
fresh clone or CI runner.

That gap is real and these tests do not close it: the round trip
(tools/train_qlib_regime.py writes -> RegimeInferenceSource loads ->
the strategy latches) was verified by hand against synthetic bars, not
here. Closing it properly means a fixture that trains a two-row booster
into tmp_path, which is worth adding the first time this strategy is
actually swept.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta

import pytest

from src.core.exceptions import ConfigurationError
from src.ml.qlib_regime import NO_READING, DailyRegimeFeatures, RegimeInferenceSource
from src.ml.regime_scaled_sizing import MLRegimeScaledSizing
from src.strategies.market_context import MarketContext

pytest.importorskip("lightgbm", reason="src/ml/ is an optional-dependency package")


def context(
    *,
    price: float = 100.0,
    score: float = -1.0,
    vol: float = -1.0,
    drawdown: float = 0.0,
    equity: float = 100_000.0,
    when: datetime | None = None,
) -> MarketContext:
    stamp = when or datetime(2026, 3, 2, 14, 30, tzinfo=UTC)
    return MarketContext(
        timestamp=stamp,
        open=price,
        high=price,
        low=price,
        close=price,
        cash=equity,
        equity=equity,
        peak_equity=equity / (1.0 - drawdown) if drawdown else equity,
        drawdown=drawdown,
        open_lot_count=0,
        bar_index=0,
        qlib_regime_score=score,
        expected_volatility=vol,
    )


@pytest.fixture
def strategy(tmp_path, monkeypatch):
    """A strategy whose model loading is bypassed.

    RegimeInferenceSource is constructed for real everywhere else; here
    the two boosters are absent and only the injection path is under
    test, so the constructor is stubbed rather than given a fake model
    file. Stubbing the SOURCE (not the strategy) keeps every method
    under test running its real code.
    """

    def _no_model(self, ticker, **kwargs):
        self.ticker = ticker
        self.uses_vol_block = False
        # The real source always has this; an empty dict is what a
        # model trained before quantiles were recorded produces.
        self.score_quantiles = {}

    monkeypatch.setattr(RegimeInferenceSource, "__init__", _no_model)
    # NO_READING, not None: the real observe() always returns a
    # RegimeReading, and a stub that returned None would be testing
    # against a source that cannot exist.
    monkeypatch.setattr(RegimeInferenceSource, "observe", lambda self, *a, **k: NO_READING)

    def build(**overrides):
        params = {"max_trade_pct": 0.05, "ticker": "XBI"}
        params.update(overrides)
        return MLRegimeScaledSizing(**params)

    return build


# --- the hysteresis latch -------------------------------------------


def test_latch_enters_only_above_enter_threshold(strategy):
    sizing = strategy(regime_enter_threshold=0.65, regime_exit_threshold=0.45)

    sizing.record_tick(context(score=0.64))
    assert sizing.step_multiplier == 1.0

    sizing.record_tick(context(score=0.65))
    assert sizing.step_multiplier == sizing.crash_step_multiplier


def test_latch_holds_through_the_hysteresis_band(strategy):
    """The whole reason for two thresholds: a score drifting back into
    the band must not re-tighten the grid."""
    sizing = strategy(regime_enter_threshold=0.65, regime_exit_threshold=0.45)

    sizing.record_tick(context(score=0.70))
    assert sizing._in_crash

    for score in (0.64, 0.55, 0.46):
        sizing.record_tick(context(score=score))
        assert sizing._in_crash, f"released at {score}, inside the band"

    sizing.record_tick(context(score=0.45))
    assert not sizing._in_crash


def test_latch_survives_a_reading_going_missing(strategy):
    """A model that drops out mid-crash must not silently re-tighten
    the grid to 1% while price is still falling."""
    sizing = strategy()
    sizing.record_tick(context(score=0.90))
    assert sizing._in_crash

    sizing.record_tick(context(score=-1.0, vol=-1.0))
    assert sizing._in_crash


# --- the widened grid -----------------------------------------------


def test_trigger_level_widens_while_latched(strategy):
    sizing = strategy(crash_step_multiplier=4.0)

    calm = context(score=0.10)
    sizing.record_tick(calm)
    assert sizing._grid_trigger_level(calm, 100.0, 0.01) == pytest.approx(99.0)

    crash = context(score=0.95)
    sizing.record_tick(crash)
    assert sizing._grid_trigger_level(crash, 100.0, 0.01) == pytest.approx(96.0)


def test_check_grid_trigger_routes_through_the_widened_level(strategy):
    """_check_grid_trigger is NOT overridden -- it must inherit the
    widening via _grid_trigger_level, which is what keeps the intrabar
    fill model (which calls the level directly) in agreement with the
    close-only path."""
    sizing = strategy(crash_step_multiplier=4.0)
    crash = context(price=97.0, score=0.95)
    sizing.record_tick(crash)

    # 97 would have triggered a 1% grid from 100; it must not trigger
    # the widened 4% one.
    assert not sizing._check_grid_trigger(crash, 100.0, 0.01)
    assert sizing._check_grid_trigger(context(price=95.9, score=0.95), 100.0, 0.01)


def test_crash_step_multiplier_of_one_disables_widening(strategy):
    sizing = strategy(crash_step_multiplier=1.0)
    crash = context(score=0.99)
    sizing.record_tick(crash)
    assert sizing._grid_trigger_level(crash, 100.0, 0.01) == pytest.approx(99.0)


def test_grid_trigger_level_does_not_mutate_the_latch(strategy):
    """Every state change belongs in record_tick. The intrabar fill
    model calls the level repeatedly for one bar; if that moved the
    latch, the grid would depend on which fill model was running."""
    sizing = strategy()
    sizing.record_tick(context(score=0.95))
    before = sizing._in_crash
    for _ in range(5):
        sizing._grid_trigger_level(context(score=0.05), 100.0, 0.01)
    assert sizing._in_crash is before


# --- sizing ----------------------------------------------------------


def test_size_shrinks_toward_the_floor_as_the_score_rises(strategy):
    sizing = strategy(regime_floor=0.25)
    ceiling = 100_000.0 * 0.05

    sizing.record_tick(context(score=0.0))
    assert sizing.calculate_trade_value(context(score=0.0)) == pytest.approx(ceiling)

    sizing.record_tick(context(score=1.0))
    assert sizing.calculate_trade_value(context(score=1.0)) == pytest.approx(ceiling * 0.25)


def test_unwarmed_model_sizes_at_the_floor_not_at_full(strategy):
    """The conservative direction, matching reachability_sizing.py's
    confidence_floor convention."""
    sizing = strategy(regime_floor=0.25)
    blind = context(score=-1.0, vol=-1.0)
    sizing.record_tick(blind)
    assert sizing.calculate_trade_value(blind) == pytest.approx(100_000.0 * 0.05 * 0.25)


def test_volatility_term_is_inert_below_the_reference(strategy):
    sizing = strategy(vol_reference=0.45, regime_floor=1.0)
    ctx = context(score=0.0, vol=0.30)
    sizing.record_tick(ctx)
    assert sizing.calculate_trade_value(ctx) == pytest.approx(100_000.0 * 0.05)


def test_volatility_term_halves_the_lot_at_twice_the_reference(strategy):
    sizing = strategy(vol_reference=0.40, vol_floor=0.1, regime_floor=1.0)
    ctx = context(score=0.0, vol=0.80)
    sizing.record_tick(ctx)
    assert sizing.calculate_trade_value(ctx) == pytest.approx(100_000.0 * 0.05 * 0.5)


def test_volatility_term_disabled_when_no_reference_is_set(strategy):
    sizing = strategy(vol_reference=None, regime_floor=1.0)
    ctx = context(score=0.0, vol=5.0)
    sizing.record_tick(ctx)
    assert sizing.calculate_trade_value(ctx) == pytest.approx(100_000.0 * 0.05)


@pytest.mark.parametrize(
    ("response", "shallow_vs_deep"),
    [
        (1.5, "shallow bigger"),  # de-risking
        (-1.5, "deep bigger"),  # escalating
    ],
)
def test_drawdown_response_direction(strategy, response, shallow_vs_deep):
    sizing = strategy(drawdown_response=response, regime_floor=1.0)

    shallow = context(score=0.0, drawdown=0.05)
    sizing.record_tick(shallow)
    shallow_value = sizing.calculate_trade_value(shallow)

    deep = context(score=0.0, drawdown=0.50)
    sizing.record_tick(deep)
    deep_value = sizing.calculate_trade_value(deep)

    if shallow_vs_deep == "shallow bigger":
        assert shallow_value > deep_value
    else:
        assert deep_value > shallow_value


def test_drawdown_response_defaults_to_inert(strategy):
    sizing = strategy(regime_floor=1.0)
    flat, deep = context(score=0.0), context(score=0.0, drawdown=0.6)
    sizing.record_tick(flat)
    sizing.record_tick(deep)
    assert sizing.calculate_trade_value(flat) == pytest.approx(sizing.calculate_trade_value(deep))


def test_no_multiplier_combination_exceeds_the_ceiling(strategy):
    """The house invariant from _BaselineScaledStrategy: a model may
    shrink a lot toward zero and may never grow one past max_trade_pct."""
    sizing = strategy(regime_floor=1.0, vol_reference=1.0, drawdown_response=-2.0)
    ceiling = 100_000.0 * 0.05
    for score in (0.0, 0.3, 0.7, 1.0):
        for dd in (0.0, 0.25, 0.9):
            ctx = context(score=score, vol=0.05, drawdown=dd)
            sizing.record_tick(ctx)
            assert sizing.calculate_trade_value(ctx) <= ceiling + 1e-9


# --- the exits it must NOT have --------------------------------------


def test_cannot_move_a_target_or_liquidate(strategy):
    """This strategy proposes buys only. Both selling hooks must stay at
    SizingStrategy's defaults, or it could realize a loss."""
    sizing = strategy()
    assert sizing.adjust_profit_target(object(), context()) is None
    assert sizing.lots_to_liquidate([object(), object()], context()) == []


# --- configuration guards --------------------------------------------


@pytest.mark.parametrize(
    "kwargs",
    [
        {"crash_step_multiplier": 0.5},  # would TIGHTEN in a crash
        {"regime_enter_threshold": 0.4, "regime_exit_threshold": 0.4},  # no band
        {"regime_enter_threshold": 0.3, "regime_exit_threshold": 0.6},  # inverted
        {"regime_floor": 1.5},
        {"vol_reference": 0.0},
        {"ticker": ""},
    ],
)
def test_rejected_configurations(strategy, kwargs):
    with pytest.raises(ConfigurationError):
        strategy(**kwargs)


# --- the silent-inertness guard --------------------------------------


@pytest.mark.parametrize(
    ("threshold", "raises"),
    [
        (0.65, True),  # above p99: the latch could never engage
        (0.25, False),  # inside the model's actual range
    ],
)
def test_threshold_above_the_models_p99_is_refused(monkeypatch, threshold, raises):
    """A threshold a model's output never reaches makes the strategy
    inert while still loading a model and computing a score every
    session -- a feature that does nothing and shows nothing. It must be
    a startup error, not a warning."""

    def _stub(self, ticker, **kwargs):
        self.ticker = ticker
        self.uses_vol_block = False
        self.score_quantiles = {"p50": 0.19, "p90": 0.23, "p95": 0.24, "p99": 0.26, "max": 0.26}

    monkeypatch.setattr(RegimeInferenceSource, "__init__", _stub)

    sizing = MLRegimeScaledSizing(
        max_trade_pct=0.05,
        ticker="XBI",
        regime_enter_threshold=threshold,
        regime_exit_threshold=0.10,
    )
    if raises:
        with pytest.raises(ConfigurationError, match="99th-percentile"):
            sizing.ensure_model_available()
    else:
        sizing.ensure_model_available()


def test_a_model_without_recorded_quantiles_is_not_blocked(monkeypatch):
    """Unknown is not unreachable -- a model trained before quantiles
    were recorded must still load."""

    def _stub(self, ticker, **kwargs):
        self.ticker = ticker
        self.uses_vol_block = False
        self.score_quantiles = {}

    monkeypatch.setattr(RegimeInferenceSource, "__init__", _stub)
    MLRegimeScaledSizing(
        max_trade_pct=0.05, ticker="XBI", regime_enter_threshold=0.99
    ).ensure_model_available()


# --- the causal guarantee in the inference source ---------------------


def test_daily_features_are_causal():
    """record() must describe sessions strictly BEFORE the one handed
    in -- the first call has nothing to describe and every column is
    NaN, exactly as IncrementalBarFeatures behaves."""
    engine = DailyRegimeFeatures()

    first = engine.record(101.0, 99.0, 100.0)
    assert all(math.isnan(v) for v in first.values())

    # Session two: one close is known (100), which is not yet two, so a
    # one-session return still cannot be formed.
    second = engine.record(103.0, 101.0, 102.0)
    assert math.isnan(second["ret_1d"])

    # Session three: ret_1d is the move INTO session two (102/100 - 1).
    # The assertion that matters is the NEGATIVE one -- it must NOT be
    # the move into session three (105/102 - 1), which is the value a
    # forgotten shift would produce and which would leak this session's
    # own close into the vector scoring it.
    third = engine.record(106.0, 104.0, 105.0)
    assert third["ret_1d"] == pytest.approx(102.0 / 100.0 - 1.0)
    assert third["ret_1d"] != pytest.approx(105.0 / 102.0 - 1.0)


def test_reading_is_computed_from_completed_sessions_only(monkeypatch):
    """A session is scored only once a bar from the NEXT one arrives, so
    the session being scored cannot contribute its own close."""
    scored_at = []

    def _no_model(self, ticker, **kwargs):
        self.ticker = ticker
        self.uses_vol_block = False
        # The real source always has this; an empty dict is what a
        # model trained before quantiles were recorded produces.
        self.score_quantiles = {}
        self.min_sessions = 1
        self._features = DailyRegimeFeatures()
        self._session = None
        self._high, self._low, self._close = -math.inf, math.inf, math.nan
        self._reading = __import__("src.ml.qlib_regime", fromlist=["NO_READING"]).NO_READING
        self._external = {}

    monkeypatch.setattr(RegimeInferenceSource, "__init__", _no_model)
    monkeypatch.setattr(
        RegimeInferenceSource,
        "_predict",
        lambda self, ts, vector: scored_at.append((self._features.sessions, vector["ret_1d"])),
    )

    source = RegimeInferenceSource("XBI")
    start = datetime(2026, 3, 2, 14, 30, tzinfo=UTC)

    # Three bars inside one session: nothing is scored.
    for minute in range(3):
        source.observe(start + timedelta(minutes=minute), 101.0, 99.0, 100.0)
    assert scored_at == []

    # First bar of the next session rolls the previous one in.
    source.observe(start + timedelta(days=1), 102.0, 100.0, 101.0)
    assert len(scored_at) == 1
