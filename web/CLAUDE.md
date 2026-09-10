# web/

React 19 + TypeScript + Tailwind v4 + shadcn/ui frontend for `server/`'s
FastAPI backend. Vite dev server + vitest.

```bash
cd web
npm install
npm run dev          # http://127.0.0.1:5173, proxies /api (incl. ws:true) to :8000
npm run typecheck     # tsc -b --noEmit
npm run lint          # eslint . --max-warnings 0
npm run test          # vitest run
npm run build          # tsc -b && vite build -> dist/ (mounted by server/app.py in prod)
```

## Structure

```
src/
├── App.tsx                # tab shell: "backtest" | "live" | "ml" — that order is deliberate
├── components/
│   ├── backtest/          # ParameterForm, SweepMatrix, BacktestChart, RunHistory, ActiveRuns, ...
│   ├── live/               # CommandCenter, DeploymentHealth, LiveOrderLedger, AlgorithmStatus
│   ├── ml/                 # ModelInsights — reads server/ml_insights.py's read-only artifacts
│   └── ui/primitives.tsx  # shadcn/ui-style primitives
├── hooks/                  # useBacktestRun, useLiveState, usePriceBars, useWebSocket
├── lib/api.ts               # typed fetch wrappers — see below
├── lib/filters.ts, utils.ts # + their own .test.ts (vitest)
└── types/                   # backtest.ts, ml.ts, telemetry.ts — the contract with server/
```

## Conventions worth knowing before editing

- **`@/...` import alias** resolves to `src/` (`vite.config.ts` +
  `tsconfig.app.json`), required because shadcn/ui-generated code emits
  imports in that form — not optional style.
- **No base URL in `lib/api.ts`.** Everything goes through the Vite proxy
  in dev and the same-origin mount in prod, on purpose: introducing a base
  URL would make dev and prod differ exactly the way CORS bugs hide in.
  Don't add one to point at a different host — extend the proxy instead.
- **Dev server binds `127.0.0.1`, not `0.0.0.0`.** This UI renders account
  balances and positions; widening the bind is a deliberate act, matching
  `server/`'s own loopback default. Same reasoning, don't decouple them.
- **`/api` proxy carries `ws: true`.** Sockets live *under* `/api`
  (`/api/live/ws`, `/api/backtest/ws/{id}`), not at a separate `/ws` path —
  a naive separate proxy entry would 404 on the upgrade in a way that
  looks like a dead server, not a routing miss.
- Types in `types/*.ts` mirror `server/`'s response shapes by hand — there
  is no shared schema generation, so a backend field rename needs a
  matching edit here.
