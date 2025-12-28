from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
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
        if self.blackout_windows and self.blackout_windows[0].start.tzinfo and now.tzinfo is None:
            now = now.replace(tzinfo=self.blackout_windows[0].start.tzinfo)
        for window in self.blackout_windows:
            start = window.start - timedelta(minutes=self.pre_block)
            end = window.end + timedelta(minutes=self.post_block)
            if start <= now <= end:
                return NewsFilterResult(False, f"blackout:{window.reason}")
        return NewsFilterResult(True, "clear")
