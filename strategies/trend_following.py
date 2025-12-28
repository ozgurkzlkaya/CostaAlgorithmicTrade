from __future__ import annotations

from typing import List

from data.models import SignalCandidate, TimeframeData
from indicators.ema import exponential_moving_average
from indicators.rsi import relative_strength_index
from risk.manager import RiskManager
from strategies.base import Strategy


class TrendFollowingStrategy(Strategy):
    name = "trend_following"

    def __init__(self, ema_fast: int = 20, ema_slow: int = 50, rsi_threshold_long: int = 50, rsi_threshold_short: int = 50):
        self.ema_fast = ema_fast
        self.ema_slow = ema_slow
        self.rsi_threshold_long = rsi_threshold_long
        self.rsi_threshold_short = rsi_threshold_short

    def generate(self, mode: str, symbol: str, data: List[TimeframeData]) -> List[SignalCandidate]:
        by_tf = {d.timeframe: d.candles for d in data}
        tf_4h = by_tf.get("4h", [])
        tf_1h = by_tf.get("1h", [])
        tf_15m = by_tf.get("15m", [])
        if not (tf_4h and tf_1h and tf_15m):
            return []
        ema_4h_fast = exponential_moving_average(tf_4h, self.ema_fast)
        ema_4h_slow = exponential_moving_average(tf_4h, self.ema_slow)
        ema_15m_fast = exponential_moving_average(tf_15m, self.ema_fast)
        ema_15m_slow = exponential_moving_average(tf_15m, self.ema_slow)
        rsi_1h = relative_strength_index(tf_1h)

        signals: List[SignalCandidate] = []
        trend_long = ema_4h_fast[-1] > ema_4h_slow[-1]
        trend_short = ema_4h_fast[-1] < ema_4h_slow[-1]
        rsi_bias_long = rsi_1h[-1] >= self.rsi_threshold_long if rsi_1h else False
        rsi_bias_short = rsi_1h[-1] <= 100 - self.rsi_threshold_short if rsi_1h else False

        entry_price = tf_15m[-1].close
        risk = RiskManager()

        if trend_long and rsi_bias_long and ema_15m_fast[-1] > ema_15m_slow[-1]:
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
                        score=70.0,
                        reason={
                            "4h_trend": "EMA20>EMA50",
                            "1h_rsi": f"RSI={rsi_1h[-1]:.1f}",
                            "15m_trend": "EMA20>EMA50",
                        },
                        filters={},
                    )
                )
        if trend_short and rsi_bias_short and ema_15m_fast[-1] < ema_15m_slow[-1]:
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
                        score=70.0,
                        reason={
                            "4h_trend": "EMA20<EMA50",
                            "1h_rsi": f"RSI={rsi_1h[-1]:.1f}",
                            "15m_trend": "EMA20<EMA50",
                        },
                        filters={},
                    )
                )
        return signals
