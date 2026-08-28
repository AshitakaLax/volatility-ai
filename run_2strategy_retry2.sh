#!/usr/bin/env bash
set -u

DATA="data/TQQQ_1Min_sip_all_2016-01-01_2026-08-21.csv"
LOG="output/2strategy_retry2_$(date +%Y%m%d_%H%M).log"

say() {
    echo "" | tee -a "$LOG"
    echo "### $(date '+%H:%M:%S')  $*" | tee -a "$LOG"
}

echo "===== RETRY 2: RSI + BAYESIAN =====" > "$LOG"
echo "Started: $(date)" >> "$LOG"
echo "" >> "$LOG"

say "RSI (3x3x3x3x3=243 combos) -- fixed aggression_factor range to [0,1]"
python cli.py backtest \
    --config config/sweep_rsi_comparative.yaml \
    --data "$DATA" \
    --output output/sweep_rsi_comparative.csv \
    >> "$LOG" 2>&1

say "BAYESIAN_DUAL_SCALE (TPE search, 200 trials) -- optuna now installed"
python cli.py search \
    --config config/sweep_bayesian_dual_scale_comparative.yaml \
    --data "$DATA" \
    --trials 200 \
    --output output/sweep_bayesian_dual_scale_comparative.csv \
    >> "$LOG" 2>&1

say "===== RETRY 2 COMPLETE ====="
echo "Completed at: $(date)" | tee -a "$LOG"
