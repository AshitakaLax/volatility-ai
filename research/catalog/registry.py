"""
Every algorithm in docs/algorithm_ledger.md, mapped to its implementation.

Each `Entry` names the ledger ID, the ledger's own status, and where the
code lives:

  * "package.module:qualname" -- an importable object (checked by
    research/tests/test_catalog_registry.py, which also checks that every
    ledger ID appears here exactly once);
  * "package.module" -- a whole module;
  * "tools/....py" or "engine/....py" style paths -- harness or engine
    plumbing that is not imported here (existence is checked).

An entry with no implementation carries a `note` saying why: an
unverified record, a framework rather than an algorithm, or an entry
that is a pointer to another one.

`CATALOG_ALIASES` maps the correction-strategy catalog's record codes
(docs/research/correction-strategies.md) that the ledger folded into
existing entries onto those entries; `LEADS` covers the catalog's
gap-analysis leads, which have no ledger ID.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Entry:
    ledger_id: str
    name: str
    status: str
    implementations: tuple[str, ...] = field(default_factory=tuple)
    note: str = ""


def _e(ledger_id: str, name: str, status: str, *impls: str, note: str = "") -> Entry:
    return Entry(ledger_id, name, status, tuple(impls), note)


_RS = "research.strategies"
_RC = "research.catalog"

ENTRIES: tuple[Entry, ...] = (
    # ---- section 3: already in volatility-ai
    _e("V1", "Fixed portfolio % sizing", "✅", f"{_RS}.size_calculators:FixedPortfolioPercentage"),
    _e("V2", "Bell-curve sizing", "✅", f"{_RS}.size_calculators:BellCurveProbabilitySizing"),
    _e("V3", "RSI momentum sizing", "✅", f"{_RS}.size_calculators:RsiMomentumSizing"),
    _e(
        "V4",
        "Bayesian dual-scale sizing",
        "✅",
        f"{_RS}.bayesian_sizing_calculators:BayesianDualScaleSizing",
    ),
    _e(
        "V5",
        "HF local-reference grid (champion)",
        "✅🔬",
        f"{_RS}.high_frequency_sizing:HighFrequencyLocalReferenceSizing",
    ),
    _e(
        "V6",
        "Event-day / earnings / weighted-event boosts",
        "✅",
        f"{_RS}.high_frequency_sizing:HighFrequencyLocalReferenceSizing",
        "engine/core/market_context.py",
    ),
    _e(
        "V7",
        "Vol-ratio scaling",
        "✅🔬",
        f"{_RS}.high_frequency_sizing:HighFrequencyLocalReferenceSizing",
    ),
    _e(
        "V8",
        "Volume scaling",
        "✅",
        f"{_RS}.high_frequency_sizing:HighFrequencyLocalReferenceSizing",
    ),
    _e(
        "V9",
        "Time-of-day scaling",
        "✅",
        f"{_RS}.high_frequency_sizing:HighFrequencyLocalReferenceSizing",
        "engine/data/intraday_profile.py",
    ),
    _e(
        "V10",
        "Trailing profit target",
        "✅",
        "research.optimization.trailing_target:TrailingTargetPolicy",
    ),
    _e(
        "V11",
        "Drawdown throttle (dd_throttle_*)",
        "✅🧪",
        "engine/trading/risk_manager.py",
        f"{_RS}.gated_local_reference_sizing:GatedLocalReferenceSizing",
    ),
    _e(
        "V12",
        "Implied-vol scaling (VIXY as VXN proxy)",
        "✅🧪",
        "engine/data/implied_vol_signal.py",
        f"{_RS}.high_frequency_sizing:HighFrequencyLocalReferenceSizing",
    ),
    _e(
        "V13",
        "ML reachability sizing",
        "✅🧪",
        "research.ml.reachability_sizing:MLReachabilitySizing",
    ),
    _e(
        "V14",
        "ML regime sizing (qlib)",
        "✅🧪",
        "research.ml.regime_scaled_sizing:MLRegimeScaledSizing",
    ),
    _e(
        "V15",
        "TA-Lib indicator regime sweep",
        "✅🔬⚠️",
        f"{_RS}.indicator_library",
        "tools/indicator_sweep.py",
    ),
    _e(
        "V16",
        "SMA200 / trend-line (LINEARREG) regime",
        "✅🔬⚠️",
        f"{_RS}.trend_regimes:sma_risk_on",
        "tools/stage2_grid.py",
    ),
    _e(
        "V17",
        "NATR-below regime, liquidate on flip",
        "✅🔬⚠️",
        f"{_RS}.natr_regime:calm_by_date",
        "tools/stage3_grid.py",
    ),
    _e("V18", "Volatility targeting (RSP)", "✅🔬", "tools/probe_rsp_alternatives.py"),
    _e("V19", "Random-regime null control", "✅🔬⚠️", "tools/stage3_grid.py"),
    _e(
        "V20",
        "SQQQ grid",
        "❌⛔",
        f"{_RS}.high_frequency_sizing:HighFrequencyLocalReferenceSizing",
        f"{_RC}.excluded:daily_reset_path",
        note="The champion grid (V5) run on SQQQ; daily_reset_path shows the inverse-ETF drag.",
    ),
    # ---- section 4: added in patches 0001-0006
    _e("N1", "Dual Thrust breakdown gate", "🆕🧪", f"{_RS}.entry_gates:BreakdownGate"),
    _e("N2", "Opening-range breakdown gate", "🆕🧪", f"{_RS}.entry_gates:BreakdownGate"),
    _e("N3", "Prior-session-low gap gate", "🆕🧪", f"{_RS}.entry_gates:BreakdownGate"),
    _e("N4", "Shooting-star gate (causal)", "🆕🧪", f"{_RS}.entry_gates:ShootingStarGate"),
    _e("N5", "Causal daily NATR regime", "🆕", f"{_RS}.natr_regime:calm_by_date"),
    _e("N6", "Regime sleeves", "🆕🧪", f"{_RS}.regime_sleeve_sizing:RegimeSleeveSizing"),
    _e(
        "N7", "Leverage step-down (TQQQ calm / QQQ turbulent)", "🆕🧪", "tools/leverage_stepdown.py"
    ),
    _e("N8", "intrabar_fill booking modes", "🆕", "engine/core/config.py", "engine/core/sizing.py"),
    _e(
        "N9", "Causal stage re-screen (--lag)", "🆕", "tools/stage1_grid.py", "tools/stage3_grid.py"
    ),
    _e("N10", "Regime minimum hold (debounce)", "🆕", f"{_RS}.natr_regime:debounce"),
    _e("N11", "Rotation harness", "🆕🧪", "tools/rotation.py"),
    # ---- section 5: je-suis-tm/quant-trading
    _e(
        "Q1",
        "MACD oscillator",
        "🆕🧪 (regime)",
        f"{_RS}.trend_regimes:macd_risk_on",
        f"{_RC}.je_suis_tm:macd_crossover",
    ),
    _e(
        "Q2",
        "Pair trading (long/short)",
        "⛔",
        f"{_RC}.je_suis_tm:pair_trading_signals",
        f"{_RS}.pairs:engle_granger",
        f"{_RS}.pairs:KalmanHedgeRatio",
    ),
    _e(
        "Q3",
        "Heikin-Ashi",
        "🆕🧪 (regime)",
        f"{_RS}.trend_regimes:heikin_ashi_risk_on",
        f"{_RC}.je_suis_tm:heikin_ashi_trades",
    ),
    _e(
        "Q4",
        "London Breakout (as a trade)",
        "⛔ (gate built)",
        f"{_RC}.je_suis_tm:london_breakout_trades",
        f"{_RS}.entry_gates:BreakdownGate",
    ),
    _e(
        "Q5",
        "Awesome oscillator",
        "🆕🧪 (regime)",
        f"{_RS}.trend_regimes:awesome_risk_on",
        f"{_RC}.je_suis_tm:awesome_trades",
    ),
    _e("Q6", "Oil Money", "❌", f"{_RC}.je_suis_tm_projects:oil_money_signals"),
    _e(
        "Q7",
        "Dual Thrust (as a trade)",
        "⛔ (gate built)",
        f"{_RC}.je_suis_tm:dual_thrust_trades",
        f"{_RS}.entry_gates:BreakdownGate",
    ),
    _e(
        "Q8",
        "Parabolic SAR",
        "🆕🧪 (regime)",
        f"{_RS}.trend_regimes:psar_risk_on",
        f"{_RC}.je_suis_tm:psar_script",
    ),
    _e(
        "Q9",
        "Bollinger W-bottom",
        "🆕🧪 (entry rule)",
        f"{_RS}.entry_gates:BollingerWGate",
        f"{_RC}.je_suis_tm:bollinger_w_trades",
    ),
    _e(
        "Q10",
        "RSI pattern recognition",
        "🆕🧪 (gate)",
        f"{_RS}.entry_gates:RsiHeadShouldersGate",
        f"{_RC}.je_suis_tm:rsi_head_shoulders_trades",
        f"{_RC}.je_suis_tm:rsi_overbought_oversold",
    ),
    _e(
        "Q11",
        "Monte Carlo project",
        "❌ (as signal)",
        f"{_RC}.je_suis_tm_projects:monte_carlo_forecast",
    ),
    _e(
        "Q12",
        "Options straddle",
        "⛔",
        f"{_RC}.options:straddle_entry",
        f"{_RC}.options:straddle_pnl_at_expiry",
    ),
    _e(
        "Q13",
        "Portfolio optimization project",
        "🆕🧪 (HRP)",
        f"{_RS}.hrp:hrp_weights",
        f"{_RC}.je_suis_tm_projects:degeneracy_selection",
        f"{_RC}.je_suis_tm_projects:clique_centrality_selection",
        f"{_RC}.je_suis_tm_projects:markowitz_weights",
    ),
    _e(
        "Q14",
        "Smart Farmers",
        "❌",
        f"{_RC}.je_suis_tm_projects:smart_farmers_plan",
        f"{_RC}.je_suis_tm_projects:constrained_demand_ols",
    ),
    _e("Q15", "VIX calculator", "🆕 (data tool)", f"{_RS}.vix_calculator:vix"),
    _e(
        "Q16",
        "Wisdom of Crowds",
        "❌",
        f"{_RC}.je_suis_tm_projects:dawid_skene",
        f"{_RC}.je_suis_tm_projects:platt_burges",
    ),
    _e(
        "Q17",
        "Shooting star (as a trade)",
        "⛔ (gate built)",
        f"{_RC}.je_suis_tm:shooting_star_trades",
        f"{_RS}.entry_gates:ShootingStarGate",
    ),
    # ---- section 6: added in this work (patches 0001-0004)
    _e(
        "A1",
        "Deep RL agents (FinRL, DQN, PPO, DDQN, gyms)",
        "❌ (for now)",
        f"{_RC}.rl_agents:HuseinQAgent",
        f"{_RC}.rl_agents:QTable",
        f"{_RC}.rl_agents:FinRLStockTradingEnv",
        f"{_RC}.rl_agents:LinearA2C",
    ),
    _e(
        "A2",
        "FinRL ensemble turbulence index",
        "🆕🧪",
        f"{_RS}.turbulence_regime:turbulence_index",
        f"{_RC}.rl_agents:finrl_turbulence_threshold",
    ),
    _e("A3", "LPPLS / Dragon-Kings crash hazard", "🆕🧪 (research)", f"{_RS}.lppls:confidence"),
    _e(
        "A4",
        "DL portfolio management (PGPortfolio, DeepDow, qtrader)",
        "❌ (for now)",
        f"{_RC}.rl_papers:EIIEPolicy",
    ),
    _e("A5", "skfolio / HRP allocation", "🆕🧪", f"{_RS}.hrp:hrp_weights"),
    _e(
        "A6",
        "HFT pairs with IB",
        "⛔",
        f"{_RC}.excluded:ib_hft_signals",
        f"{_RC}.excluded:ib_pairs_long_only",
    ),
    _e(
        "A7",
        "Crypto bots / arbitrage / blackbird",
        "❌",
        f"{_RC}.crypto:blackbird_entry",
        f"{_RC}.crypto:depth_arbitrage",
        f"{_RC}.crypto:find_arbitrage_cycle",
    ),
    _e(
        "A8",
        "Pattern / forecasting libraries (mlforecast, patternity)",
        "❌ (for now)",
        f"{_RC}.forecasting:RecursiveLagForecaster",
        f"{_RC}.forecasting:analog_forecast",
        f"{_RC}.forecasting:ewm_anomalies",
    ),
    # ---- section 7: awesome-systematic-trading
    _e(
        "S1",
        "ThetaGang (wheel)",
        "⛔❌",
        f"{_RC}.options:wheel_select_contract",
        f"{_RC}.options:wheel_should_roll",
        f"{_RC}.options:vix_hedge_weight",
    ),
    _e(
        "S2",
        "PyTrendFollow",
        "⛔ (idea → V16/Q8)",
        f"{_RC}.trend_following:ewmac_forecasts",
        f"{_RC}.trend_following:breakout_forecasts",
        f"{_RC}.trend_following:pytrendfollow_position",
    ),
    _e(
        "S3",
        "volest (Sinclair estimators, Yang-Zhang)",
        "🆕",
        f"{_RS}.volatility_estimators:SessionVolatility",
    ),
    _e(
        "S4",
        "pysystemtrade (Carver vol targeting)",
        "🆕🧪",
        f"{_RS}.gated_local_reference_sizing:GatedLocalReferenceSizing",
        f"{_RS}.volatility_estimators:SessionVolatility",
    ),
    _e("S5", "czsc (Chan theory)", "❌ (unvetted)", f"{_RC}.czsc:CZSC", f"{_RC}.czsc:get_zs_seq"),
    # ---- section 8: proposed during this research
    _e(
        "X1",
        "Intraday momentum gate (Gao et al. 2018)",
        "🆕🧪",
        f"{_RS}.entry_gates:IntradayMomentumGate",
    ),
    _e("X2", "Defensive rotation", "🆕🧪", "tools/rotation.py"),
    _e("X3", "Long-only relative-strength rotation", "🆕🧪", "tools/rotation.py"),
    _e(
        "X4",
        "Capitulation-bounce entries",
        "🆕🧪",
        f"{_RS}.entry_gates:BollingerWGate",
        "tools/leverage_stepdown.py",
    ),
    _e("X5", "Long Treasuries (TLT) as the hedge", "❌", f"{_RC}.excluded:rebalanced_mix"),
    _e(
        "X6",
        "Inverse-ETF regime sleeve",
        "⛔",
        f"{_RC}.excluded:regime_sleeve_returns",
        f"{_RC}.excluded:daily_reset_path",
    ),
    _e("X7", "Managed-futures ETF sleeve", "⛔", f"{_RC}.trend_following:tsmom_weights"),
    _e("X8", "Long-volatility ETF sleeve (VIXY)", "⛔", f"{_RC}.excluded:long_vol_sleeve"),
    _e("X9", "Gold (GLD)", "🆕🧪", "tools/rotation.py"),
    # ---- section 8A: correction-strategy catalog
    _e(
        "C-MR1",
        "Short-term reversal as paid liquidity provision",
        "🧪",
        f"{_RS}.mean_reversion:contrarian_weights",
        f"{_RS}.mean_reversion:decayed_reversal_scores",
    ),
    _e(
        "C-MR2",
        "ETF-residual OU stat arb (s-score)",
        "🧪",
        f"{_RS}.mean_reversion:s_score",
        f"{_RS}.mean_reversion:s_score_long_signal",
    ),
    _e(
        "C-MR4",
        "Mean-reversion diagnostics",
        "🧪",
        f"{_RS}.mean_reversion:adf",
        f"{_RS}.mean_reversion:hurst_exponent",
        f"{_RS}.mean_reversion:variance_ratio",
        f"{_RS}.mean_reversion:half_life",
    ),
    _e(
        "C-MR7", "R-Breaker pivot reversal and breakout", "🧪", f"{_RS}.intraday_gates:RBreakerGate"
    ),
    _e("C-M1", "Noise-Area intraday momentum", "🧪", f"{_RS}.intraday_gates:NoiseAreaGate"),
    _e(
        "C-M2",
        "Five-minute opening range breakout",
        "⛔ (as published)",
        f"{_RC}.trend_following:orb_trade",
        f"{_RC}.trend_following:stocks_in_play",
    ),
    _e("C-G2", "Inventory-skewed grid", "🧪", f"{_RS}.inventory_control:inventory_skewed_level"),
    _e("C-G3", "Volatility-scaled grid", "🧪", f"{_RS}.grid_spacing:VolatilityScaledStep"),
    _e("C-G4", "Dynamic grid reset (DGT)", "🧪", "research.strategies.grid_lifecycle:DynamicGrid"),
    _e(
        "C-G5",
        "Turtle ATR-unit pyramiding",
        "🧪 (scale-in) · ⛔ (stop)",
        f"{_RS}.position_sizing:TurtlePyramid",
        f"{_RC}.trend_following:letianzj_turtle_trades",
        f"{_RC}.trend_following:turtle_original_trades",
    ),
    _e(
        "C-G6",
        "Grid ruin analysis with absorbing barriers",
        "🧪",
        "research.strategies.grid_lifecycle:ruin_probability",
    ),
    _e(
        "C-MM1",
        "Avellaneda-Stoikov optimal quotes",
        "🧪 (buy side)",
        f"{_RS}.inventory_control:as_quotes",
    ),
    _e("C-MM2", "GLFT closed-form quotes", "🧪 (needs L1)", f"{_RS}.inventory_control:glft_quotes"),
    _e("C-MM3", "Alpha-shifted quoting", "🧪", f"{_RS}.inventory_control:alpha_shifted_quotes"),
    _e("C-MM4", "VPIN flow-toxicity filter", "🧪 (needs trades)", f"{_RS}.microstructure:vpin"),
    _e(
        "C-MM5",
        "Probabilistic queue-position fill models",
        "🧪 (needs L2)",
        f"{_RS}.microstructure:QueuePositionEstimator",
    ),
    _e(
        "C-R3",
        "HMM, Gaussian-mixture and Markov-switching regimes",
        "🧪",
        f"{_RS}.regime_models:GaussianHMM",
        f"{_RS}.regime_models:GaussianMixture",
    ),
    _e(
        "C-ML1",
        "Triple-barrier and trend-scanning labels",
        "🧪",
        "research.ml.barrier_labels:triple_barrier_labels",
        "research.ml.barrier_labels:trend_scanning_labels",
    ),
    _e(
        "C-ML3",
        "Purged k-fold, embargo and CPCV",
        "🧪",
        "research.optimization.purged_cv:purged_kfold",
        "research.optimization.purged_cv:combinatorial_purged_splits",
    ),
    _e(
        "C-ML4",
        "Deflated Sharpe ratio and PBO",
        "🧪",
        "research.optimization.overfitting:deflated_sharpe",
        "research.optimization.overfitting:probability_of_backtest_overfitting",
    ),
    _e(
        "C-ML5",
        "Information-driven bars and fractional differentiation",
        "🧪",
        "research.ml.info_bars:tick_imbalance_bars",
        "research.ml.info_bars:frac_diff_ffd",
    ),
    _e(
        "C-RL4",
        "Deep recurrent Q-network with action augmentation",
        "❌ (for now)",
        f"{_RC}.rl_papers:ActionAugmentedDRQN",
    ),
    _e(
        "C-RL5",
        "Direct reinforcement with a risk-adjusted online reward",
        "❌ (for now)",
        f"{_RC}.rl_papers:RRLTrader",
        f"{_RC}.rl_papers:differential_sharpe",
    ),
    _e("C-S2", "Kelly and fractional Kelly", "🧪", f"{_RS}.position_sizing:kelly_portfolio"),
    _e(
        "C-S4",
        "Inventory-capped inverse-exposure sizing",
        "🧪",
        f"{_RS}.inventory_control:inventory_capped_lot",
    ),
    _e(
        "C-X2",
        "Time-limit and end-of-day exits",
        "⛔ (loss-realizing) · 🧪 (profit-only)",
        "research.strategies.grid_lifecycle:profit_only_time_exits",
        f"{_RC}.trend_following:orb_trade",
        note="The loss-realizing form is the session-close exit inside orb_trade and the je-suis-tm session trades.",
    ),
    _e(
        "C-X4",
        "Session caps and cooldowns on new lots",
        "🧪",
        f"{_RS}.intraday_gates:SessionLotThrottle",
    ),
    _e("C-MS1", "Order-flow imbalance (OFI)", "🧪 (needs L1)", f"{_RS}.microstructure:ofi"),
    _e(
        "C-MS2",
        "Order-book imbalance and micro-price",
        "🧪 (needs L2)",
        f"{_RS}.microstructure:micro_price",
        f"{_RS}.microstructure:depth_imbalance",
    ),
    _e("C-MS3", "VWAP-relative gating", "🧪", f"{_RS}.intraday_gates:VwapGate"),
    _e(
        "C-MS5",
        "Bar-only microstructure proxies",
        "🧪",
        f"{_RS}.microstructure:roll_spread",
        f"{_RS}.microstructure:corwin_schultz",
        f"{_RS}.microstructure:amihud_illiquidity",
    ),
    _e(
        "C-MS6",
        "Leveraged-ETF end-of-day rebalancing flow",
        "🧪",
        f"{_RS}.microstructure:letf_rebalance_demand",
    ),
    _e(
        "C-MS7",
        "Market profile and volume profile",
        "🧪",
        f"{_RS}.microstructure:volume_profile",
        f"{_RS}.microstructure:value_area",
    ),
    _e(
        "C-E2",
        "Tactical asset allocation with MA filters",
        "🧪",
        f"{_RS}.tactical_allocation:faber_targets",
    ),
    _e(
        "C-E4",
        "Regime-aware risk for concentrated mega-cap exposure",
        "⏳ (unverified)",
        note=(
            "The catalog could not verify the source's method; the regime pieces it would use "
            "already exist (C-R3, A2, N5)."
        ),
    ),
    _e(
        "C-RJ1",
        "Dealer gamma-imbalance signals",
        "⛔",
        f"{_RC}.options:gamma_exposure",
        f"{_RC}.options:gamma_flip",
    ),
    _e(
        "C-RJ2",
        "Funding-rate arbitrage",
        "❌",
        f"{_RC}.crypto:funding_carry_positions",
        f"{_RC}.crypto:funding_carry_pnl",
    ),
    _e(
        "C-RJ3",
        "Martingale / averaging-down sizing",
        "❌",
        f"{_RC}.excluded:martingale_path",
        f"{_RC}.excluded:martingale_ruin_probability",
    ),
    _e(
        "C-RJ4",
        "18 deep sequence forecasters and stacked ensembles",
        "❌",
        f"{_RC}.forecasting:LSTMForecaster",
        f"{_RC}.forecasting:stack_forecasts",
    ),
    _e("C-RJ5", "Ghost Trader", "❌", f"{_RC}.trend_following:ghost_trader"),
    _e(
        "C-RJ6",
        "Index/ETF creation-redemption arbitrage",
        "⛔",
        f"{_RC}.excluded:creation_redemption_action",
    ),
    _e(
        "C-RJ7",
        "LLM agent frameworks (TradingAgents, FinRobot and similar)",
        "❌",
        note="Frameworks that prompt language models, not trading algorithms; nothing to transcribe.",
    ),
    _e(
        "C-RJ8",
        "Novelty strategies (tweet-driven trading, lottery prediction)",
        "❌",
        note="No algorithm with a verifiable definition behind either; recorded only.",
    ),
)

REGISTRY: dict[str, Entry] = {e.ledger_id: e for e in ENTRIES}

# catalog record -> ledger entries it was folded into (ledger section 8A)
CATALOG_ALIASES: dict[str, tuple[str, ...]] = {
    "MR3": ("Q2", "X3"),
    "MR5": ("Q9", "X4"),
    "MR6": ("V3", "Q10"),
    "MR8": ("A6",),
    "M3": ("X1",),
    "M4": ("Q7", "N1"),
    "M5": ("Q4", "N2", "N3"),
    "M6": ("Q8",),
    "M7": ("Q3",),
    "M8": ("Q1", "Q5"),
    "G1": ("V5",),
    "R1": ("V16",),
    "R2": ("A2",),
    "R4": ("V17", "N5", "V7", "V12"),
    "R5": ("V11",),
    "R6": ("A3",),
    "ML2": ("V13",),
    "ML6": ("V13", "V14"),
    "RL1": ("A1", "A2"),
    "RL2": ("A1",),
    "RL3": ("A4",),
    "RL6": ("A1",),
    "S1": ("S4", "V18"),
    "S3": ("V11", "S4"),
    "S5": ("V13",),
    "S6": ("A5",),
    "X1": ("N6",),
    "X3": ("V10",),
    "MS4": ("V9",),
    "E1": ("N7", "X2"),
    "E3": ("X3",),
}

# catalog variants built alongside the entries above (the ledger's "Built:" notes)
CATALOG_VARIANTS: dict[str, tuple[str, ...]] = {
    "MR3 Kalman hedge ratio": (f"{_RS}.pairs:KalmanHedgeRatio", f"{_RS}.pairs:spread_long_signal"),
    "M6 profit-only PSAR exit": ("research.strategies.grid_lifecycle:psar_profit_exits",),
    "R4 VIX bands": (f"{_RS}.vix_bands:vix_band",),
    "R5/S3 drawdown ladder": (f"{_RS}.position_sizing:DrawdownLadder",),
    "S5 bet sizing and conformal": (
        f"{_RS}.position_sizing:bet_size_from_probability",
        f"{_RS}.position_sizing:conformal_long_size",
    ),
    "R2 causal turbulence": (f"{_RS}.regime_models:causal_turbulence",),
}

# gap-analysis leads (no ledger ID)
LEADS: dict[str, tuple[str, ...]] = {
    "HAR-type realized-volatility forecasting": (
        f"{_RC}.leads:fit_har",
        f"{_RC}.leads:har_forecast",
    ),
    "VIX term structure as a data-only regime input": (f"{_RC}.leads:vix_term_structure_regime",),
    "Drawdown-constrained investing and CPPI (Grossman & Zhou)": (
        f"{_RC}.leads:cppi_path",
        f"{_RC}.leads:grossman_zhou_multiplier",
    ),
    "Nasdaq-100 futures -> ETF lead-lag": (
        f"{_RC}.leads:lagged_cross_correlation",
        f"{_RC}.leads:hy_lead_lag",
    ),
    "Online mean-reversion portfolios (OLMAR/PAMR)": (
        f"{_RC}.leads:olmar_weights",
        f"{_RC}.leads:pamr_weights",
    ),
    "MacroHFT, IMM, LLM crash detection": (),
    "Cartea-Jaimungal-Penalva; Gueant market-liquidity books": (
        f"{_RC}.leads:almgren_chriss",
        "research.strategies.inventory_control:as_quotes",
        "research.strategies.inventory_control:glft_quotes",
    ),
    "Intraday periodicity; overnight vs intraday returns": (
        f"{_RC}.leads:same_interval_signal",
        f"{_RC}.leads:overnight_intraday",
    ),
}

LEAD_NOTES: dict[str, str] = {
    "MacroHFT, IMM, LLM crash detection": (
        "Listed in Awesome-AI-in-Finance but never opened by the catalog; MacroHFT and IMM are "
        "deep RL market makers whose published code depends on their own training stacks. The RL "
        "building blocks here (rl_agents, rl_papers) cover their update rules."
    ),
}


def resolve(ref: str):
    """Import a 'module:qualname' or 'module' reference; path references
    (tools/..., engine/...py) are returned unchanged."""
    if ref.endswith(".py"):
        return ref
    module, _, qual = ref.partition(":")
    obj = importlib.import_module(module)
    for part in qual.split(".") if qual else ():
        obj = getattr(obj, part)
    return obj


def implementations(ledger_id: str) -> list:
    """The resolved implementation objects (or paths) for a ledger ID."""
    return [resolve(r) for r in REGISTRY[ledger_id].implementations]
