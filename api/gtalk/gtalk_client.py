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


# ============================================================
# File Upload Flow (3-step: initiate → S3 PUT → complete)
# ============================================================

def initiate_upload(
    channel_id: str,
    filename: str,
    filesize: int,
    mimetype: str,
) -> dict:
    """
    Step 1: Initiate file upload — returns presigned S3 URL and UploadId.
    """
    return _api_call("/api/gtalk/initiate-upload", {
        "ChannelId": channel_id,
        "FileName": filename,
        "FileSize": str(filesize),  # API requires string
        "MimeType": mimetype,
        "Metadata": "",
        "oaToken": GTALK_OA_TOKEN,
    })


def upload_to_s3(presigned_url: str, file_bytes: bytes, content_type: str) -> bool:
    """
    Step 2: Upload file binary to S3 presigned URL via HTTP PUT.
    Returns True on success.
    """
    req = urllib.request.Request(
        presigned_url,
        data=file_bytes,
        headers={"Content-Type": content_type},
        method="PUT",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"[GTALK] S3 upload error: {e}")
        return False


def complete_upload(upload_id: str) -> dict:
    """
    Step 3: Complete upload — returns permanent fileId.
    """
    return _api_call("/api/gtalk/complete-upload", {
        "oaToken": GTALK_OA_TOKEN,
        "UploadId": upload_id,
    })


def send_file_message(
    channel_id: str,
    file_id: str,
    filename: str,
    mimetype: str,
    filesize: int,
) -> dict:
    """Send a file attachment message to a GTalk channel."""
    client_msg_id = str(int(time.time() * 1000))
    return _api_call("/api/gtalk/send-message", {
        "channelId": channel_id,
        "clientMsgId": client_msg_id,
        "content": {
            "attachment": {
                "items": [
                    {
                        "file": {
                            "fileId": file_id,
                            "fileName": filename,
                            "mimeType": mimetype,
                            "fileSize": filesize,
                        }
                    }
                ]
            }
        },
        "oaToken": GTALK_OA_TOKEN,
    })


def upload_and_send_file(
    channel_id: str,
    file_bytes: bytes,
    filename: str,
    mimetype: str,
) -> dict:
    """
    Full file upload + send flow in one call.
    Returns the send-message result or error dict.
    """
    filesize = len(file_bytes)

    # Step 1: Initiate
    init_result = initiate_upload(channel_id, filename, filesize, mimetype)
    if init_result.get("errorCode") != "success":
        print(f"[GTALK] initiate_upload failed: {init_result}")
        return init_result

    data = init_result.get("data", {})
    presigned_url = data.get("PresignedURL", "")
    upload_id = data.get("UploadId", "")

    if not presigned_url or not upload_id:
        return {"errorCode": "missing_presigned_url"}

    # Step 2: Upload to S3
    if not upload_to_s3(presigned_url, file_bytes, mimetype):
        return {"errorCode": "s3_upload_failed"}

    # Step 3: Complete
    complete_result = complete_upload(upload_id)
    if complete_result.get("errorCode") != "success":
        print(f"[GTALK] complete_upload failed: {complete_result}")
        return complete_result

    file_id = complete_result.get("data", {}).get("Id", upload_id)

    # Step 4: Send file message
    return send_file_message(channel_id, file_id, filename, mimetype, filesize)


# ============================================================
# Template Messages (Rich Cards with Action Buttons)
# ============================================================

def send_template_message(
    channel_id: str,
    title: str,
    body_html: str,
    short_message: str,
    actions: list[dict] | None = None,
    icon_url: str = "",
    template_id: str = "treasury_report",
) -> dict:
    """
    Send a template message (rich card with optional action buttons).

    actions format: [{"text": "View Dashboard", "style": "primary",
                      "type": "browser_external", "url": "https://..."}]
    """
    template_data = {
        "title": title,
        "content": body_html,
    }
    if icon_url:
        template_data["icon_url"] = icon_url
    if actions:
        template_data["actions"] = actions

    client_msg_id = str(int(time.time() * 1000))
    return _api_call("/api/gtalk/send-message", {
        "channelId": channel_id,
        "clientMsgId": client_msg_id,
        "content": {
            "template": {
                "templateId": template_id,
                "shortMessage": short_message,
                "data": json.dumps(template_data, ensure_ascii=False),
            }
        },
        "oaToken": GTALK_OA_TOKEN,
    })

