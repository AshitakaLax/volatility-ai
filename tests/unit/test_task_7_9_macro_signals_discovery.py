"""
Task 7.9 -- Discovery gate: are macro/seasonality signals required?

DISCOVERY OUTCOME: **Not required / deferred.** No confirmed consumer
exists. Per the task's step 2 ("If no confirmed consumer exists,
record that outcome and stop. Do not add an ingestion dependency
merely to make the task appear implemented"), no ingestion pipeline
was built and no production behavior was changed.

These tests make that finding EXECUTABLE rather than a claim in a
document, which is what the acceptance criteria require. They are
deliberately written to FAIL if a consumer is ever added -- at which
point the discovery gate must be re-run and step 3 (documenting the
consuming strategy, source dataset, join semantics, defaults, and a
follow-up implementation task) becomes live. A discovery finding that
silently goes stale is worse than none.

Evidence gathered (repository-wide search, all three field names):

  src/market_context.py       DEFINES the fields with safe defaults
                              (0, False, 0.0). A definition, not a consumer.
  src/live_execution.py       build_context() accepts and FORWARDS them.
                              Pure pass-through plumbing: it type-coerces
                              and hands them to the constructor. It never
                              reads a value to make a decision.
  src/size_calculators.py     The only real strategy,
                              FixedPortfolioPercentage, reads exactly
                              context.price and context.equity. Neither
                              of the three fields.

  - No conditional logic anywhere in the repository branches on any of
    the three fields.
  - No call site ever supplies a non-default value.
  - No FinBERT / sentiment / transformers / CPI / Federal Reserve /
    FOMC reference exists anywhere in the repository.

On the external claim that prompted this task: the assertion was that
FinBERT NLP sentiment and Fed/CPI macro-event awareness were already
integrated into this system's Bayesian sizing. Nothing in this
repository supports that. BayesianDualScaleSizing is not implemented
here at all (FixedPortfolioPercentage is the only sizing strategy that
exists), and per the task's own context, "macro" in that class's name
refers to a LONG-WINDOW Bayesian posterior -- a lookback-length
distinction -- not to macroeconomic events. The two senses of "macro"
appear to be the source of the confusion.

The fields themselves are harmless and are deliberately left in place:
they are optional, defaulted, and already part of overview 5.1's
MarketContext contract. Removing them would be a breaking change for
no benefit. Populating them with real data would be the speculative
scope this gate exists to prevent.
"""

import re
from pathlib import Path

from src.market_context import MarketContext

REPO_ROOT = Path(__file__).resolve().parents[2]

MACRO_FIELDS = ("time_of_day_flag", "is_macro_event_day", "macro_surprise_factor")

# Modules where a genuine CONSUMER would have to live: something that
# reads a field to change a trading decision.
STRATEGY_MODULES = (
    "src/size_calculators.py",
    "src/decision_cycle.py",
    "src/risk_manager.py",
)


def test_the_three_fields_exist_with_the_documented_safe_defaults():
    """Contract check against overview 5.1. These stay in place; the
    finding is about whether to POPULATE them, not whether to keep them."""
    context = MarketContext(
        timestamp=None, open=1.0, high=1.0, low=1.0, close=1.0,
        cash=0.0, equity=0.0, peak_equity=0.0, drawdown=0.0,
        open_lot_count=0, bar_index=0,
    )
    assert context.time_of_day_flag == 0
    assert context.is_macro_event_day is False
    assert context.macro_surprise_factor == 0.0


def test_no_strategy_or_decision_module_consumes_the_macro_fields():
    """THE discovery finding, made executable.

    If this fails, a consumer has appeared and Task 7.9's discovery
    gate must be re-run -- step 3 then requires documenting the
    consuming strategy, required fields, source dataset, timestamp-join
    semantics, default behavior, and a follow-up implementation task
    BEFORE any ingestion is built.
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
        "A consumer of the macro/seasonality fields now exists: "
        f"{consumers}. Task 7.9's discovery outcome ('Not required / deferred') is stale -- "
        "re-run the gate and complete step 3 before building any ingestion."
    )


def test_nothing_branches_on_the_macro_fields():
    """A pass-through assignment is not consumption. A BRANCH is.

    live_execution.build_context forwards these fields into
    MarketContext, which is plumbing, not a consumer -- so this checks
    specifically for conditional logic reading them.
    """
    branch_pattern = re.compile(
        r"(if|elif|while|assert)\b[^\n]*\b(" + "|".join(MACRO_FIELDS) + r")\b"
    )
    offenders = []
    for path in (REPO_ROOT / "src").glob("*.py"):
        for line_no, line in enumerate(path.read_text().splitlines(), start=1):
            if branch_pattern.search(line):
                offenders.append(f"{path.name}:{line_no}")

    assert offenders == [], (
        f"Conditional logic now reads the macro fields at {offenders} -- "
        "a real consumer exists and Task 7.9 must be re-run."
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


def test_the_named_bayesian_strategy_is_still_absent():
    """The external claim concerned BayesianDualScaleSizing. It is not
    IMPLEMENTED in this repository, which is part of the evidence that
    the claim does not describe this codebase. If it is ever added, the
    'macro' ambiguity noted in this module's docstring should be
    re-examined at that point.

    Checks for a class DEFINITION specifically: the name does appear in
    size_calculators.py's module docstring, which documents that this
    strategy (and two others) are deliberately NOT implemented. A
    mention that something is absent is not that thing existing -- an
    earlier version of this test conflated the two and failed.
    """
    source = (REPO_ROOT / "src" / "size_calculators.py").read_text()
    definitions = re.findall(r"^class\s+(\w+)", source, flags=re.MULTILINE)
    assert "BayesianDualScaleSizing" not in definitions, (
        "BayesianDualScaleSizing is now implemented -- re-examine whether its 'macro' "
        "posterior is a lookback-length distinction or genuinely macroeconomic."
    )
    assert "FixedPortfolioPercentage" in definitions
    assert definitions == ["SizingStrategy", "FixedPortfolioPercentage"], (
        f"The set of sizing strategies changed to {definitions} -- re-run the discovery gate, "
        "since a new strategy is exactly where a macro-field consumer would appear."
    )
