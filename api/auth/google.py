"""
POST /api/auth/google
Verify Google OAuth credential and create a server-side session cookie.
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.error
import hmac
import hashlib
import base64
import time
from datetime import datetime, timezone

# --- Config ---
CLIENT_ID = "573295023298-oe07ng68edmh7a6v6iknfihf7hrp6vac.apps.googleusercontent.com"
ALLOWED_DOMAIN = "ghn.vn"
SESSION_SECRET = os.environ.get("SESSION_SECRET", "treasury-dev-secret-key-change-in-production")
SESSION_MAX_AGE = 3600  # 1 hour

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://treasury-dashboard-sepia.vercel.app",
]


def _get_origin(headers):
    origin = headers.get("Origin", "")
    if origin in ALLOWED_ORIGINS:
        return origin
    return ALLOWED_ORIGINS[1]  # default to production


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def _create_session_token(email: str, name: str, picture: str) -> str:
    payload = json.dumps({
        "email": email,
        "name": name,
        "picture": picture,
        "exp": int(time.time()) + SESSION_MAX_AGE,
    }, separators=(",", ":"))
    payload_b64 = _b64url_encode(payload.encode("utf-8"))
    sig = hmac.new(
        SESSION_SECRET.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return payload_b64 + "." + sig


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
        try:
            # --- Read body ---
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)
            credential = data.get("credential", "")
            if not credential:
                self._error(400, "Missing credential", origin)
                return

            # --- Verify with Google tokeninfo ---
            url = "https://oauth2.googleapis.com/tokeninfo?id_token=" + credential
            try:
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=10) as resp:
                    token_info = json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                ip = self.headers.get('X-Forwarded-For', self.client_address[0])
                timestamp = datetime.now(timezone.utc).isoformat()
                print(f'[AUDIT] {timestamp} | LOGIN_FAILED_INVALID_TOKEN | unknown | {ip}')
                self._error(401, "Invalid token: Google rejected the credential", origin)
                return
            except Exception as e:
                self._error(502, "Failed to verify token with Google", origin)
                return

            # --- Validate claims ---
            email_verified = token_info.get("email_verified", "false")
            if email_verified not in (True, "true"):
                self._error(401, "Email not verified", origin)
                return

            aud = token_info.get("aud", "")
            if aud != CLIENT_ID:
                self._error(401, "Token audience mismatch", origin)
                return

            email = token_info.get("email", "")
            if not email.endswith("@" + ALLOWED_DOMAIN):
                ip = self.headers.get('X-Forwarded-For', self.client_address[0])
                timestamp = datetime.now(timezone.utc).isoformat()
                print(f'[AUDIT] {timestamp} | LOGIN_FAILED_DOMAIN | {email} | {ip}')
                self._error(
                    401,
                    f"Access denied: only @{ALLOWED_DOMAIN} emails are allowed. Got {email}",
                    origin,
                )
                return

            name = token_info.get("name", email.split("@")[0])
            picture = token_info.get("picture", "")

            # --- Create session ---
            token = _create_session_token(email, name, picture)

            cookie = (
                f"treasury_session={token}; "
                f"HttpOnly; Secure; SameSite=Strict; "
                f"Path=/; Max-Age={SESSION_MAX_AGE}"
            )

            ip = self.headers.get('X-Forwarded-For', self.client_address[0])
            timestamp = datetime.now(timezone.utc).isoformat()
            print(f'[AUDIT] {timestamp} | LOGIN_SUCCESS | {email} | {ip}')

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Set-Cookie", cookie)
            self._set_cors(origin)
            self.send_header('X-RateLimit-Limit', '60')
            self.send_header('X-RateLimit-Window', '60')
            self.end_headers()
            self.wfile.write(json.dumps({
                "ok": True,
                "user": {"email": email, "name": name, "picture": picture},
            }).encode())

        except json.JSONDecodeError:
            self._error(400, "Invalid JSON body", origin)
        except Exception as exc:
            self._error(500, f"Internal error: {exc}", origin)

    def _error(self, code, message, origin):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self._set_cors(origin)
        self.send_header('X-RateLimit-Limit', '60')
        self.send_header('X-RateLimit-Window', '60')
        self.end_headers()
        self.wfile.write(json.dumps({"ok": False, "error": message}).encode())

    def log_message(self, format, *args):
        pass  # silence default stderr logging
