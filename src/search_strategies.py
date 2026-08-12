"""Canonical parameter-search strategy contracts and implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
import math
from typing import Any, Iterable

from src.exceptions import ConfigurationError
from src.market_context import SimulationResult


class SearchStrategy(ABC):
    @abstractmethod
    def suggest(self) -> dict:
        """Return the next parameter combination to evaluate."""
        raise NotImplementedError

    @abstractmethod
    def report(self, params: dict, result: SimulationResult) -> None:
        """Report a completed evaluation to the search strategy."""
        raise NotImplementedError


class GridSearch(SearchStrategy):
    """Compatibility search preserving the existing Cartesian ordering."""

    def __init__(self, combinations: Iterable[dict]):
        self._combinations = list(combinations)
        self._index = 0

    def suggest(self) -> dict:
        if self._index >= len(self._combinations):
            raise StopIteration
        params = dict(self._combinations[self._index])
        self._index += 1
        return params

    def report(self, params: dict, result: SimulationResult) -> None:
        return None


class BayesianSearch(SearchStrategy):
    """Optuna-backed reproducible categorical Bayesian search."""

    def __init__(self, combinations: Iterable[dict], *, rank_by: str, direction: str = "maximize", seed: int = 0, n_trials: int | None = None) -> None:
        try:
            import optuna
        except ImportError as exc:
            raise ConfigurationError("search_strategy='bayesian' requires the Optuna dependency") from exc
        if direction not in {"maximize", "minimize"}:
            raise ConfigurationError(f"direction={direction!r}: expected 'maximize' or 'minimize'")
        if not rank_by:
            raise ConfigurationError("rank_by must be non-empty")
        self._optuna = optuna
        self._combinations = [dict(c) for c in combinations]
        if not self._combinations:
            raise ConfigurationError("BayesianSearch requires at least one parameter combination")
        self.rank_by = rank_by
        self.direction = direction
        self.seed = int(seed)
        self.n_trials = len(self._combinations) if n_trials is None else int(n_trials)
        if self.n_trials < 1:
            raise ConfigurationError(f"n_trials={n_trials!r}: must be positive")
        self.n_trials = min(self.n_trials, len(self._combinations))
        self._domains: dict[str, list[Any]] = {}
        for combination in self._combinations:
            for key, value in combination.items():
                if value not in self._domains.setdefault(key, []):
                    self._domains[key].append(value)
        self._remaining = list(range(len(self._combinations)))
        self._pending_trial = None
        self._suggest_count = 0
        self.study = optuna.create_study(direction=direction, sampler=optuna.samplers.TPESampler(seed=self.seed))

    def suggest(self) -> dict:
        if self._suggest_count >= self.n_trials:
            raise StopIteration
        if self._pending_trial is not None:
            raise RuntimeError("BayesianSearch.report() must be called before the next suggest()")
        trial = self.study.ask()
        proposed = {key: trial.suggest_categorical(key, values) for key, values in sorted(self._domains.items())}
        candidates = [idx for idx in self._remaining if all(self._combinations[idx].get(k) == v for k, v in proposed.items())]
        if candidates:
            idx = candidates[0]
        else:
            idx = min(self._remaining, key=lambda i: (sum(self._combinations[i].get(k) != v for k, v in proposed.items()), i))
        self._remaining.remove(idx)
        self._pending_trial = trial
        self._pending_params = dict(self._combinations[idx])
        self._suggest_count += 1
        return dict(self._pending_params)

    def report(self, params: dict, result: SimulationResult) -> None:
        if self._pending_trial is None:
            raise RuntimeError("BayesianSearch.report() called without a pending suggestion")
        trial = self._pending_trial
        self._pending_trial = None
        raw = result.metrics.get(self.rank_by)
        try:
            value = float(raw)
            if not math.isfinite(value):
                raise ValueError
        except (TypeError, ValueError):
            self.study.tell(trial, state=self._optuna.trial.TrialState.FAIL)
            return
        self.study.tell(trial, value)

    @property
    def completed_trials(self) -> int:
        return len(self.study.trials)
