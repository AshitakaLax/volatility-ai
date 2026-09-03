"""
Broker rate limits, retry, and transient-failure handling. Task 7.13.

Retrying a non-idempotent order submission without knowing whether the
broker received it creates duplicate exposure. This module decides
WHEN to retry, when to stop, and when to hand off to reconciliation.
It does not perform reconciliation -- that is Task 7.11's, per this
task's Non-goals.

Classification CONFIRMED against the installed alpaca-py, not assumed
(the contract requires exactly that):
  - alpaca.common.exceptions.APIError, with .status_code / .code /
    .message / .response properties. Critically, .status_code returns
    None when the error carries no HTTP context -- handled explicitly
    below rather than assumed non-null.
  - alpaca.common.exceptions.RetryException -- the SDK's own retry signal.
  - The SDK is requests-backed, so requests.exceptions.ConnectionError
    and .Timeout (parent of ConnectTimeout/ReadTimeout) propagate.

Canonical retry parameters (contract): base 1s, multiplier 2x, max 5
total attempts INCLUDING the initial request, cap 30s, +/-20% jitter.

--------------------------------------------------------------------
NOTE ON THE ATTEMPT/DELAY COUNT -- reconciled, and flagged:

The contract says "max 5 total attempts including the initial
request", which implies 4 retries and therefore 4 delays (1, 2, 4, 8).
The acceptance criterion, however, asks backoff tests to verify the
sequence "1s, 2s, 4s, 8s, and 16s" -- five delays.

Reconciled by treating these as two different things, which is the
only reading under which both are simultaneously true:
  - canonical_delays() generates the SEQUENCE the formula defines,
    [1, 2, 4, 8, 16], which the acceptance criterion tests directly.
  - retry_call() consumes at most max_attempts-1 of them (4 delays for
    the default 5 attempts), honoring the attempt cap.
Both are asserted by tests. Raised rather than silently picking one.
--------------------------------------------------------------------
"""

from __future__ import annotations

import logging
import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from src.exceptions import ExecutionError

logger = logging.getLogger("Optimizer")


class ErrorClass(StrEnum):
    """Step 1's three categories."""

    RETRYABLE = "RETRYABLE"
    NON_RETRYABLE = "NON_RETRYABLE"
    AMBIGUOUS = "AMBIGUOUS"


@dataclass(frozen=True)
class RetryConfig:
    """Canonical retry configuration. Defaults are the contract's
    mandated values; they are configurable only through this object."""

    base_delay: float = 1.0
    multiplier: float = 2.0
    max_attempts: int = 5  # INCLUDING the initial request
    cap: float = 30.0
    jitter: float = 0.20  # +/- fraction
    # Bound on honoring a broker-supplied Retry-After, so a hostile or
    # mistaken header can never stall reconciliation indefinitely
    # (step 4).
    max_rate_limit_wait: float = 60.0

    def __post_init__(self):
        """Reject a configuration that could not retry sensibly.

        A multiplier below 1 would shrink each successive delay, and a
        jitter of 1.0 or more could produce a zero or negative wait --
        both defeat the purpose of backoff.
        """
        if self.max_attempts < 1:
            raise ValueError(f"max_attempts must be >= 1, got {self.max_attempts}")
        if self.base_delay <= 0 or self.multiplier < 1:
            raise ValueError("base_delay must be positive and multiplier >= 1")
        if not 0 <= self.jitter < 1:
            raise ValueError(f"jitter must be in [0, 1), got {self.jitter}")


def canonical_delays(config: RetryConfig = None, count: int = 5) -> list:
    """The pre-jitter backoff sequence the formula defines: base *
    multiplier**n, capped. With defaults that is [1, 2, 4, 8, 16]."""
    config = config or RetryConfig()
    return [min(config.base_delay * (config.multiplier**n), config.cap) for n in range(count)]


def apply_jitter(
    delay: float, config: RetryConfig = None, rng: random.Random | None = None
) -> float:
    """+/- jitter fraction of the delay, never negative and never above
    the cap."""
    config = config or RetryConfig()
    rng = rng or random
    factor = 1.0 + rng.uniform(-config.jitter, config.jitter)
    return max(0.0, min(delay * factor, config.cap))


def _status_code_of(error) -> int | None:
    """Best-effort HTTP status. Returns None when the error carries no
    HTTP context -- a real case for alpaca's APIError, verified."""
    status = getattr(error, "status_code", None)
    if status is not None:
        return int(status)
    response = getattr(error, "response", None)
    if response is not None and getattr(response, "status_code", None) is not None:
        return int(response.status_code)
    return None


class _NeverMatches(Exception):
    """Stand-in for an exception type from a package that is not installed.

    isinstance(x, _NeverMatches) is False for every real error, so an
    absent optional dependency degrades to "this classifier has no
    opinion about that library's errors" rather than to an ImportError
    raised from inside error handling -- which would replace a
    classifiable broker failure with an unclassifiable one, at exactly
    the moment classification matters most.
    """


def _broker_error_types():
    """Collect the exception types to classify against, skipping any
    whose package is not installed.

    Both broker stacks are OPTIONAL dependencies pulling in different
    trees: alpaca-py (with requests) from requirements.txt, playwright
    from requirements-fidelity.txt, which the Docker image does not
    install at all. classify_error previously imported alpaca
    unconditionally, so a Fidelity-only deployment would have needed
    alpaca-py installed purely to classify a Playwright error.

    Not cached: this runs only on an error path, where an import lookup
    against sys.modules is free relative to the failure being handled,
    and caching would freeze the answer if a dependency were installed
    later in a long-lived process.
    """
    transport: list[type[BaseException]] = [TimeoutError, ConnectionError]
    api_error: type[BaseException] = _NeverMatches
    retry_exception: type[BaseException] = _NeverMatches

    try:
        import requests.exceptions as rex

        transport.extend((rex.ConnectionError, rex.Timeout))
    except ImportError:
        pass

    try:
        from alpaca.common.exceptions import APIError, RetryException

        api_error, retry_exception = APIError, RetryException
    except ImportError:
        pass

    try:
        # Playwright's TimeoutError inherits from its own Error(Exception)
        # -- NOT from the builtin TimeoutError, and not from OSError.
        # Verified against playwright/_impl/_errors.py rather than
        # assumed: `class Error(Exception)`, `class TimeoutError(Error)`.
        # So the builtin TimeoutError above does not cover it, and
        # without this a browser timeout would be classified
        # NON_RETRYABLE before submission instead of RETRYABLE, quietly
        # dropping a legitimate retry.
        #
        # After submission it would have landed on AMBIGUOUS anyway via
        # the catch-all at the end of classify_error, so the safety
        # property was never at risk -- this is a lost retry, not a lost
        # order.
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

        transport.append(PlaywrightTimeoutError)
    except ImportError:
        pass

    return tuple(transport), api_error, retry_exception


def classify_error(error: BaseException, *, after_submission: bool = False) -> ErrorClass:
    """Classify a broker error.

    after_submission is the single most important argument here. ANY
    timeout or connection failure that happens after an order
    submission was sent is AMBIGUOUS -- it is unknown whether the
    broker received it -- and must never be retried blindly. The
    contract is explicit that these route through Task 7.10's UNKNOWN
    state and Task 7.11's reconciliation-by-client-order-ID instead.
    """
    transport_types, APIError, RetryException = _broker_error_types()

    is_transport_failure = isinstance(error, transport_types)

    if after_submission and is_transport_failure:
        return ErrorClass.AMBIGUOUS

    if isinstance(error, RetryException):
        return ErrorClass.RETRYABLE

    if is_transport_failure:
        return ErrorClass.RETRYABLE

    if isinstance(error, APIError):
        status = _status_code_of(error)
        if status is None:
            # No HTTP context to classify by. After a submission this is
            # ambiguous; otherwise treat as non-retryable rather than
            # retrying something we cannot reason about.
            return ErrorClass.AMBIGUOUS if after_submission else ErrorClass.NON_RETRYABLE
        if status == 429:
            return ErrorClass.RETRYABLE  # rate limited
        if 500 <= status < 600:
            return ErrorClass.RETRYABLE
        if 400 <= status < 500:
            # 4xx auth/authorization/validation -- surface immediately.
            # A 4xx AFTER submission still means the broker answered,
            # so it is a definite rejection, not ambiguous.
            return ErrorClass.NON_RETRYABLE
        return ErrorClass.NON_RETRYABLE

    return ErrorClass.AMBIGUOUS if after_submission else ErrorClass.NON_RETRYABLE


def rate_limit_wait(error, config: RetryConfig = None) -> float | None:
    """A broker-supplied Retry-After, in seconds, bounded by
    max_rate_limit_wait.

    Step 4: honored when present, but never allowed to stall
    reconciliation indefinitely -- a header asking for an hour is
    clamped, not obeyed.
    """
    config = config or RetryConfig()
    response = getattr(error, "response", None)
    headers = getattr(response, "headers", None) or {}
    raw = headers.get("Retry-After") or headers.get("retry-after")
    if raw is None:
        return None
    try:
        seconds = float(raw)
    except (TypeError, ValueError):
        return None
    if seconds < 0:
        return None
    if seconds > config.max_rate_limit_wait:
        logger.warning(
            f"Broker Retry-After of {seconds}s exceeds the {config.max_rate_limit_wait}s bound; "
            "clamping so reconciliation is never stalled indefinitely."
        )
        return config.max_rate_limit_wait
    return seconds


class AmbiguousSubmissionError(ExecutionError):
    """Raised when a submission outcome is unknown.

    Deliberately its own type so a caller CANNOT accidentally handle it
    with the same `except` branch it uses for ordinary failures -- an
    ambiguous submission must go to reconciliation, never to a retry.
    """


def retry_call(
    fn: Callable,
    config: RetryConfig = None,
    *,
    after_submission: bool = False,
    sleep: Callable[[float], None] = time.sleep,
    rng: random.Random | None = None,
    on_repeated_failure: Callable[[str], None] | None = None,
):
    """Call fn with bounded exponential backoff.

    Retries only RETRYABLE errors. NON_RETRYABLE surfaces immediately
    with no blind retry. AMBIGUOUS raises AmbiguousSubmissionError
    without any retry at all, so the caller must reconcile.

    on_repeated_failure (step 5) receives a diagnostic when the retry
    budget is exhausted -- wire it to the circuit breaker's
    halt_for_reconciliation or the observability layer.
    """
    config = config or RetryConfig()
    rng = rng or random
    delays = canonical_delays(config, count=max(0, config.max_attempts - 1))

    last_error = None
    for attempt in range(config.max_attempts):
        try:
            return fn()
        except BaseException as error:
            last_error = error
            error_class = classify_error(error, after_submission=after_submission)

            if error_class is ErrorClass.AMBIGUOUS:
                detail = (
                    f"Ambiguous broker outcome after submission ({type(error).__name__}: {error}). "
                    "It is unknown whether the broker received the order. NOT retrying -- resolve "
                    "via reconciliation by client order ID (Task 7.11) before any resubmission."
                )
                logger.error(detail)
                if on_repeated_failure is not None:
                    on_repeated_failure(detail)
                raise AmbiguousSubmissionError(detail) from error

            if error_class is ErrorClass.NON_RETRYABLE:
                logger.error(f"Non-retryable broker error, surfacing immediately: {error}")
                raise

            if attempt >= config.max_attempts - 1:
                break  # budget exhausted

            delay = rate_limit_wait(error, config)
            if delay is None:
                delay = apply_jitter(delays[attempt], config, rng)
            logger.warning(
                f"Retryable broker error (attempt {attempt + 1}/{config.max_attempts}), "
                f"backing off {delay:.2f}s: {error}"
            )
            sleep(delay)

    detail = (
        f"Broker call failed after {config.max_attempts} attempts; last error "
        f"{type(last_error).__name__}: {last_error}"
    )
    logger.error(detail)
    if on_repeated_failure is not None:
        on_repeated_failure(detail)
    raise ExecutionError(detail) from last_error
