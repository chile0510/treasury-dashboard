"""
POST /api/auth/logout
Clear the session cookie and return success.
"""
from http.server import BaseHTTPRequestHandler
import json

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://treasury-dashboard-sepia.vercel.app",
]


def _get_origin(headers):
    origin = headers.get("Origin", "")
    if origin in ALLOWED_ORIGINS:
        return origin
    return ALLOWED_ORIGINS[1]


class handler(BaseHTTPRequestHandler):

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
        self.end_headers()
        self.wfile.write(json.dumps({
            "ok": True,
            "message": "Logged out",
        }).encode())

    def log_message(self, format, *args):
        pass
