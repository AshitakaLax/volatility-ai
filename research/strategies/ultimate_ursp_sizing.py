"""
Ultimate-URSP: Ultimate-RSP's timing book with a graded bear gate, for
URSP (ProShares Ultra S&P 500 Equal Weight, 2x daily) -- design and
evidence in docs/research/ultimate-ursp.md.

URSP has traded since 2025-08-27, so the design was measured on a
simulated history: 2x RSP's daily total return, financed at fed funds
plus a spread calibrated to the real fund, less its 0.95% fee
(tools/simulate_ursp.py), spliced with the real fund.

--------------------------------------------------------------------
WHY THE RSP BOOK NEEDED ANOTHER LAYER

Ultimate-RSP was measured on 2017-2026, which holds no prolonged bear
market. On the simulated URSP over 2004-2026 its timing votes stayed
"in" for much of 2008, and the 2x fund fell 66% with them (buy-and-hold
URSP: -88%). The fix comes from the TQQQ work: a leveraged book must not
stay invested deep into a bear market. A single drawdown threshold was
a spike, since 2008 is one event and the result hung on the day the
threshold fired. So the gate is GRADED, a ridge across its settings:

  gate = clip((bear_dd_full - DD) / (bear_dd_full - bear_dd_start), 0, 1)
  DD   = 1 - close / (highest close of the last bear_window sessions)

  target = ensemble target (UltimateRspSizing's PD/AD votes) x gate

Full exposure while the fund is within bear_dd_start (25%) of its
one-year high, none once it is bear_dd_full (55%) below it, linear in
between. Read at the previous close (causal), like the votes.

--------------------------------------------------------------------
A WIDER REBALANCE BAND, BECAUSE URSP IS THIN

URSP trades a median ~12,000 shares (~$0.5M) a day; its spread is a
multiple of what the engine's cost model (built on TQQQ and RSP)
charges. The book moves only when the target is more than 20% of equity
away (Ultimate-RSP: 5%) -- indistinguishable at the model's costs, and
1-2.7 points of CAGR better at four to ten times them.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from datetime import date

from engine.core.exceptions import ConfigurationError
from research.strategies.ultimate_rsp_sizing import RspTimingSignal, UltimateRspSizing


class BearGatedTimingSignal(RspTimingSignal):
    """RspTimingSignal x a graded bear gate on the same session closes."""

    def __init__(self, *, bear_window: int, bear_dd_start: float, bear_dd_full: float, **params):
        super().__init__(**params)
        self.bear_dd_start, self.bear_dd_full = float(bear_dd_start), float(bear_dd_full)
        self._bear_closes: deque = deque(maxlen=int(bear_window))
        self.gate: float | None = None
        self.ensemble: float | None = None

    def _close_session(self) -> None:
        self._bear_closes.append(self._c)
        super()._close_session()  # sets self.target to the ensemble
        dd = 1.0 - self._bear_closes[-1] / max(self._bear_closes)
        span = self.bear_dd_full - self.bear_dd_start
        self.gate = min(1.0, max(0.0, (self.bear_dd_full - dd) / span))
        self.ensemble = self.target
        self.target = self.target * self.gate


class UltimateUrspSizing(UltimateRspSizing):
    """Ultimate-RSP's daily exposure book with a graded bear gate: see the
    module docstring."""

    def __init__(
        self,
        pd_periods: str = "14,21,42",
        pd_lookbacks: str = "100,250",
        ad_params: str = "3/10,5/20,10/40",
        ad_lookbacks: str = "100,250",
        pd_weight: float = 0.5,
        execute_minute: int = 60,
        rebalance_band: float = 0.20,
        max_exposure: float = 1.0,
        cash_buffer: float = 0.005,
        bear_window: int = 250,
        bear_dd_start: float = 0.25,
        bear_dd_full: float = 0.55,
        exposure_by_date: Mapping[date, float] | None = None,
    ) -> None:
        if bear_window < 2:
            raise ConfigurationError(f"bear_window must be >= 2, got {bear_window}")
        if not 0.0 <= bear_dd_start < bear_dd_full < 1.0:
            raise ConfigurationError(
                "need 0 <= bear_dd_start < bear_dd_full < 1, got "
                f"{bear_dd_start} and {bear_dd_full}"
            )
        super().__init__(
            pd_periods=pd_periods,
            pd_lookbacks=pd_lookbacks,
            ad_params=ad_params,
            ad_lookbacks=ad_lookbacks,
            pd_weight=pd_weight,
            execute_minute=execute_minute,
            rebalance_band=rebalance_band,
            max_exposure=max_exposure,
            cash_buffer=cash_buffer,
            exposure_by_date=exposure_by_date,
        )
        self.bear_window = int(bear_window)
        self.bear_dd_start, self.bear_dd_full = float(bear_dd_start), float(bear_dd_full)
        if self._signal is not None:
            base = self._signal
            self._signal = BearGatedTimingSignal(
                bear_window=bear_window,
                bear_dd_start=bear_dd_start,
                bear_dd_full=bear_dd_full,
                pd_periods=base.pd_periods,
                pd_lookbacks=base.pd_lookbacks,
                ad_params=base.ad_params,
                ad_lookbacks=base.ad_lookbacks,
                pd_weight=base.pd_weight,
            )

    def diagnostics(self) -> dict:
        out = super().diagnostics()
        if self._signal is not None:
            out.update(
                ultimate_ursp_gate=self._signal.gate,
                ultimate_ursp_ensemble=self._signal.ensemble,
            )
        return out


__all__ = ["BearGatedTimingSignal", "UltimateUrspSizing"]
