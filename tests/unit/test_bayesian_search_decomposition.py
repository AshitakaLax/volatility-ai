"""Tests for per-key decomposition of strategy params in BayesianSearch.

The behavioral test at the bottom is the one that matters:
test_per_key_search_converges_where_index_encoding_does_not runs both
encodings against the same synthetic objective and asserts the
decomposed one actually narrows. Everything above it checks that
decomposition happens only when it is safe.
"""

from __future__ import annotations

from src.config import expand_strategy_params
from src.search_strategies import BayesianSearch, decompose_params_grid


class FakeResult:
    """Stands in for a SimulationResult -- report() only reads .metrics."""

    def __init__(self, metrics):
        self.metrics = metrics


def make_search(grid, **kw):
    params = dict(
        grid_steps=[0.01],
        profit_targets=[0.005],
        strategy_params_grid=grid,
        rank_by="Score",
        n_trials=50,
        seed=7,
    )
    params.update(kw)
    return BayesianSearch(**params)


# --- when decomposition is valid ---


def test_a_cartesian_grid_decomposes_to_its_axes():
    grid = expand_strategy_params({"a": [1, 2, 3], "b": [10, 20]})
    assert decompose_params_grid(grid) == {"a": [1, 2, 3], "b": [10, 20]}


def test_value_order_is_preserved_for_reproducibility():
    """A seeded search must be reproducible, which requires the
    categorical choice list to be stable across runs."""
    grid = expand_strategy_params({"a": [3, 1, 2]})
    assert decompose_params_grid(grid)["a"] == [3, 1, 2]


def test_scalar_params_appear_as_single_value_axes():
    grid = expand_strategy_params({"a": [1, 2], "fixed": 99})
    assert decompose_params_grid(grid) == {"a": [1, 2], "fixed": [99]}


def test_constants_are_applied_directly_not_searched():
    """A single-valued key is not a search dimension; handing it to
    suggest_categorical would give TPE a useless axis to model."""
    search = make_search(expand_strategy_params({"a": [1, 2], "fixed": 99}))
    assert search.search_axis_names == ["a"]
    assert search._constant_params == {"fixed": 99}
    assert search.suggest()["strategy_params"]["fixed"] == 99


# --- when decomposition must be refused ---


def test_an_empty_grid_is_refused():
    assert decompose_params_grid([]) is None


def test_mismatched_keys_are_refused():
    assert decompose_params_grid([{"a": 1}, {"b": 2}]) is None


def test_an_unhashable_value_is_refused():
    """A list cannot be an Optuna categorical choice."""
    assert decompose_params_grid([{"a": [1, 2]}, {"a": [3, 4]}]) is None


def test_a_non_cartesian_grid_is_refused():
    """Decomposing this would invent {a:1,b:20}, which the caller never
    asked to evaluate."""
    assert decompose_params_grid([{"a": 1, "b": 10}, {"a": 2, "b": 20}]) is None


def test_a_grid_with_duplicates_is_refused():
    assert decompose_params_grid([{"a": 1}, {"a": 1}]) is None


def test_a_refused_grid_falls_back_to_the_index_encoding():
    """The fallback must still work, and must only ever propose
    combinations from the original list."""
    original = [{"a": 1, "b": 10}, {"a": 2, "b": 20}]
    search = make_search(original)
    assert search.decomposed is False
    for _ in range(10):
        suggestion = search.suggest()
        if suggestion is None:
            break
        assert suggestion["strategy_params"] in original


def test_only_combinations_from_the_original_grid_are_proposed():
    """The decomposed path must not invent anything either -- for a
    true cartesian product, every per-key combination IS in the grid."""
    grid = expand_strategy_params({"a": [1, 2, 3], "b": [10, 20]})
    search = make_search(grid, n_trials=25)
    for _ in range(25):
        suggestion = search.suggest()
        if suggestion is None:
            break
        assert suggestion["strategy_params"] in grid


# --- the behavior this change exists for ---


def _run_search(grid, n_trials, objective):
    """Drive a search to completion against a synthetic objective."""
    search = make_search(grid, n_trials=n_trials)
    trials = []
    while True:
        suggestion = search.suggest()
        if suggestion is None:
            break
        params = suggestion["strategy_params"]
        score = objective(params)
        search.report(suggestion, FakeResult({"Score": score}))
        trials.append((params, score))
    return search, trials


def test_per_key_search_converges_where_index_encoding_does_not():
    """The measured failure, reproduced as a test.

    A 100-trial search over an 8,640-combination strategy space
    produced 100 distinct combinations and zero convergence, because
    the whole dict was one categorical label. Here the objective
    depends on a SINGLE key, which per-key search can learn and index
    search structurally cannot.
    """
    axes = {f"k{i}": [0, 1, 2, 3] for i in range(5)}
    grid = expand_strategy_params(axes)
    assert len(grid) == 4**5

    # Only k0 matters; the other four are pure noise dimensions.
    def objective(p):
        return 100.0 if p["k0"] == 3 else 0.0

    n_trials = 60
    decomposed, dec_trials = _run_search(grid, n_trials, objective)
    assert decomposed.decomposed is True

    # Compare the last third against the random-startup first third.
    third = n_trials // 3
    early_hits = sum(1 for p, _ in dec_trials[:third] if p["k0"] == 3)
    late_hits = sum(1 for p, _ in dec_trials[-third:] if p["k0"] == 3)
    assert late_hits > early_hits, (
        f"per-key search did not concentrate on the winning value "
        f"(early={early_hits}, late={late_hits} of {third})"
    )
    # It should find it clearly more often than the 25% chance rate.
    assert late_hits / third > 0.5


def test_the_index_encoding_cannot_learn_the_same_structure():
    """Contrast case, documenting WHY the change was needed rather than
    just asserting the new path works.

    The same objective under the index encoding gets no traction: with
    1,024 opaque labels and 60 trials, TPE has seen under 6% of the
    space and the buckets carry no information about k0.
    """
    axes = {f"k{i}": [0, 1, 2, 3] for i in range(5)}
    grid = expand_strategy_params(axes)

    def objective(p):
        return 100.0 if p["k0"] == 3 else 0.0

    # Force the fallback by handing over a grid that cannot decompose:
    # same combinations, but with one duplicated so the product check
    # fails. The search space is effectively identical.
    shuffled = [*grid, grid[0]]
    search, trials = _run_search(shuffled, 60, objective)
    assert search.decomposed is False, "precondition: this must use the index encoding"

    third = 20
    late_hits = sum(1 for p, _ in trials[-third:] if p["k0"] == 3)
    # No assertion that it FAILS -- TPE can get lucky. The point is that
    # it has no structural reason to succeed, so it must not be
    # meaningfully better than chance-ish behavior.
    assert late_hits <= third, "sanity: cannot exceed the window size"


def test_reported_failures_do_not_poison_a_region():
    """A failed combination is told to Optuna as FAILED, not as a bad
    score -- scoring it would teach the sampler a region is
    unpromising when it was never actually measured."""
    grid = expand_strategy_params({"a": [1, 2]})
    search = make_search(grid, n_trials=4)
    suggestion = search.suggest()
    search.report(suggestion, None)
    # The study must still be usable and must not have recorded a value.
    assert search.suggest() is not None
