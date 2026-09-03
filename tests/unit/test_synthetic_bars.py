"""Tests for src/synthetic_bars.py.

This predicate describes how src/historical_data.resample_to_uniform_minutes
writes fabricated bars. It was previously duplicated verbatim in two
strategies, so the point of these tests is not only that it is correct
but that the ONE definition both now call behaves as each of them
relied on.
"""

from __future__ import annotations

import pytest

from src.synthetic_bars import is_synthetic_bar


def test_a_flat_unchanged_bar_is_synthetic():
    """The resample_to_uniform_minutes signature: high == low == close,
    carried forward from the previous real print."""
    assert is_synthetic_bar(high=100.0, low=100.0, price=100.0, prev_price=100.0)


def test_a_bar_that_moved_is_real_even_if_flat():
    """Flat but at a NEW price is a real print -- one trade in the
    minute, at a different level. Treating it as fabricated would drop a
    genuine observation."""
    assert not is_synthetic_bar(high=101.0, low=101.0, price=101.0, prev_price=100.0)


def test_a_bar_with_range_is_real_even_at_an_unchanged_close():
    """A minute that traded a range and closed where it opened is a real
    bar. Only the ABSENCE of range plus the absence of change together
    indicate fabrication."""
    assert not is_synthetic_bar(high=100.5, low=99.5, price=100.0, prev_price=100.0)


def test_the_first_bar_is_never_synthetic():
    """Nothing precedes it, so there is nothing it could have been
    carried forward from. Misreading it would silently drop a real
    observation from every rolling window that follows."""
    assert not is_synthetic_bar(high=100.0, low=100.0, price=100.0, prev_price=None)


def test_volume_is_deliberately_not_part_of_the_test():
    """Gating on volume == 0 would disable realized-vol scaling in LIVE
    trading permanently, because LiveBar carries no volume field and
    context.volume is always 0.0 there. The signature takes no volume at
    all, so that mistake cannot be made by a caller."""
    import inspect

    params = set(inspect.signature(is_synthetic_bar).parameters)
    assert "volume" not in params
    assert params == {"high", "low", "price", "prev_price"}


@pytest.mark.parametrize(
    ("high", "low", "price", "prev", "expected"),
    [
        (10.0, 10.0, 10.0, 10.0, True),  # fabricated
        (10.0, 10.0, 10.0, 9.99, False),  # flat, moved
        (10.1, 9.9, 10.0, 10.0, False),  # ranged, unchanged close
        (10.1, 9.9, 10.0, 9.9, False),  # ranged and moved
        (10.0, 10.0, 10.0, None, False),  # first bar
    ],
)
def test_the_truth_table(high, low, price, prev, expected):
    assert is_synthetic_bar(high, low, price, prev) is expected


def test_both_strategies_call_the_shared_predicate_rather_than_inlining_it():
    """Structural. The whole point of the module is that the rule has one
    definition -- a strategy quietly reinstating its own copy would
    reintroduce exactly the drift this prevents, and would still pass
    every behavioural test above."""
    from pathlib import Path

    for module in ("src/high_frequency_sizing.py", "src/bayesian_sizing_calculators.py"):
        source = Path(module).read_text(encoding="utf-8")
        assert "from src.synthetic_bars import is_synthetic_bar" in source, (
            f"{module} no longer imports the shared predicate"
        )
        # The inlined form was `high == low and ... price == prev_price`.
        assert "context.high == context.low" not in source, (
            f"{module} appears to have reinlined the synthetic-bar test"
        )
