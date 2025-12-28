from __future__ import annotations

import json
import logging
from dataclasses import asdict
from datetime import datetime

from data.models import SignalCandidate

logger = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self, enabled: bool = False, token: str = "", chat_id: str = ""):
        self.enabled = enabled and bool(token and chat_id)
        self.token = token
        self.chat_id = chat_id

    def format_message(self, signal: SignalCandidate) -> str:
        return (
            f"Mode: {signal.mode}\n"
            f"Symbol: {signal.symbol}\n"
            f"Direction: {signal.direction}\n"
            f"Timeframe: {signal.timeframe}\n"
            f"Entry: {signal.entry:.4f}\nSL: {signal.sl:.4f}\nTP: {signal.tp:.4f}\n"
            f"RR: {signal.rr:.2f}\n"
            f"Strategy: {signal.strategy}\n"
            f"Score: {signal.score}\n"
            f"Filters: {json.dumps(signal.filters)}\n"
            f"Reason: {json.dumps(signal.reason)}\n"
            f"Timestamp: {signal.generated_at.isoformat()}"
        )

    def send(self, signal: SignalCandidate):
        message = self.format_message(signal)
        if not self.enabled:
            logger.info("Telegram disabled; message would be sent", extra={"signal": asdict(signal)})
            return message
        # Placeholder: integrate with python-telegram-bot or requests later.
        logger.info("Telegram message sent", extra={"text": message})
        return message
