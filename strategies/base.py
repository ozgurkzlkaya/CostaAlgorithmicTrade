from __future__ import annotations

import abc
from datetime import datetime
from typing import Dict, List

from data.models import SignalCandidate, TimeframeData


class Strategy(abc.ABC):
    name: str = "base"

    @abc.abstractmethod
    def generate(self, mode: str, symbol: str, data: List[TimeframeData]) -> List[SignalCandidate]:
        raise NotImplementedError

    def _signal(self, **kwargs) -> SignalCandidate:
        defaults: Dict = {
            "strategy": self.name,
            "reason": {},
            "filters": {},
            "generated_at": datetime.utcnow(),
        }
        defaults.update(kwargs)
        if "direction" in defaults and isinstance(defaults["direction"], str):
            defaults["direction"] = defaults["direction"].upper()
        return SignalCandidate(**defaults)
