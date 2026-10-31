"""
What a buy x sell matrix says (Phase 6 of docs/research/buy-sell-composition.md).

Given the trials research/composition/matrix.py recorded, per track
("no_loss" and "loss_capable" are never ranked together) and per metric:

1. CELL SCORE: the median of a cell's trials (and the best, alongside, never
   instead) -- rewarding a policy good across its parameters, not one lucky point.
2. TWO-WAY DECOMPOSITION of the buy x sell score matrix,
       score[b, s] = mu + alpha_b + beta_s + gamma_bs
   alpha ranks the buys, beta the sells, gamma is how much the best sell
   depends on the buy. Its significance is a two-way ANOVA with replication,
   the cells' calendar-year returns as the replicates (F-test; no scipy).
3. ACROSS FUNDS: the same with the fund as a third factor, so a policy that
   wins on one fund only shows as a large buy x fund (or sell x fund) share.
4. DECISION: interaction under 10% of the explained variance and not
   significant -> the best buy is argmax alpha, the best sell argmax beta,
   chosen independently. Otherwise the answer is the best PAIR (and, for each
   buy, its best sell).
5. YEARS: a year x cell table, and LEAVE-ONE-YEAR-OUT -- each cell rescored
   without a year, and the rank correlation of the whole matrix with and
   without it. A ranking that moves when 2022 goes is a ranking 2022 made.
6. STRESS WINDOWS (2018 Q4, early 2020, 2022) and the MARKET-CONDITION
   breakdown (calm/turbulent NATR regime, above/below the 200-session average).
7. OVERFITTING: PBO by CSCV over every trial's monthly returns, and the
   deflated Sharpe of the finalists with N = every trial in the matrix.

`report(trials)` renders all of it as Markdown.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

from research.optimization import overfitting

INTERACTION_SHARE_THRESHOLD = 0.10
SIGNIFICANCE = 0.05
TRACKS = ("no_loss", "loss_capable")


# ------------------------------------------------------------------ frames


def trials_frame(trials: list[dict]) -> pd.DataFrame:
    rows = []
    for n, trial in enumerate(trials):
        if trial.get("error"):
            continue
        rows.append(
            {
                "trial": n,
                "symbol": trial["symbol"],
                "buy_id": trial["buy_id"],
                "sell_id": trial["sell_id"],
                "track": trial["track"],
                "short_history": bool(trial.get("short_history")),
                **(trial.get("metrics") or {}),
            }
        )
    return pd.DataFrame(rows)


def years_frame(trials: list[dict]) -> pd.DataFrame:
    rows = []
    for n, trial in enumerate(trials):
        if trial.get("error"):
            continue
        for year in trial.get("years") or ():
            rows.append(
                {
                    "trial": n,
                    "symbol": trial["symbol"],
                    "buy_id": trial["buy_id"],
                    "sell_id": trial["sell_id"],
                    "track": trial["track"],
                    **year,
                }
            )
    return pd.DataFrame(rows)


# ------------------------------------------------------------- cell scores


def cell_scores(trials: pd.DataFrame, metric: str, track: str) -> pd.DataFrame:
    """Per (symbol, buy, sell): the median and best of the metric, and how
    many trials it took."""
    df = trials[(trials["track"] == track) & trials[metric].notna()]
    if df.empty:
        return pd.DataFrame(columns=["symbol", "buy_id", "sell_id", "median", "best", "trials"])
    grouped = df.groupby(["symbol", "buy_id", "sell_id"])[metric]
    return pd.DataFrame(
        {"median": grouped.median(), "best": grouped.max(), "trials": grouped.size()}
    ).reset_index()


def score_matrix(scores: pd.DataFrame, symbol: str | None = None) -> pd.DataFrame:
    """buy x sell matrix of median scores (averaged over funds unless one is named)."""
    df = scores if symbol is None else scores[scores["symbol"] == symbol]
    return df.pivot_table(index="buy_id", columns="sell_id", values="median", aggfunc="mean")


def _complete(matrix: pd.DataFrame) -> pd.DataFrame:
    """Rows and columns with every cell present (a two-way decomposition needs
    a complete design); drops the sparsest line first until none is missing."""
    m = matrix.copy()
    while m.isna().to_numpy().any() and m.shape[0] > 1 and m.shape[1] > 1:
        row_missing, col_missing = m.isna().sum(axis=1), m.isna().sum(axis=0)
        if row_missing.max() / m.shape[1] >= col_missing.max() / m.shape[0]:
            m = m.drop(index=row_missing.idxmax())
        else:
            m = m.drop(columns=col_missing.idxmax())
    return m.dropna(how="any")


def decompose(matrix: pd.DataFrame) -> dict[str, Any]:
    """mu, alpha (per buy), beta (per sell), gamma (per cell) and each part's
    share of the total sum of squares."""
    m = _complete(matrix)
    if m.empty or m.shape[0] < 2 or m.shape[1] < 2:
        return {"ok": False, "reason": "needs at least 2 buys x 2 sells with every cell scored"}
    y = m.to_numpy(float)
    mu = y.mean()
    alpha = y.mean(axis=1) - mu
    beta = y.mean(axis=0) - mu
    gamma = y - mu - alpha[:, None] - beta[None, :]
    ss_buy = m.shape[1] * float((alpha**2).sum())
    ss_sell = m.shape[0] * float((beta**2).sum())
    ss_int = float((gamma**2).sum())
    total = ss_buy + ss_sell + ss_int
    return {
        "ok": True,
        "mu": float(mu),
        "alpha": pd.Series(alpha, index=m.index).sort_values(ascending=False),
        "beta": pd.Series(beta, index=m.columns).sort_values(ascending=False),
        "gamma": pd.DataFrame(gamma, index=m.index, columns=m.columns),
        "share": {
            "buy": ss_buy / total if total else 0.0,
            "sell": ss_sell / total if total else 0.0,
            "interaction": ss_int / total if total else 0.0,
        },
        "dropped": {
            "buys": sorted(set(matrix.index) - set(m.index)),
            "sells": sorted(set(matrix.columns) - set(m.columns)),
        },
        "matrix": m,
    }


# ------------------------------------------------- interaction significance


def _betacf(a: float, b: float, x: float) -> float:
    """Continued fraction for the incomplete beta (Numerical Recipes 6.4)."""
    tiny, qab, qap, qam = 1e-300, a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c if abs(c) > tiny else 1.0 + aa / tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c if abs(c) > tiny else 1.0 + aa / tiny
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 3e-14:
            break
    return h


def _betainc(a: float, b: float, x: float) -> float:
    """Regularized incomplete beta I_x(a, b)."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    ln = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log1p(-x)
    front = math.exp(ln)
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b


def f_survival(f: float, d1: float, d2: float) -> float:
    """P(F > f) for an F(d1, d2) variable."""
    if f <= 0 or not math.isfinite(f):
        return 1.0 if f <= 0 else 0.0
    return _betainc(d2 / 2.0, d1 / 2.0, d2 / (d2 + d1 * f))


def interaction_test(years: pd.DataFrame, track: str, symbol: str | None = None) -> dict:
    """Two-way ANOVA with replication: buy x sell, each cell's per-year
    returns (the median over its trials, per year) as the replicates, over the
    years every cell has. F = MS_interaction / MS_within."""
    df = years[years["track"] == track]
    if symbol is not None:
        df = df[df["symbol"] == symbol]
    if df.empty:
        return {"ok": False, "reason": "no yearly results"}
    per = df.groupby(["buy_id", "sell_id", "symbol", "year"])["return_pct"].median().reset_index()
    per = per.groupby(["buy_id", "sell_id", "year"])["return_pct"].mean().reset_index()
    cells = per.groupby(["buy_id", "sell_id"])["year"].apply(set)
    common = set.intersection(*cells.tolist()) if len(cells) else set()
    per = per[per["year"].isin(common)]
    buys, sells = sorted(per["buy_id"].unique()), sorted(per["sell_id"].unique())
    r = len(common)
    if len(buys) < 2 or len(sells) < 2 or r < 2:
        return {"ok": False, "reason": "needs 2 buys x 2 sells with 2+ common years"}
    cube = np.full((len(buys), len(sells), r), np.nan)
    years_sorted = sorted(common)
    for row in per.itertuples(index=False):
        cube[buys.index(row.buy_id), sells.index(row.sell_id), years_sorted.index(row.year)] = (
            row.return_pct
        )
    if np.isnan(cube).any():
        return {"ok": False, "reason": "the design is not complete across cells and years"}
    a, b = len(buys), len(sells)
    grand = cube.mean()
    cell = cube.mean(axis=2)
    row_m, col_m = cube.mean(axis=(1, 2)), cube.mean(axis=(0, 2))
    ss_int = r * float(((cell - row_m[:, None] - col_m[None, :] + grand) ** 2).sum())
    ss_within = float(((cube - cell[:, :, None]) ** 2).sum())
    df_int, df_within = (a - 1) * (b - 1), a * b * (r - 1)
    if ss_within <= 0:
        return {"ok": False, "reason": "no variation within cells"}
    f = (ss_int / df_int) / (ss_within / df_within)
    return {
        "ok": True,
        "F": f,
        "df": (df_int, df_within),
        "p": f_survival(f, df_int, df_within),
        "years": r,
    }


def across_funds(scores: pd.DataFrame) -> dict[str, Any]:
    """Shares of variance with the fund as a third factor (no replication:
    the three-way term is the residual)."""
    cube_df = scores.pivot_table(index=["buy_id", "sell_id"], columns="symbol", values="median")
    cube_df = cube_df.dropna(axis=1, how="any")
    if cube_df.shape[1] < 2:
        return {"ok": False, "reason": "needs 2+ funds with every cell scored"}
    buys = sorted({b for b, _ in cube_df.index})
    sells = sorted({s for _, s in cube_df.index})
    funds = list(cube_df.columns)
    y = np.full((len(buys), len(sells), len(funds)), np.nan)
    for (b, s), values in cube_df.iterrows():
        y[buys.index(b), sells.index(s), :] = values.to_numpy(float)
    if np.isnan(y).any():
        return {"ok": False, "reason": "the buy x sell x fund design is not complete"}
    g = y.mean()
    mb, ms, mf = y.mean(axis=(1, 2)) - g, y.mean(axis=(0, 2)) - g, y.mean(axis=(0, 1)) - g
    mbs = y.mean(axis=2) - g - mb[:, None] - ms[None, :]
    mbf = y.mean(axis=1) - g - mb[:, None] - mf[None, :]
    msf = y.mean(axis=0) - g - ms[:, None] - mf[None, :]
    nb, ns, nf = y.shape
    parts = {
        "buy": ns * nf * float((mb**2).sum()),
        "sell": nb * nf * float((ms**2).sum()),
        "fund": nb * ns * float((mf**2).sum()),
        "buy x sell": nf * float((mbs**2).sum()),
        "buy x fund": ns * float((mbf**2).sum()),
        "sell x fund": nb * float((msf**2).sum()),
    }
    total = float(((y - g) ** 2).sum())
    parts["buy x sell x fund"] = max(0.0, total - sum(parts.values()))
    return {
        "ok": True,
        "share": {k: v / total if total else 0.0 for k, v in parts.items()},
        "funds": funds,
    }


def decide(decomposition: dict, test: dict) -> dict[str, Any]:
    """Independent best buy and best sell, or the best pair (see module doc)."""
    if not decomposition.get("ok"):
        return {"independent": None, "reason": decomposition.get("reason")}
    share = decomposition["share"]["interaction"]
    explained = sum(decomposition["share"].values()) or 1.0
    small = share / explained < INTERACTION_SHARE_THRESHOLD
    significant = bool(test.get("ok") and test["p"] < SIGNIFICANCE)
    m = decomposition["matrix"]
    best_pair = m.stack().idxmax()
    out = {
        "interaction_share": share,
        "interaction_p": test.get("p") if test.get("ok") else None,
        "best_pair": tuple(best_pair),
        "best_sell_per_buy": {b: m.loc[b].idxmax() for b in m.index},
    }
    if small and not significant:
        out.update(
            independent=True,
            best_buy=decomposition["alpha"].index[0],
            best_sell=decomposition["beta"].index[0],
        )
    else:
        out.update(independent=False, best_buy=None, best_sell=None)
    return out


# ------------------------------------------------------------------- years


def _cagr(returns_pct: pd.Series) -> float:
    growth = float(np.prod(1 + returns_pct.to_numpy(float) / 100.0))
    return (
        (growth ** (1 / len(returns_pct)) - 1) * 100 if len(returns_pct) and growth > 0 else -100.0
    )


def year_table(years: pd.DataFrame, track: str) -> pd.DataFrame:
    """year x cell median return (all funds pooled by median)."""
    df = years[years["track"] == track]
    if df.empty:
        return pd.DataFrame()
    df = df.assign(cell=df["buy_id"] + " / " + df["sell_id"])
    return df.pivot_table(index="cell", columns="year", values="return_pct", aggfunc="median")


def leave_one_year_out(years: pd.DataFrame, track: str) -> pd.DataFrame:
    """Per year: the Spearman correlation of the cell ranking (by compound
    annual return over the remaining years) with the full-period ranking, and
    the top cell each way."""
    table = year_table(years, track)
    if table.empty or table.shape[1] < 3:
        return pd.DataFrame()
    table = table.dropna(axis=0, how="any")
    if len(table) < 2:
        return pd.DataFrame()  # a ranking needs two cells
    full = table.apply(_cagr, axis=1)
    rows = []
    for year in table.columns:
        without = table.drop(columns=year).apply(_cagr, axis=1)
        rows.append(
            {
                "year": int(year),
                "rank_correlation": float(full.rank().corr(without.rank())),
                "top_cell": full.idxmax(),
                "top_cell_without": without.idxmax(),
                "year_median_return_pct": float(table[year].median()),
            }
        )
    return pd.DataFrame(rows).sort_values("rank_correlation")


def stress_table(trials: list[dict], track: str) -> pd.DataFrame:
    rows = []
    for trial in trials:
        if trial.get("error") or trial.get("track") != track:
            continue
        for window, figures in (trial.get("stress") or {}).items():
            rows.append(
                {
                    "cell": f"{trial['buy_id']} / {trial['sell_id']}",
                    "window": window,
                    **figures,
                }
            )
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    return df.pivot_table(
        index="cell", columns="window", values=["return_pct", "max_drawdown_pct"], aggfunc="median"
    )


def regime_table(trials: list[dict], track: str) -> pd.DataFrame:
    """Per sell policy: median annualised log return in each market condition."""
    rows = []
    for trial in trials:
        if trial.get("error") or trial.get("track") != track:
            continue
        for label, figures in (trial.get("regimes") or {}).items():
            if figures["days"] > 0:
                rows.append(
                    {
                        "sell_id": trial["sell_id"],
                        "condition": label,
                        "annualised_pct": 100 * figures["log_return"] * 252 / figures["days"],
                    }
                )
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    return df.pivot_table(
        index="sell_id", columns="condition", values="annualised_pct", aggfunc="median"
    )


# ------------------------------------------------------------- overfitting


def _safe_sharpe(returns) -> float:
    r = np.asarray(returns, dtype=float)
    sd = r.std(ddof=1) if r.size > 1 else 0.0
    return float(r.mean() / sd) if sd > 0 else 0.0


def monthly_matrix(trials: list[dict], track: str) -> pd.DataFrame:
    """months x trials, the months every trial has."""
    series = {}
    for n, trial in enumerate(trials):
        if trial.get("error") or trial.get("track") != track or not trial.get("monthly"):
            continue
        series[n] = pd.Series(trial["monthly"], index=trial["monthly_index"])
    if not series:
        return pd.DataFrame()
    return pd.DataFrame(series).dropna(axis=0, how="any")


def overfitting_check(trials: list[dict], track: str, finalists: int = 3) -> dict[str, Any]:
    matrix = monthly_matrix(trials, track)
    if matrix.shape[1] < 2 or matrix.shape[0] < 16:
        return {"ok": False, "reason": "needs 2+ trials over 16+ common months"}
    groups = 8 if matrix.shape[0] >= 32 else 4
    pbo = overfitting.probability_of_backtest_overfitting(
        matrix.to_numpy(), groups, metric=_safe_sharpe
    )
    sharpes = matrix.apply(_safe_sharpe)
    variance = float(sharpes.var(ddof=1)) if len(sharpes) > 1 else 0.0
    out = []
    for trial_id in sharpes.sort_values(ascending=False).index[:finalists]:
        r = matrix[trial_id].to_numpy(float)
        if r.std(ddof=1) <= 0:
            continue
        skew, kurt = overfitting.moments(r)
        dsr = overfitting.deflated_sharpe(
            _safe_sharpe(r), variance, int(matrix.shape[1]), len(r), skew, kurt
        )
        trial = trials[trial_id]
        out.append(
            {
                "cell": f"{trial['buy_id']} / {trial['sell_id']}",
                "symbol": trial["symbol"],
                "monthly_sharpe": float(sharpes[trial_id]),
                "deflated_sharpe": float(dsr),
            }
        )
    return {
        "ok": True,
        "pbo": pbo["pbo"],
        "splits": pbo["n_splits"],
        "trials": int(matrix.shape[1]),
        "finalists": out,
    }


# ------------------------------------------------------------------ report


def _md(df: pd.DataFrame, digits: int = 2) -> str:
    if df is None or df.empty:
        return "_none_\n"
    frame = df.copy()
    frame.columns = [
        " / ".join(map(str, c)) if isinstance(c, tuple) else str(c) for c in frame.columns
    ]
    frame = frame.reset_index()
    header = "| " + " | ".join(map(str, frame.columns)) + " |"
    rule = "| " + " | ".join("---" for _ in frame.columns) + " |"
    lines = [header, rule]
    for row in frame.itertuples(index=False):
        cells = []
        for value in row:
            if isinstance(value, float):
                cells.append("" if math.isnan(value) else f"{value:.{digits}f}")
            else:
                cells.append(str(value))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def analyse(trials: list[dict], metric: str = "Calmar") -> dict[str, Any]:
    frame, years = trials_frame(trials), years_frame(trials)
    out: dict[str, Any] = {}
    for track in TRACKS:
        if frame.empty or (frame["track"] == track).sum() == 0:
            continue
        scores = cell_scores(frame, metric, track)
        decomposition = decompose(score_matrix(scores))
        test = interaction_test(years, track) if not years.empty else {"ok": False}
        out[track] = {
            "scores": scores,
            "decomposition": decomposition,
            "interaction_test": test,
            "decision": decide(decomposition, test),
            "across_funds": across_funds(scores),
            "years": year_table(years, track) if not years.empty else pd.DataFrame(),
            "leave_one_year_out": leave_one_year_out(years, track)
            if not years.empty
            else pd.DataFrame(),
            "stress": stress_table(trials, track),
            "regimes": regime_table(trials, track),
            "overfitting": overfitting_check(trials, track),
        }
    return out


def report(trials: list[dict], metric: str = "Calmar", title: str = "Buy x sell matrix") -> str:
    results = analyse(trials, metric)
    frame = trials_frame(trials)
    errors = sum(1 for t in trials if t.get("error"))
    lines = [f"# {title}", "", f"Metric: **{metric}** (cell score = median over its trials).", ""]
    if not frame.empty:
        lines.append(
            f"{len(frame)} trials over {frame['symbol'].nunique()} fund(s); {errors} trial(s) "
            "failed and are excluded."
        )
        short = sorted(frame.loc[frame["short_history"], "symbol"].unique())
        if short:
            lines.append(f"Under 10 years of history (marked, not excluded): {', '.join(short)}.")
    for track, result in results.items():
        lines += ["", f"## Track: {track.replace('_', '-')}", ""]
        if track == "loss_capable":
            lines.append("These sell policies may sell below cost (signal exits). Ranked apart.\n")
        dec = result["decomposition"]
        decision = result["decision"]
        if dec.get("ok"):
            share = dec["share"]
            lines.append(
                f"Variance shares: buy {share['buy']:.0%}, sell {share['sell']:.0%}, "
                f"interaction {share['interaction']:.0%}."
            )
            test = result["interaction_test"]
            if test.get("ok"):
                lines.append(
                    f"Interaction F({test['df'][0]}, {test['df'][1]}) = {test['F']:.2f}, "
                    f"p = {test['p']:.3f} over {test['years']} common years."
                )
            if decision.get("independent"):
                lines.append(
                    f"\n**Independent:** best buy **{decision['best_buy']}**, best sell "
                    f"**{decision['best_sell']}**."
                )
            else:
                lines.append(
                    f"\n**Not independent:** the best pair is **{decision['best_pair'][0]} + "
                    f"{decision['best_pair'][1]}**; the best sell depends on the buy (table below)."
                )
            lines += ["", "### Buy x sell (median score, funds averaged)", "", _md(dec["matrix"])]
            lines += ["### Buy main effects", "", _md(dec["alpha"].to_frame("alpha"))]
            lines += ["### Sell main effects", "", _md(dec["beta"].to_frame("beta"))]
            lines += [
                "### Best sell for each buy",
                "",
                _md(pd.Series(decision["best_sell_per_buy"]).to_frame("best sell")),
            ]
            if dec["dropped"]["buys"] or dec["dropped"]["sells"]:
                lines.append(f"Dropped for an incomplete design: {dec['dropped']}.\n")
        else:
            lines.append(f"Decomposition not possible: {dec.get('reason')}.\n")
        funds = result["across_funds"]
        if funds.get("ok"):
            lines += [
                "### Across funds (variance shares)",
                "",
                _md(pd.Series(funds["share"]).to_frame("share")),
            ]
        lines += ["### Leave one year out", "", _md(result["leave_one_year_out"], 3)]
        lines += ["### Year x cell (median return %)", "", _md(result["years"])]
        lines += ["### Stress windows (median)", "", _md(result["stress"])]
        lines += ["### Market conditions: sell policy, annualised %", "", _md(result["regimes"])]
        over = result["overfitting"]
        if over.get("ok"):
            lines.append(
                f"### Overfitting\n\nPBO {over['pbo']:.2f} over {over['splits']} CSCV splits of "
                f"{over['trials']} trials.\n"
            )
            lines.append(
                _md(
                    pd.DataFrame(over["finalists"]).set_index("cell")
                    if over["finalists"]
                    else pd.DataFrame(),
                    3,
                )
            )
        else:
            lines.append(f"### Overfitting\n\n{over.get('reason')}\n")
    return "\n".join(lines) + "\n"


__all__ = [
    "analyse",
    "cell_scores",
    "decide",
    "decompose",
    "f_survival",
    "interaction_test",
    "leave_one_year_out",
    "report",
]
