from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List

from backtest.runner import BacktestRunner
from data.models import SignalCandidate, TimeframeData
from data.providers.base import MarketDataProvider
from filters.news import NewsFilter
from filters.regime import MarketRegime
from filters.volatility import VolatilityFilter
from scoring.engine import ScoreEngine
from scoring.models import ScoreContext
from notify.telegram import TelegramNotifier
from storage.db import Storage
from strategies.base import Strategy

logger = logging.getLogger(__name__)


class SignalScanner:
    def __init__(
        self,
        mode: str,
        provider: MarketDataProvider,
        strategies: List[Strategy],
        notifier: TelegramNotifier,
        storage: Storage,
        news_filter: NewsFilter,
        volatility_filter: VolatilityFilter,
        regime_filter: MarketRegime,
        cooldown_minutes: int = 30,
        max_signals: int = 3,
        backtest_runner: BacktestRunner | None = None,
        score_engine: ScoreEngine | None = None,
        scoring_config: Dict | None = None,
    ):
        self.mode = mode
        self.provider = provider
        self.strategies = strategies
        self.notifier = notifier
        self.storage = storage
        self.news_filter = news_filter
        self.volatility_filter = volatility_filter
        self.regime_filter = regime_filter
        self.cooldown = timedelta(minutes=cooldown_minutes)
        self.max_signals = max_signals
        self.backtest_runner = backtest_runner or BacktestRunner()
        self.score_engine = score_engine
        self.scoring_config = scoring_config or {}
        self.last_sent: Dict[str, datetime] = defaultdict(lambda: datetime.min)

    def _evaluate_regime(self, tf_data: List[TimeframeData]):
        try:
            return self.regime_filter.evaluate({tf.timeframe: tf.candles for tf in tf_data}["4h"])
        except Exception:
            return self.regime_filter.evaluate([])

    def _apply_cooldown(self, signal: SignalCandidate) -> bool:
        key = f"{signal.symbol}-{signal.strategy}-{signal.direction}"
        last = self.last_sent[key]
        if datetime.utcnow() - last < self.cooldown:
            return False
        self.last_sent[key] = datetime.utcnow()
        return True

    def _passes_backtest_gate(self, signal: SignalCandidate, config: Dict) -> bool:
        # In a full implementation we'd load persisted metrics. Here we check placeholders.
        if not config.get("enabled", True):
            return True
        min_trades = config.get("min_trades", 0)
        min_profit_factor = config.get("min_profit_factor", 0)
        max_drawdown = config.get("max_drawdown", 1.0)
        dummy = config.get("dummy_metrics")
        if not dummy:
            logger.warning("Backtest gate: missing metrics", extra={"symbol": signal.symbol})
            return True
        return (
            dummy.get("trades", 0) >= min_trades
            and dummy.get("profit_factor", 0) >= min_profit_factor
            and dummy.get("max_drawdown", 1) <= max_drawdown
        )

    def scan_symbol(self, symbol: str, timeframes: List[str], backtest_gate: Dict) -> List[SignalCandidate]:
        tf_data: List[TimeframeData] = []
        for tf in timeframes:
            candles = self.provider.fetch_ohlcv(symbol, tf, limit=backtest_gate.get("min_candles", 250))
            tf_data.append(TimeframeData(timeframe=tf, candles=candles))
        vol_result = self.volatility_filter.evaluate(tf_data[0].candles)
        regime_result = self._evaluate_regime(tf_data)
        now = self.provider.server_time()
        news_result = self.news_filter.evaluate(now)
        if not regime_result.passed:
            logger.info(
                "Regime filter blocked signal",
                extra={"symbol": symbol, "regime": regime_result.reason},
            )
            return []
        if not (vol_result.passed and news_result.passed):
            logger.info(
                "Filter blocked signal",
                extra={"symbol": symbol, "vol": vol_result.reason, "news": news_result.reason},
            )
            return []
        signals: List[SignalCandidate] = []
        for strategy in self.strategies:
            signals.extend(strategy.generate(self.mode, symbol, tf_data))
        filtered = []
        for signal in signals:
            signal.filters["volatility"] = vol_result.reason
            signal.filters["news"] = news_result.reason
            signal.filters["regime"] = regime_result.reason
            if not self._passes_backtest_gate(signal, backtest_gate):
                continue
            if not self._apply_cooldown(signal):
                continue
            if self.score_engine:
                context = ScoreContext(
                    mode=self.mode,
                    volatility_reason=vol_result.reason,
                    regime_reason=regime_result.reason,
                    regime_score=regime_result.score,
                    backtest_metrics=backtest_gate.get("dummy_metrics", {}),
                    strategy_params=self.scoring_config.get("params"),
                )
                signal.score = self.score_engine.score(signal, tf_data, context)
                if not self.score_engine.passes_threshold(self.mode, signal.score):
                    continue
            filtered.append(signal)
        return sorted(filtered, key=lambda s: s.score, reverse=True)[: self.max_signals]

    def dispatch(self, signals: List[SignalCandidate]):
        for signal in signals:
            message = self.notifier.send(signal)
            self.storage.save_signal(signal)
            logger.info("Signal dispatched", extra={"message": message})
