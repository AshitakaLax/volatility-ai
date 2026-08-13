"""Repository-local broker contract and retry primitives for live execution.

This module deliberately isolates the broker-facing surface.  A concrete Alpaca
adapter can implement ``AlpacaSubmitter`` without coupling the rest of the
application to a particular SDK version.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol
import time


class AlpacaBrokerError(Exception):
    """Base class for broker failures."""


class AlpacaRateLimitError(AlpacaBrokerError):
    """Broker throttled the request."""


class AlpacaTransientError(AlpacaBrokerError):
    """Retryable transport/service failure."""


class AlpacaSubmissionAmbiguousError(AlpacaBrokerError):
    """Submission may have reached the broker; reconcile before retrying."""


class AlpacaPermanentError(AlpacaBrokerError):
    """A definitive rejection that must not be retried."""


@dataclass(frozen=True)
class BrokerOrder:
    client_order_id: str
    broker_order_id: str
    status: str
    requested_qty: float
    filled_qty: float = 0.0
    remaining_qty: float | None = None
    filled_avg_price: float | None = None


class AlpacaSubmitter(Protocol):
    def submit_order(self, *, symbol: str, side: str, qty: float, client_order_id: str) -> BrokerOrder:
        ...

    def get_order_by_client_order_id(self, client_order_id: str) -> BrokerOrder | None:
        ...


class RetryingAlpacaBroker:
    """Apply bounded retries while never blindly retrying ambiguous submits."""

    def __init__(self, broker: AlpacaSubmitter, *, max_retries: int = 3, base_delay_seconds: float = 1.0, max_delay_seconds: float = 8.0, sleep=time.sleep):
        if max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if base_delay_seconds < 0 or max_delay_seconds < 0:
            raise ValueError("backoff values must be non-negative")
        self.broker = broker
        self.max_retries = int(max_retries)
        self.base_delay_seconds = float(base_delay_seconds)
        self.max_delay_seconds = float(max_delay_seconds)
        self._sleep = sleep

    def submit_order(self, *, symbol: str, side: str, qty: float, client_order_id: str) -> BrokerOrder:
        attempt = 0
        while True:
            try:
                return self.broker.submit_order(symbol=symbol, side=side, qty=qty, client_order_id=client_order_id)
            except AlpacaSubmissionAmbiguousError:
                # Never blindly resubmit: the original request may have succeeded.
                existing = self.broker.get_order_by_client_order_id(client_order_id)
                if existing is not None:
                    return existing
                raise
            except (AlpacaRateLimitError, AlpacaTransientError):
                if attempt >= self.max_retries:
                    raise
                self._sleep(min(self.base_delay_seconds * (2 ** attempt), self.max_delay_seconds))
                attempt += 1
            except AlpacaPermanentError:
                raise
