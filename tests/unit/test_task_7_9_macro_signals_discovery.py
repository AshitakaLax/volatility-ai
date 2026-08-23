"""
Task 7.9 -- Discovery gate: are macro/seasonality signals required?

DISCOVERY OUTCOME, RE-RUN: **is_macro_event_day now has a confirmed,
deliberate consumer.** The original finding ("not required / deferred,
no confirmed consumer exists") held until HighFrequencyLocalReferenceSizing's
event_day_boost_multiplier was added -- this test module's own job was
to fail the moment that happened, and it did, which is what triggered
this re-run and the step 3 documentation below.

  Consuming strategy:  src/high_frequency_sizing.py,
                       HighFrequencyLocalReferenceSizing.calculate_trade_value,
                       via the event_day_boost_multiplier constructor
                       parameter (default 1.0 -- a no-op; see that
                       module's docstring for the full rationale).
  Source dataset:      src/fomc_calendar.py -- a STATIC, hand-verified
                       list of FOMC decision dates sourced from
                       federalreserve.gov's own historical calendar
                       pages. Not NLP, not sentiment, not a live feed:
                       FOMC dates are published a year-plus in advance,
                       so a static calendar is the complete
                       implementation, not a placeholder for one.
  Join semantics:      src/fomc_calendar.py:is_fomc_day_at() converts a
                       bar's timestamp to its Eastern calendar date
                       (naive input treated as UTC, never host-local)
                       and does an exact-date-match set lookup. Called
                       from exactly two places -- optimization_
                       controller.py's _simulate_single (backtest) and
                       live_trading_loop.py's _build_context (live) --
                       so both paths flag the same day identically.
  Defaults:            is_macro_event_day still defaults to False on
                       MarketContext itself; a bar not on the FOMC
                       calendar is indistinguishable from before this
                       existed. event_day_boost_multiplier defaults to
                       1.0, so a strategy config that never sets it
                       gets identical behavior to before this existed.

SECOND EVENT CLASS, SAME GATE: MarketContext.is_earnings_reaction_day
was added alongside the above and is documented to the same step-3
standard.

  Consuming strategy:  src/high_frequency_sizing.py, same method, via
                       the earnings_day_boost_multiplier constructor
                       parameter (default 1.0 -- a no-op). On a session
                       flagged as BOTH an FOMC day and an earnings
                       reaction day the larger multiplier wins; the two
                       do not compound.
  Source dataset:      src/earnings_calendar.py -- a STATIC list of the
                       sessions that TRADE a mega-cap earnings reaction,
                       generated once from Yahoo Finance and NOT a
                       runtime dependency. Note this flags the reaction
                       session, not the announcement date: 381 of 385
                       announcements land after the close, and that
                       mapping was verified against per-constituent
                       overnight gaps rather than assumed.
  Join semantics:      src/earnings_calendar.py:is_earnings_reaction_day_at()
                       -- identical Eastern-date conversion to the FOMC
                       helper, whose EASTERN_TZ it imports rather than
                       redefining, called from the same two places.
  Defaults:            False on MarketContext, 1.0 on the multiplier --
                       a config that never sets it behaves exactly as
                       before this existed. Verified: the pinned
                       regression baseline's values are unchanged by
                       this addition.

THIRD FIELD: time_of_day_flag, populated at last.

  Consuming strategy:  src/high_frequency_sizing.py, same method, via
                       the time_of_day_exponent constructor parameter
                       (default 0.0 -- an exact no-op).
  Source dataset:      src/intraday_profile.py -- mean intrabar range
                       per minute-of-session, measured on this repo's
                       own 10-year dataset (2,655 samples per minute)
                       and normalized to mean 1.0. Not a live feed.
  Join semantics:      minutes since 09:30 Eastern, 0-389, -1 outside
                       the regular session. The vectorized backtest path
                       and the scalar live path share the same window
                       and the same Eastern conversion.
  Defaults:            0 on MarketContext, exponent 0.0 on the strategy.
                       Verified: the pinned regression baseline is
                       unchanged by this addition.

Per the original task's step 4, no NLP/sentiment ingestion dependency
was added to build this -- confirmed by
test_no_speculative_ingestion_dependency_was_added below, unchanged and
still enforced. The remaining tests in this module have been updated
from "no consumer exists anywhere" to "exactly the one documented
consumer above exists, and nothing else has started consuming these
fields" -- still a live canary against silent, undocumented
proliferation, just no longer claiming zero consumers.
"""

import re
from pathlib import Path

from src.market_context import MarketContext

REPO_ROOT = Path(__file__).resolve().parents[2]

MACRO_FIELDS = (
    "time_of_day_flag",
    "is_macro_event_day",
    "macro_surprise_factor",
    # Added when MarketContext gained a second event flag. It is watched
    # by the same canary as the original three deliberately: a new event
    # field that nothing guards is exactly the "silent, undocumented
    # proliferation" this module exists to catch.
    "is_earnings_reaction_day",
)

# Modules that must STILL have zero consumption of these fields. Every
# strategy/decision module except the one documented, deliberate
# consumer (src/high_frequency_sizing.py) belongs here -- this is what
# keeps the canary live against a SECOND, undocumented consumer
# appearing, rather than only ever checking the one already known
# about.
STRATEGY_MODULES = (
    "src/size_calculators.py",
    "src/decision_cycle.py",
    "src/risk_manager.py",
    "src/bayesian_sizing_calculators.py",
)

# The one documented, deliberate consumer (see module docstring's
# "DISCOVERY OUTCOME, RE-RUN" section for the full step-3 writeup).
CONFIRMED_CONSUMER_MODULE = "src/high_frequency_sizing.py"
# Now two fields, not one: the same strategy branches on both event
# flags, with a separate multiplier each (see that module's docstring
# for why they are not folded into a single flag).
CONFIRMED_CONSUMER_FIELDS = (
    "is_macro_event_day",
    "is_earnings_reaction_day",
    # The third and last of Task 7.9's original fields to gain a
    # consumer. All three are now live inputs; macro_surprise_factor is
    # the only one of the four still inert.
    "time_of_day_flag",
)


def test_the_event_fields_exist_with_the_documented_safe_defaults():
    """Contract check against overview 5.1. These stay in place; the
    finding is about whether to POPULATE them, not whether to keep them."""
    context = MarketContext(
        timestamp=None,
        open=1.0,
        high=1.0,
        low=1.0,
        close=1.0,
        cash=0.0,
        equity=0.0,
        peak_equity=0.0,
        drawdown=0.0,
        open_lot_count=0,
        bar_index=0,
    )
    assert context.time_of_day_flag == 0
    assert context.is_macro_event_day is False
    assert context.macro_surprise_factor == 0.0
    assert context.is_earnings_reaction_day is False


def test_no_other_strategy_or_decision_module_consumes_the_macro_fields():
    """The narrower, still-live discovery finding: NO consumer other
    than the one documented one exists.

    If this fails, a SECOND consumer has appeared undocumented -- the
    module docstring's step-3 writeup (consuming strategy, source
    dataset, join semantics, defaults) must be extended to cover it
    before any further ingestion is built.
    """
    consumers = []
    for module in STRATEGY_MODULES:
        path = REPO_ROOT / module
        if not path.exists():
            continue
        source = path.read_text()
        for field in MACRO_FIELDS:
            if field in source:
                consumers.append(f"{module}:{field}")

    assert consumers == [], (
        f"An UNDOCUMENTED consumer of the macro/seasonality fields now exists: {consumers}. "
        "Only src/high_frequency_sizing.py is documented as a consumer (module docstring's "
        "step-3 writeup) -- extend that documentation before adding another."
    )


def test_the_confirmed_consumer_still_exists_exactly_where_documented():
    """The positive half of the re-run finding: the ONE documented
    consumer must still be there. If this fails, either the feature
    was removed (update the docstring) or moved (update this test to
    match) -- either way the documentation must track reality."""
    path = REPO_ROOT / CONFIRMED_CONSUMER_MODULE
    assert path.exists(), f"{CONFIRMED_CONSUMER_MODULE} is documented as the macro-field consumer but no longer exists"
    source = path.read_text()
    missing = [f for f in CONFIRMED_CONSUMER_FIELDS if f not in source]
    assert missing == [], (
        f"{CONFIRMED_CONSUMER_MODULE} no longer references {missing!r} -- "
        "either restore it or update this module's docstring and this test"
    )


def test_nothing_branches_on_the_macro_fields_outside_the_confirmed_consumer():
    """A pass-through assignment is not consumption. A BRANCH is --
    except in the one documented, deliberate consumer, which is
    supposed to branch on is_macro_event_day."""
    branch_pattern = re.compile(
        r"(if|elif|while|assert)\b[^\n]*\b(" + "|".join(MACRO_FIELDS) + r")\b"
    )
    offenders = []
    for path in (REPO_ROOT / "src").glob("*.py"):
        if path.name == Path(CONFIRMED_CONSUMER_MODULE).name:
            continue
        for line_no, line in enumerate(path.read_text().splitlines(), start=1):
            if branch_pattern.search(line):
                offenders.append(f"{path.name}:{line_no}")

    assert offenders == [], (
        f"Conditional logic now reads the macro fields at {offenders}, outside the one "
        "documented consumer -- extend the module docstring's step-3 writeup to cover it."
    )


def test_no_speculative_ingestion_dependency_was_added():
    """Step 4: the only permitted production change was documentation.
    No sentiment/NLP/macro data pipeline may have appeared."""
    forbidden = ("finbert", "transformers", "sentiment", "fomc", "federal reserve")
    requirements = (REPO_ROOT / "requirements.txt").read_text().lower()
    for term in forbidden:
        assert term not in requirements, (
            f"requirements.txt now contains {term!r} -- Task 7.9 forbids adding an ingestion "
            "dependency merely to make the task appear implemented."
        )


def test_the_named_bayesian_strategy_now_exists_and_is_still_not_macroeconomic():
    """BayesianDualScaleSizing is now IMPLEMENTED, so this test's
    predecessor has been re-run as it demanded.

    The earlier version asserted the strategy was absent and required
    that, "if it is ever added, the 'macro' ambiguity noted in this
    module's docstring should be re-examined at that point." That
    re-examination happened when the strategy was written, and the
    finding is unchanged:

    The two scales in BayesianDualScaleSizing are a FAST and a SLOW
    Beta posterior over the same latent quantity, differing only in
    exponential-forgetting half-life. "Macro" is the long-half-life
    posterior -- a lookback-length distinction, exactly as the task's
    original context described. It consumes no macroeconomic data.

    The discovery outcome therefore still stands: no consumer of
    time_of_day_flag / is_macro_event_day / macro_surprise_factor
    exists. The sibling tests in this module enforce that directly and
    remain the live gate; this test now guards the narrower claim that
    the Bayesian strategy did not become such a consumer.
    """
    from src.bayesian_sizing_calculators import BayesianDualScaleSizing

    source = (REPO_ROOT / "src" / "bayesian_sizing_calculators.py").read_text()

    for field in MACRO_FIELDS:
        assert field not in source, (
            f"BayesianDualScaleSizing now references {field!r} -- it has become a macro-field "
            "consumer, so the Task 7.9 discovery gate must be re-run in full (step 3: document "
            "the source dataset, join semantics, and defaults)."
        )

    # The sizing inputs are still just price and equity, as they were
    # when FixedPortfolioPercentage was the only strategy.
    import inspect

    sizing_src = inspect.getsource(BayesianDualScaleSizing.calculate_trade_value)
    assert "context.equity" in sizing_src and "context.price" in sizing_src

    ingestion_terms = ("finbert", "transformers", "sentiment", "fomc", "cpi")
    lowered = source.lower()
    for term in ingestion_terms:
        assert term not in lowered, (
            f"src/bayesian_sizing_calculators.py mentions {term!r} -- the Task 7.9 gate forbids "
            "adding macro/NLP ingestion to make the strategy appear more capable."
        )
