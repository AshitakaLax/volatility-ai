"""
Task 7.13 acceptance tests.

Acceptance criteria:
1. A timeout after order submission does not automatically submit a
   second order before reconciliation.
2. Retryable read failures recover within the configured retry budget.
3. Non-retryable errors are surfaced immediately with no blind retry.
4. An ambiguous submission outcome resolves through reconciliation,
   never through a bare retry.
5. Backoff is exactly 1s, 2s, 4s, 8s, 16s before jitter, with no more
   than 5 total attempts.
6. Jitter remains within +/-20% of each calculated delay.
7. A broker-provided rate-limit retry time is honored when present and
   never causes an unbounded reconciliation stall.

Classification is tested against alpaca-py's REAL exception types, not
hand-rolled stand-ins.
"""

import random
import sys
import types

import pytest
import requests.exceptions as rex
from alpaca.common.exceptions import APIError, RetryException

from src.exceptions import ExecutionError
from src.retry_policy import (
    AmbiguousSubmissionError,
    ErrorClass,
    RetryConfig,
    apply_jitter,
    canonical_delays,
    classify_error,
    rate_limit_wait,
    retry_call,
)


class _Response:
    def __init__(self, status_code=None, headers=None):
        self.status_code = status_code
        self.headers = headers or {}


def _api_error(status_code=None, headers=None, code=40010001, message="err"):
    """A real alpaca APIError. status_code comes from the http_error's
    response, exactly as the SDK derives it."""
    err = APIError(f'{{"code":{code},"message":"{message}"}}')
    err._http_error = type(
        "H", (), {"response": _Response(status_code, headers), "request": None}
    )()
    return err


def test_canonical_backoff_sequence_is_exactly_1_2_4_8_16():
    assert canonical_delays() == [1.0, 2.0, 4.0, 8.0, 16.0]


def test_backoff_is_capped_at_thirty_seconds():
    assert canonical_delays(count=8) == [1.0, 2.0, 4.0, 8.0, 16.0, 30.0, 30.0, 30.0]


def test_no_more_than_five_total_attempts_by_default():
    assert RetryConfig().max_attempts == 5
    attempts = {"count": 0}

    def always_fails():
        attempts["count"] += 1
        raise rex.ConnectionError("down")

    with pytest.raises(ExecutionError):
        retry_call(always_fails, sleep=lambda s: None)
    assert attempts["count"] == 5, "5 total attempts including the initial request"


def test_retry_call_uses_at_most_max_attempts_minus_one_delays():
    slept = []

    def always_fails():
        raise rex.ConnectionError("down")

    with pytest.raises(ExecutionError):
        retry_call(always_fails, RetryConfig(jitter=0.0), sleep=slept.append)
    assert len(slept) == 4, "5 attempts means 4 backoff waits"
    assert slept == [1.0, 2.0, 4.0, 8.0]


def test_canonical_defaults_match_the_contract():
    config = RetryConfig()
    assert (
        config.base_delay,
        config.multiplier,
        config.max_attempts,
        config.cap,
        config.jitter,
    ) == (1.0, 2.0, 5, 30.0, 0.20)


def test_jitter_stays_within_twenty_percent_of_the_delay():
    rng = random.Random(42)
    config = RetryConfig()
    for base in canonical_delays():
        for _ in range(200):
            jittered = apply_jitter(base, config, rng)
            assert 0.8 * base - 1e-9 <= jittered <= 1.2 * base + 1e-9


def test_jitter_never_produces_a_negative_delay_or_exceeds_the_cap():
    rng = random.Random(7)
    config = RetryConfig()
    for _ in range(200):
        assert 0.0 <= apply_jitter(30.0, config, rng) <= config.cap


def test_zero_jitter_is_exact():
    assert apply_jitter(4.0, RetryConfig(jitter=0.0)) == 4.0


@pytest.mark.parametrize(
    "error",
    [
        rex.ConnectionError("down"),
        rex.Timeout("slow"),
        rex.ReadTimeout("slow"),
        rex.ConnectTimeout("slow"),
    ],
)
def test_transport_failures_are_retryable_when_not_after_submission(error):
    assert classify_error(error, after_submission=False) is ErrorClass.RETRYABLE


def test_alpaca_retry_exception_is_retryable():
    assert classify_error(RetryException(), after_submission=False) is ErrorClass.RETRYABLE


@pytest.mark.parametrize("status", [500, 502, 503, 504])
def test_5xx_responses_are_retryable(status):
    assert classify_error(_api_error(status), after_submission=False) is ErrorClass.RETRYABLE


def test_429_rate_limit_is_retryable():
    assert classify_error(_api_error(429), after_submission=False) is ErrorClass.RETRYABLE


@pytest.mark.parametrize("status", [400, 401, 403, 404, 422])
def test_4xx_errors_are_non_retryable(status):
    assert classify_error(_api_error(status), after_submission=False) is ErrorClass.NON_RETRYABLE


def test_4xx_after_submission_is_still_non_retryable_not_ambiguous():
    # The broker ANSWERED -- that's a definite rejection, not an
    # unknown outcome.
    assert classify_error(_api_error(403), after_submission=True) is ErrorClass.NON_RETRYABLE


def test_api_error_without_http_context_is_handled_explicitly():
    # Verified real behavior: APIError.status_code is None when no
    # http_error was attached.
    bare = APIError('{"code":40010001,"message":"no http context"}')
    assert bare.status_code is None
    assert classify_error(bare, after_submission=False) is ErrorClass.NON_RETRYABLE
    assert classify_error(bare, after_submission=True) is ErrorClass.AMBIGUOUS


@pytest.mark.parametrize(
    "error", [rex.Timeout("timed out"), rex.ConnectionError("reset"), rex.ReadTimeout("slow")]
)
def test_transport_failure_after_submission_is_ambiguous(error):
    assert classify_error(error, after_submission=True) is ErrorClass.AMBIGUOUS


def test_timeout_after_submission_never_submits_a_second_order():
    """Acceptance criterion 1, the most important one in this task."""
    submissions = {"count": 0}

    def submit():
        submissions["count"] += 1
        raise rex.Timeout("timed out after sending")

    with pytest.raises(AmbiguousSubmissionError):
        retry_call(submit, after_submission=True, sleep=lambda s: None)

    assert submissions["count"] == 1, "An ambiguous submission must NEVER be retried"


def test_ambiguous_error_is_a_distinct_type_from_ordinary_failure():
    # So a caller cannot accidentally swallow it with the same except
    # branch it uses for retry exhaustion.
    assert issubclass(AmbiguousSubmissionError, ExecutionError)
    assert AmbiguousSubmissionError is not ExecutionError


def test_ambiguous_error_message_directs_to_reconciliation():
    def submit():
        raise rex.Timeout("timed out")

    with pytest.raises(AmbiguousSubmissionError) as exc_info:
        retry_call(submit, after_submission=True, sleep=lambda s: None)
    message = str(exc_info.value)
    assert "reconciliation" in message.lower()
    assert "client order id" in message.lower()
    assert "not retrying" in message.lower()


def test_ambiguous_outcome_surfaces_to_the_failure_hook():
    alerts = []

    def submit():
        raise rex.ConnectionError("reset mid-submit")

    with pytest.raises(AmbiguousSubmissionError):
        retry_call(
            submit, after_submission=True, sleep=lambda s: None, on_repeated_failure=alerts.append
        )
    assert len(alerts) == 1


def test_retryable_read_recovers_within_the_budget():
    calls = {"count": 0}

    def flaky_read():
        calls["count"] += 1
        if calls["count"] < 3:
            raise rex.ConnectionError("transient")
        return "data"

    assert retry_call(flaky_read, sleep=lambda s: None) == "data"
    assert calls["count"] == 3


def test_success_on_the_first_attempt_never_sleeps():
    slept = []
    assert retry_call(lambda: "ok", sleep=slept.append) == "ok"
    assert slept == []


def test_recovery_on_the_final_permitted_attempt_still_succeeds():
    calls = {"count": 0}

    def flaky():
        calls["count"] += 1
        if calls["count"] < 5:
            raise rex.ConnectionError("transient")
        return "ok"

    assert retry_call(flaky, sleep=lambda s: None) == "ok"
    assert calls["count"] == 5


def test_non_retryable_error_is_raised_immediately_with_no_retry():
    calls = {"count": 0}

    def unauthorized():
        calls["count"] += 1
        raise _api_error(401)

    with pytest.raises(APIError):
        retry_call(unauthorized, sleep=lambda s: None)
    assert calls["count"] == 1, "A 4xx must not be blindly retried"


def test_non_retryable_error_does_not_sleep():
    slept = []

    def unauthorized():
        raise _api_error(403)

    with pytest.raises(APIError):
        retry_call(unauthorized, sleep=slept.append)
    assert slept == []


def test_broker_retry_after_is_honored():
    error = _api_error(429, headers={"Retry-After": "5"})
    assert rate_limit_wait(error) == 5.0


def test_retry_after_is_clamped_so_reconciliation_never_stalls():
    error = _api_error(429, headers={"Retry-After": "86400"})  # one day
    config = RetryConfig(max_rate_limit_wait=60.0)
    assert rate_limit_wait(error, config) == 60.0


def test_absent_or_malformed_retry_after_falls_back_to_backoff():
    assert rate_limit_wait(_api_error(429)) is None
    assert rate_limit_wait(_api_error(429, headers={"Retry-After": "soon"})) is None
    assert rate_limit_wait(_api_error(429, headers={"Retry-After": "-5"})) is None


def test_retry_call_uses_the_brokers_retry_after_over_its_own_backoff():
    slept = []
    calls = {"count": 0}

    def rate_limited():
        calls["count"] += 1
        if calls["count"] < 2:
            raise _api_error(429, headers={"Retry-After": "7"})
        return "ok"

    assert retry_call(rate_limited, sleep=slept.append) == "ok"
    assert slept == [7.0], "Broker-supplied wait must take precedence over computed backoff"


def test_rate_limit_header_is_case_insensitive():
    assert rate_limit_wait(_api_error(429, headers={"retry-after": "3"})) == 3.0


def test_exhausted_budget_surfaces_to_the_failure_hook():
    alerts = []

    def always_fails():
        raise rex.ConnectionError("down")

    with pytest.raises(ExecutionError):
        retry_call(always_fails, sleep=lambda s: None, on_repeated_failure=alerts.append)
    assert len(alerts) == 1
    assert "5 attempts" in alerts[0]


def test_invalid_retry_config_is_rejected():
    for kwargs in ({"max_attempts": 0}, {"base_delay": 0}, {"multiplier": 0.5}, {"jitter": 1.0}):
        with pytest.raises(ValueError):
            RetryConfig(**kwargs)


# --- optional broker dependencies (Fidelity plan, item G) -------------
#
# Both broker stacks are OPTIONAL and pull in different trees: alpaca-py
# (with requests) from requirements.txt, playwright from
# requirements-fidelity.txt, which the Docker image never installs.
# classify_error used to import alpaca unconditionally, so a
# Fidelity-only deployment needed alpaca-py installed purely to classify
# a Playwright error.


def _hide_packages(monkeypatch, *prefixes):
    """Make the named top-level packages un-importable, as they would be
    in a deployment that never installed them."""
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if any(name == p or name.startswith(p + ".") for p in prefixes):
            raise ImportError(f"No module named {name!r}")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    for name in list(sys.modules):
        if any(name == p or name.startswith(p + ".") for p in prefixes):
            monkeypatch.delitem(sys.modules, name, raising=False)


def test_classify_works_without_alpaca_installed(monkeypatch):
    """A Fidelity-only deployment must not need alpaca-py."""
    _hide_packages(monkeypatch, "alpaca")
    assert classify_error(TimeoutError("t")) is ErrorClass.RETRYABLE
    assert classify_error(TimeoutError("t"), after_submission=True) is ErrorClass.AMBIGUOUS


def test_classify_works_without_requests_installed(monkeypatch):
    _hide_packages(monkeypatch, "requests")
    assert classify_error(ConnectionError("c")) is ErrorClass.RETRYABLE


def test_classify_works_with_no_broker_packages_at_all(monkeypatch):
    """The degenerate case: builtin transport errors must still classify
    on their own, and an unknown error must not raise ImportError from
    inside error handling."""
    _hide_packages(monkeypatch, "alpaca", "requests", "playwright")
    assert classify_error(ConnectionError("c")) is ErrorClass.RETRYABLE
    assert classify_error(ValueError("?")) is ErrorClass.NON_RETRYABLE
    assert classify_error(ValueError("?"), after_submission=True) is ErrorClass.AMBIGUOUS


def test_a_playwright_timeout_is_retryable_before_submission(monkeypatch):
    """Playwright's TimeoutError inherits from its own Error(Exception),
    NOT from the builtin TimeoutError and not from OSError -- verified
    against playwright/_impl/_errors.py. Without an explicit entry it
    fell through to NON_RETRYABLE, quietly dropping a legitimate retry
    on a transient browser timeout."""
    fake = types.ModuleType("playwright")
    sync_api = types.ModuleType("playwright.sync_api")

    class PlaywrightError(Exception):
        pass

    class PlaywrightTimeoutError(PlaywrightError):
        pass

    sync_api.TimeoutError = PlaywrightTimeoutError
    fake.sync_api = sync_api
    monkeypatch.setitem(sys.modules, "playwright", fake)
    monkeypatch.setitem(sys.modules, "playwright.sync_api", sync_api)

    assert not issubclass(PlaywrightTimeoutError, TimeoutError)
    assert not issubclass(PlaywrightTimeoutError, OSError)
    assert classify_error(PlaywrightTimeoutError("t")) is ErrorClass.RETRYABLE


def test_a_playwright_timeout_after_submission_is_ambiguous(monkeypatch):
    """The safety property. This already held via the catch-all at the
    end of classify_error even before Playwright was recognised -- pinned
    here so it stays true for the stated reason rather than by luck."""
    fake = types.ModuleType("playwright")
    sync_api = types.ModuleType("playwright.sync_api")

    class PlaywrightTimeoutError(Exception):
        pass

    sync_api.TimeoutError = PlaywrightTimeoutError
    fake.sync_api = sync_api
    monkeypatch.setitem(sys.modules, "playwright", fake)
    monkeypatch.setitem(sys.modules, "playwright.sync_api", sync_api)

    assert (
        classify_error(PlaywrightTimeoutError("t"), after_submission=True) is ErrorClass.AMBIGUOUS
    )
