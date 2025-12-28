from __future__ import annotations

from statistics import mean, pstdev
from typing import List

from data.models import Candle


def bollinger_bands(candles: List[Candle], period: int = 20, std_dev: float = 2.0):
    closes = [c.close for c in candles]
    if len(closes) < period:
        return [], [], []
    upper: List[float] = [None] * (period - 1)
    middle: List[float] = [None] * (period - 1)
    lower: List[float] = [None] * (period - 1)
    for i in range(period - 1, len(closes)):
        window = closes[i - period + 1 : i + 1]
        m = mean(window)
        s = pstdev(window)
        middle.append(m)
        upper.append(m + std_dev * s)
        lower.append(m - std_dev * s)
    return upper, middle, lower
