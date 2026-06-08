"""
GET /api/auth/me
Return current user info from session cookie, or 401 if not authenticated.
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import hmac
import hashlib
import base64
import time

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
    """Parse a Cookie header string into a dict."""
    cookies = {}
    if not cookie_header:
        return cookies
    for item in cookie_header.split(";"):
        item = item.strip()
        if "=" in item:
            k, v = item.split("=", 1)
            cookies[k.strip()] = v.strip()
    return cookies


def verify_session(headers) -> dict | None:
    """Verify the treasury_session cookie. Returns user dict or None."""
    cookie_header = headers.get("Cookie", "")
    cookies = _parse_cookies(cookie_header)
    token = cookies.get("treasury_session", "")
    if not token or "." not in token:
        return None

    parts = token.split(".", 1)
    if len(parts) != 2:
        return None

    payload_b64, sig_received = parts

    # Verify HMAC signature
    sig_expected = hmac.new(
        SESSION_SECRET.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(sig_expected, sig_received):
        return None

    # Decode payload
    try:
        payload_json = _b64url_decode(payload_b64).decode("utf-8")
        payload = json.loads(payload_json)
    except Exception:
        return None

    # Check expiration
    exp = payload.get("exp", 0)
    if time.time() > exp:
        return None

    return {
        "email": payload.get("email", ""),
        "name": payload.get("name", ""),
        "picture": payload.get("picture", ""),
    }


class handler(BaseHTTPRequestHandler):
    server_version = 'Server'
    sys_version = ''

    def _set_cors(self, origin):
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Credentials", "true")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        origin = _get_origin(self.headers)
        self.send_response(204)
        self._set_cors(origin)
        self.send_header('X-RateLimit-Limit', '60')
        self.send_header('X-RateLimit-Window', '60')
        self.end_headers()

    def do_GET(self):
        origin = _get_origin(self.headers)
        if origin is None:
            self.send_response(403)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": False, "error": "Forbidden"}).encode())
            return
        user = verify_session(self.headers)

        if user:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._set_cors(origin)
            self.send_header('X-RateLimit-Limit', '60')
            self.send_header('X-RateLimit-Window', '60')
            self.end_headers()
            self.wfile.write(json.dumps({
                "ok": True,
                "user": user,
            }).encode())
        else:
            self.send_response(401)
            self.send_header("Content-Type", "application/json")
            self._set_cors(origin)
            self.send_header('X-RateLimit-Limit', '60')
            self.send_header('X-RateLimit-Window', '60')
            self.end_headers()
            self.wfile.write(json.dumps({
                "ok": False,
                "error": "Not authenticated",
            }).encode())

    def log_message(self, format, *args):
        pass
