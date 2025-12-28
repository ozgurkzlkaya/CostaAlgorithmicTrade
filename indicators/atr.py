from __future__ import annotations

from typing import List

from data.models import Candle


def average_true_range(candles: List[Candle], period: int = 14) -> List[float]:
    if len(candles) < period + 1:
        return []
    trs: List[float] = []
    for i in range(1, len(candles)):
        current = candles[i]
        prev = candles[i - 1]
        tr = max(current.high - current.low, abs(current.high - prev.close), abs(current.low - prev.close))
        trs.append(tr)
    atr_values: List[float] = []
    atr = sum(trs[:period]) / period
    for i in range(period, len(trs)):
        atr = (atr * (period - 1) + trs[i]) / period
        atr_values.append(atr)
    padding = [atr_values[0]] * (len(candles) - len(atr_values)) if atr_values else [0.0] * len(candles)
    return padding + atr_values
