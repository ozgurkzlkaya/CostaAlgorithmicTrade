from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class BlackoutWindow:
    start: datetime
    end: datetime
    reason: str = ""


@dataclass
class NewsFilterResult:
    passed: bool
    reason: str


class NewsFilter:
    def __init__(self, enabled: bool = False, pre_block: int = 30, post_block: int = 30, blackout_windows: Optional[List[BlackoutWindow]] = None):
        self.enabled = enabled
        self.pre_block = pre_block
        self.post_block = post_block
        self.blackout_windows = blackout_windows or []

    def evaluate(self, now: datetime) -> NewsFilterResult:
        if not self.enabled:
            return NewsFilterResult(True, "disabled")
        for window in self.blackout_windows:
            if window.start <= now <= window.end:
                return NewsFilterResult(False, f"blackout:{window.reason}")
        return NewsFilterResult(True, "clear")
