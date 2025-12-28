from __future__ import annotations

from statistics import mean, pstdev
from typing import List

from data.models import Candle


def bollinger_bands(candles: List[Candle], period: int = 20, std_dev: float = 2.0):
    closes = [c.close for c in candles]
    if len(closes) < period:
        return [], [], []
    upper: List[float] = []
    middle: List[float] = []
    lower: List[float] = []
    for i in range(period, len(closes) + 1):
        window = closes[i - period : i]
        m = mean(window)
        s = pstdev(window)
        middle.append(m)
        upper.append(m + std_dev * s)
        lower.append(m - std_dev * s)
    padding = [closes[0]] * (len(closes) - len(upper))
    return padding + upper, padding + middle, padding + lower
