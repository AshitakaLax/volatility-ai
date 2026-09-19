"""
Detecting bars that were FABRICATED rather than traded.

--------------------------------------------------------------------
WHY THIS IS ONE FUNCTION AND NOT A COPY IN EACH STRATEGY

src/historical_data.resample_to_uniform_minutes gives every session the
same bar count by inserting flat, zero-volume bars into minutes that had
no print. That is a claim about the DATA FORMAT, and anything that reads
those datasets needs to recognise them.

Two strategies were carrying byte-identical copies of the test --
HighFrequencyLocalReferenceSizing and BayesianDualScaleSizing. Nothing
was wrong with either, but a rule that describes how another module
writes files must have exactly one definition, or the two drift the
first time the fabricator changes. If resample_to_uniform_minutes ever
wrote volume=NaN instead of 0.0, or carried forward differently, one
strategy would be updated and the other would silently keep matching the
old shape.

This project already settled this argument once, for timezones:
src/earnings_calendar.py imports EASTERN_TZ from src/fomc_calendar.py
rather than redefining it, explicitly so "the two calendars cannot drift
apart on timezone handling". Same reasoning, same fix.

It lives here rather than in src/historical_data.py because a sizing
strategy has no business importing the download layer -- historical_data
pulls in the retry policy, the SDK bootstrap and the whole fetch path.
This module imports nothing.

--------------------------------------------------------------------
WHY THE TEST IS WHAT IT IS

A fabricated bar is flat (high == low == close) AND unchanged from the
previous real print, because that is precisely what carrying a price
forward produces.

The detector is deliberately NOT `volume == 0`, and that was measured,
not assumed. On the live path context.volume is ALWAYS 0.0 (LiveBar
carries no volume field), so gating on volume would not merely skip
fabricated bars -- it would disable realized-vol scaling in live trading
permanently, including on whatever config is running in production.

--------------------------------------------------------------------
IT IS A HEURISTIC, AND THE ERROR RATE IS KNOWN

Some genuinely real bars are also flat and unchanged -- thin
extended-hours liquidity, mostly. Measured on the real (non-resampled)
extended-hours dataset, 2-5% of genuine bars match this test in every
year sampled (2016: 2.1%, 2019: 5.0%, 2023: 5.2%, 2026: 0.7%).

That rate matters less than its FLATNESS. The problem being solved is
that fabricated bars run 52.2% of 2016 against 0.6% of 2026, and with
this project's measured-negative vol_scale_exponent that gradient sizes
UP in the early years for a reason that is an artifact of bar density
rather than a market signal. A false-positive rate that is roughly
constant across years does not reintroduce that bias; it is small,
flat noise instead.

The real fix is giving the live path real volume, which would let this
read context.volume directly. That is a separate, pre-existing gap in
the live data adapter.
"""

from __future__ import annotations


def is_synthetic_bar(high: float, low: float, price: float, prev_price: float | None) -> bool:
    """True when this bar looks fabricated rather than traded.

    prev_price is the last observed price, or None if this is the first
    bar seen. The first bar is never treated as synthetic: there is
    nothing to compare it against, and misreading it would silently drop
    a real observation from every rolling window that follows.
    """
    return high == low and prev_price is not None and price == prev_price
