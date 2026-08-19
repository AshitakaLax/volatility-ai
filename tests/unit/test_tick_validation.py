"""
Task 7.6 acceptance tests (L7).

Acceptance criterion: a synthetic tick stream containing one
zero-price and one absurd-spike tick results in both being
rejected/flagged rather than processed as real triggers, while
surrounding valid ticks are processed normally.
"""

from datetime import datetime, timezone

import pytest

from src.config import BacktestConfig
from src.live_execution import LiveExecutionLoop
from src.market_context import MarketContext
from src.secrets import API_KEY_ID_ENV_VAR, API_SECRET_KEY_ENV_VAR
from src.size_calculators import FixedPortfolioPercentage
from src.tick_validation import TickRejectionReason, TickValidator


def _live_config() -> BacktestConfig:
    return BacktestConfig.from_dict(
        {
            "strategy": {"strategy_id": "fixed", "strategy_params": {"allocation_pct": 0.05}},
            "grid": {"steps": [0.01], "profit_targets": [0.005]},
            "backtest": {"symbol": "TQQQ", "initial_cash": 100_000.0},
            "live": {"enabled": True, "paper_trading": True},
        }
    )


def _context_builder(price: float) -> MarketContext:
    return MarketContext(
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
        open=price, high=price, low=price, close=price,
        cash=100_000.0, equity=100_000.0, peak_equity=100_000.0,
        drawdown=0.0, open_lot_count=0, bar_index=0,
    )


def test_synthetic_stream_rejects_zero_price_and_absurd_spike_only():
    """Acceptance criterion, at the validator level."""
    validator = TickValidator(max_move_pct=0.20)
    stream = [100.0, 101.0, 0.0, 102.0, 5000.0, 103.0]

    results = [validator.validate(p) for p in stream]
    accepted = [r.price for r in results if r.accepted]
    rejected = [(r.price, r.reason) for r in results if not r.accepted]

    assert accepted == [100.0, 101.0, 102.0, 103.0], "Surrounding valid ticks must process normally"
    assert rejected == [(0.0, TickRejectionReason.NON_POSITIVE), (5000.0, TickRejectionReason.IMPLAUSIBLE_MOVE)]
    assert validator.accepted_count == 4
    assert validator.rejected_count == 2


def test_rejected_ticks_never_advance_the_last_good_price():
    validator = TickValidator(max_move_pct=0.20)
    validator.validate(100.0)
    assert validator.last_good_price == 100.0

    validator.validate(0.0)
    assert validator.last_good_price == 100.0, "A rejected zero-price tick must not become the reference"

    validator.validate(5000.0)
    assert validator.last_good_price == 100.0, "A rejected spike must not become the reference"

    validator.validate(101.0)
    assert validator.last_good_price == 101.0, "A valid tick after rejections still advances normally"


def test_a_spike_cannot_walk_the_reference_price_across_repeated_rejections():
    # Without the guard above, each rejected spike would move the
    # baseline and eventually let the next spike through.
    validator = TickValidator(max_move_pct=0.20)
    validator.validate(100.0)
    for _ in range(5):
        assert validator.validate(5000.0).accepted is False
    assert validator.last_good_price == 100.0
    assert validator.validate(5000.0).accepted is False


@pytest.mark.parametrize("bad_price", [0.0, -1.0, -0.01])
def test_non_positive_prices_rejected(bad_price):
    validator = TickValidator()
    check = validator.validate(bad_price)
    assert not check.accepted
    assert check.reason is TickRejectionReason.NON_POSITIVE


@pytest.mark.parametrize("bad_price", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_prices_rejected(bad_price):
    validator = TickValidator()
    check = validator.validate(bad_price)
    assert not check.accepted
    assert check.reason is TickRejectionReason.NON_FINITE


@pytest.mark.parametrize("bad_price", [None, "not-a-number"])
def test_unparseable_prices_rejected_without_raising(bad_price):
    validator = TickValidator()
    check = validator.validate(bad_price)
    assert not check.accepted
    assert check.reason is TickRejectionReason.NON_FINITE


def test_first_tick_has_no_move_reference_and_is_accepted():
    # Nothing to compare against yet; only the price checks apply.
    validator = TickValidator(max_move_pct=0.01)
    assert validator.validate(100.0).accepted is True


def test_price_checks_still_apply_to_the_very_first_tick():
    validator = TickValidator(max_move_pct=0.01)
    assert validator.validate(-5.0).accepted is False


def test_move_exactly_at_the_limit_is_accepted():
    validator = TickValidator(max_move_pct=0.20)
    validator.validate(100.0)
    assert validator.validate(120.0).accepted is True  # exactly +20%


def test_move_just_over_the_limit_is_rejected():
    validator = TickValidator(max_move_pct=0.20)
    validator.validate(100.0)
    assert validator.validate(120.01).accepted is False


def test_large_but_plausible_leveraged_etf_move_is_not_rejected():
    # TQQQ is 3x-leveraged; several-percent intraday moves are routine
    # and must not be treated as feed glitches.
    validator = TickValidator()  # default 20%
    validator.validate(50.0)
    assert validator.validate(52.5).accepted is True  # +5%
    assert validator.validate(48.0).accepted is True  # -8.6% from 52.5


def test_downward_spike_also_rejected():
    validator = TickValidator(max_move_pct=0.20)
    validator.validate(100.0)
    check = validator.validate(1.0)
    assert not check.accepted
    assert check.reason is TickRejectionReason.IMPLAUSIBLE_MOVE


def test_invalid_max_move_pct_rejected():
    for bad in (0.0, -0.1):
        with pytest.raises(ValueError):
            TickValidator(max_move_pct=bad)


def test_rejections_are_logged_when_no_audit_sink_is_wired(caplog):
    validator = TickValidator(max_move_pct=0.20)
    validator.validate(100.0)
    with caplog.at_level("WARNING", logger="Optimizer"):
        validator.validate(0.0)
        validator.validate(5000.0)
    messages = " ".join(r.getMessage() for r in caplog.records)
    assert "NON_POSITIVE" in messages
    assert "IMPLAUSIBLE_MOVE" in messages


def test_rejections_route_to_an_audit_sink_when_provided():
    records = []
    validator = TickValidator(max_move_pct=0.20, audit_sink=records.append)
    validator.validate(100.0)
    validator.validate(0.0)
    validator.validate(5000.0)

    assert len(records) == 2
    assert {r["reason"] for r in records} == {"NON_POSITIVE", "IMPLAUSIBLE_MOVE"}
    assert all(r["event"] == "tick_rejected" for r in records)
    assert all("last_good_price" in r for r in records)


def test_rejected_tick_never_reaches_strategy_evaluation(monkeypatch):
    monkeypatch.setenv(API_KEY_ID_ENV_VAR, "k")
    monkeypatch.setenv(API_SECRET_KEY_ENV_VAR, "s")

    class _CountingStrategy(FixedPortfolioPercentage):
        def __init__(self, allocation_pct):
            super().__init__(allocation_pct=allocation_pct)
            self.tick_count = 0

        def record_tick(self, context):
            self.tick_count += 1

    strategy = _CountingStrategy(allocation_pct=0.05)
    loop = LiveExecutionLoop(_live_config(), strategy)
    loop.start()

    contexts_built = []

    def builder(price):
        contexts_built.append(price)
        return _context_builder(price)

    stream = [100.0, 0.0, 99.0, 5000.0, 98.0]
    decisions = [loop.process_tick(p, builder, step=0.01, last_buy_price=100.0) for p in stream]

    assert contexts_built == [100.0, 99.0, 98.0], "A rejected tick must not even build a context"
    assert strategy.tick_count == 3, "Strategy must only see the 3 valid ticks"
    assert decisions[1] is None and decisions[3] is None
    assert all(d is not None for i, d in enumerate(decisions) if i not in (1, 3))


def test_rejected_tick_proposes_no_order(monkeypatch):
    monkeypatch.setenv(API_KEY_ID_ENV_VAR, "k")
    monkeypatch.setenv(API_SECRET_KEY_ENV_VAR, "s")
    loop = LiveExecutionLoop(_live_config(), FixedPortfolioPercentage(allocation_pct=0.05))
    loop.start()

    # A zero price would otherwise look like an enormous grid drop.
    decision = loop.process_tick(0.0, _context_builder, step=0.01, last_buy_price=100.0)
    assert decision is None, "A zero-price tick must not produce a trade decision"


def test_valid_tick_after_a_rejection_still_triggers_normally(monkeypatch):
    monkeypatch.setenv(API_KEY_ID_ENV_VAR, "k")
    monkeypatch.setenv(API_SECRET_KEY_ENV_VAR, "s")
    loop = LiveExecutionLoop(_live_config(), FixedPortfolioPercentage(allocation_pct=0.05))
    loop.start()

    loop.process_tick(100.0, _context_builder, step=0.01, last_buy_price=100.0)
    assert loop.process_tick(0.0, _context_builder, step=0.01, last_buy_price=100.0) is None
    decision = loop.process_tick(98.0, _context_builder, step=0.01, last_buy_price=100.0)
    assert decision is not None
    assert decision.triggered is True  # 98 <= 100 * (1 - 0.01)
