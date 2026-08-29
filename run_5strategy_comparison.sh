#!/usr/bin/env bash
set -u

VENV="C:/workspace/volatility-ai/.venv/Scripts/python.exe"
DATA="data/TQQQ_1Min_sip_all_2016-01-01_2026-08-21.csv"
LOG="output/5strategy_$(date +%Y%m%d_%H%M).log"

say() {
    echo "" | tee -a "$LOG"
    echo "### $(date '+%H:%M:%S')  $*" | tee -a "$LOG"
}

echo "===== 5-STRATEGY COMPARATIVE SWEEP =====" > "$LOG"
echo "Started: $(date)" >> "$LOG"
echo "Data: $DATA" >> "$LOG"
echo "" >> "$LOG"

say "STRATEGY 1/5: FIXED (4x4x3=48 combos)"
python cli.py backtest \
    --config config/sweep_fixed_comparative.yaml \
    --data "$DATA" \
    --output output/sweep_fixed_comparative.csv \
    >> "$LOG" 2>&1

say "STRATEGY 2/5: BELL_CURVE (3x3x3x3x3=243 combos, exhaustive)"
python cli.py backtest \
    --config config/sweep_bell_curve_comparative.yaml \
    --data "$DATA" \
    --output output/sweep_bell_curve_comparative.csv \
    >> "$LOG" 2>&1

say "STRATEGY 3/5: RSI (3x3x3x3x3=243 combos, exhaustive)"
python cli.py backtest \
    --config config/sweep_rsi_comparative.yaml \
    --data "$DATA" \
    --output output/sweep_rsi_comparative.csv \
    >> "$LOG" 2>&1

say "STRATEGY 4/5: BAYESIAN_DUAL_SCALE (TPE search, 200 trials)"
python cli.py search \
    --config config/sweep_bayesian_dual_scale_comparative.yaml \
    --data "$DATA" \
    --trials 200 \
    --output output/sweep_bayesian_dual_scale_comparative.csv \
    >> "$LOG" 2>&1

say "STRATEGY 5/5: HF_LOCAL_REFERENCE (2x3x3=18 combos, exhaustive)"
"$VENV" run_hf_sweep.py \
    --config config/sweep_hf_comparative.yaml \
    --search grid \
    --n-jobs 4 \
    --output output/sweep_hf_comparative.csv \
    >> "$LOG" 2>&1

say "===== COMPARISON ANALYSIS ====="

say "Generating comparative summary..."
python << 'PYTHON_EOF'
import csv
import os
from pathlib import Path

output_dir = Path("output")
sweep_files = [
    "sweep_fixed_comparative.csv",
    "sweep_bell_curve_comparative.csv",
    "sweep_rsi_comparative.csv",
    "sweep_bayesian_dual_scale_comparative.csv",
    "sweep_hf_comparative.csv",
]

print("\n" + "="*90)
print("5-STRATEGY SWEEP RESULTS")
print("="*90)

strategy_names = {
    "sweep_fixed_comparative.csv": "FIXED",
    "sweep_bell_curve_comparative.csv": "BELL_CURVE",
    "sweep_rsi_comparative.csv": "RSI",
    "sweep_bayesian_dual_scale_comparative.csv": "BAYESIAN_DUAL_SCALE",
    "sweep_hf_comparative.csv": "HF_LOCAL_REFERENCE",
}

for fname in sweep_files:
    fpath = output_dir / fname
    if not fpath.exists():
        print(f"\n{strategy_names[fname]}: NOT YET COMPLETE")
        continue

    with open(fpath) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        print(f"\n{strategy_names[fname]}: EMPTY RESULTS")
        continue

    best = max(rows, key=lambda r: float(r.get("CAGR %", r.get("Total Return %", "0"))))
    cagr = float(best.get("CAGR %", best.get("Total Return %", "0")))
    dd = float(best.get("Max Drawdown %", "N/A"))
    trades = int(best.get("Trade Count", 0))
    ret = float(best.get("Total Return %", 0))

    print(f"\n{strategy_names[fname]}")
    print(f"  Best Config CAGR: {cagr:.2f}%")
    print(f"  Max Drawdown:     {dd:.2f}%")
    print(f"  Trade Count:      {trades:,}")
    print(f"  Total Return:     {ret:.2f}%")
    print(f"  Rows Generated:   {len(rows)}")

print("\n" + "="*90)
PYTHON_EOF

say "===== 5-STRATEGY SWEEP COMPLETE ====="
echo "" | tee -a "$LOG"
echo "Results logged to: $LOG" | tee -a "$LOG"
echo "Data files:" | tee -a "$LOG"
ls -lh output/sweep_*_comparative.csv 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}' | tee -a "$LOG"
