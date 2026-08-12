# Secret and credential policy

Backtest and experiment configuration is reproducible data and must not contain broker credentials or other secrets.

For Alpaca live trading, supply credentials through the environment or an approved secret store using:

- `APCA_API_KEY_ID`
- `APCA_API_SECRET_KEY`

The runtime secret boundary is `src.secrets.load_live_credentials()`. It fails closed when either required credential is absent. `LiveCredentials` is intentionally separate from `BacktestConfig` and redacts its representation.

Use `src.secrets.redact_secrets()` before serializing untrusted configuration-shaped payloads to logs or artifacts. Secret values must not appear in YAML/JSON configuration, command-line arguments, source control, artifact snapshots, audit payloads, exception messages, or structured logs.

A backtest artifact can therefore be persisted without broker credentials. Live startup must validate credentials before attempting a broker/WebSocket connection; the repository currently has no confirmed live-startup entry point, so that startup integration remains a prerequisite-boundary item rather than being invented here.
