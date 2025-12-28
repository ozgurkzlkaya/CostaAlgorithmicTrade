from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict

from data.models import SignalCandidate, BacktestResult


SCHEMA = {
    "signals": """
    CREATE TABLE IF NOT EXISTS signals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT,
        mode TEXT,
        symbol TEXT,
        strategy TEXT,
        direction TEXT,
        entry REAL,
        sl REAL,
        tp REAL,
        rr REAL,
        score REAL,
        filters TEXT,
        reason_json TEXT
    );
    """,
    "backtests": """
    CREATE TABLE IF NOT EXISTS backtests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT,
        mode TEXT,
        symbol TEXT,
        strategy TEXT,
        tf TEXT,
        params_json TEXT,
        metrics_json TEXT,
        oos_metrics_json TEXT,
        data_range TEXT
    );
    """,
    "errors": """
    CREATE TABLE IF NOT EXISTS errors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT,
        context TEXT,
        message TEXT,
        stack TEXT
    );
    """,
}


class Storage:
    def __init__(self, path: str = "storage/bot.sqlite", ensure_schema: bool = True):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        if ensure_schema:
            self._apply_schema()

    def _apply_schema(self):
        cur = self.conn.cursor()
        for ddl in SCHEMA.values():
            cur.executescript(ddl)
        self.conn.commit()

    def save_signal(self, signal: SignalCandidate):
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO signals (ts, mode, symbol, strategy, direction, entry, sl, tp, rr, score, filters, reason_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                signal.generated_at.isoformat(),
                signal.mode,
                signal.symbol,
                signal.strategy,
                signal.direction,
                signal.entry,
                signal.sl,
                signal.tp,
                signal.rr,
                signal.score,
                json.dumps(signal.filters),
                json.dumps(signal.reason),
            ),
        )
        self.conn.commit()

    def save_backtest(self, mode: str, symbol: str, strategy: str, tf: str, result: BacktestResult, data_range: str):
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO backtests (ts, mode, symbol, strategy, tf, params_json, metrics_json, oos_metrics_json, data_range)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.utcnow().isoformat(),
                mode,
                symbol,
                strategy,
                tf,
                json.dumps(result.params),
                json.dumps({
                    "trades": result.trades,
                    "total_return": result.total_return,
                    "max_drawdown": result.max_drawdown,
                    "win_rate": result.win_rate,
                    "profit_factor": result.profit_factor,
                    "expectancy": result.expectancy,
                    "sharpe": result.sharpe,
                }),
                json.dumps({"test_period": result.test_period}),
                data_range,
            ),
        )
        self.conn.commit()

    def log_error(self, context: str, message: str, stack: str = ""):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO errors (ts, context, message, stack) VALUES (?, ?, ?, ?)",
            (datetime.utcnow().isoformat(), context, message, stack),
        )
        self.conn.commit()

    def close(self):
        self.conn.close()
