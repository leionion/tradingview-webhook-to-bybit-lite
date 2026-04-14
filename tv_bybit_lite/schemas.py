from __future__ import annotations

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class WebhookPayload(BaseModel):
    symbol: str = Field(min_length=3, max_length=40)
    side: str
    qty: Decimal = Field(gt=Decimal("0"))
    orderType: str
    category: str = "linear"
    price: Optional[Decimal] = Field(default=None, gt=Decimal("0"))
    reduceOnly: bool = False
    timeInForce: Optional[str] = None
    mode: Optional[str] = None
    alertId: Optional[str] = Field(default=None, max_length=120)

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("side")
    @classmethod
    def validate_side(cls, value: str) -> str:
        side = value.strip().capitalize()
        if side not in {"Buy", "Sell"}:
            raise ValueError("side must be Buy or Sell")
        return side

    @field_validator("orderType")
    @classmethod
    def validate_order_type(cls, value: str) -> str:
        order_type = value.strip().capitalize()
        if order_type not in {"Market", "Limit"}:
            raise ValueError("orderType must be Market or Limit")
        return order_type

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str) -> str:
        category = value.strip().lower()
        if category not in {"linear", "inverse", "spot", "option"}:
            raise ValueError("category must be one of linear/inverse/spot/option")
        return category

    @field_validator("timeInForce")
    @classmethod
    def validate_tif(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        tif = value.strip().upper()
        if tif not in {"GTC", "IOC", "FOK", "POSTONLY"}:
            raise ValueError("timeInForce must be GTC/IOC/FOK/POSTONLY")
        return tif

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        mode = value.strip().lower()
        if mode not in {"paper", "live"}:
            raise ValueError("mode must be paper or live")
        return mode

    @field_validator("price")
    @classmethod
    def require_price_for_limit(cls, value: Optional[Decimal], info) -> Optional[Decimal]:
        order_type = info.data.get("orderType")
        if order_type == "Limit" and value is None:
            raise ValueError("price is required for Limit orders")
        return value
