from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any, Dict

import requests

from tv_bybit_lite.config import Settings


class BybitClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_url = (
            "https://api-testnet.bybit.com"
            if settings.bybit_testnet
            else "https://api.bybit.com"
        )

    def _headers(self, body: str, timestamp_ms: str) -> Dict[str, str]:
        signature_payload = (
            f"{timestamp_ms}{self.settings.bybit_api_key}{self.settings.bybit_recv_window}{body}"
        )
        signature = hmac.new(
            self.settings.bybit_api_secret.encode("utf-8"),
            signature_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return {
            "X-BAPI-API-KEY": self.settings.bybit_api_key,
            "X-BAPI-TIMESTAMP": timestamp_ms,
            "X-BAPI-RECV-WINDOW": str(self.settings.bybit_recv_window),
            "X-BAPI-SIGN": signature,
            "Content-Type": "application/json",
        }

    def place_order(self, order_payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.settings.bybit_api_key or not self.settings.bybit_api_secret:
            raise RuntimeError("Missing BYBIT_API_KEY/BYBIT_API_SECRET for live mode")

        body = json.dumps(order_payload, separators=(",", ":"))
        timestamp_ms = str(int(time.time() * 1000))
        headers = self._headers(body=body, timestamp_ms=timestamp_ms)
        response = requests.post(
            f"{self.base_url}/v5/order/create",
            headers=headers,
            data=body,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        ret_code = data.get("retCode")
        if ret_code != 0:
            raise RuntimeError(f"Bybit order rejected: retCode={ret_code}, response={data}")
        return data
