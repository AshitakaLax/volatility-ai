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

FOURTH AND FIFTH FIELDS: event_intensity and minutes_to_event, added
together for minute-precision, index-weighted event awareness -- NOT
one of Task 7.9's original four, so this is a first run for these two,
not a re-run.

  Consuming strategy:  src/high_frequency_sizing.py, same method, via
                       the weighted_event_boost_multiplier constructor
                       parameter (default 1.0 -- a no-op). Combines
                       with is_macro_event_day/is_earnings_reaction_day
                       via max(), not multiply -- event_intensity is a
                       minute-precise REFINEMENT of the same claim
                       those make at day granularity, not an
                       independent axis; multiplying would double-count
                       a day this project has knowledge of at both
                       granularities. minutes_to_event has NO consumer
                       yet -- event_intensity's own lead-time window
                       already carries the "aware N minutes before"
                       property the countdown would otherwise add, so
                       there was no separate use for it in this pass.
                       It is guarded here anyway, watched for the same
                       reason macro_surprise_factor already is: an
                       unguarded field is exactly the silent
                       proliferation this module exists to catch, even
                       before anything consumes it.
  Source dataset:      src/event_calendar.py's EarningsEventTable, over
                       data/earnings_releases_derived.csv -- 676 release
                       timestamps across 16 tickers, RECOVERED from the
                       tape (found the day from the next session's
                       opening gap, the minute from that day's peak
                       post-close volume; see that module's docstring
                       for why recovering a scheduled, publicly
                       announced time is not lookahead), weighted by
                       src/index_weights.py's single 2026-08-13
                       QQQ-holdings snapshot -- documented there as
                       lookahead bias applied to all history, pending
                       quarterly snapshots.
  Join semantics:      EarningsEventTable.vectorized (backtest) and
                       .scalar (live) share one window definition --
                       [release - lead_minutes, release +
                       reaction_minutes), 15/30 minutes by default --
                       and are pinned to agree on every bar by
                       tests/unit/test_event_calendar.py::test_scalar_and_vectorized_agree_on_every_bar.
                       event_intensity SUMS index weight over every
                       currently-active event rather than taking a max,
                       because two different companies reporting in the
                       same window are independent exposure, unlike the
                       day-level flags' max() above.
  Defaults:            event_intensity=0.0, minutes_to_event=-1.0 on
                       MarketContext; weighted_event_boost_multiplier=1.0
                       on the strategy -- a config that never sets it
                       behaves exactly as before this existed.

SIXTH FIELD -- implied_vol_change. The first input here sourced from
an instrument OTHER than the one being traded, which is exactly why it
is guarded: an external series is the easiest kind of thing to add
casually.

  Consuming strategy:  src/high_frequency_sizing.py, via the
                       implied_vol_exponent constructor parameter
                       (default 0.0 -- an exact no-op) in
                       _implied_vol_scale. MULTIPLIES with the other
                       scalers rather than max()-ing with the event
                       boosts, because it is a genuinely independent
                       axis and that was MEASURED, not asserted:
                       holding trailing realized vol fixed it still
                       scores partial rank correlation +0.257 against
                       next-session opening volatility. Clamped, so the
                       product stays bounded.
  Source dataset:      src/implied_vol_signal.py over an implied-vol
                       instrument's minute bars, joined by
                       src/external_index_series.py (which existed,
                       tested, with no consumer until now). Currently
                       VIXY -- a PROXY on two axes: VIX (S&P 500) not
                       VXN (Nasdaq-100), and VIX futures via an ETF
                       wrapper not spot. VXN's provider was unreachable
                       when this was written. Re-measure against real
                       VXN before trusting tuned parameters.
  Join semantics:      session-over-session percentage change in the
                       series' CLOSE, published to the as-of series at
                       midnight Eastern the day AFTER the session that
                       produced it, so every bar of the next session --
                       pre-market included -- reads a value that was
                       already history when that session opened. The
                       no-lookahead property is asserted directly in
                       tests/unit/test_implied_vol_signal.py rather than
                       inferred, and scalar/vectorized are pinned equal
                       there on every bar, the same discipline
                       event_calendar.py established.
  Defaults:            implied_vol_change=0.0 on MarketContext;
                       implied_vol_exponent=0.0 on the strategy. A
                       config that never sets it, and a deployment with
                       no implied-vol file at all, both reproduce prior
                       behavior bit for bit -- the pinned regression
                       baseline is unchanged by this field existing.

  Why it earns an axis when the day-level calendars barely did: it is
  not scheduled. It fires every session rather than on a twentieth of
  them, which is the exact ceiling the FOMC/earnings boosts hit
  (~1-2pp each). And being sourced from a different instrument, it is
  the only signal here that can be non-redundant with
  vol_scale_exponent by construction. tools/measure_vol_signal.py
  rejected the implied LEVEL (roll-decay drift, not signal) and the
  implied fast/slow RATIO (collapsed to -0.039 once controlled for
  trailing realized vol -- it was re-encoding persistence the strategy
  already had) before this one survived.

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
    # Fourth and fifth fields, minute-precision event awareness -- see
    # module docstring's "FOURTH AND FIFTH FIELDS" section.
    # minutes_to_event has no consumer yet and is watched anyway, same
    # reasoning as macro_surprise_factor: guard the field before
    # anything reads it, not after.
    "event_intensity",
    "minutes_to_event",
    # Sixth field -- see the module docstring's "SIXTH FIELD" section.
    # The first signal here sourced from an instrument OTHER than the one
    # being traded, which is precisely why it is guarded: an external
    # series is the easiest kind of input to add casually.
    "implied_vol_change",
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
    # Fourth field, first run rather than a re-run -- see module
    # docstring. minutes_to_event is deliberately NOT here: it has no
    # consumer (event_intensity's own lead window already carries the
    # lead-time property), so it must not appear in the confirmed
    # consumer's source, and test_nothing_branches_on_the_macro_fields_...
    # would catch it branching anywhere else.
    "event_intensity",
    # Sixth field. Unlike minutes_to_event, this one DOES have a
    # consumer from the moment it exists -- it was wired only because a
    # measurement justified it, so there was never a stage at which it
    # was populated and unread.
    "implied_vol_change",
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
    assert context.event_intensity == 0.0
    assert context.minutes_to_event == -1.0


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
    assert path.exists(), (
        f"{CONFIRMED_CONSUMER_MODULE} is documented as the macro-field consumer but no longer exists"
    )
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
    No sentiment/NLP/macro data pipeline may have appeared.

    Reads the DEPENDENCY LINES, not the whole file. The first version
    matched raw text, so it fired on any comment that happened to
    mention a forbidden word -- and it did: adding tzdata, which is a
    hard runtime requirement for ZoneInfo in a slim container, tripped
    it because the comment explaining WHY names src/fomc_calendar.py as
    the module doing the import.

    A gate that cannot be explained in a comment without failing pushes
    people to remove the explanation, which is the opposite of what this
    module is for. The rule it actually means -- no ingestion package
    was added -- is unchanged and is what is checked here.
    """
    forbidden = ("finbert", "transformers", "sentiment", "fomc", "federal reserve")
    lines = (REPO_ROOT / "requirements.txt").read_text().lower().splitlines()
    declared = [
        line.split("#", 1)[0].strip()
        for line in lines
        if line.strip() and not line.lstrip().startswith("#")
    ]
    for requirement in declared:
        for term in forbidden:
            assert term not in requirement, (
                f"requirements.txt declares {requirement!r}, which contains {term!r} -- "
                "Task 7.9 forbids adding an ingestion dependency merely to make the "
                "task appear implemented."
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
