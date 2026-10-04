"""research/strategies/grid_lifecycle.py -- catalog C-G4, C-G6, C-X2."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pytest

from engine.core.exceptions import ConfigurationError
from engine.execution.cost_models import ZeroCostModel
from research.strategies.grid_lifecycle import (
    DynamicGrid,
    expected_steps,
    geometric_levels,
    profit_only_time_exits,
    ruin_probability,
    rungs_for_decline,
    target_first_probability,
)

# ---------------------------------------------------------------- C-G4


def test_n_grids_give_n_plus_one_levels_at_an_equal_ratio():
    levels = geometric_levels(100.0, n_grids=6, ratio=0.02)
    assert len(levels) == 7
    assert levels[3] == pytest.approx(100.0)
    ratios = np.array(levels[1:]) / np.array(levels[:-1])
    assert ratios == pytest.approx(np.full(6, 1.02))


def test_no_reset_inside_the_range():
    grid = DynamicGrid(100.0, 4, 0.05)
    for price in (95.0, 100.0, 109.0, 91.0):
        assert grid.on_price(price) is None
    assert grid.center == pytest.approx(100.0)


def test_a_break_above_re_centres_on_the_price():
    grid = DynamicGrid(100.0, 4, 0.05)
    top = grid.levels[-1]
    assert grid.on_price(top * 1.001) == "up"
    assert grid.center == pytest.approx(top * 1.001)
    assert grid.resets_up == 1


def test_a_break_below_re_centres_and_is_reported_as_down():
    grid = DynamicGrid(100.0, 4, 0.05)
    bottom = grid.levels[0]
    assert grid.on_price(bottom * 0.999) == "down"
    assert grid.center == pytest.approx(bottom * 0.999) and grid.resets_down == 1


def test_grid_rejects_bad_parameters():
    for args in ((0.0, 4, 0.1), (100.0, 3, 0.1), (100.0, 4, 0.0)):
        with pytest.raises(ConfigurationError):
            geometric_levels(*args)


# ---------------------------------------------------------------- C-G6


def test_symmetric_walk_hits_the_target_first_in_proportion():
    assert target_first_probability(3, 7) == pytest.approx(0.3)
    assert ruin_probability(3, 7) == pytest.approx(0.7)
    assert expected_steps(3, 7) == pytest.approx(21.0)


def test_biased_walk_matches_the_gamblers_ruin_formula():
    p, q, a, b = 0.45, 0.55, 5, 5
    r = q / p
    assert target_first_probability(a, b, p) == pytest.approx((1 - r**a) / (1 - r ** (a + b)))


def test_formulas_agree_with_simulation():
    rng = np.random.default_rng(0)
    down, up, p = 4, 6, 0.48
    hits, steps = 0, 0
    trials = 20_000
    for _ in range(trials):
        pos, n = 0, 0
        while -down < pos < up:
            pos += 1 if rng.random() < p else -1
            n += 1
        hits += pos == up
        steps += n
    assert hits / trials == pytest.approx(target_first_probability(down, up, p), abs=0.01)
    assert steps / trials == pytest.approx(expected_steps(down, up, p), rel=0.03)


def test_rungs_for_a_decline():
    # Each rung is 99% of the one above: a 10% fall crosses ceil(ln .9 / ln .99) = 11 rungs.
    assert rungs_for_decline(0.10, 0.01) == 11
    assert 0.99**11 <= 0.90 < 0.99**10
    # A decline that lands exactly on a rung needs exactly that many.
    assert rungs_for_decline(1 - 0.5**3, 0.5) == 3


def test_ruin_inputs_are_validated():
    for args in ((0, 3, 0.5), (3, 3, 1.0), (3, 3, 0.0)):
        with pytest.raises(ConfigurationError):
            target_first_probability(*args)
    with pytest.raises(ConfigurationError):
        rungs_for_decline(1.0, 0.01)


# ---------------------------------------------------------------- C-X2


@dataclass
class _Lot:
    buy_price: float
    quantity: float


def test_old_profitable_lots_are_exited_and_young_ones_are_not():
    lots = [(_Lot(100.0, 10), 0), (_Lot(100.0, 10), 95)]
    out = profit_only_time_exits(
        lots, now_bar=100, price=101.0, max_hold_bars=50, cost_model=ZeroCostModel()
    )
    assert out == [lots[0][0]]


def test_old_losing_lots_are_never_exited():
    lots = [(_Lot(110.0, 10), 0)]
    assert profit_only_time_exits(lots, 1000, 100.0, 50, ZeroCostModel()) == []


def test_break_even_counts_as_permitted_by_the_guard():
    lots = [(_Lot(100.0, 5), 0)]
    assert profit_only_time_exits(lots, 60, 100.0, 50, ZeroCostModel()) == [lots[0][0]]


def test_time_exit_validates_max_hold():
    with pytest.raises(ConfigurationError):
        profit_only_time_exits([], 10, 100.0, 0, ZeroCostModel())
