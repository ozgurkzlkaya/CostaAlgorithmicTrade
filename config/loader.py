from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict

import yaml

logger = logging.getLogger(__name__)


def load_config(base: str = "config/default.yaml", override: str | None = None) -> Dict[str, Any]:
    with open(base, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    if override:
        path = Path(override)
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                override_cfg = yaml.safe_load(f)
            config.update(override_cfg)
        else:
            logger.warning("Override config not found", extra={"override": override})
    return config
