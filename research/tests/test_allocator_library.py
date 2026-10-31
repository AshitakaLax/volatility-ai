"""The portfolio-algorithm library (research/strategies/allocator_library.py):
every allocator selectable by name returns valid weights, reads its data
point-in-time, and the ones with a known answer give it."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from engine.core.exceptions import ConfigurationError
from research.strategies import allocator_library as lib
from research.strategies.portfolio_book import run_portfolio

N, K = 1400, 5
IDX = pd.bdate_range("2015-01-02", periods=N, tz="UTC")
COLS = [f"T{i}" for i in range(K)]


def _closes(seed=0, drifts=None, vols=None):
    rng = np.random.default_rng(seed)
    mu = np.zeros(K) if drifts is None else np.asarray(drifts)
    sd = np.full(K, 0.012) if vols is None else np.asarray(vols)
    r = mu + sd * rng.standard_normal((N, K))
    return pd.DataFrame(100 * np.exp(np.cumsum(r, axis=0)), index=IDX, columns=COLS)


def _fundamentals(overrides=None, seed=1):
    """Quarterly rows 2010-2020 for every field the allocators read."""
    rng = np.random.default_rng(seed)
    base = {
        "revenue": 100,
        "cogs": 60,
        "sga": 15,
        "interest": 2,
        "book_equity": 50,
        "total_assets": 200,
        "market_cap": 300,
        "dividends": 3,
        "buybacks": 2,
        "issuance": 1,
        "debt_paydown": 0.5,
        "shares": 10,
        "eps": 1,
        "eps_estimate": 1.1,
        "net_income": 8,
        "cfo": 9,
        "avg_total_assets": 195,
        "debt_to_equity": 0.5,
        "roe": 0.12,
        "quality": 0.0,
        "gross_profit": 40,
        "rd": 5,
        "book_to_market": 0.6,
        "earnings_change": 0.01,
    }
    rows = []
    for d in pd.date_range("2010-03-31", "2020-12-31", freq="QE"):
        for t in COLS:
            for f, v in base.items():
                value = v * (1 + rng.normal(0, 0.05))
                if overrides and (t, f) in overrides:
                    value = overrides[(t, f)](d, value)
                rows.append((d, t, f, value))
    return pd.DataFrame(rows, columns=["date", "ticker", "field", "value"])


DATA = {
    "fundamentals": _fundamentals(),
    "events": pd.DataFrame(
        [(IDX[-30].tz_localize(None), "T1", 0.08, "board seats, strategic alternatives")],
        columns=["date", "ticker", "value", "text"],
    ),
    "deals": pd.DataFrame(
        [
            (
                IDX[-40].tz_localize(None),
                IDX[-1].tz_localize(None) + pd.Timedelta(days=60),
                "T3",
                1e9,
                1.0,
            )
        ],
        columns=["announce", "close", "ticker", "offer", "fallback"],
    ),
    "navs": pd.DataFrame(
        [(d.tz_localize(None), t, 100.0) for d in IDX[::5] for t in COLS],
        columns=["date", "ticker", "nav"],
    ),
    "macro": pd.DataFrame(
        {
            "date": pd.date_range("2014-01-31", periods=90, freq="ME"),
            "value": 0.02 + 0.02 * np.sin(np.arange(90) / 8),
        }
    ),
    "dividends": pd.DataFrame([("T0", IDX[-100], 2.0)], columns=["ticker", "ex_date", "amount"]),
}


def _kwargs(name):
    kw = {d: DATA[d] for d in lib.DATA_NEEDS.get(name, ())}
    if name == "state_filtered_momentum":
        kw["market"] = "T0"
    return kw


def _valid(w):
    assert list(w.index) == COLS
    assert (w >= -1e-12).all() and w.sum() <= 1 + 1e-9


def test_every_allocator_is_named_and_mapped_to_its_ledger_id():
    assert set(lib.LEDGER) == set(lib.ALLOCATOR_LIBRARY)
    assert len(lib.NEW) == 41
    ids = list(lib.LEDGER.values())
    assert all(i.startswith("RK") for i in ids)


@pytest.mark.parametrize("name", sorted(lib.ALLOCATOR_LIBRARY))
def test_every_allocator_returns_valid_weights(name):
    _valid(lib.ALLOCATOR_LIBRARY[name](_closes(), **_kwargs(name)))


@pytest.mark.parametrize("name", sorted(n for n in lib.NEW if not n.endswith("scenarios")))
def test_no_allocator_reads_past_its_input(name):
    """A wild extra row is not visible: weights over closes[:-1] equal the
    weights over the same rows with the wild row dropped again."""
    c = _closes(seed=2)
    wild = pd.concat([c, c.iloc[[-1]].set_axis([c.index[-1] + pd.Timedelta(days=1)]) * 5])
    a = lib.ALLOCATOR_LIBRARY[name](c, **_kwargs(name))
    b = lib.ALLOCATOR_LIBRARY[name](wild.iloc[:-1], **_kwargs(name))
    assert np.allclose(a, b)


def test_field_snapshot_is_point_in_time():
    f = pd.DataFrame(
        [("2020-01-31", "T0", "eps", 1.0), ("2020-04-30", "T0", "eps", 2.0)],
        columns=["date", "ticker", "field", "value"],
    )
    assert lib.field_snapshot(f, "eps", pd.Timestamp("2020-03-01", tz="UTC"), ["T0"]).iloc[0] == 1.0
    assert lib.field_snapshot(f, "eps", pd.Timestamp("2020-04-30", tz="UTC"), ["T0"]).iloc[0] == 2.0
    assert np.isnan(lib.field_snapshot(f, "eps", pd.Timestamp("2020-01-01"), ["T0"]).iloc[0])
    year_ago = lib.field_snapshot(f, "eps", pd.Timestamp("2021-02-15"), ["T0"], years_back=1.0)
    assert year_ago.iloc[0] == 1.0


def test_fundamental_factors_pick_the_planted_winner():
    planted = _fundamentals(
        {
            ("T2", "revenue"): lambda d, v: v * 3,  # most profitable
            ("T4", "total_assets"): lambda d, v: v * (1 + 0.5 * (d.year - 2009)),  # fastest growing
            ("T1", "book_equity"): lambda d, v: v * 4,  # cheapest
        }
    )
    c = _closes()
    w = lib.gross_profitability(c, fundamentals=planted, q=0.2)
    assert w.idxmax() == "T2" and w["T2"] == 1.0
    assert lib.operating_profitability(c, fundamentals=planted, q=0.2).idxmax() == "T2"
    assert lib.asset_growth(c, fundamentals=planted, q=0.8)["T4"] == 0.0
    assert lib.book_to_market(c, fundamentals=planted, q=0.2).idxmax() == "T1"


def test_missing_data_fails_clearly():
    with pytest.raises(ConfigurationError, match="--data"):
        lib.gross_profitability(_closes(), fundamentals=None)


def test_momentum_and_low_risk_answers():
    c = _closes(drifts=[0.002, 0, 0, -0.002, 0], vols=[0.005] * 5)
    assert lib.momentum_12_1(c, q=0.2).idxmax() == "T0"
    vol = _closes(vols=[0.004, 0.01, 0.02, 0.03, 0.04])
    gmv = lib.global_min_variance(vol)
    assert gmv.idxmax() == "T0"
    eq = vol.pct_change().iloc[-252:]
    assert (eq @ gmv).var() < eq.mean(axis=1).var()
    assert lib.max_diversification(vol).sum() == pytest.approx(1.0)
    assert lib.min_cvar(vol).idxmax() == "T0"


def test_events_deals_and_navs():
    c = _closes()
    w = lib.activist_13d(c, events=DATA["events"], threshold=0.1, hold=60)
    assert w["T1"] == 1.0
    old = DATA["events"].assign(date=IDX[-200].tz_localize(None))
    assert lib.activist_13d(c, events=old, hold=60).sum() == 0
    deal = lib.merger_arbitrage(c, deals=DATA["deals"])
    assert deal["T3"] == 1.0
    closed = DATA["deals"].assign(close=IDX[-5].tz_localize(None))
    assert lib.merger_arbitrage(c, deals=closed).sum() == 0
    wide = c.copy()
    wide.iloc[-5:, 2] *= 0.7  # T2 trades far below its NAV
    navs = pd.DataFrame(
        [(d.tz_localize(None), t, float(c[t].loc[d])) for d in IDX for t in COLS],
        columns=["date", "ticker", "nav"],
    )
    assert lib.cef_discount(wide, navs=navs, window=250)["T2"] > 0


def test_topk_dropout_limits_turnover_in_the_book():
    c = _closes(seed=5)
    r = run_portfolio(
        c,
        lib.topk_dropout,
        rebalance="monthly",
        min_history=300,
        allocator_kwargs={"k": 3, "n_drop": 1},
    )
    held = (r.weights > 0.05).astype(int)
    changes = held.diff().abs().sum(axis=1)
    assert changes.max() <= 2  # at most one name out and one in per rebalance


def test_inflation_rotation_needs_macro_data():
    with pytest.raises(ConfigurationError):
        lib.inflation_rotation(_closes(), macro=None)
    _valid(lib.inflation_rotation(_closes(), macro=DATA["macro"]))
