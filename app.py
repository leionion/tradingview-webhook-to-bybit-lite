from __future__ import annotations

from typing import Any, Dict

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from pydantic import ValidationError

from tv_bybit_lite.bybit import BybitClient
from tv_bybit_lite.config import Settings, load_settings
from tv_bybit_lite.dedup import InMemoryDeduplicator
from tv_bybit_lite.logging_utils import log_event, setup_logging
from tv_bybit_lite.schemas import WebhookPayload
from tv_bybit_lite.service import execute_order


def _authorized(req, settings: Settings) -> bool:
    if not settings.webhook_secret:
        return True
    provided = req.headers.get(settings.webhook_secret_header, "")
    return provided == settings.webhook_secret


def create_app(
    settings: Settings | None = None,
    bybit_client: BybitClient | None = None,
    deduplicator: InMemoryDeduplicator | None = None,
) -> Flask:
    load_dotenv()
    app = Flask(__name__)
    settings = settings or load_settings()
    bybit_client = bybit_client or BybitClient(settings)
    deduplicator = deduplicator or InMemoryDeduplicator(ttl_seconds=settings.dedup_ttl_seconds)

    setup_logging(settings.log_level)

    @app.get("/health")
    def health() -> Any:
        return jsonify({"status": "ok"}), 200

    @app.post("/webhook")
    def webhook() -> Any:
        if not _authorized(request, settings):
            log_event("webhook.rejected", reason="unauthorized")
            return jsonify({"ok": False, "error": "Unauthorized webhook"}), 401

        body: Dict[str, Any] = request.get_json(silent=True) or {}
        if not body:
            return jsonify({"ok": False, "error": "Invalid or empty JSON payload"}), 400

        try:
            payload = WebhookPayload(**body)
        except ValidationError as exc:
            return jsonify({"ok": False, "error": "Validation failed", "details": exc.errors()}), 400

        if settings.enable_dedup:
            key = payload.alertId if payload.alertId else deduplicator.make_key(body)
            if not deduplicator.check_and_record(key):
                log_event("webhook.duplicate", key=key)
                return jsonify({"ok": False, "error": "Duplicate payload detected"}), 409

        try:
            result = execute_order(
                payload=payload,
                settings=settings,
                bybit_client=bybit_client,
            )
            log_event(
                "webhook.processed",
                symbol=payload.symbol,
                side=payload.side,
                mode=result.get("status"),
            )
            return jsonify({"ok": True, "result": result}), 200
        except PermissionError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 403
        except Exception as exc:
            log_event("webhook.failed", error=str(exc))
            return jsonify({"ok": False, "error": str(exc)}), 502

    return app


if __name__ == "__main__":
    app = create_app()
    settings = load_settings()
    app.run(host=settings.host, port=settings.port)
