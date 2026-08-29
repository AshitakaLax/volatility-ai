"""
Alpaca market-data adapter -- the live loop's price source.

Separate from src/alpaca_broker.py on purpose: trading and market data
are different Alpaca products with different clients, different
entitlements, and different failure modes. A data-subscription problem
should not look like a broker outage, and an account that can trade may
still be unable to read SIP.

Supplies exactly what src/live_trading_loop.py needs to build one
MarketContext -- the latest bar and whether the market is open -- and
nothing else. It holds no state, so it cannot disagree with itself
between ticks.

--------------------------------------------------------------------
ON THE FEED, which is the setting most likely to bite:

IEX is the default because every Alpaca account has it. It reports
only IEX's own prints, roughly a few percent of consolidated volume,
so its bars can differ from the consolidated tape -- thinner bars,
occasional gaps in a quiet minute.

SIP is the consolidated tape and is what a backtest built from
historical SIP data actually assumed. It requires a paid subscription;
selecting it without one fails every request rather than silently
degrading. If the backtest that chose these parameters used SIP data,
running live on IEX is a real backtest/live mismatch -- flagged here
because it is invisible at runtime, not because the code can fix it.
--------------------------------------------------------------------
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from src.exceptions import ConfigurationError, DataValidationError
from src.retry_policy import RetryConfig, retry_call


@dataclass(frozen=True)
class LiveBar:
    """One bar, reduced to the fields MarketContext needs.

    A plain local type rather than alpaca-py's Bar so the trading loop
    depends on this codebase's shape and not on the SDK's -- the same
    reason the broker adapter returns a BrokerSnapshot rather than raw
    Alpaca objects.
    """

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    # Alpaca's Bar model has always carried this (verified against the
    # installed SDK: Bar.model_fields includes 'volume'). It was simply
    # never read here, which meant context.volume was ALWAYS 0.0 on the
    # live path regardless of what the feed actually reported --
    # MarketContext.volume's own convention treats 0.0 as "unknown," so
    # HighFrequencyLocalReferenceSizing's volume_scale_exponent silently
    # never activates live no matter what a config sets it to. Defaults
    # to 0.0 (not None) so a feed that ever omits it degrades to the
    # existing "unknown" behavior rather than raising.
    volume: float = 0.0


def _require_alpaca_data():
    """Import the market-data SDK lazily, matching the broker adapter's
    optional-dependency handling."""
    try:
        from alpaca.data.enums import DataFeed
        from alpaca.data.historical import StockHistoricalDataClient
        from alpaca.data.requests import StockLatestBarRequest
    except ImportError as e:  # pragma: no cover - exercised only without the SDK
        raise ConfigurationError(
            "alpaca-py is required for live market data but is not installed. "
            "Install it with `pip install alpaca-py`."
        ) from e
    return DataFeed, StockHistoricalDataClient, StockLatestBarRequest


class AlpacaMarketData:
    """Reads the latest bar and the market clock from Alpaca."""

    def __init__(
        self,
        credentials=None,
        *,
        feed: str = "iex",
        data_client: Any = None,
        trading_client: Any = None,
        retry_config: RetryConfig | None = None,
    ) -> None:
        """Build a data reader.

        trading_client is where the market clock comes from -- the clock
        is a trading-API endpoint, not a data-API one. Pass the same
        client AlpacaBroker already holds rather than opening a second
        connection; is_open() needs it and latest_bar() does not.

        Both clients are injectable so the trading loop's tests can run
        a full session with no network.
        """
        self.feed = feed
        self._retry_config = retry_config or RetryConfig()
        self._trading_client = trading_client

        if data_client is not None:
            self._data_client = data_client
        else:
            if credentials is None:
                raise ConfigurationError(
                    "AlpacaMarketData requires either LiveCredentials or an injected data_client."
                )
            _, StockHistoricalDataClient, _ = _require_alpaca_data()
            # Credentials are used here and not retained, matching
            # AlpacaBroker: nothing on this instance can leak them.
            self._data_client = StockHistoricalDataClient(
                api_key=credentials.api_key_id,
                secret_key=credentials.api_secret_key,
            )

    def latest_bar(self, symbol: str) -> LiveBar:
        """The most recent bar for symbol.

        Raises DataValidationError when the feed returns no bar for the
        symbol rather than fabricating one or returning None. A missing
        bar is a real condition on IEX during a quiet minute, and the
        trading loop must skip that tick rather than act on invented
        prices -- an exception makes that impossible to ignore, where a
        None would invite a caller to paper over it.
        """
        DataFeed, _, StockLatestBarRequest = _require_alpaca_data()
        request = StockLatestBarRequest(symbol_or_symbols=symbol, feed=DataFeed(self.feed))

        bars = retry_call(
            lambda: self._data_client.get_stock_latest_bar(request),
            self._retry_config,
            after_submission=False,
        )
        bar = (bars or {}).get(symbol)
        if bar is None:
            raise DataValidationError(
                f"No bar returned for {symbol!r} on the {self.feed!r} feed. On IEX this can "
                "simply mean no IEX print occurred in the interval; the tick must be skipped, "
                "not filled in."
            )
        return LiveBar(
            timestamp=bar.timestamp,
            open=float(bar.open),
            high=float(bar.high),
            low=float(bar.low),
            close=float(bar.close),
            volume=float(getattr(bar, "volume", 0.0) or 0.0),
        )

    def is_open(self) -> bool:
        """Whether the market is currently open, per Alpaca's own clock.

        Alpaca's clock is authoritative rather than a local
        weekday/time calculation: it already accounts for holidays and
        early closes, which a hand-rolled schedule gets wrong a handful
        of days a year -- exactly the days an unattended 24/7 process
        would be trading against a closed book.
        """
        if self._trading_client is None:
            raise ConfigurationError(
                "is_open() needs the trading client (the market clock is a trading-API "
                "endpoint). Construct AlpacaMarketData with trading_client=..."
            )
        clock = retry_call(
            self._trading_client.get_clock, self._retry_config, after_submission=False
        )
        return bool(clock.is_open)
