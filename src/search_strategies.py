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
    """Optuna-backed reproducible categorical Bayesian search.

    Domains are explicit: every parameter is represented by the finite set of
    values supplied to the constructor. This keeps the search bounded by the
    same valid combinations as the exhaustive grid while allowing Optuna's
    sampler to prioritize promising combinations.
    """

    def __init__(
        self,
        combinations: Iterable[dict],
        *,
        rank_by: str,
        direction: str = "maximize",
        seed: int = 0,
        n_trials: int | None = None,
    ) -> None:
        try:
            import optuna
        except ImportError as exc:
            raise ConfigurationError("search_strategy='bayesian' requires the Optuna dependency") from exc

        self._optuna = optuna
        self._combinations = [dict(c) for c in combinations]
        if not self._combinations:
            raise ConfigurationError("BayesianSearch requires at least one parameter combination")
        if direction not in {"maximize", "minimize"}:
            raise ConfigurationError(f"direction={direction!r}: expected 'maximize' or 'minimize'")
        if not rank_by:
            raise ConfigurationError("rank_by must be non-empty")
        self.rank_by = rank_by
        self.direction = direction
        self.seed = int(seed)
        self.n_trials = len(self._combinations) if n_trials is None else int(n_trials)
        if self.n_trials < 1:
            raise ConfigurationError(f"n_trials={n_trials!r}: must be positive")
        self.n_trials = min(self.n_trials, len(self._combinations))

        # A categorical domain is explicit and deterministic for every field.
        self._domains: dict[str, list[Any]] = {}
        for combination in self._combinations:
            for key, value in combination.items():
                domain = self._domains.setdefault(key, [])
                if value not in domain:
                    domain.append(value)
        self._remaining = list(range(len(self._combinations)))
        self._suggested: dict[int, dict] = {}
        self._trial_count = 0
        self.study = optuna.create_study(
            direction=direction,
            sampler=optuna.samplers.TPESampler(seed=self.seed),
        )

    def suggest(self) -> dict:
        if self._trial_count >= self.n_trials:
            raise StopIteration

        # Ask Optuna for a categorical proposal, then map it to a valid grid
        # combination. The mapping is deterministic and never evaluates a
        # combination outside the supplied search domain.
        trial = self.study.ask()
        proposed = {
            key: trial.suggest_categorical(key, values)
            for key, values in sorted(self._domains.items())
        }
        candidates = [
            idx for idx in self._remaining
            if all(self._combinations[idx].get(k) == v for k, v in proposed.items())
        ]
        if not candidates:
            # Categorical suggestions can describe a cross-product point that
            # was not present in the supplied Cartesian domain. Choose the
            # nearest remaining valid combination deterministically.
            def distance(idx: int) -> tuple[int, int]:
                combo = self._combinations[idx]
                return (
                    sum(combo.get(k) != v for k, v in proposed.items()),
                    idx,
                )
            idx = min(self._remaining, key=distance)
        else:
            idx = candidates[0]
        self._remaining.remove(idx)
        params = dict(self._combinations[idx])
        self._suggested[self._trial_count] = {"trial": trial, "params": params}
        self._trial_count += 1
        return params

    def report(self, params: dict, result: SimulationResult) -> None:
        trial_info = self._suggested.get(self._trial_count - 1)
        if trial_info is None:
            return
        trial = trial_info["trial"]
        raw = result.metrics.get(self.rank_by)
        try:
            value = float(raw)
            if not math.isfinite(value):
                raise ValueError
        except (TypeError, ValueError):
            # Invalid evaluations are failed trials, not search-loop crashes.
            trial_value = None
            self.study.tell(trial, state=self._optuna.trial.TrialState.FAIL, values=trial_value)
            return
        self.study.tell(trial, value)

    @property
    def completed_trials(self) -> int:
        return len(self.study.trials)
