"""
GTalk API client — utility functions for sending messages and receipts.
Uses only Python standard library (urllib.request).
"""

import json
import hashlib
import hmac
import os
import time
import urllib.request
import urllib.error

GTALK_BASE_URL = os.environ.get("GTALK_BASE_URL", "https://test-api.mbff.ghn.tech")
GTALK_OA_TOKEN = os.environ.get("GTALK_OA_TOKEN", "")
GTALK_OA_ID = os.environ.get("GTALK_OA_ID", "")


def _api_call(endpoint: str, payload: dict) -> dict:
    """Make a POST request to a GTalk API endpoint."""
    url = f"{GTALK_BASE_URL}{endpoint}"
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        print(f"[GTALK] HTTP {e.code} on {endpoint}: {error_body}")
        return {"errorCode": "http_error", "error": {"errorMessage": f"HTTP {e.code}"}}
    except Exception as e:
        print(f"[GTALK] Error calling {endpoint}: {e}")
        return {"errorCode": "network_error", "error": {"errorMessage": str(e)}}


def send_text_message(channel_id: str, text: str, parse_mode: str = "MARKDOWN") -> dict:
    """Send a text message to a GTalk channel."""
    client_msg_id = str(int(time.time() * 1000))
    return _api_call("/api/gtalk/send-message", {
        "channelId": channel_id,
        "clientMsgId": client_msg_id,
        "content": {
            "text": text,
            "parseMode": parse_mode,
        },
        "oaToken": GTALK_OA_TOKEN,
    })


def send_receipt(oa_id: str, channel_id: str, global_msg_id: str, statuses: list) -> dict:
    """
    Send message receipts (SEEN, TYPING, etc.) to GTalk.
    statuses: list of ReceiptStatus integers (2=SEEN, 3=TYPING, etc.)
    """
    now_ms = int(time.time() * 1000)
    receipts = [
        {
            "status": status,
            "receiptedTs": now_ms + i,  # offset by 1ms to ensure unique timestamps
            "globalMsgId": global_msg_id,
        }
        for i, status in enumerate(statuses)
    ]
    return _api_call("/api/gtalk/send-message-receipt", {
        "oaId": oa_id,
        "oaToken": GTALK_OA_TOKEN,
        "receiptMessage": {
            "channelId": channel_id,
            "receipts": receipts,
        },
    })


def verify_webhook_signature(
    raw_body: bytes,
    signature_header: str,
    webhook_secret: str,
) -> bool:
    """
    Verify the HMAC-SHA256 signature on an incoming GTalk webhook request.

    Signature = SHA256(oaId + jsonPayload + timestamp + webhookSecret)
    Header format: "mac=<hex_digest>"
    """
    if not signature_header or not signature_header.startswith("mac="):
        return False

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return False

    oa_id = payload.get("oaId", "")
    timestamp = payload.get("timestamp", "")
    json_payload = raw_body.decode("utf-8")

    input_str = oa_id + json_payload + timestamp + webhook_secret
    hex_digest = hashlib.sha256(input_str.encode("utf-8")).hexdigest()
    expected = "mac=" + hex_digest

    # Constant-time comparison to prevent timing attacks
    return hmac.compare_digest(signature_header, expected)
