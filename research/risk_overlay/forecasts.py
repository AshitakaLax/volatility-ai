"""
The forecast database: every nightly risk report the Live page was given,
and what each session then did. It is the record that says whether the
reports are worth anything (docs/daily_risk_report_plan.md, "Scoring the
forecasts every night"), kept apart from any one deployment: a report is
stored when it is checked, whether or not a trader is ever sent it.

--------------------------------------------------------------------
WHERE IT IS, AND WHO WRITES IT

  warehouse/forecasts/risk_reports.db      SQLite; VAI_FORECAST_DB overrides.
                                           Backed up nightly with the
                                           warehouse catalogs
                                           (tools/docker_backup_loop.sh).

  server/risk_forecasts.py                 records a report when the Live
                                           page's Check is pressed, the
                                           Forecast tab's Keep, and each
                                           trading morning's from the
                                           forecast service
                                           (tools/forecast_morning.py), which
                                           sends it through the same route;
                                           the last two send what the
                                           generator read beside it
  tools/score_risk_reports.py --forecasts  run nightly by tools/track_live.py
                                           after the close: copies in every
                                           report a trader archived (an
                                           Apply sent some other way is not
                                           lost), records each finished
                                           session's closes from the
                                           warehouse, and scores each report
                                           against them: the next session,
                                           and each longer horizon once its
                                           last session has closed

A report is keyed by its SHA-256 (engine/core/risk_report.py's
report_sha256), the id the traders' archives use, so a row here joins
theirs. The browser re-serialises every report the page sends, which writes
a whole-number float as an integer (-22.0 becomes -22) and so changes the
hash; a report is therefore stored in that same form (as_the_page_sends), so
the copy imported from a file, the copy Check sent and the copy a trader
archived are one report. It is stored only once it passes the audit -- one
that fails cannot be scored -- and is never rewritten or deleted. Each time
it is added is a receipt.

--------------------------------------------------------------------
TABLES

  reports   one row a report: the session it is for, its as_of, when it was
            first received, the 1-day forecast (quantiles, median, mean,
            std, ES5, the expected move), the labels the mapping reads, and
            the raw report as canonical JSON
  receipts  each time it was added: when, by whom, and how (check, import,
            archive:<deployment>)
  closes    a session's regular-hours close and the previous session's, by
            symbol, from the warehouse's minute bars
  scores    a report against its session's closes
            (tools/score_risk_reports.score_session): the return, inside
            the 90% and 50% bands, the PIT, the pinball loss and
            |return| / expected move
  horizon_scores
            each longer horizon (next_week ... next_year) against the close
            of its last session -- the report's session counted as the
            first, so a week ends four sessions after it -- measured from
            the same prior close as the next session's score
            (tools/score_risk_reports.score_horizon)
  inputs    what the generator read for a report it made
            (research/forecast_generator: the snapshot of overnight inputs,
            the run's diagnostics and its sources), sent beside the report
            by the Forecast tab's Keep or the forecast service. Display
            only, written once, and absent for a report made anywhere else
            (an LLM's, a pasted file's): what those read was never recorded
            and is not reconstructed.

Nothing is migrated in place: a database made before a table existed gets it
(CREATE TABLE IF NOT EXISTS) the next time it is opened.
"""

from __future__ import annotations

import json
import os
import sqlite3
from collections.abc import Iterator, Mapping
from contextlib import contextmanager, suppress
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from engine.core.risk_report import (
    HORIZONS,
    Audit,
    RiskReport,
    canonical_json,
    parse_report,
)

SCHEMA_VERSION = 2
_DB_ENV = "VAI_FORECAST_DB"
_WAREHOUSE_ENV = "VAI_WAREHOUSE_DIR"
_REPO_ROOT = Path(__file__).resolve().parents[2]
QUANTILE_KEYS = ("p01", "p05", "p25", "p75", "p95", "p99")
# The horizons scored against a later close; "tomorrow" is `scores`.
LONGER_HORIZONS = tuple(name for name, days in HORIZONS.items() if days > 1)
# What a report's inputs may hold, and how much of it.
INPUT_PARTS = ("snapshot", "diagnostics", "sources")
INPUTS_MAX_BYTES = 256 * 1024

_SCHEMA = """
CREATE TABLE IF NOT EXISTS reports (
    sha256            TEXT PRIMARY KEY,
    symbol            TEXT NOT NULL,
    session           TEXT NOT NULL,
    as_of             TEXT NOT NULL,
    received_at       TEXT NOT NULL,
    schema_version    TEXT NOT NULL,
    model             TEXT,
    base_price        REAL,
    expected_move_pct REAL NOT NULL,
    p01 REAL NOT NULL, p05 REAL NOT NULL, p25 REAL NOT NULL,
    p75 REAL NOT NULL, p95 REAL NOT NULL, p99 REAL NOT NULL,
    median_pct        REAL NOT NULL,
    mean_pct          REAL NOT NULL,
    std_pct           REAL NOT NULL,
    prob_positive     REAL NOT NULL,
    es5_pct           REAL NOT NULL,
    regime            TEXT,
    volatility_state  TEXT,
    gap_risk          TEXT,
    skew_bias         TEXT,
    confidence        REAL,
    warnings          INTEGER NOT NULL,
    raw               TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS reports_by_session ON reports (symbol, session);

CREATE TABLE IF NOT EXISTS receipts (
    sha256       TEXT NOT NULL REFERENCES reports (sha256),
    received_at  TEXT NOT NULL,
    operator     TEXT,
    via          TEXT NOT NULL,
    PRIMARY KEY (sha256, received_at, via)
);

CREATE TABLE IF NOT EXISTS closes (
    symbol         TEXT NOT NULL,
    session        TEXT NOT NULL,
    close          REAL NOT NULL,
    prior_session  TEXT NOT NULL,
    prior_close    REAL NOT NULL,
    return_pct     REAL NOT NULL,
    source         TEXT NOT NULL,
    recorded_at    TEXT NOT NULL,
    PRIMARY KEY (symbol, session)
);

CREATE TABLE IF NOT EXISTS scores (
    sha256      TEXT PRIMARY KEY REFERENCES reports (sha256),
    return_pct  REAL NOT NULL,
    in_90       INTEGER NOT NULL,
    in_50       INTEGER NOT NULL,
    pit         REAL NOT NULL,
    pinball     REAL NOT NULL,
    move_ratio  REAL NOT NULL,
    scored_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS horizon_scores (
    sha256       TEXT NOT NULL REFERENCES reports (sha256),
    horizon      TEXT NOT NULL,
    end_session  TEXT NOT NULL,
    end_close    REAL NOT NULL,
    return_pct   REAL NOT NULL,
    in_90        INTEGER NOT NULL,
    in_50        INTEGER NOT NULL,
    pit          REAL NOT NULL,
    pinball      REAL NOT NULL,
    scored_at    TEXT NOT NULL,
    PRIMARY KEY (sha256, horizon)
);

CREATE TABLE IF NOT EXISTS inputs (
    sha256       TEXT PRIMARY KEY REFERENCES reports (sha256),
    inputs       TEXT NOT NULL,
    recorded_at  TEXT NOT NULL
);
"""


class ForecastRefused(ValueError):
    """The report does not pass the audit, so it is not stored."""

    def __init__(self, audit: Audit) -> None:
        self.audit = audit
        listed = "; ".join(f"{f.where}: {f.message}" for f in audit.errors[:3])
        super().__init__(f"the report does not pass the audit: {listed}")


class InputsRefused(ValueError):
    """The inputs sent beside a report are not that report's, or are not
    what the generator writes; neither is stored."""


def horizon_end(session: date, name: str) -> date:
    """The last session `name` spans from `session`, which counts as its
    first: a week (5 sessions) ends four sessions later."""
    from engine.core.trading_calendar import next_session

    days = HORIZONS[name]
    return session if days == 1 else next_session(session, days - 1)


def _inputs_text(inputs: Any, report: RiskReport) -> str:
    """`inputs` as stored (canonical JSON), once it is shown to be this
    report's: a mapping of INPUT_PARTS whose snapshot names the report's
    fund and session."""
    if not isinstance(inputs, Mapping):
        raise InputsRefused("inputs must be an object")
    extra = sorted(set(inputs) - set(INPUT_PARTS))
    if extra:
        raise InputsRefused(f"inputs carry {', '.join(extra)}; only {', '.join(INPUT_PARTS)}")
    snapshot = inputs.get("snapshot")
    if not isinstance(snapshot, Mapping):
        raise InputsRefused("inputs carry no snapshot")
    symbol = str(snapshot.get("symbol", "")).upper()
    session = str(snapshot.get("target_session", ""))
    if symbol != report.symbol or session != report.session.isoformat():
        raise InputsRefused(
            f"the inputs are for {symbol or '?'} {session or '?'}, the report for "
            f"{report.symbol} {report.session.isoformat()}"
        )
    text = canonical_json(dict(inputs))
    if len(text.encode("utf-8")) > INPUTS_MAX_BYTES:
        raise InputsRefused(f"the inputs are over {INPUTS_MAX_BYTES // 1024} KB")
    return text


def default_path() -> Path:
    """VAI_FORECAST_DB, else forecasts/risk_reports.db in the warehouse."""
    configured = os.environ.get(_DB_ENV)
    if configured:
        return Path(configured)
    warehouse = os.environ.get(_WAREHOUSE_ENV)
    root = Path(warehouse) if warehouse else _REPO_ROOT / "warehouse"
    return root / "forecasts" / "risk_reports.db"


def _iso(moment: datetime) -> str:
    return moment.astimezone(UTC).isoformat()


def as_the_page_sends(value: Any) -> Any:
    """`value` with every whole-number float an integer, as the browser's
    JSON.parse and JSON.stringify leave a report the Live page sends
    (module docstring): -22.0 becomes -22, 0.5 stays 0.5."""
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, Mapping):
        return {key: as_the_page_sends(item) for key, item in value.items()}
    if isinstance(value, list):
        return [as_the_page_sends(item) for item in value]
    return value


class ForecastStore:
    """The database at `path` (module docstring). Each call opens its own
    connection: the server and the tracking service write it from two
    processes, and SQLite serialises them."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path is not None else default_path()

    @contextmanager
    def _open(self) -> Iterator[sqlite3.Connection]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(self.path, timeout=30)
        con.row_factory = sqlite3.Row
        try:
            con.execute("PRAGMA foreign_keys = ON")
            if con.execute("PRAGMA user_version").fetchone()[0] < SCHEMA_VERSION:
                con.executescript(_SCHEMA)
                con.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
            with con:
                yield con
        finally:
            con.close()

    # ---- Writing ---------------------------------------------------------

    def record(
        self,
        report: Mapping[str, Any] | str | bytes,
        *,
        via: str,
        operator: str | None = None,
        at: datetime | None = None,
        inputs: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Store `report` and a receipt for this adding of it, and what the
        generator read for it when `inputs` are given (kept the first time
        they are). Raises ForecastRefused when it does not pass the audit,
        InputsRefused when the inputs are not its own; neither stores
        anything. Returns its id, the session it is for, and whether it was
        new."""
        if isinstance(report, (str, bytes)):
            with suppress(ValueError):  # not JSON: the audit says so
                report = json.loads(report)
        if isinstance(report, Mapping):
            report = as_the_page_sends(report)
        audit = parse_report(report)
        if not audit.ok:
            raise ForecastRefused(audit)
        parsed = audit.require()
        inputs_text = _inputs_text(inputs, parsed) if inputs is not None else None
        received = _iso(at or datetime.now(UTC))
        row = _report_row(parsed, received_at=received, warnings=len(audit.warnings))
        columns = ", ".join(row)
        marks = ", ".join("?" for _ in row)
        with self._open() as con:
            new = (
                con.execute(
                    f"INSERT OR IGNORE INTO reports ({columns}) VALUES ({marks})",
                    list(row.values()),
                ).rowcount
                == 1
            )
            # An archive copied in later can say it arrived earlier than the
            # page recorded it: the row keeps the first arrival.
            con.execute(
                "UPDATE reports SET received_at = ? WHERE sha256 = ? AND received_at > ?",
                [received, parsed.sha256, received],
            )
            con.execute(
                "INSERT OR IGNORE INTO receipts (sha256, received_at, operator, via) "
                "VALUES (?, ?, ?, ?)",
                [parsed.sha256, received, operator, via],
            )
            if inputs_text is not None:
                con.execute(
                    "INSERT OR IGNORE INTO inputs (sha256, inputs, recorded_at) VALUES (?, ?, ?)",
                    [parsed.sha256, inputs_text, received],
                )
        return {
            "sha256": parsed.sha256,
            "symbol": parsed.symbol,
            "session": parsed.session.isoformat(),
            "new": new,
            "warnings": len(audit.warnings),
        }

    def record_close(
        self,
        symbol: str,
        session: date,
        *,
        close: float,
        prior_session: date,
        prior_close: float,
        source: str,
        at: datetime | None = None,
    ) -> None:
        """A finished session's close. Written once: a close is a fact."""
        with self._open() as con:
            con.execute(
                "INSERT OR IGNORE INTO closes (symbol, session, close, prior_session, "
                "prior_close, return_pct, source, recorded_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    symbol,
                    session.isoformat(),
                    float(close),
                    prior_session.isoformat(),
                    float(prior_close),
                    round(100.0 * (float(close) / float(prior_close) - 1.0), 4),
                    source,
                    _iso(at or datetime.now(UTC)),
                ],
            )

    def record_score(
        self, sha256: str, score: Mapping[str, Any], *, at: datetime | None = None
    ) -> None:
        with self._open() as con:
            con.execute(
                "INSERT OR REPLACE INTO scores (sha256, return_pct, in_90, in_50, pit, pinball, "
                "move_ratio, scored_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    sha256,
                    float(score["return_pct"]),
                    int(bool(score["in_90"])),
                    int(bool(score["in_50"])),
                    float(score["pit"]),
                    float(score["pinball"]),
                    float(score["move_ratio"]),
                    _iso(at or datetime.now(UTC)),
                ],
            )

    def record_horizon_score(
        self,
        sha256: str,
        horizon: str,
        score: Mapping[str, Any],
        *,
        end_session: date,
        end_close: float,
        at: datetime | None = None,
    ) -> None:
        """One longer horizon's score (tools/score_risk_reports.score_horizon),
        written once: the close it is measured against is a fact."""
        if horizon not in LONGER_HORIZONS:
            raise ValueError(f"{horizon!r} is not a longer horizon")
        with self._open() as con:
            con.execute(
                "INSERT OR IGNORE INTO horizon_scores (sha256, horizon, end_session, end_close, "
                "return_pct, in_90, in_50, pit, pinball, scored_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    sha256,
                    horizon,
                    end_session.isoformat(),
                    float(end_close),
                    float(score["return_pct"]),
                    int(bool(score["in_90"])),
                    int(bool(score["in_50"])),
                    float(score["pit"]),
                    float(score["pinball"]),
                    _iso(at or datetime.now(UTC)),
                ],
            )

    # ---- Reading ---------------------------------------------------------

    def symbols(self) -> list[str]:
        """Every symbol with a report, the most recently received first."""
        if not self.path.exists():
            return []
        with self._open() as con:
            rows = con.execute(
                "SELECT symbol, MAX(received_at) AS newest FROM reports GROUP BY symbol "
                "ORDER BY newest DESC"
            ).fetchall()
        return [row["symbol"] for row in rows]

    def unclosed(self, now: datetime) -> list[tuple[str, date]]:
        """(symbol, session) for each session with a report and no close
        yet whose regular session has ended by `now`."""
        from engine.core.risk_report import regular_bounds

        if not self.path.exists():
            return []
        with self._open() as con:
            rows = con.execute(
                "SELECT DISTINCT r.symbol, r.session FROM reports r LEFT JOIN closes c "
                "ON c.symbol = r.symbol AND c.session = r.session WHERE c.session IS NULL "
                "ORDER BY r.session"
            ).fetchall()
        out = []
        for row in rows:
            session = date.fromisoformat(row["session"])
            if regular_bounds(session)[1] <= now:
                out.append((row["symbol"], session))
        return out

    def unscored(self) -> list[tuple[RiskReport, dict[str, Any]]]:
        """Each report whose session has its close and no score yet, with
        that close."""
        if not self.path.exists():
            return []
        with self._open() as con:
            rows = con.execute(
                "SELECT r.raw, c.close, c.prior_close FROM reports r JOIN closes c "
                "ON c.symbol = r.symbol AND c.session = r.session LEFT JOIN scores s "
                "ON s.sha256 = r.sha256 WHERE s.sha256 IS NULL ORDER BY r.session"
            ).fetchall()
        out = []
        for row in rows:
            parsed = parse_report(row["raw"]).require()
            out.append((parsed, {"close": row["close"], "prior_close": row["prior_close"]}))
        return out

    def unscored_horizons(self, now: datetime) -> list[tuple[RiskReport, float, str, date]]:
        """(report, prior close, horizon, last session) for each longer
        horizon whose last session has ended by `now` and has no score, of
        each report whose own session's closes are recorded (the prior close
        every horizon is measured from)."""
        from engine.core.risk_report import regular_bounds

        if not self.path.exists():
            return []
        with self._open() as con:
            rows = con.execute(
                "SELECT r.sha256, r.session, r.raw, c.prior_close FROM reports r JOIN closes c "
                "ON c.symbol = r.symbol AND c.session = r.session ORDER BY r.session"
            ).fetchall()
            done = {
                (row["sha256"], row["horizon"])
                for row in con.execute("SELECT sha256, horizon FROM horizon_scores").fetchall()
            }
        out = []
        for row in rows:
            session = date.fromisoformat(row["session"])
            due = [
                (name, horizon_end(session, name))
                for name in LONGER_HORIZONS
                if (row["sha256"], name) not in done
            ]
            due = [(name, end) for name, end in due if regular_bounds(end)[1] <= now]
            if not due:
                continue
            parsed = parse_report(row["raw"]).require()
            out.extend((parsed, float(row["prior_close"]), name, end) for name, end in due)
        return out

    def sessions(self, symbol: str, limit: int = 20) -> list[dict[str, Any]]:
        """The last `limit` sessions with a report for `symbol`, oldest
        first: each session's newest report (by as_of), its close once
        recorded and its score once scored."""
        if not self.path.exists():
            return []
        with self._open() as con:
            rows = con.execute(
                """
                SELECT r.*, c.close, c.prior_close, c.prior_session, c.return_pct AS actual_pct,
                       c.recorded_at AS closed_at, s.in_90, s.in_50, s.pit, s.pinball,
                       s.move_ratio,
                       (SELECT COUNT(*) FROM reports o
                         WHERE o.symbol = r.symbol AND o.session = r.session) AS reports
                FROM reports r
                LEFT JOIN closes c ON c.symbol = r.symbol AND c.session = r.session
                LEFT JOIN scores s ON s.sha256 = r.sha256
                WHERE r.symbol = ? AND r.sha256 = (
                    SELECT n.sha256 FROM reports n
                     WHERE n.symbol = r.symbol AND n.session = r.session
                     ORDER BY n.as_of DESC, n.received_at DESC LIMIT 1)
                ORDER BY r.session DESC LIMIT ?
                """,
                [symbol, int(limit)],
            ).fetchall()
        return [_session_row(row) for row in reversed(rows)]

    def receipts(self, sha256: str) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        with self._open() as con:
            rows = con.execute(
                "SELECT received_at, operator, via FROM receipts WHERE sha256 = ? "
                "ORDER BY received_at",
                [sha256],
            ).fetchall()
        return [dict(row) for row in rows]

    def reports(self, symbol: str, limit: int = 60) -> list[dict[str, Any]]:
        """Every report for `symbol`, not only each session's newest: the
        newest session first and, inside a session, the newest report first.
        Each as `sessions` serves it, with who added it and how, whether it
        is its session's newest (the one the chart shows), whether its
        inputs are kept, and each longer horizon's score once it has one."""
        if not self.path.exists():
            return []
        with self._open() as con:
            rows = con.execute(
                f"{_LISTED} WHERE r.symbol = ? ORDER BY r.session DESC, r.as_of DESC, "
                "r.received_at DESC LIMIT ?",
                [symbol, int(limit)],
            ).fetchall()
            return _listed_rows(con, rows)

    def report(self, sha256: str) -> dict[str, Any] | None:
        """One report as `reports` lists it, with the report itself, every
        receipt, and its inputs (None when none were kept). None when it is
        not stored."""
        if not self.path.exists():
            return None
        with self._open() as con:
            row = con.execute(f"{_LISTED} WHERE r.sha256 = ?", [sha256]).fetchone()
            if row is None:
                return None
            (listed,) = _listed_rows(con, [row])
            kept = con.execute("SELECT inputs FROM inputs WHERE sha256 = ?", [sha256]).fetchone()
        return {
            **listed,
            "report": json.loads(row["raw"]),
            "receipts": self.receipts(sha256),
            "inputs": json.loads(kept["inputs"]) if kept else None,
        }


def _report_row(report: RiskReport, *, received_at: str, warnings: int) -> dict[str, Any]:
    tomorrow = report.horizon("tomorrow")
    row: dict[str, Any] = {
        "sha256": report.sha256,
        "symbol": report.symbol,
        "session": report.session.isoformat(),
        "as_of": _iso(report.as_of),
        "received_at": received_at,
        "schema_version": report.schema_version,
        "model": report.model,
        "base_price": report.base_price,
        "expected_move_pct": report.expected_move_pct,
    }
    for key in QUANTILE_KEYS:
        row[key] = float(tomorrow.quantiles[key])
    row.update(
        median_pct=tomorrow.median_pct,
        mean_pct=tomorrow.mean_pct,
        std_pct=tomorrow.std_pct,
        prob_positive=tomorrow.prob_positive,
        es5_pct=tomorrow.es5_pct,
        regime=report.regime,
        volatility_state=report.volatility_state,
        gap_risk=report.gap_risk,
        skew_bias=report.skew_bias,
        confidence=report.confidence,
        warnings=warnings,
        raw=canonical_json(dict(report.raw)),
    )
    return row


# One report and everything listed beside it (ForecastStore.reports).
_LISTED = """
SELECT r.*, c.close, c.prior_close, c.prior_session, c.return_pct AS actual_pct,
       c.recorded_at AS closed_at, s.in_90, s.in_50, s.pit, s.pinball, s.move_ratio,
       (SELECT COUNT(*) FROM reports o
         WHERE o.symbol = r.symbol AND o.session = r.session) AS reports,
       (SELECT n.sha256 FROM reports n
         WHERE n.symbol = r.symbol AND n.session = r.session
         ORDER BY n.as_of DESC, n.received_at DESC LIMIT 1) = r.sha256 AS newest,
       EXISTS (SELECT 1 FROM inputs i WHERE i.sha256 = r.sha256) AS has_inputs
FROM reports r
LEFT JOIN closes c ON c.symbol = r.symbol AND c.session = r.session
LEFT JOIN scores s ON s.sha256 = r.sha256
"""
# Receipts listed beside each report; the rest are counted.
_LISTED_RECEIPTS = 10


def _listed_rows(con: sqlite3.Connection, rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    """`rows` (from _LISTED) as ForecastStore.reports serves them."""
    if not rows:
        return []
    ids = [row["sha256"] for row in rows]
    marks = ", ".join("?" for _ in ids)
    receipts: dict[str, list[dict[str, Any]]] = {sha: [] for sha in ids}
    for found in con.execute(
        f"SELECT sha256, received_at, operator, via FROM receipts WHERE sha256 IN ({marks}) "
        "ORDER BY received_at",
        ids,
    ).fetchall():
        receipts[found["sha256"]].append(
            {
                "received_at": found["received_at"],
                "operator": found["operator"],
                "via": found["via"],
            }
        )
    horizons: dict[str, dict[str, Any]] = {sha: {} for sha in ids}
    for found in con.execute(
        f"SELECT * FROM horizon_scores WHERE sha256 IN ({marks})", ids
    ).fetchall():
        horizons[found["sha256"]][found["horizon"]] = {
            "end_session": found["end_session"],
            "end_close": found["end_close"],
            "return_pct": found["return_pct"],
            "in_90": bool(found["in_90"]),
            "in_50": bool(found["in_50"]),
            "pit": found["pit"],
            "pinball": found["pinball"],
        }
    out = []
    for row in rows:
        mine = receipts[row["sha256"]]
        out.append(
            {
                **_session_row(row),
                "model": row["model"],
                "base_price": row["base_price"],
                "mean_pct": row["mean_pct"],
                "std_pct": row["std_pct"],
                "prob_positive": row["prob_positive"],
                "es5_pct": row["es5_pct"],
                "regime": row["regime"],
                "gap_risk": row["gap_risk"],
                "skew_bias": row["skew_bias"],
                "confidence": row["confidence"],
                "warnings": row["warnings"],
                "newest": bool(row["newest"]),
                "has_inputs": bool(row["has_inputs"]),
                "receipt_count": len(mine),
                "receipts": mine[:_LISTED_RECEIPTS],
                "horizons": {
                    name: {
                        "end_session": horizon_end(
                            date.fromisoformat(row["session"]), name
                        ).isoformat(),
                        "score": horizons[row["sha256"]].get(name),
                    }
                    for name in LONGER_HORIZONS
                },
            }
        )
    return out


def _session_row(row: sqlite3.Row) -> dict[str, Any]:
    """One session as GET /api/live/risk-forecasts serves it."""
    actual = (
        {
            "return_pct": row["actual_pct"],
            "close": row["close"],
            "prior_close": row["prior_close"],
            "prior_session": row["prior_session"],
            "recorded_at": row["closed_at"],
        }
        if row["actual_pct"] is not None
        else None
    )
    score = (
        {
            "in_90": bool(row["in_90"]),
            "in_50": bool(row["in_50"]),
            "pit": row["pit"],
            "pinball": row["pinball"],
            "move_ratio": row["move_ratio"],
        }
        if row["in_90"] is not None
        else None
    )
    return {
        "session": row["session"],
        "symbol": row["symbol"],
        "sha256": row["sha256"],
        "as_of": row["as_of"],
        "received_at": row["received_at"],
        "reports": row["reports"],
        "expected_move_pct": row["expected_move_pct"],
        "median_pct": row["median_pct"],
        "quantiles": {key: row[key] for key in QUANTILE_KEYS},
        "volatility_state": row["volatility_state"],
        "actual": actual,
        "score": score,
    }


__all__ = [
    "INPUT_PARTS",
    "LONGER_HORIZONS",
    "QUANTILE_KEYS",
    "ForecastRefused",
    "ForecastStore",
    "InputsRefused",
    "as_the_page_sends",
    "default_path",
    "horizon_end",
]
