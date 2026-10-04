"""
The algorithm database: every trading algorithm recorded in
docs/algorithm_ledger.md, implemented as standalone research code whether
or not it fits volatility-ai's engine or constraints.

Nothing here is wired into the engine, the engine host or a harness, and
nothing here trades: these are signal, sizing, pricing and decision
functions, each transcribed from its cited source and pinned by tests in
research/tests/test_catalog_*.py. Out-of-scope algorithms (short selling, options,
crypto, reinforcement learning) live here precisely so the record is
complete; the ledger says which ones the platform may actually use.

`registry.py` maps every ledger ID to its implementation (or records why an
entry has none). The modules:

  je_suis_tm           Q-series strategies as the original trades
  je_suis_tm_projects  Oil Money, Monte Carlo, Smart Farmers, Wisdom of
                       Crowds, graph-theory portfolio selection
  options              Black-Scholes, straddle, ThetaGang wheel, VXTH
                       hedge, tail hedges, dealer gamma
  trend_following      PyTrendFollow, Turtle, time-series momentum, Ghost
                       Trader, opening range breakout
  czsc                 Chan-theory fractals, strokes and pivot zones
  crypto               blackbird, depth arbitrage, triangular arbitrage,
                       funding carry
  rl_agents            huseinzol05 agents, evolution strategies, FinRL
                       environment and ensemble, policy-gradient rules
  rl_papers            Moody-Saffell RRL, action-augmented DRQN, EIIE
  forecasting          LSTM forecaster, stacking, lag regression,
                       analogues, anomalies
  leads                the catalog's gap-analysis leads
  excluded             IB HFT pairs, stock/bond mix, inverse and long-vol
                       sleeves, martingale, creation/redemption arbitrage
"""
