# research/ — Algorithm Development

**Generated:** 2026-09-24T02:20:00Z — score 12 (distinct domain)

## OVERVIEW
Strategies, sweep/search orchestration, metrics, ML. Imports `engine` only.

## STRUCTURE
```
research/
├── strategies/   # size_calculators, high_frequency_sizing, bayesian_sizing, sizing_indicators, indicator_library, strategy_registry
├── optimization/ # optimization_controller, search_strategies (grid/bayesian/random), walk_forward, monte_carlo, intraday_validation
├── analysis/     # performance_analyzer, analyze_annual
├── ml/           # features, labels, rolling (IncrementalBarFeatures), reachability_sizing — read-only research
├── run_hf_sweep.py
└── tests/        # regression_baseline, hf_sizing, search
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Add strategy | `strategies/strategy_registry.py` | Map `strategy_id` → class; `BacktestConfig` never resolves |
| HF sizing | `strategies/high_frequency_sizing.py` | `per_lot_pct`, `vol_scale`, `event_day_boost` |
| Sweep | `optimization/optimization_controller.py` | `_simulate_single` per combo; `result_sink` Protocol |
| Search | `optimization/search_strategies.py` | Grid / Bayesian (Optuna) / Random |
| Validation | `optimization/walk_forward.py`, `monte_carlo.py` | Train/test prefixes; block-bootstrap |
| Regime ML | `ml/regime_scaled_sizing.py`, `qlib_regime.py` | Not default trading input |
| Parallel driver | `run_hf_sweep.py` | `--n-jobs`, checkpointed CSV, `--max-drawdown` penalty |

## CONVENTIONS
- `record_tick` every bar, `calculate_trade_value` on trigger only — accumulate state in former or get sparse biased sample.
- Causal only: `ml/rolling.py` trailing + shift; `ml/features.py` offline must agree with incremental by construction.
- `cli.py backtest/search` read warehouse by `backtest.symbol`; no `--data` flag. Ingest via `tools/build_warehouse.py`.

## ANTI-PATTERNS
- Never reimplement no-loss guard; test scans `engine/`+`research/` for duplicate.
- Never touch no-loss comparison via `SizingStrategy.adjust_profit_target` — guard rejects independently.
- Don't add result column without updating `test_regression_baseline.py` deliberately.
