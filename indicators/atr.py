from __future__ import annotations

from typing import List

from data.models import Candle


def average_true_range(candles: List[Candle], period: int = 14) -> List[float]:
    length = len(candles)
    if length < period + 1:
        return [None] * length

    trs: List[float] = []
    for i in range(1, length):
        current = candles[i]
        prev = candles[i - 1]
        tr = max(current.high - current.low, abs(current.high - prev.close), abs(current.low - prev.close))
        trs.append(tr)

    atr_values: List[float | None] = [None] * length
    atr = sum(trs[:period]) / period
    atr_values[period] = atr

    for i in range(period + 1, length):
        tr_index = i - 1
        atr = (atr * (period - 1) + trs[tr_index]) / period
        atr_values[i] = atr

    return atr_values
