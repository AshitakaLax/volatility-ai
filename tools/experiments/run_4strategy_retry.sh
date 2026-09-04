#!/usr/bin/env bash
set -u

VENV="C:/workspace/volatility-ai/.venv/Scripts/python.exe"
DATA="data/TQQQ_1Min_sip_all_2016-01-01_2026-08-21.csv"
LOG="output/4strategy_retry_$(date +%Y%m%d_%H%M).log"

say() {
    echo "" | tee -a "$LOG"
    echo "### $(date '+%H:%M:%S')  $*" | tee -a "$LOG"
}

echo "===== RETRY: STRATEGIES 1-4 =====" > "$LOG"
echo "Started: $(date)" >> "$LOG"
echo "Data: $DATA" >> "$LOG"
echo "" >> "$LOG"

say "STRATEGY 1/4: FIXED (4x4x3=48 combos)"
python cli.py backtest \
    --config config/sweep_fixed_comparative.yaml \
    --data "$DATA" \
    --output output/sweep_fixed_comparative.csv \
    >> "$LOG" 2>&1

say "STRATEGY 2/4: BELL_CURVE (3x3x3x3x3=243 combos)"
python cli.py backtest \
    --config config/sweep_bell_curve_comparative.yaml \
    --data "$DATA" \
    --output output/sweep_bell_curve_comparative.csv \
    >> "$LOG" 2>&1

say "STRATEGY 3/4: RSI (3x3x3x3x3=243 combos)"
python cli.py backtest \
    --config config/sweep_rsi_comparative.yaml \
    --data "$DATA" \
    --output output/sweep_rsi_comparative.csv \
    >> "$LOG" 2>&1

say "STRATEGY 4/4: BAYESIAN_DUAL_SCALE (TPE search, 200 trials)"
python cli.py search \
    --config config/sweep_bayesian_dual_scale_comparative.yaml \
    --data "$DATA" \
    --trials 200 \
    --output output/sweep_bayesian_dual_scale_comparative.csv \
    >> "$LOG" 2>&1

say "===== RETRY COMPLETE ====="
echo "" | tee -a "$LOG"
echo "Completed at: $(date)" | tee -a "$LOG"
