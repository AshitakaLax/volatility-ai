"""The README's factual claims must track the code.

WHY THIS FILE EXISTS. The "Known limitations" list had rotted into
saying things that were no longer true:

  * "No strategy registry. strategy_id requires a manual mapping" --
    while src/strategy_registry.py existed with a STRATEGIES dict and a
    lookup that raises on an unknown id.
  * "Macro/seasonality fields are inert ... nothing consumes them" --
    while HighFrequencyLocalReferenceSizing consumed four of them and
    config/best_known_*.yaml shipped event_day_boost_multiplier: 2.5 in
    production.
  * "905 tests" -- against a suite well past 1,400.

`grep -rn README tests/` returned nothing before this file: no test
asserted anything the README said, so all three went stale silently.

A stale limitations list is worse than no list. A reader trusts it, and
either avoids capability the system already has or re-does work that is
already done -- which is exactly the failure a limitations section is
supposed to prevent.

These tests only cover claims that are MECHANICALLY CHECKABLE. Prose
about design intent is not testable and is not tested; the point is to
catch the specific claims that a code change can silently falsify. The
repo already uses source-grep assertions this way -- see
test_no_source_path_can_set_dry_false and the Task 7.9 discovery gate.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
README = REPO_ROOT / "README.md"


@pytest.fixture(scope="module")
def readme() -> str:
    return README.read_text(encoding="utf-8")


def test_the_readme_does_not_deny_the_strategy_registry(readme):
    """src/strategy_registry.py exists and is imported by the config
    layer, so a claim that there is no registry is simply false."""
    from src.strategy_registry import STRATEGIES

    assert STRATEGIES, "the registry is empty; this test's premise changed"
    assert "No strategy registry" not in readme, (
        "README claims there is no strategy registry, but src/strategy_registry.py "
        f"defines {len(STRATEGIES)} strategies. Update the README."
    )


def test_the_readme_does_not_claim_the_consumed_macro_fields_are_inert(readme):
    """Four MarketContext signal fields have a real consumer. If the
    README says nothing consumes them, one of the two is wrong."""
    consumer = (REPO_ROOT / "src" / "high_frequency_sizing.py").read_text(encoding="utf-8")
    consumed = [
        field
        for field in (
            "is_macro_event_day",
            "is_earnings_reaction_day",
            "time_of_day_flag",
            "event_intensity",
            "implied_vol_change",
        )
        if field in consumer
    ]
    assert len(consumed) >= 4, f"expected several consumed fields, found {consumed}"
    assert "but nothing consumes them" not in readme, (
        f"README says nothing consumes the macro fields, but {consumed} are all read "
        "by HighFrequencyLocalReferenceSizing."
    )


def test_the_readme_does_not_pin_a_stale_test_count(readme):
    """A hardcoded count is guaranteed to rot. Three had already: "905
    tests" against a suite past 1,400, plus "660 tests"/"143 tests" in
    the directory tree, and "35 modules" against an actual 52. This test
    found the last three -- they were not in the block being edited, and
    would not have been noticed by hand.

    Any literal "<number> tests|modules" claim drifts on the next commit,
    so the README should not carry one at all."""
    import re

    stale = re.findall(r"\b(\d+)\s+(?:tests|modules)\b", readme)
    assert not stale, (
        f"README hardcodes a count {stale}, which rots on the next commit. "
        "Describe it without a number."
    )


def test_macro_surprise_factor_really_is_still_inert(readme):
    """The README now claims this ONE field is unconsumed. That claim
    must also be kept honest -- if someone wires it up, this fails and
    the README gets corrected rather than becoming stale in the other
    direction."""
    sources = [
        (REPO_ROOT / "src" / path).read_text(encoding="utf-8")
        for path in ("high_frequency_sizing.py", "bayesian_sizing_calculators.py")
    ]
    assert all("macro_surprise_factor" not in src for src in sources), (
        "macro_surprise_factor now has a consumer -- update the README's "
        "limitations list and the Task 7.9 discovery-gate docstring."
    )
    assert "macro_surprise_factor" in readme, (
        "README no longer mentions the one field that is genuinely inert"
    )
