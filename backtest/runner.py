from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import json

from data.models import BacktestResult


class BacktestRunner:
    def __init__(self, storage_dir: str = "storage/backtests"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_result(self, mode: str, symbol: str, strategy: str, tf: str, result: BacktestResult) -> Path:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        path = self.storage_dir / f"{mode}_{symbol}_{strategy}_{tf}_{timestamp}.json"
        with path.open("w", encoding="utf-8") as f:
            json.dump(asdict(result), f, indent=2)
        return path

    def meets_gate(self, result: BacktestResult, min_trades: int, min_profit_factor: float, max_drawdown: float) -> bool:
        return (
            result.trades >= min_trades
            and result.profit_factor >= min_profit_factor
            and result.max_drawdown <= max_drawdown
        )
