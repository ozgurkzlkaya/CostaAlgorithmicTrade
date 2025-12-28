from __future__ import annotations

from typing import List

from data.models import SignalCandidate, TimeframeData
from indicators.atr import average_true_range
from indicators.rsi import relative_strength_index
from risk.manager import RiskManager
from strategies.base import Strategy


def _donchian_high_low(closes: List[float], lookback: int):
    if len(closes) < lookback:
        return None, None
    high = max(closes[-lookback:])
    low = min(closes[-lookback:])
    return high, low


class BreakoutStrategy(Strategy):
    name = "breakout"

    def __init__(self, lookback: int = 20, rsi_confirm: bool = True):
        self.lookback = lookback
        self.rsi_confirm = rsi_confirm

    def generate(self, mode: str, symbol: str, data: List[TimeframeData]) -> List[SignalCandidate]:
        by_tf = {d.timeframe: d.candles for d in data}
        tf_1h = by_tf.get("1h", [])
        tf_15m = by_tf.get("15m", [])
        if not (tf_1h and tf_15m):
            return []
        closes = [c.close for c in tf_15m]
        breakout_high, breakout_low = _donchian_high_low(closes, self.lookback)
        if breakout_high is None:
            return []
        atr_values = average_true_range(tf_15m)
        atr = atr_values[-1] if atr_values else 0
        rsi_values = relative_strength_index(tf_1h)
        rsi_ok_long = not self.rsi_confirm or (rsi_values and rsi_values[-1] > 50)
        rsi_ok_short = not self.rsi_confirm or (rsi_values and rsi_values[-1] < 50)

        entry_price = tf_15m[-1].close
        risk = RiskManager()
        signals: List[SignalCandidate] = []

        if entry_price >= breakout_high and rsi_ok_long:
            sl, tp, rr = risk.determine_levels(entry_price, tf_15m, direction="LONG", atr_override=atr)
            if rr >= risk.min_rr:
                signals.append(
                    self._signal(
                        mode=mode,
                        symbol=symbol,
                        direction="LONG",
                        timeframe="15m",
                        entry=entry_price,
                        sl=sl,
                        tp=tp,
                        rr=rr,
                        score=65.0,
                        reason={"breakout": f"15m high {self.lookback} bars"},
                        filters={},
                    )
                )
        if entry_price <= breakout_low and rsi_ok_short:
            sl, tp, rr = risk.determine_levels(entry_price, tf_15m, direction="SHORT", atr_override=atr)
            if rr >= risk.min_rr:
                signals.append(
                    self._signal(
                        mode=mode,
                        symbol=symbol,
                        direction="SHORT",
                        timeframe="15m",
                        entry=entry_price,
                        sl=sl,
                        tp=tp,
                        rr=rr,
                        score=65.0,
                        reason={"breakdown": f"15m low {self.lookback} bars"},
                        filters={},
                    )
                )
        return signals
