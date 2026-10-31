"""Phase 0 of docs/research/buy-sell-composition.md: every sell path the
composition work changes, pinned value for value against today's behaviour.

See tests/fixtures/composition_baseline.py for the cases and how to
regenerate the baseline -- only ever on purpose, saying why. A failure here
means a change moved which lots sell, when, or for how much."""

from __future__ import annotations

import math

import pytest

from tests.fixtures import composition_baseline as fixture

BASELINE = fixture.load_baseline()
MONEY_EPSILON = 1e-8


@pytest.fixture(scope="module")
def ohlcv():
    return fixture.load_ohlcv()


def test_the_baseline_covers_every_case():
    assert BASELINE is not None, "run `python -m tests.fixtures.composition_baseline --write`"
    assert set(BASELINE) == {case.name for case in fixture.CASES}


def test_the_dataset_is_the_generated_one():
    """The committed CSV is what the generator writes, so the data is
    reproducible from its source, not only from the file."""
    generated = fixture.generate_ohlcv()
    committed = fixture.load_ohlcv()
    assert len(generated) == len(committed) == fixture.SESSIONS * fixture.BARS_PER_DAY
    assert generated["close"].tolist() == pytest.approx(committed["close"].tolist(), abs=1e-9)


def _close(expected, actual) -> bool:
    if isinstance(expected, float) and isinstance(actual, (int, float)):
        return math.isclose(actual, expected, rel_tol=1e-9, abs_tol=MONEY_EPSILON)
    return expected == actual


@pytest.mark.parametrize("case", fixture.CASES, ids=lambda case: case.name)
def test_case_matches_the_pinned_baseline(case, ohlcv):
    expected = BASELINE[case.name]
    actual = fixture.run_case(case, ohlcv)

    assert actual["blotter"] == expected["blotter"], (
        f"{case.name}: the trade blotter changed (rows/sells/sha256) -- which lots sold, "
        "when, or for how much moved."
    )
    missing = set(expected["summary"]) - set(actual["summary"])
    extra = set(actual["summary"]) - set(expected["summary"])
    assert not missing and not extra, f"{case.name}: columns missing {missing}, extra {extra}"
    diffs = {
        key: (value, actual["summary"][key])
        for key, value in expected["summary"].items()
        if not _close(value, actual["summary"][key])
    }
    assert not diffs, f"{case.name}: baseline vs fresh differ: {diffs}"


def test_the_cases_exercise_every_sell_path():
    """The baseline only protects what it covers: target harvests, retargeted
    harvests, signal exits of every lot and of some, and reversal lots."""
    sells = {name: (result["blotter"] or {}).get("sells", 0) for name, result in BASELINE.items()}
    signal = {
        name: result["summary"].get("Signal Exit Count", 0) for name, result in BASELINE.items()
    }
    assert all(sells[name] > 0 for name in sells if BASELINE[name]["blotter"] is not None)
    for name in (
        "harvest-calm-sleeve-full-exit",
        "harvest-calm-sleeve-partial-exit",
        "ultimate",
        "ultimate-rsp",
        "catalog-exposure-sma",
    ):
        assert signal[name] > 0, f"{name} took no signal exit"
    assert signal["harvest-calm-sleeve-partial-exit"] < signal["harvest-calm-sleeve-full-exit"]
    assert BASELINE["champion-trailing"]["blotter"] != BASELINE["champion-intrabar"]["blotter"]
    assert BASELINE["harvest-decay"]["blotter"] != BASELINE["champion-intrabar"]["blotter"]
