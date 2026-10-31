"""research/composition/matrix.py and analysis.py (Phases 5 and 6 of
docs/research/buy-sell-composition.md): the matrix runs every cell on every
fund with an equal budget and records what the analysis needs; the analysis
tells an additive world from an interacting one, and finds a ranking that
one year made."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from engine.core.exceptions import ConfigurationError
from research.composition import analysis, matrix


def _fund(seed: int, sessions: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows, price = [], 50.0
    for day in pd.bdate_range("2016-01-04", periods=sessions):
        for minute in (0, 60, 200, 389):
            ts = pd.Timestamp(day).tz_localize("America/New_York") + pd.Timedelta(
                hours=9, minutes=30 + minute
            )
            o = price
            price *= math.exp(0.0002 + 0.012 * rng.standard_normal())
            rows.append(
                (ts.tz_convert("UTC"), o, max(o, price) * 1.002, min(o, price) * 0.998, price, 1e5)
            )
    return pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume"]).set_index(
        "ts"
    )


FUNDS = {"AAA": _fund(1, 1400), "BBB": _fund(2, 1400), "TINY": _fund(3, 600)}
HF = {"per_lot_pct": 0.002, "lookback_days": 0.5, "bars_per_day": 4}


def _spec(**matrix_overrides):
    data = {
        "matrix": {
            "name": "t",
            "symbols": ["AAA", "BBB", "TINY"],
            "min_history_years": 5,
            "trials_per_cell": 2,
            "seed": 3,
            "buys": [{"id": "hf_local_reference", "params": HF}],
            "sells": [
                {"id": "fixed_target"},
                {
                    "id": "scale_out",
                    "params": {"rungs": ["0.5@0.01,0.5@0.03", "0.5@0.02,0.5@0.04"]},
                },
                {"id": "regime_exit"},
            ],
            **matrix_overrides,
        },
        "grid": {"steps": [0.01, 0.02], "profit_targets": [0.01, 0.02]},
        "costs": {
            "model_type": "slippage_commission",
            "commission_per_trade": 0.0,
            "slippage_bps": 1.0,
        },
    }
    return matrix.load_spec(data)


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    out = tmp_path_factory.mktemp("matrix")
    result = matrix.run_matrix(_spec(), load_bars=FUNDS.__getitem__, out_dir=out)
    return result, out


# --- the spec ---------------------------------------------------------------


def test_history_below_the_five_year_floor_is_refused():
    with pytest.raises(ConfigurationError, match="at least 5"):
        _spec(min_history_years=3)


def test_the_default_minimum_history_is_ten_years():
    data = {"matrix": {"buys": [{"id": "fixed"}], "sells": [{"id": "fixed_target"}]}}
    assert matrix.load_spec(data).min_history_years == 10


def test_a_matrix_config_names_policies_not_a_strategy():
    data = {"matrix": {"buys": [{"id": "fixed"}], "sells": [{"id": "fixed_target"}]}}
    data["strategy"] = {"strategy_id": "fixed"}
    with pytest.raises(ConfigurationError, match="not a strategy"):
        matrix.load_spec(data)


def test_cells_group_each_policys_variants_and_take_its_defaults():
    cells = matrix.plan_cells(_spec())
    assert [c.key for c in cells] == [
        "hf_local_reference|fixed_target",
        "hf_local_reference|scale_out",
        "hf_local_reference|regime_exit",
    ]
    scale_out = cells[1]
    assert len(scale_out.sells) == 2
    assert scale_out.sells[0]["params"]["min_tranche_notional"] == 0.0, "the policy's default"
    assert matrix.track_of(cells[2]) == "loss_capable"
    assert matrix.track_of(cells[0]) == "no_loss"


# --- the run ----------------------------------------------------------------


def test_every_cell_runs_on_every_fund_with_enough_history(run):
    result, _ = run
    assert {(t["symbol"], t["cell"]) for t in result.trials} == {
        (s, c.key) for s in ("AAA", "BBB") for c in matrix.plan_cells(result.spec)
    }
    assert [s["symbol"] for s in result.skipped] == ["TINY"]
    assert all(t["short_history"] for t in result.trials), "5.4 years is under the recommended 10"
    assert not any(t.get("error") for t in result.trials)


def test_each_cell_gets_the_same_budget(run):
    result, _ = run
    counts = pd.Series([(t["symbol"], t["cell"]) for t in result.trials]).value_counts()
    assert set(counts) == {2}


def test_a_target_replacing_sell_does_not_spend_its_budget_on_the_grid_target(run):
    result, _ = run
    trials = [t for t in result.trials if t["sell_id"] == "scale_out"]
    assert {t["profit_target"] for t in trials} == {0.01}


def test_the_same_cell_draws_the_same_parameters_on_every_fund(run):
    result, _ = run
    for cell in matrix.plan_cells(result.spec):
        draws = {
            symbol: sorted(
                (t["grid_step"], t["profit_target"], str(t["sell_params"]))
                for t in result.trials
                if t["cell"] == cell.key and t["symbol"] == symbol
            )
            for symbol in ("AAA", "BBB")
        }
        assert draws["AAA"] == draws["BBB"]


def test_the_loss_gate_opens_only_for_the_loss_capable_cells(run):
    result, _ = run
    for trial in result.trials:
        exits = trial["metrics"]["Signal Exit Count"]
        if trial["track"] == "no_loss":
            assert exits == 0
    assert any(
        t["metrics"]["Signal Exit Count"] > 0 for t in result.trials if t["track"] == "loss_capable"
    )


def test_the_years_compound_to_the_whole_return(run):
    result, _ = run
    for trial in result.trials[:4]:
        growth = np.prod([1 + y["return_pct"] / 100 for y in trial["years"]])
        assert (growth - 1) * 100 == pytest.approx(trial["metrics"]["Total Return %"], abs=1e-6)
        assert [y["year"] for y in trial["years"]] == list(range(2016, 2016 + len(trial["years"])))


def test_partial_sales_are_counted(run):
    result, _ = run
    scale_out = [t for t in result.trials if t["sell_id"] == "scale_out"]
    assert all(t["metrics"]["Partial Sale Lots"] > 0 for t in scale_out)
    fixed = [t for t in result.trials if t["sell_id"] == "fixed_target"]
    assert all(t["metrics"]["Partial Sale Lots"] == 0 for t in fixed)


def test_trials_are_written_as_they_finish_and_read_back(run):
    result, out = run
    written = matrix.load_trials(out / "trials.jsonl")
    assert len(written) == len(result.trials)
    assert written[0]["metrics"] == pytest.approx(result.trials[0]["metrics"])
    assert (out / "skipped.json").exists()


def test_a_policy_researched_on_another_fund_is_skipped_there():
    spec = _spec(
        symbols=["AAA"],
        buys=[{"id": "ml_reachability_rsp"}],
        sells=[{"id": "fixed_target"}],
    )
    result = matrix.run_matrix(spec, load_bars=FUNDS.__getitem__)
    assert result.trials == []
    assert "researched on RSP" in result.skipped[0]["reason"]


def test_the_report_renders_both_tracks(run):
    result, _ = run
    text = analysis.report(result.trials, metric="Calmar", title="t")
    assert "## Track: no-loss" in text and "## Track: loss-capable" in text
    assert "may sell below cost" in text


# --- the analysis -------------------------------------------------------------


def _scores(values: dict) -> pd.DataFrame:
    rows = [
        {"symbol": "X", "buy_id": b, "sell_id": s, "median": v, "best": v, "trials": 1}
        for (b, s), v in values.items()
    ]
    return pd.DataFrame(rows)


def test_an_additive_matrix_has_no_interaction_and_independent_winners():
    buy = {"b1": 1.0, "b2": 3.0, "b3": 0.0}
    sell = {"s1": 0.5, "s2": 2.0}
    dec = analysis.decompose(
        analysis.score_matrix(_scores({(b, s): buy[b] + sell[s] for b in buy for s in sell}))
    )
    assert dec["share"]["interaction"] == pytest.approx(0.0, abs=1e-12)
    decision = analysis.decide(dec, {"ok": True, "p": 0.9})
    assert (
        decision["independent"] and decision["best_buy"] == "b2" and decision["best_sell"] == "s2"
    )


def test_a_crossed_matrix_answers_with_the_best_pair():
    values = {("b1", "s1"): 5.0, ("b1", "s2"): 0.0, ("b2", "s1"): 0.0, ("b2", "s2"): 4.0}
    dec = analysis.decompose(analysis.score_matrix(_scores(values)))
    assert dec["share"]["interaction"] > 0.9
    decision = analysis.decide(dec, {"ok": True, "p": 0.001})
    assert decision["independent"] is False
    assert decision["best_pair"] == ("b1", "s1")
    assert decision["best_sell_per_buy"] == {"b1": "s1", "b2": "s2"}


def test_the_f_survival_function_matches_published_critical_values():
    assert analysis.f_survival(4.10, 2, 10) == pytest.approx(0.05, abs=0.001)
    assert analysis.f_survival(3.10, 4, 20) == pytest.approx(0.039, abs=0.002)
    assert analysis.f_survival(1.0, 7, 7) == pytest.approx(0.5, abs=1e-9)


def _years(effect):
    rng = np.random.default_rng(0)
    rows = []
    for b in ("b1", "b2", "b3"):
        for s in ("s1", "s2", "s3"):
            for year in range(2012, 2024):
                rows.append(
                    {
                        "trial": 0,
                        "symbol": "X",
                        "buy_id": b,
                        "sell_id": s,
                        "track": "no_loss",
                        "year": year,
                        "return_pct": effect(b, s) + rng.normal(0, 1.0),
                    }
                )
    return pd.DataFrame(rows)


def test_the_interaction_test_tells_additive_from_crossed():
    additive = analysis.interaction_test(_years(lambda b, s: int(b[1]) + int(s[1])), "no_loss")
    crossed = analysis.interaction_test(
        _years(lambda b, s: 5.0 if b[1] == s[1] else 0.0), "no_loss"
    )
    assert additive["ok"] and additive["p"] > 0.05
    assert crossed["ok"] and crossed["p"] < 1e-6


def test_leave_one_year_out_finds_the_ranking_one_year_made():
    def effect(b, s, year):
        if (b, s) == ("b1", "s1"):
            return 200.0 if year == 2022 else -5.0  # wins only through 2022
        return 2.0

    rows = []
    for b in ("b1", "b2"):
        for s in ("s1", "s2"):
            for year in range(2016, 2024):
                rows.append(
                    {
                        "trial": 0,
                        "symbol": "X",
                        "buy_id": b,
                        "sell_id": s,
                        "track": "no_loss",
                        "year": year,
                        "return_pct": effect(b, s, year),
                    }
                )
    loyo = analysis.leave_one_year_out(pd.DataFrame(rows), "no_loss")
    worst = loyo.iloc[0]
    assert worst["year"] == 2022
    assert worst["top_cell"] == "b1 / s1" and worst["top_cell_without"] != "b1 / s1"
