from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from data.models import Candle
from indicators.atr import average_true_range


@dataclass
class VolatilityFilterResult:
    passed: bool
    reason: str


class VolatilityFilter:
    def __init__(
        self,
        enabled: bool = True,
        high: float = 0.06,
        low: float = 0.01,
        atr_ratio_high: float | None = None,
        atr_ratio_low: float | None = None,
    ):
        self.enabled = enabled
        self.high = high if atr_ratio_high is None else atr_ratio_high
        self.low = low if atr_ratio_low is None else atr_ratio_low

    def evaluate(self, candles: List[Candle]) -> VolatilityFilterResult:
        if not self.enabled or not candles:
            return VolatilityFilterResult(True, "disabled")
        atr_values = average_true_range(candles)
        if not atr_values:
            return VolatilityFilterResult(False, "insufficient_data")
        atr = self._last_value(atr_values)
        if atr is None:
            return VolatilityFilterResult(False, "insufficient_data")
        price = candles[-1].close
        ratio = atr / price if price else 0
        if ratio > self.high:
            return VolatilityFilterResult(False, f"atr_ratio_high:{ratio:.4f}")
        if ratio < self.low:
            return VolatilityFilterResult(False, f"atr_ratio_low:{ratio:.4f}")
        return VolatilityFilterResult(True, f"atr_ratio_ok:{ratio:.4f}")

    @staticmethod
    def _last_value(values: List[Optional[float]]) -> Optional[float]:
        for value in reversed(values):
            if value is not None:
                return value
        return None
