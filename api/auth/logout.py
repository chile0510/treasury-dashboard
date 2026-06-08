"""
POST /api/auth/logout
Clear the session cookie and return success.
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import hmac
import hashlib
import base64
import time
from datetime import datetime, timezone

SESSION_SECRET = os.environ.get("SESSION_SECRET", "treasury-dev-secret-key-change-in-production")

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://treasury-dashboard-sepia.vercel.app",
]


def _get_origin(headers):
    origin = headers.get("Origin", "")
    if origin in ALLOWED_ORIGINS:
        return origin
    return ALLOWED_ORIGINS[1]


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


def _get_email_from_session(headers) -> str:
    """Extract email from session cookie for audit logging. Returns 'unknown' on failure."""
    try:
        cookie_header = headers.get("Cookie", "")
        cookies = _parse_cookies(cookie_header)
        token = cookies.get("treasury_session", "")
        if not token or "." not in token:
            return "unknown"
        payload_b64 = token.split(".", 1)[0]
        sig_expected = hmac.new(
            SESSION_SECRET.encode("utf-8"),
            payload_b64.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        sig_received = token.split(".", 1)[1]
        if not hmac.compare_digest(sig_expected, sig_received):
            return "unknown"
        payload_json = _b64url_decode(payload_b64).decode("utf-8")
        payload = json.loads(payload_json)
        return payload.get("email", "unknown")
    except Exception:
        return "unknown"


class handler(BaseHTTPRequestHandler):
    server_version = 'Server'
    sys_version = ''

    def _set_cors(self, origin):
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Credentials", "true")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        origin = _get_origin(self.headers)
        self.send_response(204)
        self._set_cors(origin)
        self.send_header('X-RateLimit-Limit', '60')
        self.send_header('X-RateLimit-Window', '60')
        self.end_headers()

    def do_POST(self):
        origin = _get_origin(self.headers)

        # Audit log before clearing cookie
        email = _get_email_from_session(self.headers)
        ip = self.headers.get('X-Forwarded-For', self.client_address[0])
        timestamp = datetime.now(timezone.utc).isoformat()
        print(f'[AUDIT] {timestamp} | LOGOUT | {email} | {ip}')

        # Clear the session cookie
        cookie = (
            "treasury_session=; "
            "HttpOnly; Secure; SameSite=Strict; "
            "Path=/; Max-Age=0"
        )

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Set-Cookie", cookie)
        self._set_cors(origin)
        self.send_header('X-RateLimit-Limit', '60')
        self.send_header('X-RateLimit-Window', '60')
        self.end_headers()
        self.wfile.write(json.dumps({
            "ok": True,
            "message": "Logged out",
        }).encode())

    def log_message(self, format, *args):
        pass
