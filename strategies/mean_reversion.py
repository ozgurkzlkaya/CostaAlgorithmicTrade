from __future__ import annotations

from typing import List, Optional

from data.models import SignalCandidate, TimeframeData
from indicators.bollinger import bollinger_bands
from indicators.rsi import relative_strength_index
from risk.manager import RiskManager
from strategies.base import Strategy


class MeanReversionStrategy(Strategy):
    name = "mean_reversion"

    def __init__(self, bollinger_period: int = 20, bollinger_std: float = 2.0, rsi_ob: int = 70, rsi_os: int = 30):
        self.bollinger_period = bollinger_period
        self.bollinger_std = bollinger_std
        self.rsi_ob = rsi_ob
        self.rsi_os = rsi_os

    def generate(self, mode: str, symbol: str, data: List[TimeframeData]) -> List[SignalCandidate]:
        by_tf = {d.timeframe: d.candles for d in data}
        tf_4h = by_tf.get("4h", [])
        tf_15m = by_tf.get("15m", [])
        if not (tf_4h and tf_15m):
            return []
        upper, _, lower = bollinger_bands(tf_15m, self.bollinger_period, self.bollinger_std)
        upper_last = _last_non_none(upper)
        lower_last = _last_non_none(lower)
        rsi = relative_strength_index(tf_15m)
        if upper_last is None or lower_last is None or not rsi:
            return []
        entry_price = tf_15m[-1].close
        risk = RiskManager()
        signals: List[SignalCandidate] = []

        trending_up = tf_4h[-1].close > tf_4h[0].close
        trending_down = tf_4h[-1].close < tf_4h[0].close

        if entry_price <= lower_last and rsi[-1] < self.rsi_os and not trending_down:
            sl, tp, rr = risk.determine_levels(entry_price, tf_15m, direction="LONG")
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
                        score=55.0,
                        reason={"mean_reversion": "Lower band + RSI oversold"},
                        filters={"trend_bias": "Range/Bullish" if trending_up else "Neutral"},
                    )
                )
        if entry_price >= upper_last and rsi[-1] > self.rsi_ob and not trending_up:
            sl, tp, rr = risk.determine_levels(entry_price, tf_15m, direction="SHORT")
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
                        score=55.0,
                        reason={"mean_reversion": "Upper band + RSI overbought"},
                        filters={"trend_bias": "Range/Bearish" if trending_down else "Neutral"},
                    )
                )
        return signals


def _last_non_none(values: List[Optional[float]]) -> Optional[float]:
    for value in reversed(values):
        if value is not None:
            return value
    return None
