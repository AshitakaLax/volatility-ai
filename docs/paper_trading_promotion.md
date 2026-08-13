# Paper-trading promotion gate

Live capital is a separate promotion stage. A backtest or walk-forward result does not directly authorize live capital.

## Required path

1. Complete the backtest sweep and record its immutable experiment/deployment provenance.
2. Preferably complete walk-forward validation before paper promotion.
3. Run the selected parameter set against Alpaca paper trading for the configured minimum duration and decision/fill counts.
4. Record a `PaperTradingResult` and evaluate it with `PromotionGate`.
5. Record the returned promotion ID and gate result in the deployment/promotion artifact.
6. Only after the gate passes may `LiveConfig(paper_trading=False)` be used.

## Mandatory machine-checkable promotion criteria

The promotion artifact must record explicit thresholds for:

- minimum paper-trading duration;
- minimum strategy decisions;
- minimum fills;
- zero accounting discrepancies;
- zero duplicate-order incidents;
- zero no-loss guard violations;
- no unresolved reconciliation state;
- zero unhandled runtime exceptions.

The values must not be inferred from operator judgment.

## Runtime enforcement

`LiveExecutionLoop` requires a passed `PromotionGate` whenever `live.enabled=True` and `live.paper_trading=False`. Therefore a normal live-capital code path cannot be entered merely by changing a configuration flag from paper mode to live mode.

Paper trading itself uses the same live execution decision path; the distinction is the deployment endpoint/capital mode. The current repository does not claim an Alpaca paper endpoint implementation unless an actual broker adapter is supplied.

## No-loss and operational requirements

Promotion does not override the no-loss invariant. Any accounting discrepancy, duplicate-order incident, no-loss violation, unresolved reconciliation, or unhandled runtime exception fails promotion. The promotion record must be retained with the deployment artifact for auditability.
