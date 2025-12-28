from __future__ import annotations

import logging
import sys
from datetime import datetime

from backtest.runner import BacktestRunner
from config.loader import load_config
from data.providers.crypto import StubCryptoProvider
from data.providers.forex import StubForexProvider
from filters.news import BlackoutWindow, NewsFilter
from filters.regime import MarketRegime
from filters.volatility import VolatilityFilter
from live.scanner import SignalScanner
from notify.telegram import TelegramNotifier
from scoring.engine import ScoreEngine
from storage.db import Storage
from storage.logging_config import setup_logging
from strategies.breakout import BreakoutStrategy
from strategies.mean_reversion import MeanReversionStrategy
from strategies.trend_following import TrendFollowingStrategy

logger = logging.getLogger(__name__)


def build_provider(mode: str, config: dict):
    if mode == "FOREX":
        return StubForexProvider()
    return StubCryptoProvider(exchange=config.get("exchange", "binance"), cache=config.get("cache", True))


def _parse_iso8601(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def build_news_filter(cfg: dict) -> NewsFilter:
    windows = [
        BlackoutWindow(start=_parse_iso8601(item["start"]), end=_parse_iso8601(item["end"]), reason=item.get("reason", ""))
        for item in cfg.get("blackout_windows", [])
    ]
    return NewsFilter(
        enabled=cfg.get("enabled", False),
        pre_block=cfg.get("pre_event_block_minutes", 30),
        post_block=cfg.get("post_event_block_minutes", 30),
        blackout_windows=windows,
    )


def main():
    override_path = sys.argv[1] if len(sys.argv) > 1 else None
    config = load_config(override=override_path)
    setup_logging(config["logging"]["path"], config["logging"]["signal_path"], config["logging"].get("level", "INFO"))
    storage = Storage(config["storage"]["sqlite_path"], ensure_schema=config["storage"].get("ensure_schema", True))
    notifier = TelegramNotifier(**config.get("telegram", {}))
    provider_cfg = config.get("providers", {})
    provider = build_provider(config["mode"], provider_cfg)
    strategies = []
    if config["strategies"]["trend_following"]["enabled"]:
        s = config["strategies"]["trend_following"]
        strategies.append(
            TrendFollowingStrategy(
                ema_fast=s.get("ema_fast", 20),
                ema_slow=s.get("ema_slow", 50),
                rsi_threshold_long=s.get("rsi_threshold_long", 50),
                rsi_threshold_short=s.get("rsi_threshold_short", 50),
            )
        )
    if config["strategies"]["breakout"]["enabled"]:
        s = config["strategies"]["breakout"]
        strategies.append(BreakoutStrategy(lookback=s.get("lookback", 20), rsi_confirm=s.get("rsi_confirm", True)))
    if config["strategies"]["mean_reversion"]["enabled"]:
        s = config["strategies"]["mean_reversion"]
        strategies.append(
            MeanReversionStrategy(
                bollinger_period=s.get("bollinger_period", 20),
                bollinger_std=s.get("bollinger_std", 2.0),
            )
        )

    vol_filter = VolatilityFilter(**config["filters"]["volatility"])
    news_filter = build_news_filter(config["filters"].get("news", {}))
    regime_filter = MarketRegime(min_trending_ratio=config["filters"].get("market_regime", {}).get("min_trending_ratio", 0.6))
    backtest_gate = {
        "enabled": config.get("backtest", {}).get("enabled", True),
        "min_trades": config["backtest"].get("min_trades", 0),
        "min_profit_factor": config["backtest"].get("min_profit_factor", 0),
        "max_drawdown": config["backtest"].get("max_drawdown", 1),
        "min_candles": config.get("scan", {}).get("min_closed_candles", 250),
        "dummy_metrics": {"trades": 100, "profit_factor": 1.5, "max_drawdown": 0.2},
    }
    scoring_engine = ScoreEngine(config.get("scoring", {}))

    scanner = SignalScanner(
        mode=config["mode"],
        provider=provider,
        strategies=strategies,
        notifier=notifier,
        storage=storage,
        news_filter=news_filter,
        volatility_filter=vol_filter,
        regime_filter=regime_filter,
        cooldown_minutes=config["scan"].get("cooldown_minutes", 30),
        max_signals=config["scan"].get("max_signals_per_cycle", 3),
        score_engine=scoring_engine,
        scoring_config=config.get("scoring", {}),
    )

    symbols = config.get("symbols", {}).get("pairs" if config["mode"] == "FOREX" else "universe", [])
    if isinstance(symbols, str):
        symbols = [symbols]
    timeframes = config["scan"].get("timeframes", ["15m", "1h", "4h"])
    try:
        for symbol in symbols:
            signals = scanner.scan_symbol(symbol, timeframes, backtest_gate)
            scanner.dispatch(signals)
    finally:
        storage.close()


if __name__ == "__main__":
    main()
