from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class ScoreContext:
    mode: str
    volatility_reason: str = ""
    regime_reason: str = ""
    regime_score: float = 1.0
    backtest_metrics: Optional[Dict[str, float]] = None
    strategy_params: Optional[Dict[str, float]] = None
