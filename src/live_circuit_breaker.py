"""Live-only new-buy circuit breaker with durable halt state."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import logging
import sqlite3

logger = logging.getLogger("LiveCircuitBreaker")


class CircuitState(str, Enum):
    ACTIVE = "ACTIVE"
    HALTED_NEW_BUYS = "HALTED_NEW_BUYS"
    MANUAL_RESET_REQUIRED = "MANUAL_RESET_REQUIRED"


@dataclass
class LiveCircuitBreaker:
    threshold: float | None = None
    state: CircuitState = CircuitState.ACTIVE

    def evaluate(self, drawdown: float) -> bool:
        if self.threshold is not None and float(drawdown) >= self.threshold and self.state is CircuitState.ACTIVE:
            self.state = CircuitState.MANUAL_RESET_REQUIRED
            logger.error("LIVE CIRCUIT BREAKER: HALTED_NEW_BUYS drawdown=%.6f threshold=%.6f", float(drawdown), self.threshold)
        return self.halted

    @property
    def halted(self) -> bool:
        return self.state in {CircuitState.HALTED_NEW_BUYS, CircuitState.MANUAL_RESET_REQUIRED}

    def reset(self) -> None:
        self.state = CircuitState.ACTIVE
        logger.warning("LIVE CIRCUIT BREAKER manually reset; new buys enabled")


class SQLiteCircuitBreakerStore:
    """Persist the circuit-breaker state in the same SQLite state database."""

    def __init__(self, path: str):
        self._conn = sqlite3.connect(path)
        self._conn.execute("CREATE TABLE IF NOT EXISTS live_circuit_breaker (id INTEGER PRIMARY KEY CHECK(id=1), state TEXT NOT NULL)")
        self._conn.commit()

    def load(self) -> CircuitState:
        row = self._conn.execute("SELECT state FROM live_circuit_breaker WHERE id=1").fetchone()
        return CircuitState(row[0]) if row else CircuitState.ACTIVE

    def save(self, state: CircuitState) -> None:
        with self._conn:
            self._conn.execute("INSERT INTO live_circuit_breaker(id,state) VALUES(1,?) ON CONFLICT(id) DO UPDATE SET state=excluded.state", (state.value,))

    def close(self) -> None:
        self._conn.close()
