"""
The nightly risk report: its schema, its audit, and the session it is for.

docs/daily_risk_report_plan.md is the design. Every evening the owner runs a
prompt through an LLM with web search; it returns one JSON report (schema
1.1.0, and 1.2.0 with the plan's prompt changes): data quality, regime, the
volatility state, an expected 1-day move, overnight gap risk, the next day's
catalysts, and return distributions over 1, 5, 21, 63 and 252 sessions.

--------------------------------------------------------------------
ONE PARSER FOR EVERY READER

The server's preview, the trader that applies a report, the tracking
service that scores it and the backtests that replay an archive all parse
with parse_report(), so no two of them can disagree about whether a report
is whole or what it says. It is standard library only, like the rest of
engine/core.

--------------------------------------------------------------------
WHAT THE AUDIT REFUSES, AND WHAT IT ONLY SAYS

An ERROR makes the report unusable: a missing or mistyped field, a value
outside its enum, a horizon whose probabilities do not sum to one, a CDF
that does not chain, quantiles out of order, an expected shortfall above
its 5% quantile, a timestamp without a zone. Every error is listed, not the
first: a report is fixed by whoever pasted it, in one go.

A WARNING is shown beside the report and changes nothing here: bins that
hold little of the probability (the schema's SPY template on TQQQ leaves
72% of the 1-day mass in the open-ended tails, so the bins' moments cannot
be checked against mean_pct and std_pct), inputs the report says it lacked,
a probability above zero that the bins cannot confirm. Whether a report is
followed is the mapping's decision (research/risk_overlay/mapping.py), not
the parser's.

--------------------------------------------------------------------
THE SESSION A REPORT IS FOR

Exactly one: the session after `as_of`'s evening. A report stamped after a
session's regular close (or on a day without a session) is for the next
session; one stamped before a session's 09:30 open is for that session; one
stamped during regular hours is not an end-of-day report and is refused. The
regular session decides, whatever windows a deployment trades: the report
is about the day's market, and a deployment that starts at 07:00 learns
from the trader whether its report arrived before its first window.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from itertools import pairwise
from typing import Any

from engine.core.trading_calendar import EASTERN, SESSION_CLOSE, is_session, next_session

SCHEMA_MAJOR = 1
KNOWN_SCHEMAS = ("1.1.0", "1.2.0")

# The horizons the schema carries, with the sessions each spans.
HORIZONS: dict[str, int] = {
    "tomorrow": 1,
    "next_week": 5,
    "next_month": 21,
    "next_quarter": 63,
    "next_year": 252,
}
QUANTILES = ("p01", "p05", "p25", "p75", "p95", "p99")

REGIMES = (
    "low_vol_uptrend",
    "mean_reverting_range",
    "breakout_expansion",
    "event_driven",
    "high_vol_downtrend",
)
VOLATILITY_STATES = ("compressed", "normal", "elevated", "extreme")
SKEW_BIASES = ("bullish_tail", "neutral", "bearish_tail")
GAP_RISKS = ("low", "moderate", "high")
IMPACTS = ("low", "medium", "high")
DEGRADED = "degraded"

REGULAR_OPEN = time(9, 30)

# A report travels as a command's arguments (engine/trading/control_inbox.py
# allows 16 KB of them); tonight's is 5.8 KB compact. Room is left for the
# envelope the command adds.
MAX_REPORT_BYTES = 12 * 1024

# Tolerances for the arithmetic the audit checks. A report's figures are
# rounded to four places, and an LLM's to fewer: these accept rounding and
# refuse arithmetic that is simply wrong.
_SUM_TOLERANCE = 0.005
_CDF_TOLERANCE = 0.003
_PROB_POSITIVE_TOLERANCE = 0.01
_WEIGHT_TOLERANCE = 0.011
# Below this share of probability inside the bins, their moments say little.
LOW_BIN_COVERAGE = 0.90


class ReportError(ValueError):
    """A report that cannot be used; `findings` lists every reason."""

    def __init__(self, findings: list[Finding]) -> None:
        self.findings = findings
        errors = [f for f in findings if f.level == "error"]
        super().__init__("; ".join(f"{f.where}: {f.message}" for f in errors[:8]))


@dataclass(frozen=True)
class Finding:
    """One thing the audit found: an `error` refuses the report, a
    `warning` is shown beside it. `where` names the field."""

    level: str
    where: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"level": self.level, "where": self.where, "message": self.message}


@dataclass(frozen=True)
class Catalyst:
    """One scheduled event. `at` is its UTC time when the report gave one
    (`time_utc` HH:MM on the target session's date, or a full ISO
    timestamp from schema 1.2.0); None when it gave only a day."""

    event: str
    impact: str
    at: datetime | None = None
    source: str = "report"

    def to_dict(self) -> dict[str, Any]:
        return {
            "event": self.event,
            "impact": self.impact,
            "at": self.at.isoformat() if self.at is not None else None,
            "source": self.source,
        }


@dataclass(frozen=True)
class HorizonSummary:
    """One horizon's distribution, as the mappings and the scorecard read
    it. `bin_coverage` is the share of probability inside the bins."""

    name: str
    trading_days: int
    mean_pct: float
    median_pct: float
    std_pct: float
    prob_positive: float
    es5_pct: float
    quantiles: Mapping[str, float]
    bin_coverage: float


@dataclass(frozen=True)
class RiskReport:
    """A report that passed the audit, with the fields read typed."""

    schema_version: str
    symbol: str
    as_of: datetime
    base_price: float
    confidence: float
    coverage: str
    missing_inputs: tuple[str, ...]
    regime: str
    volatility_state: str
    expected_move_pct: float
    skew_bias: str
    gap_risk: str
    kelly_cap: float | None
    cash_defensive: float | None
    iv_rv_spread_pct: float | None
    catalysts: tuple[Catalyst, ...]
    horizons: Mapping[str, HorizonSummary]
    sha256: str
    raw: Mapping[str, Any] = field(repr=False, compare=False)
    # Schema 1.2.0 (docs/daily_risk_report_plan.md "Prompt changes").
    declared_session: date | None = None
    prompt_version: str | None = None
    model: str | None = None

    @property
    def session(self) -> date:
        """The session this report is for (target_session)."""
        return target_session(self.as_of)

    def horizon(self, name: str) -> HorizonSummary:
        return self.horizons[name]


@dataclass
class Audit:
    """What parse_report found: the report (None when an error refuses it)
    and every finding."""

    report: RiskReport | None
    findings: list[Finding]

    @property
    def ok(self) -> bool:
        return self.report is not None

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.level == "error"]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.level == "warning"]

    def require(self) -> RiskReport:
        """The report, or ReportError listing every error."""
        if self.report is None:
            raise ReportError(self.findings)
        return self.report

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": [f.to_dict() for f in self.errors],
            "warnings": [f.to_dict() for f in self.warnings],
        }


# --------------------------------------------------------------------
# Identity
# --------------------------------------------------------------------


def canonical_json(data: Any) -> str:
    """The one serialisation hashed and sized: sorted keys, no spaces."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def report_sha256(data: Mapping[str, Any]) -> str:
    """SHA-256 of the report's canonical JSON: the same report pasted twice,
    or with its keys in another order, has the same hash."""
    return hashlib.sha256(canonical_json(data).encode("utf-8")).hexdigest()


# --------------------------------------------------------------------
# Sessions
# --------------------------------------------------------------------


def regular_bounds(day: date) -> tuple[datetime, datetime]:
    """The regular session of `day` (09:30-16:00 Eastern) in UTC. Early
    closes are not modelled (engine/core/trading_calendar.py)."""
    opens = datetime.combine(day, REGULAR_OPEN, tzinfo=EASTERN).astimezone(UTC)
    closes = datetime.combine(day, SESSION_CLOSE, tzinfo=EASTERN).astimezone(UTC)
    return opens, closes


def day_bounds(day: date) -> tuple[datetime, datetime]:
    """What a session's report covers: from the previous session's close
    to this session's, in UTC. A catalyst at 08:30 before the open moves
    the session as surely as one at 10:00."""
    previous = day - timedelta(days=1)
    while not is_session(previous):
        previous -= timedelta(days=1)
    return regular_bounds(previous)[1], regular_bounds(day)[1]


def target_session(as_of: datetime) -> date:
    """The one session a report stamped `as_of` is for (module docstring).
    ValueError for a stamp inside a regular session: not an end-of-day
    report."""
    if as_of.tzinfo is None:
        raise ValueError("as_of has no time zone")
    local = as_of.astimezone(EASTERN)
    day = local.date()
    if is_session(day):
        if local.time() < REGULAR_OPEN:
            return day
        if local.time() < SESSION_CLOSE:
            raise ValueError(
                f"as_of {as_of.isoformat()} is inside the {day} regular session: not an "
                "end-of-day report"
            )
    return next_session(day)


# --------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------


class _Collector:
    def __init__(self) -> None:
        self.findings: list[Finding] = []

    def error(self, where: str, message: str) -> None:
        self.findings.append(Finding("error", where, message))

    def warning(self, where: str, message: str) -> None:
        self.findings.append(Finding("warning", where, message))

    @property
    def failed(self) -> bool:
        return any(f.level == "error" for f in self.findings)


def _number(found: _Collector, data: Mapping, key: str, where: str, **bounds) -> float | None:
    value = data.get(key) if isinstance(data, Mapping) else None
    path = f"{where}.{key}" if where else key
    if value is None:
        if bounds.get("optional"):
            return None
        found.error(path, "missing")
        return None
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        found.error(path, f"must be a number, got {value!r}")
        return None
    value = float(value)
    low, high = bounds.get("low"), bounds.get("high")
    if low is not None and value < low:
        found.error(path, f"must be at least {low}, got {value}")
    if high is not None and value > high:
        found.error(path, f"must be at most {high}, got {value}")
    if bounds.get("positive") and value <= 0:
        found.error(path, f"must be above 0, got {value}")
    return value


def _choice(found: _Collector, data: Mapping, key: str, where: str, choices) -> str | None:
    value = data.get(key) if isinstance(data, Mapping) else None
    path = f"{where}.{key}" if where else key
    if value is None:
        found.error(path, "missing")
        return None
    if value not in choices:
        found.error(path, f"must be one of {', '.join(choices)}, got {value!r}")
        return None
    return str(value)


def _mapping(found: _Collector, data: Mapping, key: str, where: str = "") -> Mapping | None:
    value = data.get(key) if isinstance(data, Mapping) else None
    path = f"{where}.{key}" if where else key
    if not isinstance(value, Mapping):
        found.error(path, "missing" if value is None else "must be an object")
        return None
    return value


def _timestamp(text: Any) -> datetime | None:
    if not isinstance(text, str):
        return None
    try:
        moment = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return moment.astimezone(UTC) if moment.tzinfo is not None else None


def _catalyst_time(text: Any, session: date | None) -> tuple[datetime | None, str | None]:
    """A catalyst's time: an ISO timestamp, or HH:MM UTC on `session`'s
    date. (None, None) when it has none; (None, error) when it is not one."""
    if text is None or text == "":
        return None, None
    moment = _timestamp(text)
    if moment is not None:
        return moment, None
    if isinstance(text, str) and len(text) == 5 and text[2] == ":":
        try:
            clock = time(int(text[:2]), int(text[3:]))
        except ValueError:
            return None, f"time {text!r} is not HH:MM"
        if session is None:
            return None, None
        return datetime.combine(session, clock, tzinfo=UTC), None
    return None, f"time {text!r} is neither HH:MM (UTC) nor an ISO timestamp"


def _horizon(found: _Collector, name: str, days: int, data: Any) -> HorizonSummary | None:
    where = f"horizons.{name}"
    if not isinstance(data, Mapping):
        found.error(where, "missing" if data is None else "must be an object")
        return None
    start = len(found.findings)
    trading_days = data.get("trading_days")
    if trading_days != days:
        found.error(f"{where}.trading_days", f"must be {days}, got {trading_days!r}")
    under = _number(found, data, "underflow_prob", where, low=0.0, high=1.0)
    over = _number(found, data, "overflow_prob", where, low=0.0, high=1.0)
    bins = data.get("bins")
    if not isinstance(bins, list) or not bins:
        found.error(f"{where}.bins", "must be a non-empty list")
        bins = []
    inside = 0.0
    cdf_at_zero: float | None = None
    running = under or 0.0
    previous_max = None
    for i, entry in enumerate(bins):
        here = f"{where}.bins[{i}]"
        if not isinstance(entry, Mapping):
            found.error(here, "must be an object")
            continue
        low = _number(found, entry, "min_pct", here)
        high = _number(found, entry, "max_pct", here)
        prob = _number(found, entry, "prob", here, low=0.0, high=1.0)
        cdf = _number(found, entry, "cdf", here, low=0.0, high=1.0)
        if low is not None and high is not None and low >= high:
            found.error(here, f"min_pct {low} is not below max_pct {high}")
        if previous_max is not None and low is not None and abs(low - previous_max) > 1e-9:
            found.error(here, f"starts at {low}, not where the bin before ended ({previous_max})")
        previous_max = high
        if prob is None:
            continue
        inside += prob
        running += prob
        if cdf is not None and abs(cdf - running) > _CDF_TOLERANCE:
            found.error(
                f"{here}.cdf", f"is {cdf}, but the probabilities before it sum to {running:.4f}"
            )
        if high is not None and abs(high) < 1e-12:
            cdf_at_zero = cdf if cdf is not None else running
    if under is not None and over is not None and bins:
        total = under + inside + over
        if abs(total - 1.0) > _SUM_TOLERANCE:
            found.error(where, f"probabilities sum to {total:.4f}, not 1")
    summary = _mapping(found, data, "summary", where)
    quantiles: dict[str, float] = {}
    if summary is None:
        return None
    swhere = f"{where}.summary"
    mean = _number(found, summary, "mean_pct", swhere)
    median = _number(found, summary, "median_pct", swhere)
    std = _number(found, summary, "std_pct", swhere, positive=True)
    prob_positive = _number(found, summary, "prob_positive", swhere, low=0.0, high=1.0)
    es5 = _number(found, summary, "expected_shortfall_5pct", swhere)
    q = _mapping(found, summary, "quantiles_pct", swhere)
    if q is not None:
        for key in QUANTILES:
            value = _number(found, q, key, f"{swhere}.quantiles_pct")
            if value is not None:
                quantiles[key] = value
        ordered = [quantiles[k] for k in QUANTILES if k in quantiles]
        if len(ordered) == len(QUANTILES) and any(a > b for a, b in pairwise(ordered)):
            found.error(f"{swhere}.quantiles_pct", "the quantiles are not in order")
        if es5 is not None and "p05" in quantiles and es5 > quantiles["p05"] + 1e-9:
            found.error(
                f"{swhere}.expected_shortfall_5pct",
                f"is {es5}, above the 5% quantile {quantiles['p05']}: a shortfall is the mean "
                "below it",
            )
        if (
            median is not None
            and "p25" in quantiles
            and "p75" in quantiles
            and not quantiles["p25"] <= median <= quantiles["p75"]
        ):
            found.error(f"{swhere}.median_pct", f"{median} is outside its own p25-p75")
    if prob_positive is not None and cdf_at_zero is not None:
        if abs((1.0 - cdf_at_zero) - prob_positive) > _PROB_POSITIVE_TOLERANCE:
            found.error(
                f"{swhere}.prob_positive",
                f"is {prob_positive}, but the bins put {1 - cdf_at_zero:.4f} above zero",
            )
    elif prob_positive is not None and bins:
        found.warning(f"{swhere}.prob_positive", "no bin ends at 0, so it cannot be checked")
    if bins and inside < LOW_BIN_COVERAGE and under is not None and over is not None:
        found.warning(
            f"{where}.bins",
            f"hold {inside:.0%} of the probability ({under:.0%} below, {over:.0%} above): their "
            "moments cannot be checked against mean_pct and std_pct; the quantiles and the "
            "expected shortfall are what is usable",
        )
    if len(found.findings) > start and any(f.level == "error" for f in found.findings[start:]):
        return None
    if None in (mean, median, std, prob_positive, es5) or len(quantiles) != len(QUANTILES):
        return None
    return HorizonSummary(
        name=name,
        trading_days=days,
        mean_pct=mean,
        median_pct=median,
        std_pct=std,
        prob_positive=prob_positive,
        es5_pct=es5,
        quantiles=dict(quantiles),
        bin_coverage=round(inside, 6),
    )


def parse_report(data: Mapping[str, Any] | str | bytes) -> Audit:
    """Parse and audit one report (a dict, or its JSON text). Never raises
    for a bad report: every problem is a finding."""
    found = _Collector()
    if isinstance(data, bytes | bytearray):
        data = data.decode("utf-8", errors="replace")
    if isinstance(data, str):
        if len(data.encode("utf-8")) > 4 * MAX_REPORT_BYTES:
            return Audit(None, [Finding("error", "report", "is far too large to be one report")])
        try:
            data = json.loads(data)
        except ValueError as exc:
            return Audit(None, [Finding("error", "report", f"is not JSON: {exc}")])
    if not isinstance(data, Mapping):
        return Audit(None, [Finding("error", "report", "must be a JSON object")])
    size = len(canonical_json(data).encode("utf-8"))
    if size > MAX_REPORT_BYTES:
        found.error("report", f"is {size:,} bytes; at most {MAX_REPORT_BYTES:,} are taken")

    version = data.get("schema_version")
    if not isinstance(version, str) or version.split(".")[0] != str(SCHEMA_MAJOR):
        found.error("schema_version", f"must be {SCHEMA_MAJOR}.x, got {version!r}")
    elif version not in KNOWN_SCHEMAS:
        found.warning("schema_version", f"{version} is newer than this reader knows")

    symbol = data.get("symbol")
    if not isinstance(symbol, str) or not symbol.strip() or not symbol.isascii():
        found.error("symbol", f"must name the fund, got {symbol!r}")
        symbol = None
    else:
        symbol = symbol.strip().upper()

    as_of = _timestamp(data.get("as_of"))
    session: date | None = None
    if as_of is None:
        found.error("as_of", f"must be an ISO-8601 time with a zone, got {data.get('as_of')!r}")
    else:
        try:
            session = target_session(as_of)
        except ValueError as exc:
            found.error("as_of", str(exc))
    declared = None
    if data.get("target_session") is not None:
        try:
            declared = date.fromisoformat(str(data["target_session"]))
        except ValueError:
            found.error("target_session", f"is not a date: {data['target_session']!r}")
        else:
            if session is not None and declared != session:
                found.error(
                    "target_session",
                    f"says {declared}, but a report stamped {data.get('as_of')} is for {session}",
                )

    base_price = _number(found, data, "base_price", "", positive=True)
    if data.get("return_type", "simple_pct") != "simple_pct":
        found.error("return_type", f"must be simple_pct, got {data.get('return_type')!r}")

    signals = _mapping(found, data, "execution_signals")
    confidence = coverage = regime = vol_state = skew = gap = None
    move = kelly = spread = cash_defensive = None
    missing: tuple[str, ...] = ()
    catalysts: list[Catalyst] = []
    if signals is not None:
        where = "execution_signals"
        quality = _mapping(found, signals, "data_quality", where)
        if quality is not None:
            qwhere = f"{where}.data_quality"
            confidence = _number(found, quality, "confidence_score", qwhere, low=0.0, high=1.0)
            coverage = quality.get("source_coverage")
            if not isinstance(coverage, str) or not coverage:
                found.error(f"{qwhere}.source_coverage", f"must be a word, got {coverage!r}")
                coverage = None
            raw_missing = quality.get("missing_inputs") or []
            if not isinstance(raw_missing, list):
                found.error(f"{qwhere}.missing_inputs", "must be a list")
            else:
                missing = tuple(str(item) for item in raw_missing)
                if missing:
                    found.warning(
                        f"{qwhere}.missing_inputs",
                        f"the report lacked {len(missing)} input(s): {', '.join(missing)}",
                    )
        regime = _choice(found, signals, "regime", where, REGIMES)
        vol_state = _choice(found, signals, "volatility_state", where, VOLATILITY_STATES)
        skew = _choice(found, signals, "skew_bias", where, SKEW_BIASES)
        gap = _choice(found, signals, "overnight_gap_risk", where, GAP_RISKS)
        move = _number(found, signals, "expected_1d_move_pct", where, positive=True)
        kelly = _number(
            found, signals, "kelly_fraction_cap", where, low=0.0, high=1.0, optional=True
        )
        spread = _number(found, signals, "implied_vs_realized_vol_spread_pct", where, optional=True)
        raw_catalysts = signals.get("next_day_catalysts", [])
        if not isinstance(raw_catalysts, list):
            found.error(f"{where}.next_day_catalysts", "must be a list")
            raw_catalysts = []
        for i, entry in enumerate(raw_catalysts):
            here = f"{where}.next_day_catalysts[{i}]"
            if not isinstance(entry, Mapping):
                found.error(here, "must be an object")
                continue
            event = entry.get("event")
            if not isinstance(event, str) or not event.strip():
                found.error(f"{here}.event", "must name the event")
                continue
            impact = _choice(found, entry, "impact", here, IMPACTS)
            at, problem = _catalyst_time(entry.get("time_utc", entry.get("time")), session)
            if problem:
                found.error(f"{here}.time_utc", problem)
            if impact is not None and not problem:
                catalysts.append(Catalyst(event=event.strip(), impact=impact, at=at))
        weights = signals.get("suggested_strategy_weights")
        if weights is not None:
            if not isinstance(weights, Mapping) or not weights:
                found.error(f"{where}.suggested_strategy_weights", "must be an object of weights")
            else:
                values = []
                for key in weights:
                    number = _number(
                        found, weights, key, f"{where}.suggested_strategy_weights", low=0, high=1
                    )
                    if number is not None:
                        values.append(number)
                if len(values) == len(weights) and abs(sum(values) - 1.0) > _WEIGHT_TOLERANCE:
                    found.error(
                        f"{where}.suggested_strategy_weights",
                        f"sum to {sum(values):.3f}, not 1",
                    )
                cash = weights.get("cash_defensive")
                if isinstance(cash, int | float) and not isinstance(cash, bool):
                    cash_defensive = float(cash)

    raw_horizons = _mapping(found, data, "horizons")
    horizons: dict[str, HorizonSummary] = {}
    if raw_horizons is not None:
        for name, days in HORIZONS.items():
            summary = _horizon(found, name, days, raw_horizons.get(name))
            if summary is not None:
                horizons[name] = summary

    if found.failed:
        return Audit(None, found.findings)
    report = RiskReport(
        schema_version=str(version),
        symbol=str(symbol),
        as_of=as_of,
        base_price=float(base_price),
        confidence=float(confidence),
        coverage=str(coverage),
        missing_inputs=missing,
        regime=str(regime),
        volatility_state=str(vol_state),
        expected_move_pct=float(move),
        skew_bias=str(skew),
        gap_risk=str(gap),
        kelly_cap=kelly,
        cash_defensive=cash_defensive,
        iv_rv_spread_pct=spread,
        catalysts=tuple(catalysts),
        horizons=horizons,
        sha256=report_sha256(data),
        raw=dict(data),
        declared_session=declared,
        prompt_version=str(data["prompt_version"]) if data.get("prompt_version") else None,
        model=str(data["model"]) if data.get("model") else None,
    )
    return Audit(report, found.findings)


__all__ = [
    "DEGRADED",
    "GAP_RISKS",
    "HORIZONS",
    "IMPACTS",
    "KNOWN_SCHEMAS",
    "LOW_BIN_COVERAGE",
    "MAX_REPORT_BYTES",
    "QUANTILES",
    "REGIMES",
    "SKEW_BIASES",
    "VOLATILITY_STATES",
    "Audit",
    "Catalyst",
    "Finding",
    "HorizonSummary",
    "ReportError",
    "RiskReport",
    "canonical_json",
    "day_bounds",
    "parse_report",
    "regular_bounds",
    "report_sha256",
    "target_session",
]
