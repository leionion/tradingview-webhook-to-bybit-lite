from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(message)s",
    )


def log_event(event: str, **extra: Any) -> None:
    payload: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        **extra,
    }
    logging.info(json.dumps(payload, separators=(",", ":")))
