from __future__ import annotations

from typing import List

from data.models import Candle


def relative_strength_index(candles: List[Candle], period: int = 14) -> List[float]:
    closes = [c.close for c in candles]
    if len(closes) < period + 1:
        return []
    gains: List[float] = []
    losses: List[float] = []
    for i in range(1, len(closes)):
        change = closes[i] - closes[i - 1]
        gains.append(max(change, 0))
        losses.append(abs(min(change, 0)))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    rsi_values: List[float] = []
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0:
            rsi_values.append(100.0)
            continue
        rs = avg_gain / avg_loss
        rsi_values.append(100 - (100 / (1 + rs)))
    # Pad with NaN-like placeholders for early candles
    padding = [50.0] * (len(closes) - len(rsi_values))
    return padding + rsi_values
