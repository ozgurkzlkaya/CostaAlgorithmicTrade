from __future__ import annotations

import abc
from datetime import datetime
from typing import Dict, Iterable, List

from data.models import Candle


class MarketDataProvider(abc.ABC):
    """Abstract market data provider supporting multiple timeframes."""

    @abc.abstractmethod
    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int) -> List[Candle]:
        raise NotImplementedError

    def fetch_multiple(self, symbols: Iterable[str], timeframe: str, limit: int) -> Dict[str, List[Candle]]:
        return {symbol: self.fetch_ohlcv(symbol, timeframe, limit) for symbol in symbols}

    def server_time(self) -> datetime:
        return datetime.utcnow()
