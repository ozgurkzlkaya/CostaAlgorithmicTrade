from __future__ import annotations

import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Dict


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        payload: Dict = {
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if record.args:
            payload["extra_args"] = record.args
        if record.exc_info:
            payload["exception"] = True
        return json.dumps(payload)


def setup_logging(app_log: str, signal_log: str, level: str = "INFO"):
    Path(app_log).parent.mkdir(parents=True, exist_ok=True)
    Path(signal_log).parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO))
    app_handler = RotatingFileHandler(app_log, maxBytes=1_000_000, backupCount=3)
    signal_handler = RotatingFileHandler(signal_log, maxBytes=1_000_000, backupCount=3)

    formatter = JsonFormatter()
    app_handler.setFormatter(formatter)
    signal_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.addHandler(app_handler)
    root.addHandler(signal_handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
