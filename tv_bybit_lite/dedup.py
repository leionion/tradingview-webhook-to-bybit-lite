from __future__ import annotations

import hashlib
import json
import time
from threading import Lock
from typing import Any, Dict


class InMemoryDeduplicator:
    def __init__(self, ttl_seconds: int = 120):
        self.ttl_seconds = ttl_seconds
        self._seen: Dict[str, float] = {}
        self._lock = Lock()

    def _cleanup(self, now: float) -> None:
        expired = [key for key, expires_at in self._seen.items() if expires_at <= now]
        for key in expired:
            self._seen.pop(key, None)

    def make_key(self, payload: Dict[str, Any]) -> str:
        stable = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(stable.encode("utf-8")).hexdigest()

    def check_and_record(self, key: str) -> bool:
        now = time.time()
        with self._lock:
            self._cleanup(now)
            if key in self._seen:
                return False
            self._seen[key] = now + self.ttl_seconds
            return True
