# TradingView Webhook to Bybit

Production-ready webhook bridge for executing Bybit orders from TradingView alerts with strong safety defaults.

## What Is Implemented

This project is fully implemented as a robust Flask service (not a minimal prototype).  
It includes:

- TradingView webhook endpoint: `POST /webhook`
- Health endpoint: `GET /health`
- Payload schema validation with Pydantic
- Webhook secret authentication via configurable header
- Paper vs live execution modes
- Live execution gate (`ALLOW_LIVE_WITHOUT_OVERRIDE`)
- Bybit V5 request signing and order submission
- In-memory replay/duplicate protection (TTL-based)
- Structured JSON logging for operations and failures
- Automated test suite with success and failure cases

## Architecture

```text
TradingView Alert
      |
      v
Flask API (/webhook)
  -> auth check
  -> payload validation
  -> dedup check
  -> mode gate (paper/live)
  -> Bybit V5 signed request (live)
      |
      v
Bybit Order API
```

## Project Structure

```text
.
├── app.py
├── requirements.txt
├── .env.example
├── tv_bybit_lite
│   ├── bybit.py
│   ├── config.py
│   ├── dedup.py
│   ├── logging_utils.py
│   ├── schemas.py
│   └── service.py
└── tests
    ├── conftest.py
    └── test_webhook.py
```

## Requirements

- Python 3.10+
- Bybit API key/secret (only required for live mode)

## Quick Start

1) Clone and install dependencies:

```bash
git clone https://github.com/YOUR_USERNAME/tradingview-webhook-to-bybit-lite.git
cd tradingview-webhook-to-bybit-lite
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) Configure environment:

```bash
cp .env.example .env
```

3) Run the service:

```bash
python app.py
```

4) Verify health:

```bash
curl http://localhost:5000/health
```

## Environment Variables

Core settings (see `.env.example` for full list):

- `BYBIT_API_KEY`
- `BYBIT_API_SECRET`
- `BYBIT_TESTNET` (`true|false`)
- `BYBIT_RECV_WINDOW` (default: `5000`)
- `HOST` (default: `0.0.0.0`)
- `PORT` (default: `5000`)
- `WEBHOOK_SECRET` (recommended for production)
- `WEBHOOK_SECRET_HEADER` (default: `X-Webhook-Secret`)
- `DEFAULT_MODE` (`paper|live`, default: `paper`)
- `ALLOW_LIVE_WITHOUT_OVERRIDE` (`false` by default)
- `ENABLE_DEDUP` (`true` by default)
- `DEDUP_TTL_SECONDS` (default: `120`)

## Webhook Payload

### Required fields

```json
{
  "symbol": "BTCUSDT",
  "side": "Buy",
  "qty": "0.01",
  "orderType": "Market",
  "category": "linear"
}
```

### Optional fields

- `price` (required when `orderType` is `Limit`)
- `reduceOnly` (`true|false`)
- `timeInForce` (`GTC|IOC|FOK|POSTONLY`)
- `mode` (`paper|live`) - overrides `DEFAULT_MODE`
- `alertId` (recommended for deterministic dedupe key)

## Example Requests

### Paper mode (safe default)

```bash
curl -X POST http://localhost:5000/webhook \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: change-me" \
  -d '{
    "symbol":"BTCUSDT",
    "side":"Buy",
    "qty":"0.001",
    "orderType":"Market",
    "category":"linear",
    "mode":"paper",
    "alertId":"tv-btc-001"
  }'
```

### Live mode

```bash
curl -X POST http://localhost:5000/webhook \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: change-me" \
  -d '{
    "symbol":"ETHUSDT",
    "side":"Sell",
    "qty":"0.02",
    "orderType":"Limit",
    "price":"3600",
    "category":"linear",
    "mode":"live",
    "alertId":"tv-eth-002"
  }'
```

## Response Behavior

- `200`: accepted and processed (`paper` or `live`)
- `400`: invalid JSON or schema validation failed
- `401`: webhook secret invalid/missing
- `403`: policy restriction (e.g., live mode blocked)
- `409`: duplicate payload detected
- `502`: upstream Bybit/API execution failure

## Testing

Run tests:

```bash
pytest -q
```

Current status: **6 passing tests**.

Covered scenarios:

- authentication required
- paper mode success
- live mode success path
- duplicate detection
- live mode policy blocking
- order payload mapping correctness

## Security and Production Notes

- Always set `WEBHOOK_SECRET` in production.
- Keep `DEFAULT_MODE=paper` while validating strategy behavior.
- Only enable `ALLOW_LIVE_WITHOUT_OVERRIDE=true` when you intentionally want live execution.
- Use unique `alertId` from TradingView to improve replay protection.
- Use Bybit testnet first before any real capital.

## TradingView Alert Message Template

Use this JSON in TradingView alert message body:

```json
{
  "symbol": "{{ticker}}",
  "side": "Buy",
  "qty": "0.01",
  "orderType": "Market",
  "category": "linear",
  "mode": "paper",
  "alertId": "{{timenow}}-{{strategy.order.action}}"
}
```

## Contact

- GitHub: [@leionion](https://github.com/leionion)

## Disclaimer

This software can place real orders. Misconfiguration, payload errors, or logic flaws can cause losses.  
Use testnet, paper mode, strict risk controls, and independent monitoring before live trading.
