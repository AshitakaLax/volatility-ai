"""
Static intraday volatility profile -- how volatile each minute of the
session is, relative to the session average.

--------------------------------------------------------------------
WHY THIS EXISTS

The two event calendars in this package (fomc_calendar,
earnings_calendar) both flag rare DAYS: 2.8% and 11.1% of sessions
respectively, each worth ~1-2 percentage points of total return when
wired to a sizing multiplier. Time of day is a far larger effect and it
is present in EVERY session:

    09:30-10:00   +152% vs the all-day average
    12:00-14:00    -36%

Measured on this repo's own 10-year TQQQ SIP dataset, 2,655 samples per
minute -- this is one of the best-sampled effects in the project, not an
inference from a handful of events.

--------------------------------------------------------------------
WHY RANGE, NOT CLOSE-TO-CLOSE

The stored quantity is mean intrabar RANGE, (high - low) / close, not
the standard deviation of close-to-close returns. Two reasons, and the
first is decisive:

  1. It is what the strategy actually experiences. The intrabar fill
     model (see config/search_hf_intrabar.yaml's header) fills resting
     limit orders when a level is TOUCHED inside a bar. Bar range is
     exactly the quantity that determines whether a touch happens;
     close-to-close is not, and undercounts by ~1.85x on this dataset.

  2. It is defined for the first bar of the session. A close-to-close
     return at 09:30 is computed against the PREVIOUS session's close,
     so it measures the overnight gap rather than intraday movement.
     Measured that way, minute 0 reads 15.6x the session average --
     an artifact of the gap, not a property of the minute. Range has no
     such contamination.

--------------------------------------------------------------------
WHAT THE CURVE LOOKS LIKE

A U, with two additional spikes that are structural rather than noise:

    minute   0 (09:30)   2.56   <- the peak; the open
    minute  30 (10:00)   2.09   <- 10:00 ET macro releases (ISM,
                                   consumer confidence, JOLTS)
    minute 180 (12:30)   0.92   <- midday trough
    minute 269 (13:59)   0.71   <- the minimum
    minute 380 (15:50)   1.82   <- closing auction / MOC imbalances
    minute 389 (15:59)   1.61

Open (first 30 minutes) runs 2.18x midday (12:30-14:30).

--------------------------------------------------------------------
NORMALIZATION AND JOIN SEMANTICS

Values are normalized so the session mean is exactly 1.0, which makes
the profile directly usable as a multiplier base: an exponent of 0.0
turns the whole thing into a no-op without needing a separate flag.

Indexed by MINUTES SINCE 09:30 EASTERN, 0-389, matching how
MarketContext.time_of_day_flag is populated. Eastern rather than UTC
because the session boundary is an Eastern-time concept and the offset
changes twice a year; the conversion helper here mirrors
fomc_calendar's exactly and imports its EASTERN_TZ rather than
redefining it.

Minutes outside 0-389 return 1.0 (neutral). That is not a defensive
nicety: the backtest dataset is regular-hours only, but the live path
can legitimately see an extended-hours bar, and a neutral multiplier is
the only safe reading for a minute this profile says nothing about.
"""

from __future__ import annotations

from datetime import UTC, datetime

from src.fomc_calendar import EASTERN_TZ

SESSION_OPEN_MINUTE = 9 * 60 + 30  # 09:30 Eastern
SESSION_MINUTES = 390

# Mean intrabar range per minute-of-session, normalized to mean 1.0.
# Generated from data/TQQQ_1Min_sip_all_2016-01-01_2026-08-21.csv
# (1,035,332 bars / 2,674 sessions). Regenerate with the same
# normalization if the dataset is extended.
INTRADAY_RANGE_PROFILE: tuple[float, ...] = (
    2.5606, 2.2905, 2.1042, 1.9636, 1.8899, 2.0488,  # 09:30
    1.8930, 1.7479, 1.7190, 1.6775, 1.8793, 1.6824,  # 09:36
    1.6448, 1.5845, 1.5575, 1.8643, 1.6641, 1.5699,  # 09:42
    1.5822, 1.5323, 1.7208, 1.5674, 1.5141, 1.4623,  # 09:48
    1.4309, 1.5177, 1.4357, 1.3560, 1.3160, 1.3121,  # 09:54
    2.0874, 1.6561, 1.5421, 1.4305, 1.4079, 1.5185,  # 10:00
    1.4806, 1.4051, 1.3566, 1.3296, 1.4725, 1.3878,  # 10:06
    1.3949, 1.3061, 1.2864, 1.4465, 1.3803, 1.2990,  # 10:12
    1.2731, 1.2303, 1.3517, 1.3069, 1.2783, 1.2273,  # 10:18
    1.2331, 1.3089, 1.2565, 1.2118, 1.2051, 1.1853,  # 10:24
    1.4756, 1.2787, 1.2383, 1.2320, 1.1596, 1.2660,  # 10:30
    1.2472, 1.2038, 1.1956, 1.1288, 1.2636, 1.1798,  # 10:36
    1.1693, 1.1334, 1.1109, 1.2372, 1.1975, 1.1218,  # 10:42
    1.1144, 1.0673, 1.2237, 1.1633, 1.1225, 1.0614,  # 10:48
    1.0626, 1.1430, 1.0956, 1.0557, 1.0308, 1.0238,  # 10:54
    1.3307, 1.1680, 1.1254, 1.0859, 1.0463, 1.1227,  # 11:00
    1.1037, 1.0534, 1.0273, 1.0065, 1.1083, 1.0359,  # 11:06
    1.0290, 0.9934, 0.9794, 1.1154, 1.0435, 0.9877,  # 11:12
    0.9772, 0.9597, 1.0606, 1.0057, 0.9765, 0.9455,  # 11:18
    0.9357, 1.0125, 0.9987, 0.9328, 0.9483, 0.9409,  # 11:24
    1.1306, 1.0278, 0.9835, 0.9659, 0.9567, 1.0243,  # 11:30
    0.9827, 0.9463, 0.9253, 0.8930, 0.9794, 0.9297,  # 11:36
    0.9310, 0.9062, 0.9039, 0.9812, 0.9309, 0.9070,  # 11:42
    0.8842, 0.8421, 0.9697, 0.9014, 0.8897, 0.8570,  # 11:48
    0.8431, 0.9036, 0.9088, 0.8610, 0.8586, 0.8316,  # 11:54
    1.0577, 0.9494, 0.9111, 0.8700, 0.8391, 0.9221,  # 12:00
    0.8926, 0.8664, 0.8425, 0.8176, 0.9045, 0.8451,  # 12:06
    0.8310, 0.8093, 0.7921, 0.9162, 0.8606, 0.8303,  # 12:12
    0.8174, 0.7872, 0.8825, 0.8458, 0.8121, 0.7974,  # 12:18
    0.8004, 0.8585, 0.8075, 0.8014, 0.7830, 0.7518,  # 12:24
    0.9193, 0.8648, 0.8171, 0.8113, 0.7735, 0.8468,  # 12:30
    0.8214, 0.7877, 0.7826, 0.7435, 0.8358, 0.7937,  # 12:36
    0.7770, 0.7605, 0.7430, 0.8471, 0.7981, 0.7726,  # 12:42
    0.7717, 0.7327, 0.8439, 0.8041, 0.7895, 0.7551,  # 12:48
    0.7269, 0.8017, 0.7826, 0.7484, 0.7299, 0.7305,  # 12:54
    0.9630, 0.8947, 0.9068, 0.8299, 0.7810, 0.8455,  # 13:00
    0.8431, 0.7981, 0.7769, 0.7437, 0.8435, 0.7928,  # 13:06
    0.7720, 0.7515, 0.7350, 0.8382, 0.8053, 0.7736,  # 13:12
    0.7589, 0.7444, 0.8422, 0.7955, 0.7814, 0.7693,  # 13:18
    0.7259, 0.7941, 0.7603, 0.7473, 0.7668, 0.7296,  # 13:24
    0.9239, 0.8107, 0.8032, 0.7661, 0.7399, 0.8127,  # 13:30
    0.8014, 0.7623, 0.7609, 0.7263, 0.8229, 0.7638,  # 13:36
    0.7522, 0.7319, 0.7130, 0.8100, 0.7879, 0.7528,  # 13:42
    0.7551, 0.7237, 0.8025, 0.7660, 0.7386, 0.7167,  # 13:48
    0.7180, 0.7825, 0.7387, 0.7254, 0.7193, 0.7082,  # 13:54
    1.2025, 1.0314, 0.9663, 0.8998, 0.8559, 0.9288,  # 14:00
    0.8875, 0.8714, 0.8276, 0.8102, 0.8989, 0.8412,  # 14:06
    0.8239, 0.7921, 0.7751, 0.8958, 0.8539, 0.8038,  # 14:12
    0.7965, 0.7766, 0.8679, 0.8228, 0.8078, 0.7899,  # 14:18
    0.7659, 0.8467, 0.7962, 0.8094, 0.7907, 0.7625,  # 14:24
    0.9916, 0.8828, 0.8465, 0.8250, 0.7838, 0.8940,  # 14:30
    0.8636, 0.8427, 0.8096, 0.7923, 0.8870, 0.8353,  # 14:36
    0.8486, 0.8186, 0.7928, 0.9047, 0.8375, 0.8399,  # 14:42
    0.8416, 0.7940, 0.9003, 0.8656, 0.8330, 0.8137,  # 14:48
    0.8139, 0.8803, 0.8271, 0.8006, 0.7762, 0.7836,  # 14:54
    1.0980, 0.9621, 0.9360, 0.8917, 0.8437, 0.9153,  # 15:00
    0.8996, 0.8521, 0.8589, 0.8282, 0.9340, 0.8865,  # 15:06
    0.8828, 0.8399, 0.8259, 0.9596, 0.8916, 0.8680,  # 15:12
    0.8400, 0.8041, 0.9392, 0.8774, 0.8506, 0.8277,  # 15:18
    0.8232, 0.8905, 0.8308, 0.8357, 0.8353, 0.8192,  # 15:24
    1.0703, 0.9500, 0.9365, 0.9000, 0.8572, 0.9497,  # 15:30
    0.9002, 0.8815, 0.8668, 0.8549, 0.9703, 0.8911,  # 15:36
    0.9014, 0.8629, 0.8814, 1.1035, 0.9548, 0.9175,  # 15:42
    0.9178, 0.9401, 1.8166, 1.0828, 0.9987, 0.9808,  # 15:48
    1.3108, 1.3832, 0.9725, 0.9307, 0.9110, 1.6079,  # 15:54
)


def minutes_since_open(timestamp: datetime) -> int:
    """Minutes from 09:30 Eastern, or -1 if outside the regular session.

    Naive input is treated as UTC, matching fomc_calendar's stated
    convention and every real data source in this codebase.
    """
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)
    eastern = timestamp.astimezone(EASTERN_TZ)
    offset = eastern.hour * 60 + eastern.minute - SESSION_OPEN_MINUTE
    return offset if 0 <= offset < SESSION_MINUTES else -1


def relative_range(minute: int) -> float:
    """Profile value for a minute-since-open, or 1.0 (neutral) for any
    minute outside the regular session. See module docstring."""
    if 0 <= minute < SESSION_MINUTES:
        return INTRADAY_RANGE_PROFILE[minute]
    return 1.0
