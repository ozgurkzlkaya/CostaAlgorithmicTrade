from __future__ import annotations

from typing import List

from data.models import Candle


def exponential_moving_average(candles: List[Candle], period: int) -> List[float]:
    closes = [c.close for c in candles]
    if not closes or period <= 0:
        return []
    k = 2 / (period + 1)
    ema_values: List[float] = []
    ema = closes[0]
    for price in closes:
        ema = price * k + ema * (1 - k)
        ema_values.append(ema)
    return ema_values
