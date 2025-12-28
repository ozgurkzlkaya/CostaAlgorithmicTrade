from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class Candle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class SignalCandidate:
    mode: str
    symbol: str
    strategy: str
    direction: str
    timeframe: str
    entry: float
    sl: float
    tp: float
    rr: float
    score: float
    reason: Dict[str, str]
    filters: Dict[str, str]
    generated_at: datetime


@dataclass
class BacktestResult:
    trades: int
    total_return: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    expectancy: float
    sharpe: Optional[float]
    train_period: str
    test_period: str
    params: Dict[str, float]


@dataclass
class TimeframeData:
    timeframe: str
    candles: List[Candle]
