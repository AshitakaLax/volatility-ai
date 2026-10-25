# Changelog

## The bridge sends notifications to a phone

**Nothing told you when the engine bought, sold or stopped, or that the
connection would not be ready for the open,** unless you were at the
computer: the Live page, the extension's popup and the logs all live there.
- **The bridge host now tells apps what it sees, as it happens.**
  `fidelity_gateway/bridge/notifications.py` turns each event into a
  notification of one kind:
  - a fill (`buy`, `sell`), from the extension's order reports, and a
    rejected, refused or unknown order (`order_problem`);
  - a trader's engine changing state (`engine`), a second trader refused or
    a session ending without saying it stopped (`session`);
  - not ready to trade, and the one thing to fix; not ready 15 minutes
    before an open; ready again (`readiness`);
  - a Fidelity sign-out (`fidelity_signin`), a failed account check
    (`account_check`), the extension coming and going (`connected`,
    `disconnected`), its "Allow trading" switch (`trading_switch`), a
    refused connection (`refused`), the bridge's own port (`bridge`).

  `live.fidelity.bridge.notifications.events` chooses which are sent.
  Accepted, cancelled and expired orders (`order_update`) are off by default.
- **From the always-on `fidelity-bridge` service, not the session.** A
  session's bridge now attaches to the host and lives only as long as the
  session, so the host owns the apps' hub and listener: a phone stays
  connected overnight, a bridge the host restarts with new settings keeps
  the apps' stream, and an edit to the notifications alone restarts only
  their listener. One that cannot start (no key, a taken port) is reported
  and retried; a phone never stops the bridge.
- **On a listener of its own.** Its own port (8766), address lists and key,
  `FIDELITY_BRIDGE_NOTIFY_KEY` (`keygen --notify`); the extension's key is
  refused there. Read-only: an app can ask for a test notification and
  nothing else.
- **The same protocol design as the extension's.** `fidelity-bridge-notify/v1`
  uses HMAC proofs both ways, so the key never crosses the wire. Every frame
  after the handshake is sealed, so on a plain `ws://` LAN nobody can forge
  a "Sold" notification.
- **An app that was away catches up.** Notifications are numbered within a
  stream that is new each host run, and the last 200 are kept. A
  reconnecting app is sent exactly what it missed, and is shown the host's
  readiness checklist, what is attached, the last account check and the
  next open.
- **Only news.**
  - An engine's state when it changes, never the host's standby status.
  - The trading switch when it flips; a sign-out once, not again at every
    reconnect; a refusal once per address and reason per 10 minutes.
  - Not ready only after a minute, and not again for a cause its own kind
    already said.
  - An order the extension's resent log mentions, which this bridge never
    heard of, is history unless it changed after the host started.
- **`fidelity-bridge-notifier-android/`** is the app: Kotlin, minSdk 26,
  kept as if it were its own repository. Its `core/` (the protocol, and the
  client on OkHttp) is a separate Gradle build that tests without the
  Android SDK. Its `PROTOCOL.md` is the spec. Its protocol vectors, and the
  list of kinds, are reproduced by
  `fidelity_gateway/tests/test_bridge_notify_protocol.py`.
- **A published release carries the APK.** `.github/workflows/android.yml`
  builds the app on a pull request that touches it, and attaches the APK
  to each published release. The APK is signed with the owner's key, from
  the repository's secrets. A phone installs an update only when it is
  signed with the same key, and a CI runner's debug key is new every
  build. So without the secrets the release gets the debug APK with a
  warning, rather than nothing. The upload runs in a job of its own, the
  only one that can write to the repository, and it runs no build code.

## The Fidelity connection stays up, says whether it is ready, and explains its disconnects

**Fidelity traded nothing on 10-22 or 10-23, and neither cause reached the
Live page.** On 10-22 the extension never connected; on 10-23 a bridge and a
trading loop started by hand held port 8765 all day and the container's
trader failed 65 times on "Address already in use". Both days the page said
"between sessions": the trader's status read "see the engine's log", and
five fast failures spent the supervisor's restart cap before a 15-minute
wait. The bridge lived inside each session's `cli.py live`, so nothing
listened between sessions, every failed start dropped the extension, and
anything else that wanted the port fought the trader for it.
- **The bridge is a service of its own** (`fidelity_gateway/bridge/host.py`,
  compose `fidelity-bridge`), up for the deployment's life. The extension
  connects once and stays connected; recreating the trader does not drop it.
  Each session's loop attaches over a Unix socket only the two Fidelity
  services mount (`bridge/attach.py`; `open_bridge()` attaches whenever
  `VAI_BRIDGE_SOCKET` is set) and is handed what the extension already said
  -- its headers, tab, switches and order log -- so it connects in seconds.
  Errors keep their meaning across the link: an order is ambiguous exactly
  when it was before. One process attaches at a time, and a second is told
  which holds it.
- **Ready, or the one thing to fix** (`bridge/readiness.py`): listening; the
  extension connected and heard from in the last minute; its version; the
  Fidelity tab signed in (new: from its `tab` events); "Allow trading" on;
  the last account check. The supervisor starts a Fidelity session only once
  it is ready ("Waiting for Fidelity", with why). `check_connection` from
  the page, and the bridge by itself 30 and 10 minutes before each open,
  reads the account through the extension, read-only.
- **Every failure says why.** `RuntimeLifecycle` keeps the stage and reason
  a start stopped with, and the trader's status carries it. A start that
  could not reach the broker for a reason that clears by itself (a
  `BrokerUnavailableError`: no extension, signed out, the port taken) exits
  3, and the supervisor retries it every minute instead of counting a crash.
  The bridge names a taken port, an address it turned away and a key that
  did not match (`last_refused`), and how each connection ended.
- **The bridge journals its connection** (`bridge/events/`, 14 days):
  connects, disconnects with their close codes, refusals, sign-ins and
  sign-outs, the trading switch, attaches, verdicts, checks.
- **The Live page's Fidelity section** is built on it: one verdict ("Ready
  for Mon 09:30 ET", "Not ready: Fidelity tab"), the chain Bridge ->
  Extension -> Fidelity tab -> Allow trading -> Trader -> Account check with
  the first broken link's fix, what is running, Check connection, and a
  48-hour timeline that says how long each disconnect lasted.
- **An algorithm is described by what it does**
  (`live_algorithm.algorithm_summary`), on the page and in the extension:
  `ultimate_rsp` as a regime-timed book rebalanced at minute 60, not "target
  1000%" -- a target set out of reach on purpose.
- **The extension (0.7.0)** shows "Standing by: ready / not ready" with the
  next open, the deployment and the algorithm's summary; logs Fidelity's
  overnight sign-out without a toast while standing by, and toasts "Not
  ready for the open" instead when an open is near. 0.6.0 still works.

## The warehouse is kept current daily, and three index funds join it

**Its bars had stopped on 2026-10-08**, nine sessions behind, and two of
the funds it listed (URSP, XBI) had none. Adding bars was a manual fetch to
CSV, then an ingest that APPENDs.
- **That path had already left a step in six funds.** Their bars to
  August were adjusted for the dividends paid before that download, and an
  increment fetched in October was adjusted for September's too. Asked for
  again, Alpaca's 2016 bars differed from the stored ones by 0.07% (SOXL)
  to 1.4% (SQQQ). A backtest saw a fake drop of that size where the two
  met.
- **`tools/refresh_warehouse.py`** asks Alpaca for each fund's oldest
  stored session again. If it moved, a dividend or split has happened, and
  the whole history is downloaded again rather than appended to. Otherwise
  it adds the new sessions and re-checks the last three, which picks up the
  tape's late volume corrections (seen on 0.3% of a session's bars). A
  re-download that lacks any stored session is refused. URSP_SIM gains
  URSP's new daily bars drawn on that day's RSP minutes, and is rebuilt as
  `simulate_ursp.py` builds it if URSP's adjusted prices moved.
- **It writes the bar lake directly** (`engine/warehouse/lake.py`), never
  the catalog the server records sweeps in. Each year is one file, swapped
  in with renameat2's RENAME_EXCHANGE, and a whole fund in one exchange of
  its directory, so a backtest never reads half of an update.
- **The compose `market-data` service** runs it at start and daily at
  20:30 Eastern, after the extended session and SIP's 15-minute delay; a
  failed run is retried hourly. It shares the traders' Alpaca key, so it
  asks at most about once a second, a month of one fund at a time.

**SPY, IWM and EEM** (S&P 500, Russell 2000, MSCI Emerging Markets: index
funds trading since 1993, 2000 and 2003) are tracked with pre- and
after-market bars, from 2016, where Alpaca's minutes begin.
- **A regular-session strategy now backtests on the regular session.**
  The Ultimate family declares `regular_session_only`, and the live loop
  already refused it extended hours; a backtest fed it every bar of SQQQ.
  `strategy_registry.session_bars` gives it the regular session's alone, in
  the server and in `cli.py backtest`.
- **The brute-force campaign covers them** (`tools/sweep_brute_force.py
  --fund SPY IWM EEM`): every strategy that is not bound to an RSP model,
  with each fund's own minutes per session for the grid strategies, which
  trade every bar.
- **Its runs go to the shards.** The tool queued every run `local_only`,
  so a connected `cli.py shard` sat idle; that is now `--local-only`, asked
  for. A shard runs its own checkout's engine, so it must be on the
  server's commit for its results to be this code's.

## Ultimate-RSP can trade live

**`ultimate_rsp` was backtest-only.** It seeds its votes from session
history (`warm_up`). The live loop starts a fresh process every session and
could not rebuild that, so `live_algorithm.check_live_support` refused it.
- **It now answers `live_history_sessions()`:** every vote's history plus
  150 sessions for PLUS_DM's and ADOSC's seeds to settle, replayed through
  `record_tick` like the Ultimate's regime. A PLUS_DM value exists from
  session p - 1 and an ADOSC from slow - 1, and a vote then needs `lb` of
  them. The replay hands it no equity, so no replayed bar rebalances.
- **It is regular-session-only**, as the Ultimate is.
- **`ultimate_ursp` inherits it**, and counts its bear window when that is
  the longer history.
- **On the live feed:** from a cold start on IEX minute bars, its target
  matched the SIP backtest's on 65% of sessions over 2025-07..2026-10,
  with a mean difference of 0.025 of equity and 123 rebalances against 117.

## Fix: the RSP regime sweeps, and a run with failed configurations

**Both RSP `ml_regime_rsp` sweeps of the 2026-10 campaign failed at 100%.**
- **The thresholds:** `tools/sweep_brute_force.py` took them at the
  model's own quantiles and rounded to the nearest 4 places. This model's
  scores sit on three exact levels; its latch enters at `score >= enter`
  and leaves at `score <= exit`.
  - Rounded up, the p99 entry (0.247875 to 0.2479) sat above every score,
    and MLRegimeScaledSizing refused it. That was half of each sweep, 1,296
    configurations.
  - The p90 entry (0.238054 to 0.2381) sat above its own level, so it
    latched only at the top one.
  - The URSP_SIM sweep completed, but with the same skew.
  - Entry levels now round down and the exit rounds up, so each threshold
    fires at the level it was taken from.
- **The crash:** the refused rows' metrics are all NaN, and `fund_metrics`
  called `int()` on one, failing both runs after every configuration had
  finished. A failed configuration is now left out of the report's cells
  and logged, and a missing count reads as zero.

## Fix: a Fidelity trader's status reaches the Live page

**A Fidelity loop never reported to the Live page.** Its status named the
account twice -- the Alpaca key's tag, which `LoopControl` always wrote, and
the Fidelity account's, from `cli.py`'s `_fidelity_status` -- so every
write raised a `TypeError`, caught as "Operator control failed this tick;
trading continues". The page kept the supervisor's "starting" and, 30
minutes into a session, called a loop that was trading "not running". The
supervisor's own reports carried the Alpaca key's tag, the same one the
paper trader sharing that key reports, so the page took the two for one
account and would refuse to enable either beside the other.

**One function now decides the tag,** `operator_control.account_tag`: a
Fidelity deployment's is "fidelity-" and a hash of its account, any other's
the Alpaca key's. The loop and the supervisor (from the config it already
loads) both report it. `tests/test_cli_live_fidelity.py` now runs a
Fidelity loop with a control directory -- the way the supervisor runs it,
and the path no test had taken.

## Live page: what a deployment trades and is doing, and a Fidelity section

**The Ultimate paper trader looked broken for two sessions, and nothing on
the page could say why.** Its NATR regime turned turbulent on 2026-10-19
(TQQQ fell 19% from Oct 6 to Oct 16), so by design it made no grid buys --
but that reading lived only in the trader's log. The page also misled in
smaller ways:
- **The deployment cards showed the config file's algorithm,** not the one
  trading, so a switch from the page was invisible on them.
- **The Deployment card's build and process were the web server's,** not the
  trader's, and inside the image (no `.git`) the commit read "--" anyway.
- **The "live" chart drew warehouse bars**, which lag a running deployment
  by days (TQQQ's ended Oct 8), and its RSI came from a bar file.
- **No trades were shown:** the ledger keeps lots but never what a sale
  fetched, and the activity log route had no reader.

**The trader now says what it is doing** (`engine/trading/live_trading_loop.py`,
through its status file):
- **Every tick:** the price its next buy triggers at -- the strategy's own
  `_grid_trigger_level`, the one definition the buy uses -- or what blocks
  one (a pause, a strategy buying at no price, no buying power, the lot
  cap), with the strategy's `diagnostics()`. Ultimate's now carry its
  regime: since when, the NATR against its median at the last close, and
  the first session it may change (`IncrementalNatrRegime.describe`).
- **While an override trades,** the config file's algorithm runs beside it
  as a shadow -- the same bars, trading nothing -- and reports what
  switching back would do now. Reverting to Ultimate during a turbulent
  spell would market-sell every lot it did not buy as a reversal lot (its
  exit stays active for the whole spell); the page says so before the
  revert is sent.
- **Its journals,** in its control directory: the minute bars it traded on
  (the last sessions of its replayed history included) and every fill it
  booked, each sale with what it fetched against what its lot cost.
- **Its build:** a fingerprint of the code it loaded and, when the image was
  built with `VAI_BUILD_COMMIT`, the commit (`engine/core/build_info.py`).
  `/api/health` reports the same fingerprint, so the page can tell whether
  the trader and the web server run the same code.

**The page** (`web/src/components/live/`): an overview of the fund, its
price, the book and today's trades, with the "doing now" line; one
Algorithm card (a readable name, the grid in words, every parameter against
the config file's, the profit-target check); the chart from the trader's own
bars with its fills and the next-buy price; a trades list; the ledger's
activity; and the trader's own build on the Deployment card.

**Alpaca and Fidelity are separate sections.** A Fidelity deployment's card
and panel show the browser extension's side of the bridge
(`BridgeServer.connection_report`): connected or not and since when, when it
was last heard from, its version against the expected ones, "Allow trading"
and previews, the account's display name and the per-buy cap. Its status is
tagged with a hash of the Fidelity account, not the Alpaca key it reads
prices with, so it no longer looks like a second loop on a paper trader's
account. A deployment can be registered before its config exists
(`broker:` in `config/deployments.yaml`); the page then says how to set it
up.

**The Fidelity engine is a compose service now,** `fidelity` (profile
`fidelity`, started only by name), so the page sees it like the paper
traders: its own ledger and control volumes (`state_fidelity`,
`control_fidelity`; the backup service archives the ledger), on the host's
network so the bridge listens on this server and checks the browser's real
address. Its config is read from the host and kept out of the image
(`.dockerignore`), since it names the account. Setup: docs/DEPLOY.md,
"Fidelity".

**Started before its config exists, the service waits for it**
(`tools/docker_session_loop.sh`). The first start, before anyone had
written `config/fidelity_live.yaml`, failed a session with a traceback
every 15 minutes, which looked like a container restarting over and over.
The loop now:
- says once what it is waiting for, and starts as soon as the file
  appears;
- after a session fails, tries again as soon as the config changes, so
  fixing a mistake in a new config is not followed by a quarter-hour
  wait.

## Live deployment control

**The Live page's emergency halt did not work, in two ways.**
- **In the compose deployment it failed outright.** `server/control.py`
  opened the ledger writable, but `web` mounts the ledgers read-only.
- **Where the write did succeed, a running loop ignored it.** The loop reads
  the halt once, at startup, so it kept buying while the page said
  "halted".

There was also no way to clear a halt from the page, to stop or start a
deployment, or to change an Alpaca deployment's algorithm. Every live route
took a file path from the browser; the halt would open any writable file
as a SQLite ledger.

**Commands now go to the trading process, and it applies them.**
- The server queues a command as a file in the deployment's control volume
  (`engine/trading/control_inbox.py`).
- The trader applies it (`engine/trading/operator_control.py`) through the
  circuit breaker, algorithm and loop it trades with:
  - while trading, the loop applies it between ticks, so a pause lands
    before the next buy decision;
  - between sessions, the supervisor applies it within 15 s, under the
    ledger's own lock.
- Every command is answered (applied, rejected with the reason, superseded,
  expired, cancelled), and the directory is the audit trail. The trader
  stays the only writer of its ledger.

**What the page offers:**
- **Every deployment, by id** (`config/deployments.yaml`), with the state
  its trader reports. A report that stops arriving reads "Not running".
- **Buying:** pause and resume. Resuming can re-base the drawdown, so a
  drawdown halt does not trip again on the next tick.
- **Trading on or off:** wind down (pause buys, stop once flat), disable,
  enable.
- **The algorithm:** switch, revert to the config file's, and re-warm. A
  switch goes through the extension's validation, override file and
  rebuild, which `AlgorithmControl` now offers to every broker with one
  grant per channel. It takes effect at the next tick, at the next session,
  or once the book is flat. A dry-run check shows what it would do to the
  open lots.
- **A fresh paper ledger:** the old one is archived, not deleted. Only while
  disabled, on paper, with the Alpaca account flat.
- **Profiles:** committed algorithms in `config/live_profiles/`. A backtest
  result can propose one ("Copy as live profile"); `config/` stays
  read-only to the server, so a commit decides.

**Safety:**
- **The config decides what the page may do.** Each deployment's
  `live.control` grants it, and pausing is always allowed.
- **Real money is narrower.** It takes only profiles with a passing paper
  promotion, switches at most once a day, needs the id typed back for
  everything but a pause, and never resets its ledger.
- **One account, one loop.** Two deployments reporting the same account tag
  (a one-way hash of the key id) cannot both be enabled from the page.
- **No liquidation command.** There is none, and the capability tests hold
  the control module to queueing only.
- **No login, by the operator's choice.** A cross-site guard refuses
  requests from other sites' pages, and every command records who sent it
  and from where.

**Fixed while there:**
- The target warning now compares against the deployment's own config.
  Ultimate's 30% calm-lot target is intended.
- `/bars` and `/indicators` no longer take a directory from the browser.

## The Warehouse tab

**A tab for what the warehouse holds and the state of the machine filling
it.** Until now the only way to see it was ad-hoc SQL through
`docker exec`. The tab has five parts:
- **Funds:** bars, span, sessions, duplicates and size, and how far behind
  each fund is.
- **Results:** the sweeps and simulations recorded, the activity per hour,
  and the best found per fund and strategy.
- **Storage:** catalogs, lakes, the reference tables and free disk.
- **Server:** load, CPU temperatures against the CPU's own limits, and
  memory. It also shows thermal throttling since boot, but only outside a
  container: Docker hides those counters, while the temperatures stay
  visible.
- **Queue and backups:** the work left in the queue and its ETA, the
  shards, and the newest backup.

The server side is two GET routes (`server/warehouse_status.py`), held
read-only by `test_server_capability.py`.

**"Up to date" needed a trading calendar**, and the project had none. The
supervisor asks Alpaca, and the web server holds no keys.
`engine/core/trading_calendar.py` encodes the NYSE holidays, each moved the
way the exchange moves it, plus the one-off closures since 2001. It counts
exactly the 2,707 sessions RSP holds from 2016-01-04 to 2026-10-08. Early
closes are not modelled. "Bars to add" is the sessions missing times each
fund's own median bars per session over its last 20. A flat 390 would be
wrong twice over: SQQQ keeps extended hours (~940 a session), and some
minutes of thin funds never print. A last session fetched before it closed
counts as missing its afternoon.

**The bar scan is cached until an ingest.** One pass over 9.7M bars takes
3.3 s while a sweep has every core. Its answer can only change when the
lake's files do, so it is recomputed only then. Results and storage refresh
every 30 s. Every read goes through `bars.py`'s read-only open under the
writer lock, with 4 DuckDB threads.

**Fixed while there:**
- A server sweep recorded the request's default symbol as its
  `backtest.symbol`, so every RSP sweep claimed to be TQQQ. It now records
  the fund. Older rows still resolve through `server_run.ticker`.
- A read-only open that found a writer holding the lock warned that the
  warehouse "has views with absolute paths". It now waits the lock out
  quietly, as the open after it already did.
- `web` mounts the backup directory read-only, for the backups tile.

## One-order exits, brute-force sweeps into the warehouse, and qlib

**A signal exit is one order.** Ultimate's regime exit sent an order per lot,
at most `max_sells_per_tick` a minute, so a calm book of thousands of lots
took an hour to leave where the backtest sells it on one bar. It now sends
one limit order for every condemned lot. The limit sits `live.exit_limit_buffer`
(0.5%) through the bar's price, because a limit at the last trade often rests
a tick above the bid. The fill is allocated back to the lots oldest first,
each through the no-loss guard. An exit still resting on a later bar is
cancelled (`AlpacaBroker.cancel_order`), and what is left is offered again at
the new price. The order and its lots survive a restart.

**Every configuration a server run finishes is in the warehouse.** Server
runs kept their configurations only in Run History. They now also land in
`sim_results.duckdb`, one sweep per run and fund (`server-<run id>-<fund>`),
with the best configuration's trade log. The server also reads bars from the
same files, and DuckDB refuses a second connection in another mode, so a
sink held open for a sweep would have failed every bar read. Instead,
`engine/warehouse/result_writer.py` writes in batches of up to 500 rows or
2 minutes, never holding the warehouse open, under a reader/writer lock.
Other processes' reads wait out a write instead of answering "no data".
`VAI_RECORD_WAREHOUSE=0` turns recording off, and the test suite does: a
first run wrote 33 test rows into the real warehouse (removed).

**`local_only` runs** are never claimed by a remote shard.

**Sweeps keep every worker busy.** `run_sweep`'s parallel path ran batches
of `n_jobs` and waited for each batch's slowest member before starting the
next. Measured on a 64-thread sweep, those tails left 35% of the machine
idle. It is a rolling window now: a finished combination's slot is refilled
at once.

**`tools/sweep_brute_force.py`** queues every strategy that can trade a fund
as local-only server runs. It generalises `tools/sweep_rsp_all.py`, keeping
its spaces over each strategy's committed defaults. `URSP_SIM`, the
ten-year URSP history (`tools/simulate_ursp.py`: simulated before the fund's
2025-08-27 launch, the fund after), is ingested and listed in the UI. The
first campaign covers RSP and URSP_SIM: 110 runs, 138,564 configurations.

**Deployment.** `.env` and `.env.ultimate` held the same Alpaca key, so the
champion's `paper` service is behind a `champion` profile and `paper-ultimate`
is the default trader. Backups go to `/workspace/backups`, a separate disk
(`$VAI_BACKUP_DIR`, the same default for `cli.py backup`).

**qlib, and the ML strategies on both funds.** qlib lives in a `research`
image target (`docker compose run --rm research ...`), because pyqlib
publishes nothing for the workstation's Python 3.14. The image is pyqlib
0.9.7, plus CPU torch, which qlib's concept-drift modules import without
declaring. With it, `tools/train_qlib_regime.py --use-qlib` trained two
regime models:
- RSP: held-out AUC 0.580, against 0.516 for the same data unweighted.
- URSP_SIM: AUC 0.622.

`tools/train_ml_model.py` trained RSP's reachability model (AUC 0.607).
The drift weighting compresses a regime model's output to a few levels.
So `ml_regime_rsp`'s committed thresholds now come from its new model, and
`ml_regime_ursp`, a placeholder with no model before, runs on URSP_SIM. The
sweep reads each model's own quantiles for its thresholds. All three joined
the brute-force campaign.

## Ultimate goes to paper, and one compose file runs everything

**The live loop gives a strategy the history its state spans.** The
market-hours supervisor starts a process per session, so every strategy
began each morning cold. The champion's 10-session volatility and volume
windows were empty: it measured the open's volatility against the open
alone and never sized it down, at the moment the backtest sizes down
hardest. Ultimate's regime carried no flag for ~250 sessions, so it never
bought. Even seeded, Ultimate started each session with no mode, so the
flip to turbulent (its regime exit's only trigger) was never seen and the
calm book would have ridden every downturn; its reversal signal had no
previous close either. `LiveTradingLoop` now replays
`live_history_sessions()` sessions of regular-hours minute bars through
`record_tick` before the first tick (`engine/trading/live_history.py`:
the loop's own feed, adjusted like the warehouse, today's session so far
included), with a neutral portfolio so nothing is taken from equity.
Then `resume(open_lots)` rebuilds what no bar carries: Ultimate re-tags
its reversal lots by their target. A strategy that wants history and
gets none is refused. Against Alpaca: 400 sessions, 145,206 bars, fetched
in 13 s and replayed in 3 s.

**Ultimate's regime exit finishes live.** It fired for one bar. A backtest
sells every condemned lot on that bar, but live sends at most
`max_sells_per_tick` orders a tick, and a limit at the market can go
unfilled, so a book larger than 25 lots was never fully exited. Calm lots
left after the exit are now offered on every later bar of the spell from
`liquidate_minute`. Backtests are unchanged: the full-history Ultimate run
is identical in all 61 result columns.

**A live deployment must be the researched strategy.**
`live_algorithm.build_strategy`, at start-up and in the extension's
algorithm editor, refuses:
- an `ultimate*` strategy without `execution.allow_signal_exit`. It must
  be set in the deployment file, never switched on by the code, so the
  second key of the two-key gate stays a reviewed decision;
- a `regular_session_only` strategy with `extended_hours`;
- a `live.profit_target` equal to `reversal_target`;
- `ultimate_rsp`/`ultimate_ursp`, which have no live history support yet.

`SIGNAL_EXIT_STRATEGIES` moved to the registry, so the server and the live
path share it. Preflight reports these rules and fetches the start-up
history. `config/ultimate_paper.yaml` is the paper deployment.

**One compose file.** `docker-compose.yml` replaces itself and
`docker-compose.pi.yml`:
- `web`: the UI, the API and the backtest engine, published on loopback;
- `paper`: the Pi's loop;
- `backup`: daily, into `./backups`;
- behind profiles: Ultimate in paper, real money, and one-off tools.

Each trading service has its own env file and named volume. `docker stop`
now reaches the trading loop as a graceful stop: the shell at PID 1
forwarded nothing, so the loop was killed mid-tick when the grace period
ran out. `tools/install_services.sh` and `tools/sync_to_pi.sh` are gone,
and `docs/DEPLOY.md` replaces `docs/DEPLOY_RASPBERRY_PI.md`.

**The Docker build context is an allowlist.** The denylist had let three
Fidelity `.har` captures (authenticated brokerage traffic), `server.log`,
the warehouse and agent directories into every image through `COPY . .`.

**The warehouse's views read relative paths**, resolved through DuckDB's
`file_search_path` on every connection. The host and the engine container
share one catalog without rewriting it, and an older warehouse's absolute
views are rewritten once.

## The move from Windows to Linux, and a shorter root

The repository moved to a Linux workstation. What broke, and the fixes:

- **The warehouse read as empty.** Its DuckDB views store an absolute
  `read_parquet` path (`C:/workspace/...`), and `bars.load_frame` turns a
  failed query into "no data" by design, so every backtest, the server and
  nine tests saw no bars, with no error. The views are relative now (see
  above), and `load_frame` logs the failure it absorbs.
- **Windows-only service scripts** (`.cmd`/`.ps1` scheduled tasks) are
  replaced by the compose deployment (above): credentials stay in `.env`,
  and the supervisor reads the market calendar.
- **Hard-coded Windows paths** in the chain scripts, two probes and the
  Fidelity launch hints now use repo-relative paths and Linux commands. The
  chain scripts also called `run_hf_sweep.py`/`analyze_annual.py` at their
  pre-`research/` locations; they run as modules now.
- **CI ran a fraction of the suite.** `pytest tests/` predates the split of
  the suite into each directory's `tests/`, so it covered only the root
  part. CI runs `cli.py test` with every dependency set.
- **Tests that were wrong, not code:** the Pi deployment tests still
  expected the Streamlit `dashboard` service removed in 3e7857d; the run
  resume test compared a warehouse-backed server run against a CSV that
  had since fallen behind the warehouse; the shard-link test's fake asked
  to stop once where the real server asks on every sync, a race that
  Windows' coarse timers hid.
- **Optuna is capped below 5.** Its default TPE sampler converges
  differently (the decomposition test plateaus at 50%), and every recorded
  Bayesian sweep was produced on 4.x.

Root documents were consolidated: the finished web-UI plan and ledger and
the old quick start moved to `docs/history/`; `Run_Instructions` (whose
code blocks the tests execute) and `ml_plan.md` moved to `docs/`; the
sweep-running guide and the simulation record moved from the README to
`docs/sweeps.md`; the chain scripts moved to `tools/experiments/`. Every
`AGENTS.md` is now a symlink to the guide beside it, so agent tools read
one maintained text instead of a September snapshot. The README was
rewritten around a feature list and Linux setup, and corrected where it
had drifted (it still said four strategies existed, denied the registry,
and said there was no CI).

## `ultimate_ursp` and a simulated URSP history

URSP (ProShares Ultra S&P 500 Equal Weight, 2x daily) has traded only since
2025-08-27, so `tools/simulate_ursp.py` builds its history from RSP (2003
on). Each session is 2x RSP's total return, less financing on the borrowed
1x (fed funds plus a spread calibrated so the simulated return over the
real fund's first 278 sessions equals its actual return: 2.09%/yr) and the
0.95% fee. Intraday prices follow the same daily-reset rule. The series is
spliced with the real fund, and minute bars are drawn from same-day RSP
minutes where the warehouse has them. Two bad RSP prints (the 2010 Flash
Crash low, a 2007 stray high) are clipped first; doubled, the Flash Crash
print made the fund's price negative.

`research/strategies/ultimate_ursp_sizing.UltimateUrspSizing`, registered as
`ultimate_ursp` (design and evidence in `docs/research/ultimate-ursp.md`),
is Ultimate-RSP's daily exposure book times a GRADED bear gate. Exposure
scales from full at a 25% drawdown from the 250-session high to none at
55%. The book rebalances only when the target is more than 20% of equity
away, because URSP is thin. On the simulated 2004-2026 URSP: 11.7% CAGR at
a 28% max drawdown, against buy-and-hold URSP's 11.2% at 88.5% (2008: -16%
against -72%).

**Why the gate, and why graded.** Ultimate-RSP's record (2017-2026) holds
no prolonged bear market. On the longer simulated history its votes stayed
in through much of 2008, and the 2x fund fell 66%. A single drawdown
threshold fixed that but was a spike (0.15-0.49 across neighbouring
settings, because 2008 is one event). A linear ramp is a ridge (0.30-0.41
across 30 settings). The deflated Sharpe is not significant (0.42); the
proven gain is the drawdown.

## `ultimate_rsp`: a timing book for RSP, not a grid

`research/strategies/ultimate_rsp_sizing.UltimateRspSizing` (design,
component review and evidence in `docs/research/ultimate-rsp.md`) is
registered as `ultimate_rsp`, with `config/ultimate_rsp.yaml`. It is built
from scratch for RSP, not derived from the Ultimate algorithm, because
every grid this project measured on RSP lost to holding it, and every
regime-gated grid realised its losses at the flips and then could not
re-enter.

It holds a daily target fraction of equity in RSP: the share of PLUS_DM
and Chaikin ADOSC votes (each below its own trailing median, averaged
over their parameters) that say "in". The target is decided at the close
and reached an hour into the next session. Research-lab result,
2017-2026: 11.2% CAGR at an 11.9% max drawdown, against buy-and-hold's
12.0% at 39.1%. That meets plan.md's RSP bar: 27 points of drawdown for
0.85 points of CAGR. Deflated Sharpe 0.88 over the ~1,400 configurations
screened.

**Its exits are signal exits by design**, so the server adds the id to
`SIGNAL_EXIT_STRATEGIES`. A rebalance down sells whole lots at market,
whatever their cost; there is no price stop and no profit-target
harvest (the profit target is set out of reach). `warm_up_history` now
carries volume, which the ADOSC votes need. The trigger method is a new
locked `exposure_target`, because no grid step or reference price is
involved.

**No TA-Lib at run time.** The registry is loaded by `cli.py live`, which
must start without requirements-indicators.txt, so the strategy updates
PLUS_DM and ADOSC incrementally with TA-Lib's own recursions in numpy. A
test pins them to TA-Lib, and another checks in a fresh interpreter that
loading the registry imports neither TA-Lib nor polars.

## `ultimate`: the Ultimate algorithm, runnable from the server and a YAML

`research/strategies/ultimate_sizing.UltimateSizing` (design and evidence
in `docs/research/ultimate-algorithm.md`) is registered as `ultimate`,
with the recommended configuration as its constructor defaults, as
`STRATEGY_DEFAULTS["ultimate"]`, and as `config/ultimate_tqqq.yaml`.
Three decisions came with it.

**The server turns the signal exit on for this id.** Its regime exit sells
the calm-mode lots during the first turbulent session, which can realise
a loss, so it needs `execution.allow_signal_exit` -- and `RunRequest` has
no field for it. Rather than add a form control whose only correct value
for this strategy is "on", `SIGNAL_EXIT_STRATEGIES` names the ids whose
design includes the exit and `build_config` sets the flag for them. It is
half of a two-part gate (`decision_cycle.collect_liquidations` also needs
the strategy's `lots_to_liquidate`), so it cannot change any other
strategy's result.

**`run_sweep` gained `warm_up_daily`.** The strategy's volatility regime
needs ~250 completed sessions before it flags anything, and it buys
nothing until then. The server windows the bars before simulating, so
every server run would have spent its first year idle -- a window
starting in January 2022 would have sat out the whole downturn the
design exists for. A strategy that defines `warm_up(daily)` is now handed
session OHLC for the bars before the window, and the server passes what
its window cut off. Duck-typed like the `target_return` and `ticker`
checks beside it; None (the default) calls nothing. A warmed row carries
`warm_up_sessions`, which `split_row` hashes as a parameter, so a warmed
and a cold run of the same window cannot collide in the warehouse. The
live loop does not warm up yet: that needs regular-session daily bars
from `engine/data`'s feed (see the design doc's "Not done yet").

**`to_run_sweep_kwargs` no longer drops `allow_signal_exit` and
`settlement_days`.** A YAML that set either was simulated without it by
`cli.py backtest`/`search` (the algorithm ledger's V5 caveat records the
same gap in `run_hf_sweep`). The only committed config that sets them
(`paper_aggressive.yaml`) sets the defaults, so no recorded result
changes.

## `cli.py submit`: hand any BacktestConfig sweep to the server's shard queue

Getting a big COWZ sweep watchable in the browser across shards
(server/jobs.py's queue, server/shards.py's multi-machine claiming) had
no path except writing a one-off script per campaign -- `tools/
sweep_rsp_all.py` did this by hand for RSP, and this project's first
attempt at the same thing for COWZ (`tools/sweep_cowz_all.py`, now
deleted) duplicated most of it: recursive bisection under
MAX_SWEEP_COMBINATIONS, the bayesian_dual_scale target_return fan-out,
dedup against already-queued/completed runs. That is exactly the kind
of thing that belongs in the CLI once a second script needs it, not
copied a third time for the next fund.

`cli.py submit --config C` now does this generically for ANY
`BacktestConfig` YAML -- the same config format `backtest`/`search`
already read, converted into `RunRequest` chunks and POSTed to
`/api/backtest/runs`. `--search grid|bayesian` overrides the config's
own `search.strategy` (the server has no `random`); `--trials N` (max
500) is the bayesian budget **per chunk**, not a total. A config whose
declared space exceeds one submission's ceiling arrives as multiple
queued runs, each a coherent slice, exactly as `tools/sweep_rsp_all.py`
did by hand. `--dry-run` prints the plan; `--resubmit` bypasses the
completed/pending dedup.

**Known gap, inherited from the server, not introduced here:**
`RunRequest` has no cost-model field, so every run submitted this way
executes at zero transaction cost regardless of the config's own
`costs:` section -- this is not new to `submit`, every prior
web-submitted sweep in this project (RSP included) already ran this
way; it is just more visible now that a config with real non-zero
costs is being submitted through it.

## `cli.py backtest`/`search` and `run_hf_sweep.py` now read the warehouse only

`server/backtest.py` switched its simulation read path from `data/*.csv`
to the DuckDB/Parquet warehouse back on 2026-09-16, after that directory's
entire contents were lost to an unrelated `git worktree remove` walking a
directory junction (`src/warehouse/bars.py`'s docstring has the full
story) -- the web-submitted path stopped depending on `data/` surviving
at all. The CLI entrypoints did not get the same fix at the time: `cli.py
backtest`, `cli.py search`, and `src/scripts/run_hf_sweep.py` all still
took a `--data <csv>` flag and read it with `pd.read_csv`, so the exact
failure mode `bars.py` exists to prevent was still reachable through
every non-web sweep.

All three now read bars from `src/warehouse/bars.load_frame(ticker)` by
`config.backtest.symbol` -- the same function the server already used --
and `--data` is gone from both CLI subcommands (`src/analysis/
analyze_annual.py` gained a `--ticker` flag in its place, default
`TQQQ`). A ticker must be ingested (`tools/build_warehouse.py --ingest
TICKER`) before any of them can see it; `cli.py fetch-data` still writes
`data/*.csv`, but purely as that ingest step's intake format now, not as
something a backtest reads.

**Consequence worth knowing:** `duckdb`/`polars` (`requirements-warehouse.txt`)
were previously optional for `cli.py backtest`/`search` -- needed only for
the opt-in `--warehouse` result-recording flag. They are now required for
these commands to read any data at all, since there is no CSV fallback
left. `cli.py test`, `cli.py live`, and the Raspberry Pi live loop do not
import this path and remain core-dependency-only.

`_open_result_sink`'s `dataset_version` (the identity a recorded sweep is
tagged with) now comes from `bars.fingerprint(ticker)` instead of hashing
a CSV's `.meta.json` sidecar (`src/warehouse/ingest.dataset_version`) --
there is no file left to hash it from.

## Grouped sweep progress + follow-on queuing (web UI + backtest API)

The Backtesting page's "Active runs" showed every queued/running job as a
bare row with no sense of what it actually covers or how many other
sweeps were waiting behind it -- and pressing Run while a previous sweep
was still processing was blocked outright, even though the backend
already queues a second submission correctly (`server/jobs.py`'s
`JobQueue` is a real single-worker FIFO). Both gaps are closed:

- `Job.snapshot()` (`server/jobs.py`) now echoes the submitted request
  back (`"request": self.request`) -- a pure echo of what the browser
  itself POSTed, nothing new exposed -- so a QUEUED or RUNNING job can be
  described (tickers, grid, strategy params) before it has a report.
- `lib/requestSummary.ts` (new): `expandStrategyParams()` is a TS port of
  `src/core/config.py`'s own function, so a frontend-computed simulation
  count (`grid_steps × profit_targets × strategy-param combos × tickers`)
  matches the engine's exactly; `describeSweepAxes()`'s sibling
  `describeRequestAxes()` answers the same "what varies" question from a
  submitted request instead of a completed report.
- `lib/runQueue.ts` (new): `queuePositions()` computes each queued job's
  1-indexed position purely client-side, safe because the single-worker
  FIFO guarantees at most one job is ever running and every other
  non-terminal job is strictly queued in submission order.
- `ActiveRuns.tsx`: each row now shows its own simulation count, swept
  axes, and (when queued) "next up" / "position N of M" instead of a
  bare pulsing bar -- one job already is one sweep, so "grouping by
  sweep" means describing what one job covers, not merging jobs together.
- `ParameterForm.tsx`: the Run button/form no longer disables itself
  because a *previously submitted* run is still processing -- only the
  POST itself gates it now, so a follow-on sweep actually queues instead
  of being blocked. A non-gating hint explains this when it applies.

`App.tsx`'s single tracked `run` (and the "jump to result" banner keyed
on it) is left as-is on purpose -- `ActiveRuns` is now the authoritative
multi-job view; rewriting `App.tsx` into full multi-run tracking would be
the same scope this feature's own aggregate-progress (not
per-simulation) decision already ruled out one level down.

## Run History gains a Timestamp column (web UI)

`HistoryRow.saved_at` (epoch seconds, from the archived report file's
mtime) was already on the wire and already used behind the scenes, but
never shown. Run History now has a sortable "Timestamp" column for it.

- A row with no recorded save time (an old/legacy report, or a
  corrupted mtime) is shown, and SORTS, as if it happened right now --
  not "unknown," and not pushed to the bottom the way a genuinely
  missing metric is. Computed once per render (`RunHistory.tsx`) and
  once per sort pass (`lib/filters.ts`'s `sortHistoryRows`), not once
  per row, so every such row agrees on what "now" means within one
  view/sort.
- `lib/utils.ts` gains `timestamp()` (epoch seconds -> a local
  date-time string; "--" for null/undefined/NaN), tested.
- `Date.now()` can't be called directly in a component's render body
  (React's purity lint rule flags it even inside `useMemo`) -- the
  "now" fallback is read once via `useState`'s lazy initializer, the
  sanctioned escape hatch for exactly this.
- No backend change -- `saved_at` was already served by
  `GET /api/backtest/history`.

## Sweep summary + per-configuration selection (Backtest result, web UI)

The result page used to show one fund's top-ranked configuration
implicitly and silently: the metrics cards, chart and trade log were
always that configuration's, with no on-screen indication a sweep had
produced any others, and the only way to look at another was
`SweepMatrix`'s heatmap (metrics-only) or clicking a cell, which jumped
to the *other* tab to stage a brand-new sweep rather than showing that
cell's own detail. Now: a **Sweep details** overview at the top (which
arguments actually varied, and by how much), a **Simulations** list of
every configuration the sweep ran, and selecting one populates the
metrics/chart/trade log below for exactly that configuration.

- Per-cell trade-level data (chart, trade log) doesn't exist on the wire
  for any configuration except the winner — an explicit, deliberate prior
  decision (`server/backtest.py`: "carrying each one's executions...
  would multiply the payload by the size of the grid"), not reopened by
  this feature. Selecting a non-winning configuration shows its
  **metrics instantly** (already shipped for every cell); the chart/trade
  log offer a **"View full detail"** button that re-runs just that one
  configuration (~23s, the existing `POST /api/backtest/runs`, no new
  backend surface) and shows its real data once that completes, cached
  per configuration for the page's lifetime. **No backend changes at
  all** — confirmed each `SweepConfiguration.strategy_params` cell
  already carries its full resolved combo (`server/backtest.py`'s
  `strategy_param_keys` covers the whole run, not just the swept subset),
  so the re-run request needs no merging.
- `lib/sweepSummary.ts` (new, pure, tested): `configurationKey()` — a
  stable per-cell identity (grid_step + profit_target + resolved
  strategy_params together) — fixes a real bug in `SweepMatrix`'s own
  narrower, pre-existing combo key (strategy_params alone), which would
  have collided two cells sharing a strategy-params combo but differing
  in grid_step/profit_target. `describeSweepAxes()` reports only the axes
  that actually varied.
- `SweepMatrix`'s cell click now selects in place (no tab navigation) —
  a strictly better version of "see this configuration's detail" than
  jumping tabs. The old capability (stage a cell into the form to launch
  a broader new sweep) is preserved, not dropped: a small per-cell "load
  into form" icon does that explicitly.

## Click-to-sort Run History columns (web UI)

Every column header in "Run history" is now clickable and cycles
ascending -> descending -> off, the same convention a spreadsheet or
data grid uses. "Off" is not a third sort of its own -- it falls back to
exactly today's "Rank by" behavior (a fixed direction per metric,
`higherIsBetter`), so a column click *overrides* that default only while
it is active, rather than replacing the concept.

- `lib/filters.ts` gains `nextRunHistorySort()` (the 3-state cycle, pure)
  and `sortHistoryRows()` (one column's sort, `null` returns the rows
  unchanged so the caller's default applies) -- both unit-tested in
  `filters.test.ts`, following this codebase's pure-function-first
  pattern rather than living inline in the component.
- The dynamic "Rank by" metric column keeps its existing default arrow
  (up when higher is better, down otherwise) until clicked; clicking it
  sorts by whichever metric is currently selected and shows the real
  direction instead.
- A `null` value (a metric absent from an older report, an unset grid
  axis) sorts LAST regardless of direction, matching the existing
  Rank-by ranking's own rule.

## Per-argument "enable sweep" + Sweep Strategy (web UI + backtest API)

Generalizes the Fixed | Sweep toggle below into a per-argument "enable
sweep" checkbox, usable on grid step, profit target, *and* any numeric
strategy param (`ParamSpec.sweepable`), each revealing a **Sweep
Strategy** dropdown: Linear, Logarithmic, Random / Monte Carlo, and two
disabled "(coming soon)" entries -- Multi-Resolution/coarse-to-fine and
Adaptive/Heuristic, which imply a coarse pass inspecting its own results
before refining, i.e. genuine multi-round orchestration nothing reachable
from the web submit path does today. Faking either as a static list
would have claimed behavior that doesn't exist, so both are stubs
(`sweepStrategies.ts`) that error rather than silently do the wrong
thing.

- `web/src/lib/sweepStrategies.ts` (new, pure, tested) holds the three
  working generators (`buildLinearSweep`/`buildLogarithmicSweep`/
  `buildRandomSweep`) plus the two stubs, unit-agnostic so grid step,
  profit target, and a strategy param all share one implementation
  instead of three copies. `gridSteps.ts`'s existing Sweep-mode math
  became a thin percent-domain wrapper over it -- `buildGridSteps` is
  byte-identical for `strategy: "linear"` (the default), so nothing
  built earlier this session regressed.
- The engine turned out to already be wired for a 3-axis sweep:
  `BacktestConfig.to_run_sweep_kwargs()` already calls
  `expand_strategy_params()` to build a `strategy_params_grid`, and
  `GridSearch` already cross-products `grid_steps × profit_targets ×
  strategy_params_grid` -- confirmed by reading the code, not assumed.
  So `server/backtest.py` needed wiring, not new engine surface:
  `RunRequest.strategy_params` already accepted a list value per key
  (`dict[str, Any]`); `build_config()` now expands it, guards against a
  swept `target_return` (would otherwise be silently discarded by the
  existing mirror-alignment code), and caps the resulting combination
  count at `MAX_SWEEP_COMBINATIONS` (2000, `VAI_MAX_SWEEP_COMBINATIONS`
  overridable); `run_backtest()`'s `combinations` count gained the third
  factor and each result cell now carries the exact `strategy_params`
  combo it ran with (`_native()` coerces the numpy scalars `summary.iterrows()`
  yields, since `history.save()` calls bare `json.dumps`); `history_rows()`
  prefers a cell's own combo over the run-level snapshot, fixing a real
  bug this feature would otherwise have introduced (every row of a swept
  run showing the same first-resolved combo).
- `describe_params()` gains `sweepable` per param
  (`type in ("int","float") and editable and mirrors is None`) --
  server-computed, matching this project's "server describes capability"
  pattern (`_apply_locks`, `describe_grid_trigger`), so `target_return`
  (mirrors the grid) and every locked/non-numeric field never render the
  checkbox.
- `SweepMatrix.tsx`'s heatmap was hard-keyed to `(grid_step, profit_target)`
  -- once a strategy param is also swept, several cells share that key.
  A "Params" selector (reusing the existing Fund-selector idiom) now
  picks which combo's 2D slice to render when more than one is present,
  rather than the old `Map` construction silently keeping only the last.

A no-edit, no-sweep submit is still byte-identical to before.

## Grid-step method + Fixed/Sweep (web UI + backtest API)

The lone "Grid step %" input in "Run a Backtest" becomes a small panel
with two orthogonal controls:

- **Fixed | Sweep** for the step *value*. Fixed is one % (as today);
  Sweep takes min / max / count and submits a sorted, de-duped
  `grid_steps` list so the engine tries them all and the Sweep Matrix /
  Run history fill in — with a live "N configurations · ~23s each"
  readout. No server change: `RunRequest.grid_steps` was already a
  1–12 `list[float]` and the sweep path already flattens per cell.
  `web/src/lib/gridSteps.ts` (pure, tested) maps the inputs to the list
  with hard client validation (0 < step < 100 %, count an integer 1–12,
  min < max, no oversized array even mid-paste).

- **Trigger method**, where the strategy has a choice: "Last buy price"
  (`last_buy_price × (1 − step)`) vs "Local reference (rolling high)"
  (`max(last_buy, N-day high) × (1 − step)` — re-fires on local dips).
  `GET /funds` gains a `grid_trigger[id]` descriptor
  (`{methods, default, controlled_by, window_param, window_default}`)
  from an explicit `_GRID_TRIGGER` map in `server/backtest.py` — this
  is *presentation* over the existing `_grid_trigger_level` override
  point, not a new engine param. `hf_local_reference` is locked to
  local-reference; `bayesian_dual_scale` is the one model that switches
  (via its optional `lookback_days`); everything else is locked to
  last-buy. A `test_backtest_grid_trigger.py` anti-rot check ties the
  descriptor to whether the class actually overrides the trigger, and a
  behavioural check confirms the advertised strategies build a rolling
  high. The window param (`lookback_days` for hf *and* bayesian, never
  bell_curve's Gaussian-sizing `lookback_days`) moves out of the param
  grid into one "reference window (days)" input in the panel.

A no-edit submit of any model is byte-identical to before.

## Execution-chart zoom: 1D / 1H / 1m (web UI)

The Execution chart's candle resolution used to be a dropdown on the
filter panel (1Min…1Day) that only *re-aggregated* a fixed ~3000-point
server payload -- so "1Min" over a ten-year run was a rollup of a
rollup, never actual minute bars. It is now a **1D / 1H / 1m** toggle on
the chart itself, and each level bounds the window it pulls so the
resolution is real:

- **1D** — daily candles over the whole backtest.
- **1H** — hourly candles, at most a 10-day window.
- **1m** — minute candles, at most a 2-day window.

Each level fetches `/api/backtest/bars` for its capped window with a high
`max_points`, anchored to the end of the filter range (or the run's data
end when the range is open) and never starting before the range does --
so narrowing the filter panel's dates first, then zooming, works as
expected. The window math is `chartWindow()` in `lib/filters.ts`, pure
and unit-tested. `ExecutionFilters.timeframe` becomes `chartResolution`
(`"1d" | "1h" | "1m"`); the filter panel's Timeframe control is removed.
No server change -- `/bars` already took `max_points` and an arbitrary
window.

## Dynamic sizing-model parameters (web UI + backtest API)

"Run a backtest" now renders one input per sizing-model constructor
argument and swaps the whole set when the Sizing Model changes -- so
picking `rsi` shows `period` / `oversold_threshold`, picking
`bell_curve` shows `lookback_days` / `bars_per_day` / `mu` / `sigma`,
and so on. Fields are pre-filled from this project's committed configs,
grouped Primary vs a collapsed **Advanced** block, and each carries a
reset-to-suggested control; a readout says which values differ from the
committed defaults.

**Server (`server/backtest.py`).** `describe_params()` introspects each
strategy's `__init__` (`inspect.signature` + `typing.get_type_hints`,
which is needed because the strategy modules use
`from __future__ import annotations`) into a typed spec per argument:
`type` (float/int/bool/str), `nullable`, `required`, `default`,
`suggested`, `enum`, `group`, `editable`, `mirrors`, `step`. Three
things `inspect` cannot see are named once: `_PARAM_ENUMS`
(`vol_measure` -> stdev/range), `_HIDDEN_PARAMS` (`model_dir` /
`external_dir` -- never shown or sent), `_DERIVED_PARAMS`
(`baseline_price` -- shown locked). `bayesian_dual_scale.target_return`
is surfaced locked with `mirrors: "profit_target"` (the form tracks the
Profit target field and never sends it -- `build_config` already
aligns it to the grid); `ml_reachability_*` `ticker` is locked to the
id's fund. `GET /funds` gains a `sizing_params` key; `sizing_details`
(`required` / `defaults`) is byte-for-byte unchanged for its existing
consumers.

**"More than read-only": `POST /api/backtest/validate`.** Dry-runs the
*same* `build_config(request)` the submit path uses -- one definition of
"valid", no second to drift -- queues nothing, writes no history, opens
no store, and returns `{ ok, resolved_strategy_params, aligned, errors:
[{field, message}] }` always as HTTP 200. The form debounces a call to
it and renders a bad argument as a red line under its field, so
`max_trade_pct = 1.5` or a partial parameter set is caught before the
run is ever queued instead of as a 400 on click or a job that dies
twenty seconds in. A 404 (a deployment whose backtest half predates the
route) degrades silently to submit-time validation.

**Client.** `strategyParams.ts` holds the pure schema->form->wire logic
(covered in `strategyParams.test.ts`): a blank field is omitted (never
sent as `null`); a `mirrors` field and the `percentage` alias are never
sent; an `editable:false` field is never sent except `ticker`; ints go
out as integers and bools as JSON booleans (the server does no
coercion). A no-edit submit of any model therefore sends exactly that
model's committed defaults -- byte-identical to the old blind
`sizing_details.defaults` splat. The e2e hooks (`sizing-model` /
`bars` / `run` test-ids, the `bars` option order, the `Run a backtest`
title) are untouched; the Advanced block is collapsed on load so no new
`<select>` shifts.

## "Backtest result" nav tab (web UI)

Opening a run (from Run history or Active runs) already opened `?run=<id>`
in a new browser tab. That tab now lands on a **fourth nav tab**,
"Backtest result", instead of rendering the report inline under
Backtesting. The report — summary metrics, OHLC chart, trade log, sweep
surface, fund comparison — moved into `web/src/components/backtest/
BacktestResult.tsx`; the Backtesting tab is now just the instrument
(ParameterForm, ActiveRuns, RunHistory).

- A deep link (`?run=`) selects the result tab on load and attaches.
- A run submitted from the form finishes on the Backtesting tab (the Run
  button and status badge report it there), and a "Run complete → Backtest
  result" card offers the jump. It deliberately does **not** force-navigate
  on completion — that races the "complete" state a reader and the e2e
  suite both watch for.
- A sweep-matrix cell click on the result tab still stages the
  configuration onto the form and switches back to Backtesting, so the
  prefilled form is in view rather than changed on a hidden tab.
- The execution filter (its date range doubles as the submitted run's
  window) stays lifted in `App`; `BacktestResult` derives the chart data
  from it.

## Run-history filtering (web UI)

The **Run history** table can now be narrowed before it is ranked.

- **Categorical**, as multi-select chips: fund, algorithm (`sizing_model`),
  fill model. Empty = no restriction; picking several is OR-within,
  AND-between.
- **Name**, as a case-insensitive substring. A row with no name drops
  out once the box is non-empty.
- **Input arguments**: `grid_step` and `profit_target` are always shown
  (in percent, matching the table); every numeric sizing-model argument
  seen across the loaded rows is offered through an "add filter"
  dropdown. Each takes a set of exact values (chips, when the distinct
  count is 2–12) **and** a min/max band — a row passes on either, so
  "1% or 1.5%" and "0.5%–2%" both work.
- **Results**: every `FundPerformanceMetrics` field (CAGR, worst year,
  max drawdown, Sharpe, return/drawdown, trade count, …) can be added as
  a min/max band from the same dropdown.

A row missing a gated field — an old report with no `worst_year_pct`, a
model that never took `period` — is **excluded**, not passed through, the
same rule `filterExecutions` already follows for an execution with no
RSI. The filtering itself is `filterHistoryRows` and friends in
`web/src/lib/filters.ts`, pure and covered in `filters.test.ts`; the
panel only edits the filter object.

To make an input argument filterable at all, the resolved
`strategy_params` (what the engine was built with, after defaults and
`target_return` alignment) now ride on the report's `parameters` and on
every flattened history row — `{}` for a run archived before this.

## Named backtest runs (web UI)

"Run a backtest" now has an optional **Name** field. It is descriptive
only — the engine never reads it — and deliberately stops at the server
boundary rather than entering `BacktestConfig`: it is a UI/history
concern, so it is carried on the `Job` snapshot (`server/jobs.py`) and
the archived report's `parameters.name` (`server/backtest.py`), never
handed to `from_dict()`.

Because it rides the job snapshot, a queued or running sweep shows by
name in **Active runs** before its report exists; once complete it labels
the header strip and gets its own column in **Run history**, repeated on
every configuration row since that table is flattened one row per cell.
Blank and whitespace-only names normalise to unnamed at both the queue
and the report, so the history table never shows a row labelled `"   "`.

## Analytical warehouse (DuckDB + Polars)

Sweep output previously landed in four stores that could not be joined:
flat CSVs (`cli.py`, `run_hf_sweep.py`), per-run JSON (`server/history.py`),
JSONL probe journals (`tools/stage*_grid.py`), and SQLite for live state
only (`src/core/persistence.py`, which deliberately refuses backtest
results). Three consequences drove this change:

1. **Trade blotters were computed and discarded.** `_simulate_single`
   builds the blotter unconditionally because `trade_metrics` needs it,
   then `run_sweep` drops it unless `return_full_results` is set.
   `cli.py:150` said so outright: *"cli.py does not yet write them to
   disk."*
2. **No dedup survived a process.** The only one was an in-process dict
   in `run_hf_sweep.py`, which measured 140 of 200 TPE trials as
   re-measurements of 60 unique combinations.
3. **No lineage.** A results CSV recorded parameters and metrics but not
   *which data file* produced them.

`warehouse/` now holds `market_data.duckdb` (assets, market_events,
external_series) and `sim_results.duckdb` (broker_environments, sweeps,
simulations), linked by `ATTACH`, over ZSTD Parquet lakes partitioned
`ticker/year`, `provider/series_key` and `simulation_id`. Build it with
`tools/build_warehouse.py --ingest-all`; record into it with
`cli.py backtest --warehouse`. On this repo's data, 7.36M bars compress
to 87 MB and 0.69M macro rows to 6 MB, with the catalogs at ~2 MB.

### Decisions worth keeping

**The sweep engine does not import duckdb.** `run_sweep` gained one
keyword, `result_sink=None`, typed against a stdlib `Protocol` in
`src/optimization/result_sink.py`. `src/optimization` is reachable from
the live path, and the Pi must not need an analytics library to boot.
`DuckDBResultSink` satisfies the Protocol structurally and never imports
it.

**`parameter_hash` includes `dataset_version` and `broker_id`.** It
carries the `UNIQUE` constraint that *is* the dedup, so it must cover
everything that changes what a run means. A hash that is "purely about
parameters" reads cleaner and silently makes the warehouse refuse to
re-measure a strategy on newer data. `rank_by` is excluded: ranking
chooses which row you look at, not what was computed. It builds on
`core/artifacts.canonical_hash` rather than adding a third hashing
scheme to a project that already had two.

**Sorting at write time replaces the index that a view cannot have.**
DuckDB refuses `CREATE INDEX` on a view ("can only create an index on a
base table"), so the OHLCV lake is written `ORDER BY ticker, timestamp`.
Partition pruning plus row-group zonemaps do the work — but zonemaps
only prune if the data was sorted. Dropping the `ORDER BY` fails no
query; it just silently makes every `ASOF JOIN` a full scan.

**`TimeZone` is pinned to UTC.** Measured: DuckDB defaults to the system
zone (America/Denver on this machine), and it changes what
`TIMESTAMPTZ::TIMESTAMP` yields — the same instant read back as 14:30
under UTC and 07:30 under America/Denver. A casting mistake in an ASOF
join does **not** raise; it shifts the instant and joins anyway.

**Blotter columns are cast explicitly.** Polars types an all-null column
as `String`. A combination that closes no trades has an all-null
`profit_realized`, whose Parquet file would then disagree about that
column's type with every other run's and break the view. `BLOTTER_SCHEMA`
pins all twelve columns.

**Cross-database foreign keys do not exist**, so `dataset_version` is a
plain `VARCHAR`. Lineage is recorded, not enforced — the alternative was
collapsing both catalogs into one file.

**A sink may not raise, and may not retain its `SimulationResult`.**
Both come from incidents already recorded in `optimization_controller.py`:
losing hours of engine time to a storage fault, and the 1,260-combination
run whose RAM was exhausted by holding results. Writing the blotter costs
nothing extra because it already exists; only *keeping* it does.

**`/warehouse/` is anchored in `.gitignore`.** A bare `warehouse/` also
matches `src/warehouse/`, which would leave the package's own source
untracked and missing from every clone — precisely what the bare `data/`
rule still does to `src/data/`.

### External-series lake — `data/external/` (FRED / CBOE / Yahoo)

`build_warehouse.py --external` (also folded into `--ingest-all`) ingests
the 118 macro series in `data/external/` — 56 FRED, 52 Yahoo, 10 CBOE,
~0.69M rows → 6 MB — into a Parquet lake partitioned `provider/series_key`
with an `external` view and an `external_series` dimension table.

**Manifest-driven, not glob-driven.** `data/external/manifest.json`
(written by `tools/fetch_market_inputs.py`) is the list of series and the
only source of each one's provider, category and — critically —
`lag_days`. A CSV with no manifest entry is skipped rather than guessed
at: its publication lag would be unknown, and lag is not optional.

**The join is lag-aware.** 55 of 56 FRED series carry a real publication
lag (CPI +45d, GDP +90d, ...). `queries.EXTERNAL_SERIES_AT_BARS` shifts
every observation forward by `lag_days` to a `known_at` and does the
`ASOF` match on that, so a March backtest bar sees the January CPI print,
not the March one that wasn't released until mid-April. Verified against
real data: 0 of 1,035,332 TQQQ bars joined a CPI value dated less than
45 days before them. `EXTERNAL_VALUE_AT` is the raw
`ExternalIndexSeries.scalar()` equivalent for non-backtest lookups.

**Heterogeneous shapes, one view.** FRED is `timestamp,close`; some CBOE
series add `high,low`; Yahoo adds `volume`. Every series is projected
onto a fixed 8-column superset with NULLs, and `union_by_name` binds the
differing per-partition files.

## Tooling — Docker

The project runs in a container via `cli.py`, a single entrypoint with
three subcommands. Build once, run any of them:

```
docker build -t volatility-ai .
docker run --rm volatility-ai --help
```

Or via compose, which also wires up the right volumes:

```
docker compose run --rm test
docker compose run --rm backtest --config /app/config/config.yaml --data /app/data/TQQQ_historical.csv
docker compose run --rm live --config /app/config/config.yaml
```

**`test`** — runs pytest inside the image. Arguments forward straight
through: `docker compose run --rm test -k my_test -v`.

**`backtest`** — loads a `BacktestConfig` YAML and a historical CSV,
runs the sweep, prints a summary, and optionally writes full results
with `--output`. Mount `./data` and `./config` read-only, `./output`
read-write.

**`live`** — validates config and credentials and runs the Task 7.12
startup sequence against a persistent SQLite store. **It cannot place
a real order.** No class in this codebase implements the `LiveBroker`
protocol against an actual Alpaca connection — confirmed by search
before writing this, not assumed — so `live` correctly and honestly
lands in `RECOVERY_REQUIRED` rather than pretending to connect. What
it does verify for real: config validation, credential presence
(`APCA_API_KEY_ID` / `APCA_API_SECRET_KEY`, sourced only from the
environment — see the secret policy above), and that ledger/audit
state persists to `/app/state` across the run.

Credentials for `live` come from an uncommitted `.env` file passed via
`env_file:` in `docker-compose.yml` — never baked into the image, and
excluded from the build context by `.dockerignore` even if one existed
locally.

State persistence: `/app/state` is a named volume (`state:` in
compose), not a bind mount, so the SQLite ledger and audit log survive
`docker compose run` invocations across separate container instances
— the point of Task 7.3/7.12's design, now actually exercised by the
container lifecycle rather than only by tests.

**A real bug was caught before this was committed.** The `test`
subcommand originally routed pytest arguments through
`argparse.REMAINDER`, which cannot reliably capture a leading
option-like token with no preceding positional — `cli.py test -q`
(the single most common invocation) raised `unrecognized arguments:
-q`, while `cli.py test some/path.py -q` worked fine. Fixed by
forwarding `sys.argv` directly for that subcommand instead of routing
it through argparse. Regression-tested in
`tests/integration/test_cli_docker_entrypoint.py`.

The full build was also simulated without Docker itself (unavailable
in the authoring sandbox): a clean virtualenv installing only
`requirements.txt`, against a build context mirrored through the exact
`.dockerignore` exclusions, running the exact entrypoint commands.
All 677 tests passed in that simulated environment before any of this
was committed.


## Tooling — ruff (formatter + linter)

Formatting and linting are both handled by [ruff](https://docs.astral.sh/ruff/),
configured in `pyproject.toml`.

```
ruff format .           # apply formatting
ruff format --check .   # verify only, for CI
ruff check .            # lint
ruff check --fix .      # lint and apply safe fixes
```

**Configuration choices, and why:**

- **`line-length = 100`**, not ruff's default 88. Measured against the
  existing code: p95 of line lengths is 87 and p99 is 106, so 88 would
  have rewrapped ~4.5% of all lines while 100 touches ~1.6%. This keeps
  formatting churn off code that was already readable.
- **`E501` (line-too-long) is ignored** at lint level. Operator-facing
  error strings — reconciliation diagnostics, no-loss rejections —
  deliberately name the specific delta so someone paged at 3am can act
  without reading source. The *formatter* still enforces line length on
  code; this only exempts strings it cannot split.
- **`C408` is exempted in `tests/` only.** Test helpers build kwargs
  dicts that are immediately splatted (`base = dict(...)` →
  `Model(**base)`), where the call form mirrors the keywords it becomes.
  `src/` and `optimization_controller.py` are held to the rule and are
  C408-clean.
- **`docstring-code-format = false`.** Several docstrings contain spec
  excerpts and illustrative pseudo-code that are not valid Python and
  must not be rewritten.

Two `noqa` comments exist, both in `tests/unit/test_secret_policy.py`,
both with stated reasons: that test verifies credentials stay redacted
through *every* string-conversion path, so the `%`-format and
`.format()` call sites are the code paths under test — modernizing them
would silently drop coverage.


## Phase 1 — Fix the confirmed bugs (B1–B5)

Tasks 1.1–1.5 fixed. Task 1.6 (this entry) re-runs the Task 0.1
regression fixture and documents deltas, per
`implementation_task_specs.md`.

### FixedPortfolioPercentage: unchanged, value-for-value

`FixedPortfolioPercentage` doesn't use drawdown or ticks in its
sizing, so its output should be identical to the pre-Phase-1 baseline
captured in Task 0.1 — confirmed by
`tests/integration/test_task_1_6_regression_verification.py`, which
re-runs the exact Task 0.1 fixture/parameters post-Phase-1 and asserts
every column matches the frozen `BASELINE` in
`tests/fixtures/regression_baseline.py` exactly:

| Metric | Value |
|---|---|
| Final Equity | 100099.81489816227 |
| Trade Count | 4 |
| Closed Trade Count | 4 |
| Capital Velocity Index | 1.0 |
| Max Drawdown % | 0.4430668810465577 |

Unchanged despite: drawdown now being tracked every bar instead of
only trigger bars (Task 1.2), `record_tick` now firing every bar
(Task 1.3), `current_dd` now being threaded into
`calculate_trade_value` (Task 1.4), and fill-status/no-loss validation
now gating cash and ledger mutation (Task 1.5) — all expected, since
none of those changes touch a code path `FixedPortfolioPercentage`
reads from.

### Drawdown/tick-consuming strategies: not applicable yet

Task 1.6 also asks to re-run and record an updated baseline for "any
drawdown/tick-consuming strategy available." None exists in this repo
yet — `BellCurveProbabilitySizing`, `RsiMomentumSizing`, and
`BayesianDualScaleSizing` were out of scope for the from-scratch
`src/size_calculators.py` implementation (see that file's docstring:
no sizing formula was specified anywhere to implement them against).
B2/B3/B4's underlying mechanism is fixed at the controller level
regardless (Tasks 1.2–1.4), so whenever a drawdown- or
tick-consuming strategy is added, it will receive real per-bar ticks
and real drawdown from day one rather than needing its own fix.

### No collision between the controller's and analyzer's drawdown figures

`PerformanceAnalyzer.calculate_metrics()` deliberately never produces
a `"Max Drawdown %"` key (see that file's docstring) — the value in
every `run_sweep()` result row is exactly
`optimization_controller.py`'s own `state.max_drawdown * 100.0`
assignment, with nothing else able to write or silently overwrite it.
Confirmed by
`test_no_collision_between_controller_and_analyzer_drawdown_figures`.

### Bugs fixed this phase

| Task | Bug | Fix |
|---|---|---|
| 1.1 | B1 | `Run_Instructions` example used a non-existent `allocations=` param and a wrong import path; both fixed |
| 1.2 | B3 | Peak equity / drawdown now computed every bar, not only on grid-trigger bars |
| 1.3 | B4 | `sizing_engine.record_tick(current_price)` now called every bar (previously never called) |
| 1.4 | B2 | `current_dd` now threaded into `calculate_trade_value` (previously always defaulted to 0.0) |
| 1.5 | B5 | Fill status (`OrderStatus.FILLED`) and the no-loss invariant now validated before cash/ledger mutation on both buy and sell paths |

## Phase 6 — Config & docs

### Task 6.2: integration-test coverage for scenarios 1–6

Task 6.2 lists 13 integration-test scenarios; scenarios 7–13 need
Phase 7 tasks that don't exist in this repo yet and were explicitly
not attempted, per that task's own instruction not to build ahead of
the tasks they depend on. Scenarios 1–6 were each already covered by
a dedicated, traceably-named test written when its source task was
originally implemented — re-verified together (not assumed still
passing) before this entry was written, rather than duplicated into
new tests that would just re-check the same behavior a second time:

| # | Scenario | Test |
|---|---|---|
| 1 | `record_tick` called exactly once per bar regardless of trigger state (Task 1.3) | `tests/integration/test_task_1_3_record_tick.py::test_record_tick_called_exactly_once_per_bar_including_non_trigger_bars` |
| 2 | `calculate_trade_value` receives a non-zero drawdown during a scripted drawdown (Task 1.4) | `tests/integration/test_task_1_4_drawdown_threading.py::test_calculate_trade_value_receives_real_drawdown_not_default_zero` |
| 3 | Each `RiskManager` cap clamps rather than silently over-allocating (Tasks 3.1/3.2) | `tests/unit/test_risk_manager.py::test_max_concurrent_lots_clamps_to_zero_once_at_cap`, `::test_max_total_exposure_pct_clamps_to_zero_when_already_at_or_over_cap`, and `tests/integration/test_task_3_2_risk_manager_wiring.py::test_max_concurrent_lots_caps_trade_count` |
| 4 | A single raised exception inside one combination doesn't abort the sweep (Task 4.4) | `tests/integration/test_task_4_4_error_isolation.py::test_one_bad_combination_does_not_abort_the_others` |
| 5 | `n_jobs>1` output matches `n_jobs=1` output (Task 4.5) | `tests/integration/test_task_4_5_parallel_execution.py::test_n_jobs_greater_than_1_produces_the_same_result_set_as_sequential` |
| 6 | Walk-forward out-of-sample metrics are computed on data never used for that fold's selection (Task 5.1) | `tests/unit/test_walk_forward.py::test_no_test_slice_overlaps_its_own_train_slice` |

### Tasks 6.3 / 6.4: deployment artifacts and secret policy

**Backtest artifacts are safe to persist without credentials.** A
`DeploymentArtifact` (`src/artifacts.py`) contains only provenance
identifiers and hashes — no credential fields exist on it, and
`canonical_hash()` actively *rejects* any content carrying a
secret-looking key (`secret`, `password`, `api_key`, `token`,
`credential`, `private_key`, checked case-insensitively through
nested structures) rather than silently hashing it. The same is true
of `BacktestConfig`: it has no credential fields by design, so a
serialized config is safe to commit to source control.

**Credentials come only from the environment**, never from YAML/JSON
config, command-line arguments, or source control:

| Variable | Purpose |
|---|---|
| `APCA_API_KEY_ID` | Alpaca API key ID |
| `APCA_API_SECRET_KEY` | Alpaca API secret key |

`load_live_credentials()` (`src/secrets.py`) raises
`ConfigurationError` naming exactly which variables are missing —
it never falls back to simulation mode, and never echoes a value
(even partially) into the error message.

**Redaction is structural, not conventional.** `LiveCredentials`
overrides `__repr__`/`__str__`, so credentials cannot reach a log
line, f-string, `%`-format, `.format()` call, or traceback frame even
when the object is logged directly. `redact_secrets(payload)` is
available for masking secret-bearing values inside arbitrary
structured-logging payloads (non-mutating — the caller's live values
are untouched).

## Phase 7 — Live execution parity

### Task 7.7: promotion runbook (backtest → paper → live capital)

**No code path goes from a backtest result directly to live capital.**
This is enforced structurally, not by convention: constructing a
`Mode.LIVE` `OrderManagementSystem` requires a passing
`PromotionEvaluation`, which requires a real `PaperTradingRecord` that
met every threshold. There is deliberately no `enable_live=True`
boolean shortcut.

**The three stages, in required order:**

| Stage | Mode | What it proves |
|---|---|---|
| 1. Backtest | `Mode.SIMULATION` | The parameter set survives historical data (and ideally Task 5.1 walk-forward validation) |
| 2. Paper | `Mode.PAPER` | It survives real-time execution against Alpaca's paper endpoint, risk-free |
| 3. Live | `Mode.LIVE` | Only reachable with recorded evidence that stage 2 passed |

`Mode.PAPER` is a first-class mode rather than a flag on `LIVE`,
so reaching real capital is an explicit, auditable step.

**Promotion criteria** (`src/promotion.py::PromotionCriteria`) — all
machine-checkable, all recorded in the promotion artifact rather than
left to operator judgment:

| Criterion | Default |
|---|---|
| Minimum paper-trading duration | 5 days |
| Minimum strategy decisions | 20 |
| Minimum fills | 5 |
| Accounting discrepancies | 0 allowed |
| Duplicate-order incidents | 0 allowed |
| No-loss guard violations | 0 allowed |
| Unresolved reconciliation state | 0 allowed |
| Unhandled runtime exceptions | 0 allowed |

**Operator procedure:**

1. Run the backtest sweep; select a parameter set.
2. Build a `BacktestConfig` with `live.paper_trading: true` and run it.
   `LiveExecutionLoop` builds a `Mode.PAPER` OMS — real capital is
   unreachable at this stage regardless of what else is configured.
3. Collect results into a `PaperTradingRecord`. Its `metrics` field
   mirrors `SimulationResult.metrics` (Task 4.6), so paper and
   backtest results are directly comparable rather than living in two
   incompatible report formats.
4. Call `assert_promotable_to_live(artifact, record)`. It reports
   *every* unmet criterion at once, not just the first.
5. Only on success, pass the returned evaluation as
   `live_capital_promotion` to enable `Mode.LIVE`. Record
   `evaluation.criteria` in the deployment artifact — that is the
   auditable record of which bar was cleared.

**Gap closed during this task:** `LiveExecutionLoop` previously
constructed `Mode.LIVE` unconditionally, ignoring
`config.live.paper_trading` entirely — a config asking for paper
trading still got a real-capital OMS. It now honors the flag.

### Task 7.9: macro/seasonality signals — **Not required / deferred**

Discovery gate outcome. **No confirmed consumer exists**, so per the
task's own step 2 no ingestion pipeline was built and no production
behavior was changed.

Evidence from a repository-wide search of all three field names
(`time_of_day_flag`, `is_macro_event_day`, `macro_surprise_factor`):

| Location | Role |
|---|---|
| `src/market_context.py` | **Defines** the fields with safe defaults (`0`, `False`, `0.0`) — a definition, not a consumer |
| `src/live_execution.py` | `build_context()` **forwards** them. Pure pass-through plumbing; it type-coerces and hands them to the constructor, never reading a value to make a decision |
| `src/size_calculators.py` | The only real strategy, `FixedPortfolioPercentage`, reads exactly `context.price` and `context.equity` — neither of the three fields |

Also confirmed: no conditional logic anywhere branches on these
fields; no call site supplies a non-default value; and no FinBERT /
sentiment / transformers / CPI / Federal Reserve / FOMC reference
exists anywhere in the repository.

**On the external claim that prompted this task** — that FinBERT NLP
sentiment and Fed/CPI macro-event awareness were already integrated
into this system's Bayesian sizing — nothing here supports it.
`BayesianDualScaleSizing` is not implemented in this repository at all
(`FixedPortfolioPercentage` is the only sizing strategy that exists),
and "macro" in that class's name refers to a **long-window Bayesian
posterior** — a lookback-length distinction — not to macroeconomic
events. The two senses of "macro" appear to be the source of the
confusion.

The fields are deliberately **left in place**: they are optional,
defaulted, and already part of overview §5.1's `MarketContext`
contract. Removing them would be a breaking change for no benefit;
populating them would be the speculative scope this gate exists to
prevent.

This finding is **executable, not just documented** —
`tests/unit/test_task_7_9_macro_signals_discovery.py` fails if a
consumer, a branch, an ingestion dependency, or a new sizing strategy
appears, at which point the gate must be re-run and step 3 (consuming
strategy, source dataset, timestamp-join semantics, defaults, and a
follow-up implementation task) becomes live.
