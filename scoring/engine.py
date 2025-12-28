from __future__ import annotations

from typing import Dict, List

from data.models import SignalCandidate, TimeframeData
from indicators.bollinger import bollinger_bands
from indicators.ema import exponential_moving_average
from indicators.rsi import relative_strength_index
from scoring.models import ScoreContext


def clamp(value: float, min_value: float = 0.0, max_value: float = 1.0) -> float:
    return max(min_value, min(max_value, value))


class ScoreEngine:
    def __init__(self, config: Dict):
        self.config = config or {}
        thresholds = self.config.get("thresholds", {})
        self.threshold_crypto = thresholds.get("CRYPTO_FUTURES", 0)
        self.threshold_forex = thresholds.get("FOREX", 0)
        self.regime_multipliers = self.config.get(
            "regime_multiplier", {"risk_on": 1.0, "neutral": 0.85, "risk_off": 0.65}
        )
        self.enabled = self.config.get("enabled", True)

    def passes_threshold(self, mode: str, score: float) -> bool:
        if not self.enabled:
            return True
        if mode == "FOREX":
            return score >= self.threshold_forex
        return score >= self.threshold_crypto

    def _component_trend(self, candidate: SignalCandidate, tf_map: Dict[str, List], context: ScoreContext) -> float:
        candles_4h = tf_map.get("4h", [])
        if not candles_4h:
            return 0.0
        ema_fast = exponential_moving_average(candles_4h, 20)
        ema_slow = exponential_moving_average(candles_4h, 50)
        if len(ema_fast) < 1 or len(ema_slow) < 1:
            return 0.0
        close = candles_4h[-1].close
        diff = abs(ema_fast[-1] - ema_slow[-1])
        trend_strength = clamp((diff / close) / 0.02 if close else 0.0)
        trend_long = ema_fast[-1] > ema_slow[-1]
        trend_short = ema_fast[-1] < ema_slow[-1]
        base = 0.0
        if candidate.strategy in {"trend_following", "breakout"}:
            if (candidate.direction == "LONG" and trend_long) or (candidate.direction == "SHORT" and trend_short):
                base = 10 + 15 * trend_strength
        else:  # mean_reversion
            base = 6 * (1 - trend_strength)
        if candidate.mode == "CRYPTO_FUTURES":
            multiplier = self.regime_multipliers.get(context.regime_reason, 1.0)
            base *= multiplier
        return base

    def _component_setup(self, candidate: SignalCandidate, tf_map: Dict[str, List]) -> float:
        rsi_1h = relative_strength_index(tf_map.get("1h", []))
        rsi_15m = relative_strength_index(tf_map.get("15m", []))
        score = 0.0
        if candidate.strategy in {"trend_following", "breakout"}:
            if not rsi_1h:
                return 0.0
            last = rsi_1h[-1]
            if candidate.direction == "LONG":
                score = 20 * clamp((last - 50) / 20)
            else:
                score = 20 * clamp((50 - last) / 20)
        else:
            if not rsi_15m:
                return 0.0
            last = rsi_15m[-1]
            if candidate.direction == "LONG":
                score = 20 * clamp((35 - last) / 15)
            else:
                score = 20 * clamp((last - 65) / 15)
        return score

    def _component_entry_trigger(self, candidate: SignalCandidate, tf_map: Dict[str, List]) -> float:
        candles_15m = tf_map.get("15m", [])
        if not candles_15m:
            return 0.0
        close = candles_15m[-1].close
        if candidate.strategy == "trend_following":
            ema_20 = exponential_moving_average(candles_15m, 20)
            if not ema_20:
                return 0.0
            momentum = clamp((abs(close - ema_20[-1]) / close) / 0.003 if close else 0.0)
            return 10 + 5 * momentum
        if candidate.strategy == "breakout":
            closes = [c.close for c in candles_15m]
            lookback = int(self.config.get("params", {}).get("breakout_lookback", 20))
            if len(closes) < lookback:
                return 0.0
            high = max(closes[-lookback:])
            low = min(closes[-lookback:])
            if candidate.direction == "LONG":
                breakout_margin = clamp(((close - high) / close) / 0.002 if close else 0.0)
            else:
                breakout_margin = clamp(((low - close) / close) / 0.002 if close else 0.0)
            return 15 * breakout_margin
        # mean_reversion
        upper, _, lower = bollinger_bands(candles_15m, period=20, std_dev=2)
        if not upper or not lower:
            return 0.0
        if candidate.direction == "LONG":
            band_margin = clamp(((lower[-1] - close) / close) / 0.002 if close else 0.0)
        else:
            band_margin = clamp(((close - upper[-1]) / close) / 0.002 if close else 0.0)
        return 15 * band_margin

    def _component_vol_penalty(self, candidate: SignalCandidate, context: ScoreContext) -> float:
        reason = context.volatility_reason or ""
        score = 0.0
        if "atr_ratio_high" in reason:
            score -= 5
        if "atr_ratio_low" in reason:
            if candidate.strategy == "breakout":
                score -= 5
            elif candidate.strategy == "mean_reversion":
                score += 2
        return score

    def _component_rr(self, candidate: SignalCandidate) -> float:
        return 10 + 5 * clamp((candidate.rr - 2) / 1)

    def _component_strategy_specific(self, candidate: SignalCandidate) -> float:
        if candidate.strategy == "trend_following":
            return 7 + 5 + 3
        if candidate.strategy == "breakout":
            return 5 + 5 + 5
        return 8 + 4 + 3

    def _component_backtest(self, context: ScoreContext) -> float:
        metrics = context.backtest_metrics or {}
        pf = metrics.get("profit_factor")
        dd = metrics.get("max_drawdown")
        trades = metrics.get("trades")
        score = 0.0
        if pf is not None:
            score += 6 * clamp((pf - 1.0) / 1.0)
        if dd is not None:
            score += 4 * clamp((0.3 - dd) / 0.3)
        if trades is not None:
            score += 2 * clamp((trades - 50) / 50)
        return score

    def score(self, candidate: SignalCandidate, tf_data: List[TimeframeData], context: ScoreContext) -> float:
        if not self.enabled:
            return candidate.score
        tf_map = {tf.timeframe: tf.candles for tf in tf_data}
        components = [
            self._component_trend(candidate, tf_map, context),
            self._component_setup(candidate, tf_map),
            self._component_entry_trigger(candidate, tf_map),
            self._component_vol_penalty(candidate, context),
            self._component_rr(candidate),
            self._component_strategy_specific(candidate),
            self._component_backtest(context),
        ]
        total = sum(components)
        return clamp(total, 0, 100)
