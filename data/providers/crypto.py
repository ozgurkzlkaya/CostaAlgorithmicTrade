from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

from data.models import Candle
from data.providers.base import MarketDataProvider


class StubCryptoProvider(MarketDataProvider):
    """CCXT-compatible placeholder provider with in-memory synthetic candles."""

    def __init__(self, exchange: str = "binance", cache: bool = True):
        self.exchange = exchange
        self.cache = cache

    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int) -> List[Candle]:
        # Synthetic sine-wave candles keep architecture testable without API keys.
        now = datetime.utcnow()
        candles: List[Candle] = []
        duration = self._timeframe_to_timedelta(timeframe)
        price = 100.0
        for i in range(limit):
            ts = now - duration * (limit - i)
            high = price * 1.01
            low = price * 0.99
            close = price * (1.0 + ((i % 5) - 2) * 0.001)
            candle = Candle(timestamp=ts, open=price, high=high, low=low, close=close, volume=1000)
            candles.append(candle)
            price = close
        return candles

    @staticmethod
    def _timeframe_to_timedelta(tf: str) -> timedelta:
        mapping = {"15m": timedelta(minutes=15), "1h": timedelta(hours=1), "4h": timedelta(hours=4)}
        return mapping.get(tf, timedelta(minutes=1))
