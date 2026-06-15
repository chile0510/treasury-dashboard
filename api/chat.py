"""
POST /api/chat
Web chat API — processes user messages and returns bot responses.
Reuses the same intent parsing and response logic as the GTalk webhook.
Requires authentication (session cookie).
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import hmac
import hashlib
import base64
import time

# Reuse reply logic from webhook
from lib.treasury_data import FINANCIAL_DATA
from datetime import datetime

SESSION_SECRET = os.environ.get("SESSION_SECRET")
if not SESSION_SECRET:
    raise RuntimeError("FATAL: SESSION_SECRET environment variable must be set")

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://treasury-dashboard-sepia.vercel.app",
]


def _get_origin(headers):
    origin = headers.get("Origin", "")
    if origin in ALLOWED_ORIGINS:
        return origin
    if not origin:
        return ALLOWED_ORIGINS[1]
    return None


def _b64url_decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def _parse_cookies(cookie_header: str) -> dict:
    cookies = {}
    if not cookie_header:
        return cookies
    for item in cookie_header.split(";"):
        item = item.strip()
        if "=" in item:
            k, v = item.split("=", 1)
            cookies[k.strip()] = v.strip()
    return cookies


def _verify_session(headers) -> dict | None:
    cookie_header = headers.get("Cookie", "")
    cookies = _parse_cookies(cookie_header)
    token = cookies.get("treasury_session", "")
    if not token or "." not in token:
        return None
    parts = token.split(".", 1)
    if len(parts) != 2:
        return None
    payload_b64, sig_received = parts
    sig_expected = hmac.new(
        SESSION_SECRET.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(sig_expected, sig_received):
        return None
    try:
        payload_json = _b64url_decode(payload_b64).decode("utf-8")
        payload = json.loads(payload_json)
    except Exception:
        return None
    exp = payload.get("exp", 0)
    if time.time() > exp:
        return None
    return {
        "email": payload.get("email", ""),
        "name": payload.get("name", ""),
    }


# ============================================================
# Import reply functions from webhook module
# ============================================================

# We re-import the intent parsing and reply logic
import importlib
import sys

# Add project root to path
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from api.gtalk.webhook import (
    smart_parse_intent,
    INTENT_HANDLERS,
)


class handler(BaseHTTPRequestHandler):
    server_version = "Server"
    sys_version = ""

    def _set_cors(self, origin):
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Credentials", "true")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        origin = _get_origin(self.headers)
        self.send_response(204)
        self._set_cors(origin)
        self.end_headers()

    def do_POST(self):
        origin = _get_origin(self.headers)
        if origin is None:
            self.send_response(403)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": False, "error": "Forbidden"}).encode())
            return

        user = _verify_session(self.headers)
        if not user:
            self.send_response(401)
            self.send_header("Content-Type", "application/json")
            self._set_cors(origin)
            self.end_headers()
            self.wfile.write(json.dumps({"ok": False, "error": "Auth required"}).encode())
            return

        # Read request body
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self._set_cors(origin)
            self.end_headers()
            self.wfile.write(json.dumps({"ok": False, "error": "Invalid JSON"}).encode())
            return

        user_message = data.get("message", "").strip()
        if not user_message:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self._set_cors(origin)
            self.end_headers()
            self.wfile.write(json.dumps({"ok": False, "error": "Empty message"}).encode())
            return

        # Parse intent and generate reply
        intent, params = smart_parse_intent(user_message)

        # Handle export specially (no file upload in web chat, just text)
        if intent == "export_report":
            reply_text = (
                "📄 Chức năng xuất PDF hiện chỉ hỗ trợ qua GTalk.\n\n"
                "Bạn có thể xem toàn bộ dữ liệu trên Dashboard này."
            )
        else:
            handler_fn = INTENT_HANDLERS.get(intent, INTENT_HANDLERS["unknown"])
            reply_text = handler_fn(params)

        # Log
        timestamp = datetime.now().isoformat()
        print(f'[WEB_CHAT] {timestamp} | {user["email"]} | "{user_message}" -> {intent}')

        # Convert markdown bold **text** to simple text for web display
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self._set_cors(origin)
        self.end_headers()
        self.wfile.write(json.dumps({
            "ok": True,
            "intent": intent,
            "reply": reply_text,
        }, ensure_ascii=False).encode("utf-8"))

    def log_message(self, format, *args):
        pass
