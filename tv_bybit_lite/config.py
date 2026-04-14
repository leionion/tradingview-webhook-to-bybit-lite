from __future__ import annotations

import os
from dataclasses import dataclass


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"Invalid integer for {name}: {value}") from exc


@dataclass(frozen=True)
class Settings:
    bybit_api_key: str
    bybit_api_secret: str
    bybit_testnet: bool
    bybit_recv_window: int
    host: str
    port: int
    webhook_secret: str
    webhook_secret_header: str
    default_mode: str
    allow_live_without_override: bool
    allow_reduce_only: bool
    default_category: str
    default_order_type: str
    default_time_in_force: str
    enable_dedup: bool
    dedup_ttl_seconds: int
    log_level: str


def load_settings() -> Settings:
    default_mode = os.getenv("DEFAULT_MODE", "paper").strip().lower()
    if default_mode not in {"paper", "live"}:
        raise ValueError("DEFAULT_MODE must be 'paper' or 'live'")

    return Settings(
        bybit_api_key=os.getenv("BYBIT_API_KEY", ""),
        bybit_api_secret=os.getenv("BYBIT_API_SECRET", ""),
        bybit_testnet=_get_bool("BYBIT_TESTNET", True),
        bybit_recv_window=_get_int("BYBIT_RECV_WINDOW", 5000),
        host=os.getenv("HOST", "0.0.0.0"),
        port=_get_int("PORT", 5000),
        webhook_secret=os.getenv("WEBHOOK_SECRET", ""),
        webhook_secret_header=os.getenv("WEBHOOK_SECRET_HEADER", "X-Webhook-Secret"),
        default_mode=default_mode,
        allow_live_without_override=_get_bool("ALLOW_LIVE_WITHOUT_OVERRIDE", False),
        allow_reduce_only=_get_bool("ALLOW_REDUCE_ONLY", True),
        default_category=os.getenv("DEFAULT_CATEGORY", "linear"),
        default_order_type=os.getenv("DEFAULT_ORDER_TYPE", "Market"),
        default_time_in_force=os.getenv("DEFAULT_TIME_IN_FORCE", "GTC"),
        enable_dedup=_get_bool("ENABLE_DEDUP", True),
        dedup_ttl_seconds=_get_int("DEDUP_TTL_SECONDS", 120),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )
