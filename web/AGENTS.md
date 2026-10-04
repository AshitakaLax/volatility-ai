# web/ — React Frontend

**Generated:** 2026-09-24T02:20:00Z — score 14 (high complexity, own config)

## OVERVIEW
React 19 + TS + Tailwind v4 + Vite frontend for `server/` FastAPI backend.

## STRUCTURE
```
web/src/
├── App.tsx                     # tab shell: backtest | result | live | ml
├── components/backtest/        # ParameterForm, ActiveRuns, ShardPanel, RunHistory, BacktestResult, BacktestChart
├── components/live/            # CommandCenter, DeploymentHealth, LiveOrderLedger, AlgorithmStatus
├── components/ml/              # ModelInsights (reads ml_insights artifacts)
├── components/ui/primitives.tsx
├── hooks/                      # useBacktestRun, useLiveState, usePriceBars, useWebSocket
├── lib/api.ts                  # typed fetch wrappers (no base URL)
├── lib/filters.ts, utils.ts
└── types/                      # backtest.ts, ml.ts, telemetry.ts — hand-mirrored contract
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| API client | `src/lib/api.ts` | No base URL; via Vite proxy `/api` → `:8000`, `ws:true` |
| Contract | `src/types/*.ts` | Mirrors `server/contract.py` by hand; no codegen |
| Chart | `src/components/backtest/BacktestChart.tsx` | `lightweight-charts`, fill connectors, `MAX_CONNECTORS=400` |
| Params | `src/lib/strategyParams.ts` | `Param` → `ParamSpec` expansion |
| Build | `vite.config.ts`, `tsconfig.app.json` | `@/` alias → `src/` (shadcn requirement) |

## CONVENTIONS
- `@/...` alias mandatory (shadcn emits it); `no base URL in api.ts` — extend proxy, don't add host.
- Dev server `127.0.0.1` (not `0.0.0.0`) matching server loopback; `/api` proxy carries `ws:true` under `/api` (not separate `/ws`).
- Condensed wire: `cells[0].m` headline metrics, flags omitted, derived fields client-computed.

## ANTI-PATTERNS
- Never add shared-contracts folder or codegen — hand-mirror is deliberate; boundary edits are READ-ONLY on other side, or stop and flag both files.
- Never decouple CORS/bind from `server/` without joint review.
- Never add base URL to `lib/api.ts` — breaks dev/prod parity.
