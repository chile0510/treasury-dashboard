"""
GET /api/data
Return financial data only to authenticated users.
Session cookie is verified using the same HMAC-SHA256 logic as me.py.
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
        "picture": payload.get("picture", ""),
    }


# ============================================================
# FINANCIAL DATA — Treasury Portfolio (server-side only)
# ============================================================
FINANCIAL_DATA = {
    "summary": {
        "totalLoan": 1204420673710,
        "fundingRate": 6.88,
        "totalInvest": 1271603094800,
        "investYield": 8.76,
        "netSpread": 1.88,
        "netPL": 33558962527.6,
        "tdPct": 28.9,
        "bondPct": 71.1,
        "tdAmount": 736000000000,
        "bondAmount": 1814203094800,
        "totalTSDB": 240500000000,
        "totalHanMuc": 1610000000000,
    },
    "limitControls": [
        {"bank": "Cathay", "duNo": 200000000000, "hanMuc": 200000000000, "util": 100.0, "room": 0, "status": "danger"},
        {"bank": "VCB", "duNo": 749962921699, "hanMuc": 750000000000, "util": 100.0, "room": 37078301, "status": "danger"},
        {"bank": "Shinhan", "duNo": 159921586864, "hanMuc": 160000000000, "util": 100.0, "room": 78413136, "status": "danger"},
        {"bank": "BIDV", "duNo": 94536165147, "hanMuc": 250000000000, "util": 37.8, "room": 155463834853, "status": "safe"},
        {"bank": "HSBC", "duNo": 0, "hanMuc": 250000000000, "util": 0.0, "room": 250000000000, "status": "safe"},
    ],
    "loans": [
        {"bank": "VCB", "amount": 79744415313, "rate": 5.8, "startDate": "2025-12-16", "endDate": "2026-06-15", "status": "Outstanding"},
        {"bank": "VCB", "amount": 16317332243, "rate": 5.8, "startDate": "2025-12-17", "endDate": "2026-06-15", "status": "Outstanding"},
        {"bank": "VCB", "amount": 74100000000, "rate": 6.0, "startDate": "2025-12-22", "endDate": "2026-06-19", "status": "Outstanding"},
        {"bank": "VCB", "amount": 119000000000, "rate": 6.0, "startDate": "2026-01-05", "endDate": "2026-07-03", "status": "Outstanding"},
        {"bank": "VCB", "amount": 87701174143, "rate": 6.0, "startDate": "2026-01-15", "endDate": "2026-07-13", "status": "Outstanding"},
        {"bank": "VCB", "amount": 72100000000, "rate": 6.0, "startDate": "2026-01-20", "endDate": "2026-07-20", "status": "Outstanding"},
        {"bank": "Cathay", "amount": 200000000000, "rate": 7.2, "startDate": "2026-02-05", "endDate": "2026-08-04", "status": "Outstanding"},
        {"bank": "Shinhan", "amount": 143663435630, "rate": 6.9, "startDate": "2026-04-15", "endDate": "2026-10-15", "status": "Outstanding"},
        {"bank": "Shinhan", "amount": 9637371651, "rate": 6.9, "startDate": "2026-04-20", "endDate": "2026-10-20", "status": "Outstanding"},
        {"bank": "Shinhan", "amount": 6620779583, "rate": 6.9, "startDate": "2026-04-23", "endDate": "2026-10-23", "status": "Outstanding"},
        {"bank": "VCB", "amount": 124000000000, "rate": 8.0, "startDate": "2026-04-20", "endDate": "2026-10-19", "status": "Outstanding"},
        {"bank": "VCB", "amount": 177000000000, "rate": 8.0, "startDate": "2026-05-05", "endDate": "2026-11-02", "status": "Outstanding"},
        {"bank": "BIDV", "amount": 14709047762, "rate": 7.0, "startDate": "2026-05-05", "endDate": "2026-11-02", "status": "Outstanding"},
        {"bank": "BIDV", "amount": 79827117385, "rate": 7.0, "startDate": "2026-05-11", "endDate": "2026-11-06", "status": "Outstanding"},
    ],
    "investments": [
        {"bank": "TCBS", "amount": 221128300000, "rate": 8.0, "type": "BOND", "startDate": "2025-12-16", "endDate": "2026-06-16", "status": "Outstanding"},
        {"bank": "TCBS", "amount": 120736438800, "rate": 8.5, "type": "BOND", "startDate": "2026-01-28", "endDate": "2026-07-28", "status": "Outstanding"},
        {"bank": "VPB", "amount": 100000000000, "rate": 8.3, "type": "TD", "startDate": "2026-01-28", "endDate": "2026-07-28", "status": "Outstanding"},
        {"bank": "VPB", "amount": 70000000000, "rate": 8.3, "type": "TD", "startDate": "2026-01-28", "endDate": "2026-07-28", "status": "Outstanding"},
        {"bank": "VHM", "amount": 207457534000, "rate": 9.0, "type": "BOND", "startDate": "2026-02-06", "endDate": "2026-08-06", "status": "Outstanding"},
        {"bank": "TVS", "amount": 150000000000, "rate": 9.0, "type": "BOND", "startDate": "2026-03-16", "endDate": "2026-06-16", "status": "Outstanding"},
        {"bank": "TVS", "amount": 152280822000, "rate": 9.3, "type": "BOND", "startDate": "2026-05-28", "endDate": "2026-11-30", "status": "Outstanding"},
        {"bank": "TCBS", "amount": 250000000000, "rate": 9.2, "type": "BOND", "startDate": "2026-06-02", "endDate": "2026-12-02", "status": "Outstanding"},
    ],
    "durationMismatches": [
        {"investBank": "TCBS", "loanBank": "VCB", "investEnd": "2026-07-28", "loanEnd": "2026-07-03", "daysDiff": 25, "investAmt": 120736438800, "loanAmt": 119000000000},
        {"investBank": "VPB", "loanBank": "VCB", "investEnd": "2026-07-28", "loanEnd": "2026-07-13", "daysDiff": 15, "investAmt": 100000000000, "loanAmt": 87701174143},
        {"investBank": "VPB", "loanBank": "VCB", "investEnd": "2026-07-28", "loanEnd": "2026-07-20", "daysDiff": 8, "investAmt": 70000000000, "loanAmt": 72100000000},
        {"investBank": "VHM", "loanBank": "Cathay", "investEnd": "2026-08-06", "loanEnd": "2026-08-04", "daysDiff": 2, "investAmt": 207457534000, "loanAmt": 200000000000},
        {"investBank": "TVS", "loanBank": "Shinhan", "investEnd": "2026-11-30", "loanEnd": "2026-10-23", "daysDiff": 38, "investAmt": 152280822000, "loanAmt": 6620779583},
        {"investBank": "TCBS", "loanBank": "VCB", "investEnd": "2026-12-02", "loanEnd": "2026-10-19", "daysDiff": 44, "investAmt": 250000000000, "loanAmt": 124000000000},
    ],
    "tsdbAnomalies": [
        {"bank": "BIDV", "amount": 87500000000, "reasons": ["Đã hết hạn (2025-03-20)"]},
        {"bank": "VCB", "amount": 15000000000, "reasons": ["Đã hết hạn (2025-04-10)"]},
        {"bank": "VCB", "amount": 35000000000, "reasons": ["Đã hết hạn (2025-06-12)"]},
        {"bank": "VCB", "amount": 25000000000, "reasons": ["Đã hết hạn (2025-06-18)"]},
        {"bank": "VIB", "amount": 85000000000, "reasons": ["Đã hết hạn (2025-06-16)"]},
        {"bank": "Shinhan", "amount": 48000000000, "reasons": ["Đã hết hạn (2025-09-20)"]},
        {"bank": "Cathay", "amount": 30000000000, "reasons": ["Đã hết hạn (2026-02-04)"]},
        {"bank": "N/A", "amount": 30000000000, "reasons": ["Đã hết hạn (2026-01-28)"]},
        {"bank": "N/A", "amount": 355500000000, "reasons": ["Lãi suất bằng 0 hoặc trống"]},
    ],
    "loanByBank": [
        {"bank": "VCB", "amount": 749962921699},
        {"bank": "Cathay", "amount": 200000000000},
        {"bank": "Shinhan", "amount": 159921586864},
        {"bank": "BIDV", "amount": 94536165147},
    ],
    "investByBank": [
        {"bank": "TCBS", "amount": 591864738800},
        {"bank": "VPB", "amount": 170000000000},
        {"bank": "VHM", "amount": 207457534000},
        {"bank": "TVS", "amount": 302280822000},
    ],
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
        user = _verify_session(self.headers)

        if not user:
            self.send_response(401)
            self.send_header("Content-Type", "application/json")
            self._set_cors(origin)
            self.send_header('X-RateLimit-Limit', '60')
            self.send_header('X-RateLimit-Window', '60')
            self.end_headers()
            self.wfile.write(json.dumps({
                "ok": False,
                "error": "Authentication required",
            }).encode())
            return

        ip = self.headers.get('X-Forwarded-For', self.client_address[0])
        timestamp = datetime.now(timezone.utc).isoformat()
        print(f'[AUDIT] {timestamp} | DATA_ACCESS | {user["email"]} | {ip}')

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self._set_cors(origin)
        self.send_header('X-RateLimit-Limit', '60')
        self.send_header('X-RateLimit-Window', '60')
        self.end_headers()
        self.wfile.write(json.dumps(FINANCIAL_DATA, ensure_ascii=False).encode("utf-8"))

    def log_message(self, format, *args):
        pass
