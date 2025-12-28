from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from data.models import Candle
from indicators.ema import exponential_moving_average


@dataclass
class RegimeResult:
    passed: bool
    score: float
    reason: str


class MarketRegime:
    def __init__(self, enabled: bool = True, min_trending_ratio: float = 0.6):
        self.enabled = enabled
        self.min_trending_ratio = min_trending_ratio

    def evaluate(self, btc_candles: List[Candle], breadth_ratio: float | None = None) -> RegimeResult:
        if not self.enabled:
            return RegimeResult(True, 1.0, "disabled")
        ema_fast = exponential_moving_average(btc_candles, 20)
        ema_slow = exponential_moving_average(btc_candles, 50)
        if not ema_fast or not ema_slow:
            return RegimeResult(False, 0.0, "insufficient_data")
        trending = ema_fast[-1] > ema_slow[-1]
        breadth_ok = breadth_ratio is None or breadth_ratio >= self.min_trending_ratio
        if trending and breadth_ok:
            return RegimeResult(True, 1.0, "risk_on")
        if not trending and breadth_ok:
            return RegimeResult(True, 0.7, "neutral")
        return RegimeResult(False, 0.3, "risk_off")
