from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from typing import Any, Dict

from app import create_app
from tv_bybit_lite.config import Settings
from tv_bybit_lite.service import to_order_payload


class FakeBybitClient:
    def __init__(self):
        self.calls = []

    def place_order(self, order_payload: Dict[str, Any]) -> Dict[str, Any]:
        self.calls.append(order_payload)
        return {"retCode": 0, "retMsg": "OK", "result": {"orderId": "123"}}


def _settings() -> Settings:
    return Settings(
        bybit_api_key="k",
        bybit_api_secret="s",
        bybit_testnet=True,
        bybit_recv_window=5000,
        host="127.0.0.1",
        port=5000,
        webhook_secret="secret",
        webhook_secret_header="X-Webhook-Secret",
        default_mode="paper",
        allow_live_without_override=True,
        allow_reduce_only=True,
        default_category="linear",
        default_order_type="Market",
        default_time_in_force="GTC",
        enable_dedup=True,
        dedup_ttl_seconds=120,
        log_level="INFO",
    )


def _base_payload() -> Dict[str, Any]:
    return {
        "symbol": "BTCUSDT",
        "side": "Buy",
        "qty": "0.01",
        "orderType": "Market",
        "category": "linear",
        "alertId": "a1",
    }


def test_webhook_requires_auth_header() -> None:
    fake = FakeBybitClient()
    app = create_app(settings=_settings(), bybit_client=fake)
    client = app.test_client()

    response = client.post("/webhook", json=_base_payload())
    assert response.status_code == 401


def test_webhook_paper_mode_success() -> None:
    fake = FakeBybitClient()
    app = create_app(settings=_settings(), bybit_client=fake)
    client = app.test_client()

    response = client.post(
        "/webhook",
        json=_base_payload(),
        headers={"X-Webhook-Secret": "secret"},
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["ok"] is True
    assert body["result"]["status"] == "paper"
    assert len(fake.calls) == 0


def test_webhook_live_mode_executes() -> None:
    fake = FakeBybitClient()
    app = create_app(settings=_settings(), bybit_client=fake)
    client = app.test_client()
    payload = _base_payload()
    payload["mode"] = "live"
    payload["orderType"] = "Limit"
    payload["price"] = "80000"

    response = client.post(
        "/webhook",
        json=payload,
        headers={"X-Webhook-Secret": "secret"},
    )
    assert response.status_code == 200
    assert len(fake.calls) == 1
    assert fake.calls[0]["price"] == "80000"


def test_duplicate_detection() -> None:
    fake = FakeBybitClient()
    app = create_app(settings=_settings(), bybit_client=fake)
    client = app.test_client()
    payload = _base_payload()

    r1 = client.post("/webhook", json=payload, headers={"X-Webhook-Secret": "secret"})
    r2 = client.post("/webhook", json=payload, headers={"X-Webhook-Secret": "secret"})
    assert r1.status_code == 200
    assert r2.status_code == 409


def test_live_mode_can_be_blocked() -> None:
    fake = FakeBybitClient()
    s = replace(_settings(), allow_live_without_override=False)
    app = create_app(settings=s, bybit_client=fake)
    client = app.test_client()
    payload = _base_payload()
    payload["mode"] = "live"

    response = client.post(
        "/webhook",
        json=payload,
        headers={"X-Webhook-Secret": "secret"},
    )
    assert response.status_code == 403
    assert len(fake.calls) == 0


def test_order_payload_mapping_defaults() -> None:
    from tv_bybit_lite.schemas import WebhookPayload

    payload = WebhookPayload(
        symbol="ethusdt",
        side="buy",
        qty=Decimal("1.5"),
        orderType="Market",
        category="linear",
    )
    order_payload = to_order_payload(payload, _settings())
    assert order_payload["symbol"] == "ETHUSDT"
    assert order_payload["side"] == "Buy"
    assert order_payload["qty"] == "1.5"
