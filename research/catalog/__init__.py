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

The ranked list of section 8C (RK entries and the concepts of ranks
426-700), built on two shared foundations -- `autodiff` (a small
reverse-mode autodiff with Adam, MLP and LSTM, since torch is not
installed) and `econometrics` (GARCH, DCC, Kalman, Johansen/VECM,
fractional differencing, VAR, copulas and C-vines):

  factors              equity factor scores, Fama-French sorts, BAB,
                       SUE/PEAD, event studies, index and dividend events
  carry_rates          carry measures, commodity sorts, basis, duration
                       momentum, steepeners, curve models
  allocation           CVaR and robust allocators, Black-Litterman,
                       risk budgets, tensor rotation, top-K dropout
  spd_covariance       Riemannian (SPD) covariance, graph attention and
                       graph diffusion estimators
  stat_arb             Johansen baskets, distance and copula pairs,
                       PC-algorithm pairs, merger/convertible/capital-
                       structure/closed-end-fund arbitrage
  point_processes      Hawkes processes, neural Hawkes, signatures,
                       Hawkes-driven execution
  koopman              DMD, EDMD, Koopman MPC, deep Koopman
  topology             Vietoris-Rips persistence, landscapes, diagram
                       distances
  quantum              QUBOs, annealing, QAOA, adiabatic and tensor-
                       network solvers, quantum kernels, a QNN
  information          transfer entropy, fBm trend scanning
  deep_rl              DQN, MADDPG, genetic search, EMV and robust
                       portfolio agents
  market_making        Avellaneda-Stoikov simulator and the RL, robust,
                       Nash, Stackelberg and evolutionary quoters
  execution            schedules, volume models, RL/mean-field/robust/
                       operator execution
  neural_models        TCN, TFT, DeepLOB, neural CDE/RDE/ODE/jump ODE,
                       spiking networks, wavelet scalper
  cross_section        graph and hyperbolic rankers, FactorVAE, domain-
                       adversarial training, quantile networks,
                       signature trading
  generative           DDPM, flow matching, factor diffusion, TimeGAN,
                       GMMN, conditional WGAN-GP
  derivatives          dispersion, iron condors, gamma scalping, Heston and
                       rough Heston, deep hedging, DGM/PINN, neural SDEs
  technical_ml         Supertrend, breakouts, breadth thrust, LambdaRank,
                       causal impact, sequential bootstrap, sentiment, EMD
  defi                 constant-product arbitrage, concentrated liquidity
  concepts             the 34 researched concepts of ranks 426-700
"""
