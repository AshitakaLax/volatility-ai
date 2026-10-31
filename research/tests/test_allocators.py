"""The multi-asset allocators (research/strategies/allocators.py) and the
portfolio book that runs them (research/strategies/portfolio_book.py),
on synthetic closes with known answers."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from engine.core.exceptions import ConfigurationError
from research.strategies import allocators as al
from research.strategies.portfolio_book import metrics_of, run_portfolio


def _closes(n=800, vols=(0.01, 0.02, 0.03, 0.015), drifts=None, seed=0, corr=0.0):
    rng = np.random.default_rng(seed)
    k = len(vols)
    common = rng.normal(0, 1, n)
    cols = {}
    for i, v in enumerate(vols):
        z = np.sqrt(corr) * common + np.sqrt(1 - corr) * rng.normal(0, 1, n)
        mu = 0.0 if drifts is None else drifts[i]
        cols[f"A{i}"] = 100 * np.exp(np.cumsum(mu + v * z))
    idx = pd.bdate_range("2015-01-02", periods=n, tz="UTC")
    return pd.DataFrame(cols, index=idx).iloc[:, :k]


def _valid(w, columns):
    assert list(w.index) == list(columns)
    assert (w >= -1e-12).all() and w.sum() <= 1 + 1e-9


def test_equal_weight():
    c = _closes()
    w = al.equal_weight(c)
    _valid(w, c.columns)
    assert np.allclose(w, 0.25)


def test_inverse_volatility_orders_by_risk():
    c = _closes()
    w = al.inverse_volatility(c, lookback=500)
    _valid(w, c.columns)
    assert w["A0"] > w["A3"] > w["A1"] > w["A2"]
    assert w.sum() == pytest.approx(1.0)


def test_erc_equalises_risk_contributions():
    rng = np.random.default_rng(3)
    a = rng.normal(size=(5, 5))
    cov = a @ a.T + 5 * np.eye(5)
    w = al.erc_weights(cov)
    assert np.allclose(al.risk_contributions(w, cov), 0.2, atol=1e-6)
    budgets = [0.4, 0.3, 0.1, 0.1, 0.1]
    wb = al.erc_weights(cov, budgets)
    assert np.allclose(al.risk_contributions(wb, cov), budgets, atol=1e-6)
    # uncorrelated: ERC is inverse volatility
    diag = np.diag([0.01, 0.04, 0.09])
    assert np.allclose(
        al.erc_weights(diag), np.array([1 / 0.1, 1 / 0.2, 1 / 0.3]) / (10 + 5 + 10 / 3)
    )


def test_equal_risk_contribution_on_closes():
    c = _closes(corr=0.3)
    w = al.equal_risk_contribution(c, lookback=500)
    _valid(w, c.columns)
    cov = c.pct_change().iloc[-500:].cov().to_numpy()
    assert np.allclose(al.risk_contributions(w, cov), 0.25, atol=1e-6)


def test_conformal_risk_parity_scales_down_to_the_loss_budget():
    c = _closes(vols=(0.03, 0.04, 0.05, 0.035))
    full = al.equal_risk_contribution(c)
    tight = al.conformal_risk_parity(c, max_daily_loss=0.01)
    loose = al.conformal_risk_parity(c, max_daily_loss=1.0)
    assert np.allclose(loose, full)
    ratio = tight / full
    assert ratio.std() < 1e-12 and 0 < ratio.iloc[0] < 1


def test_conformal_allocation_holds_only_a_confident_trend():
    c = _closes(n=900, vols=(0.002, 0.01, 0.01), drifts=(0.004, 0.0, -0.002), seed=4)
    w = al.conformal_allocation(c, horizon=21, calibration=250, alpha=0.2)
    _valid(w, c.columns)
    assert w["A0"] > 0.99 and w["A2"] == 0


def test_cross_sectional_momentum_picks_the_winners():
    c = _closes(drifts=(0.002, -0.001, 0.0015, -0.002), vols=(0.005,) * 4)
    w = al.cross_sectional_momentum(c, lookback=252, skip=21, k=2)
    _valid(w, c.columns)
    assert set(w[w > 0].index) == {"A0", "A2"}
    with pytest.raises(ConfigurationError):
        al.cross_sectional_momentum(c, lookback=21, skip=21)


def test_state_filtered_momentum_is_cash_after_a_down_market():
    up = _closes(n=900, drifts=(0.001, 0.002, -0.001, 0.0), vols=(0.005,) * 4)
    w = al.state_filtered_momentum(up, market="A0", k=1)
    assert w["A1"] == 1.0 and w["A0"] == 0.0
    down = _closes(n=900, drifts=(-0.001, 0.002, -0.001, 0.0), vols=(0.005,) * 4)
    assert al.state_filtered_momentum(down, market="A0", k=1).sum() == 0


def test_low_volatility_holds_the_calmest():
    c = _closes()
    w = al.low_volatility(c, k=2)
    assert set(w[w > 0].index) == {"A0", "A3"}


def test_dividend_yield_ranks_by_trailing_yield_without_lookahead():
    c = _closes(n=600, vols=(0.001,) * 3)
    days = c.index
    divs = pd.DataFrame(
        [
            ("A0", days[400], 4.0),
            ("A1", days[450], 1.0),
            ("A2", days[599], 9.0),  # paid on the last row: counted
        ],
        columns=["ticker", "ex_date", "amount"],
    )
    y = al.trailing_yield(c, divs)
    assert y["A2"] > y["A0"] > y["A1"] > 0
    y_before = al.trailing_yield(c.iloc[:599], divs)  # A2's not yet paid
    assert y_before["A2"] == 0
    w = al.dividend_yield(c.iloc[:599], divs, k=1)
    assert w["A0"] == 1.0


def test_dividend_growth_filter():
    c = _closes(n=800, vols=(0.0005,) * 2)
    d = c.index
    divs = pd.DataFrame(
        [("A0", d[300], 1.0), ("A0", d[700], 2.0), ("A1", d[300], 3.0), ("A1", d[700], 2.5)],
        columns=["ticker", "ex_date", "amount"],
    )
    w = al.dividend_yield(c, divs, k=2, require_growth=True)
    assert w["A0"] == 1.0 and w["A1"] == 0.0


def test_alpha_stacking_follows_a_planted_signal():
    """A0 trends steadily, the rest are noise: the stacked forecast must
    put the book in A0."""
    c = _closes(n=1100, drifts=(0.002, 0.0, 0.0, 0.0), vols=(0.004, 0.01, 0.01, 0.01), seed=7)
    w = al.alpha_stacking(c)
    _valid(w, c.columns)
    assert w.idxmax() == "A0" and w["A0"] > 0.5


def test_risk_neutral_reversal_buys_the_residual_loser():
    c = _closes(n=400, vols=(0.005,) * 4, corr=0.5, seed=9)
    c.iloc[-3:, 2] *= np.array([0.97, 0.95, 0.93])  # A2 falls apart from the market
    w = al.risk_neutral_reversal(c, k=1)
    assert w["A2"] == pytest.approx(1.0)


def test_betti0_counts_clusters():
    corr = np.array([[1, 0.95, 0, 0], [0.95, 1, 0, 0], [0, 0, 1, 0.9], [0, 0, 0.9, 1]], dtype=float)
    assert al.betti0(corr, 0.05) == 4
    assert al.betti0(corr, 0.25) == 2
    assert al.betti0(corr, 0.8) == 1


def test_contagion_guard_derisks_when_correlations_converge():
    calm = _closes(n=600, corr=0.0, seed=11)
    rng = np.random.default_rng(12)
    shock = rng.normal(0, 0.03, 63)
    tail = calm.iloc[-1].to_numpy() * np.exp(
        np.cumsum(shock)[:, None] + rng.normal(0, 0.001, (63, 4))
    )
    idx = pd.bdate_range(calm.index[-1] + pd.Timedelta(days=1), periods=63, tz="UTC")
    crisis = pd.concat([calm, pd.DataFrame(tail, index=idx, columns=calm.columns)])
    assert al.contagion_score(crisis) > al.contagion_score(calm)
    assert al.contagion_guard(calm).sum() == pytest.approx(1.0)
    assert al.contagion_guard(crisis).sum() == pytest.approx(0.25)


def test_every_registered_allocator_returns_valid_weights():
    c = _closes(n=1200, corr=0.2, seed=13)
    divs = pd.DataFrame([("A0", c.index[1000], 2.0)], columns=["ticker", "ex_date", "amount"])
    extra = {"state_filtered_momentum": {"market": "A0"}, "dividend_yield": {"dividends": divs}}
    for name, fn in al.ALLOCATORS.items():
        w = fn(c, **extra.get(name, {}))
        _valid(w, c.columns)


def test_allocators_never_read_past_their_input():
    """Appending a wild future row must not change today's weights."""
    c = _closes(n=1100, corr=0.2, seed=14)
    future = c.iloc[[-1]] * 3.0
    future.index = [c.index[-1] + pd.Timedelta(days=1)]
    for name in ("inverse_volatility", "equal_risk_contribution", "cross_sectional_momentum"):
        fn = al.ALLOCATORS[name]
        before = fn(c)
        after = fn(pd.concat([c, future]).iloc[:-1])
        assert np.allclose(before, after)


# ---------------------------------------------------------------- the book


def test_book_tracks_equal_weight_and_reports_metrics():
    c = _closes(n=600, drifts=(0.0005,) * 4, vols=(0.01,) * 4)
    r = run_portfolio(c, al.equal_weight, rebalance="monthly", min_history=100)
    assert len(r.equity) == 500
    assert r.weights.iloc[-1].sum() == pytest.approx(1.0, abs=0.01)
    for key in ("CAGR %", "Max Drawdown %", "Calmar", "Sharpe", "Trades"):
        assert key in r.metrics


def test_book_never_realises_a_loss_by_default():
    """Rotate out of an instrument that has fallen: with no_loss the sale is
    blocked; with no_loss=False it is a signal exit that realises the loss."""
    idx = pd.bdate_range("2020-01-01", periods=40, tz="UTC")
    a = np.r_[np.full(20, 100.0), np.full(20, 80.0)]
    b = np.full(40, 50.0)
    c = pd.DataFrame({"A": a, "B": b}, index=idx)

    def first_a_then_b(hist):
        return pd.Series({"A": 1.0, "B": 0.0} if len(hist) < 25 else {"A": 0.0, "B": 1.0})

    safe = run_portfolio(c, first_a_then_b, rebalance=1, min_history=5)
    assert safe.metrics["Sells blocked by the no-loss guard"] > 0
    assert safe.metrics["Sells realising a loss"] == 0
    assert safe.weights.iloc[-1]["A"] > 0.9  # held overweight, not sold
    loss = run_portfolio(c, first_a_then_b, rebalance=1, min_history=5, no_loss=False)
    assert loss.metrics["Sells realising a loss"] == 1
    assert loss.metrics["Realized PnL"] < 0
    assert loss.weights.iloc[-1]["B"] > 0.99


def test_book_uses_only_past_closes():
    seen = []
    c = _closes(n=300)

    def spy(hist):
        seen.append(hist.index[-1])
        return al.equal_weight(hist)

    r = run_portfolio(c, spy, rebalance=1, min_history=100)
    trade_days = list(r.equity.index)
    assert all(s < d for s, d in zip(seen, trade_days, strict=True))


def test_book_validation():
    c = _closes(n=50)
    with pytest.raises(ConfigurationError):
        run_portfolio(c, al.equal_weight, min_history=100)
    with pytest.raises(ConfigurationError):
        run_portfolio(c, al.equal_weight, min_history=10, rebalance="yearly")
    with pytest.raises(ConfigurationError):
        run_portfolio(c, lambda h: pd.Series(1.0, index=h.columns), min_history=10)


def test_metrics_of_known_series():
    eq = pd.Series([100.0, 110.0, 99.0, 121.0])
    m = metrics_of(eq, periods_per_year=3)
    assert m["Total Return %"] == pytest.approx(21.0)
    assert m["Max Drawdown %"] == pytest.approx(-10.0)
