from __future__ import annotations

from typing import Any, Dict

from tv_bybit_lite.bybit import BybitClient
from tv_bybit_lite.config import Settings
from tv_bybit_lite.schemas import WebhookPayload


def resolve_mode(payload: WebhookPayload, settings: Settings) -> str:
    return payload.mode or settings.default_mode


def to_order_payload(payload: WebhookPayload, settings: Settings) -> Dict[str, Any]:
    order = {
        "category": payload.category or settings.default_category,
        "symbol": payload.symbol,
        "side": payload.side,
        "orderType": payload.orderType or settings.default_order_type,
        "qty": str(payload.qty),
        "timeInForce": payload.timeInForce or settings.default_time_in_force,
    }
    if payload.orderType == "Limit" and payload.price is not None:
        order["price"] = str(payload.price)
    if payload.reduceOnly:
        order["reduceOnly"] = True
    return order


def execute_order(
    payload: WebhookPayload,
    settings: Settings,
    bybit_client: BybitClient,
) -> Dict[str, Any]:
    mode = resolve_mode(payload, settings)
    if payload.reduceOnly and not settings.allow_reduce_only:
        raise PermissionError("reduceOnly is disabled by server policy")

    order_payload = to_order_payload(payload, settings)
    if mode == "paper":
        return {
            "status": "paper",
            "message": "Paper mode: order accepted but not sent to Bybit",
            "orderPayload": order_payload,
        }

    if mode == "live" and not settings.allow_live_without_override:
        raise PermissionError(
            "Live mode blocked. Set ALLOW_LIVE_WITHOUT_OVERRIDE=true to allow live execution."
        )
    bybit_response = bybit_client.place_order(order_payload)
    return {
        "status": "live",
        "message": "Order sent to Bybit",
        "orderPayload": order_payload,
        "bybit": bybit_response,
    }
