# AI-Skipped Steps

## Phase 7 — Task 7.13: Broker rate limits, retry, and transient-failure handling

### Intentionally skipped test file

Per implementation direction, the generated test file `tests/test_task_7_13_broker_retry.py` is intentionally **not** being added to the repository.

The four acceptance cases that were prepared but skipped are:

1. **Transient and rate-limit retry:** transient and rate-limit failures retry with bounded exponential backoff (`1s`, `2s`, capped by the configured maximum).
2. **Ambiguous submission reconciliation:** an ambiguous post-submission failure first performs a client-order-ID lookup and returns the already-created broker order when found; it does not blindly submit again.
3. **Ambiguous submission with no matching order:** when client-order-ID reconciliation finds no broker order, the ambiguity is surfaced rather than silently resubmitting.
4. **Permanent rejection:** a definitive broker rejection is propagated without retry.

### Implemented instead

The repository contains `src/alpaca_broker.py`, which defines the repository-local broker contract and retry behavior:

- `AlpacaBrokerError`
- `AlpacaRateLimitError`
- `AlpacaTransientError`
- `AlpacaSubmissionAmbiguousError`
- `AlpacaPermanentError`
- `BrokerOrder`
- `AlpacaSubmitter.submit_order(...)`
- `AlpacaSubmitter.get_order_by_client_order_id(...)`
- `RetryingAlpacaBroker`

The retry implementation applies bounded exponential backoff for transient/rate-limit failures, does not retry permanent failures, and performs client-order-ID reconciliation before acting on an ambiguous submission.

### Verification limitation

The four acceptance cases above have not been committed as executable tests because the requested workflow explicitly skips generation of `tests/test_task_7_13_broker_retry.py`. Repository test execution has not been claimed where the available GitHub tooling cannot execute the test suite.

### Branch constraint

All work in this continuation is restricted to `chat-gpt-impl`. No changes are to be made to `main`.
