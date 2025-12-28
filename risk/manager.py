from __future__ import annotations

from typing import Tuple

from data.models import Candle


class RiskManager:
    def __init__(self, min_rr: float = 2.0, atr_multiplier: float = 1.5, swing_lookback: int = 5):
        self.min_rr = min_rr
        self.atr_multiplier = atr_multiplier
        self.swing_lookback = swing_lookback

    def determine_levels(self, entry: float, candles: list[Candle], direction: str, atr_override: float | None = None) -> Tuple[float, float, float]:
        sl = self._swing_stop(candles, direction)
        if sl is None:
            sl = self._atr_stop(candles, direction, atr_override)
        rr = self.min_rr
        if direction.upper() == "LONG":
            tp = entry + (entry - sl) * rr
        else:
            tp = entry - (sl - entry) * rr
        achieved_rr = abs(tp - entry) / abs(entry - sl) if sl != entry else 0
        return sl, tp, achieved_rr

    def _swing_stop(self, candles: list[Candle], direction: str) -> float | None:
        if len(candles) < self.swing_lookback + 1:
            return None
        recent = candles[-self.swing_lookback :]
        if direction.upper() == "LONG":
            return min(c.low for c in recent)
        return max(c.high for c in recent)

    def _atr_stop(self, candles: list[Candle], direction: str, atr_override: float | None = None) -> float:
        atr = atr_override if atr_override is not None else (candles[-1].high - candles[-1].low)
        if direction.upper() == "LONG":
            return candles[-1].close - atr * self.atr_multiplier
        return candles[-1].close + atr * self.atr_multiplier
