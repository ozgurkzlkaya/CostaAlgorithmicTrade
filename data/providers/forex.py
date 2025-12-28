from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

from data.models import Candle
from data.providers.base import MarketDataProvider


class StubForexProvider(MarketDataProvider):
    """Simple synthetic forex provider to exercise filters/news gates."""

    def __init__(self, name: str = "stub-forex"):
        self.name = name

    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int) -> List[Candle]:
        now = datetime.utcnow()
        duration = self._timeframe_to_timedelta(timeframe)
        candles: List[Candle] = []
        price = 1800.0 if symbol == "XAUUSD" else 1.1
        for i in range(limit):
            ts = now - duration * (limit - i)
            drift = ((i % 4) - 1) * 0.0005
            close = price * (1 + drift)
            high = max(price, close) * 1.0008
            low = min(price, close) * 0.9992
            candles.append(Candle(timestamp=ts, open=price, high=high, low=low, close=close, volume=1000))
            price = close
        return candles

    @staticmethod
    def _timeframe_to_timedelta(tf: str) -> timedelta:
        mapping = {"15m": timedelta(minutes=15), "1h": timedelta(hours=1), "4h": timedelta(hours=4)}
        return mapping.get(tf, timedelta(minutes=1))
