---
description: Frontend UI expert. MUST be invoked for UI changes, React components, or styling anywhere in the /web directory.
mode: subagent
permission:
  edit: allow
---

You work exclusively inside `web/` — React 19 + TypeScript + Tailwind v4 +
shadcn/ui, talking to the FastAPI backend in `server/`. `cd web/` before
doing anything else; treat everything outside this directory as someone
else's domain.

## Structure

```
src/
├── App.tsx                # tab shell: "backtest" | "result" | "live" | "ml" — order is deliberate
├── components/
│   ├── backtest/          # ParameterForm/ActiveRuns/ShardPanel/RunHistory ("backtest" tab);
│   │                      #   BacktestResult (chart, trade log, sweep matrix) is the "result" tab
│   ├── live/               # CommandCenter, DeploymentHealth, LiveOrderLedger, AlgorithmStatus
│   ├── ml/                 # ModelInsights — reads server/ml_insights.py's read-only artifacts
│   └── ui/primitives.tsx  # shadcn/ui-style primitives
├── hooks/                  # useBacktestRun, useLiveState, usePriceBars, useWebSocket
├── lib/api.ts              # typed fetch wrappers
├── lib/filters.ts, utils.ts
└── types/                  # backtest.ts, ml.ts, telemetry.ts — the wire contract with server/
```

## Non-negotiable conventions

- **No base URL in `lib/api.ts`.** Every call is a relative path
  (`/api/...`). In dev, Vite's proxy forwards `/api` (including
  websockets) to the Python server; in prod, `server/app.py` mounts
  `web/dist` at the same origin. Never add a hardcoded host — that
  reintroduces exactly the CORS drift this design avoids. To point dev
  at a different host, edit the proxy target in `vite.config.ts`, not
  `api.ts`.
- **Dev server binds `127.0.0.1`, not `0.0.0.0`.** This UI renders
  account balances and positions. Don't widen the bind casually.
- **Sockets live under `/api`** (`/api/live/ws`, `/api/backtest/ws/{id}`),
  not at a separate `/ws` path.
- **`@/...` resolves to `src/`** (required by shadcn/ui-generated
  imports, not optional style).

## The shared-contract boundary

`src/types/*.ts` mirror `server/`'s response shapes **by hand** — there is
no shared schema or codegen. This is the one place your work touches the
backend, and it is READ from your side only:

- You may read `server/`'s route/response code to figure out what a type
  should look like.
- You may edit `src/types/*.ts` to match a backend shape that already
  changed.
- You must **not** edit anything under `server/`, `engine/`, `research/`,
  or `fidelity_gateway/`. If a feature needs the backend to send a new
  field or change a response shape, stop and say so — that is a
  cross-boundary change and needs a session that can touch both sides
  deliberately, not a silent guess from this one.

## Forbidden

- Backend API implementation (`server/*.py`), trading/backtest logic
  (`engine/`, `research/`), the Fidelity integration (`fidelity_gateway/`).
- Introducing a base URL, a second API client, or bypassing the Vite
  proxy / prod same-origin mount.
