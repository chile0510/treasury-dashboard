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
    # Same-origin requests may not include Origin header — allow them
    # Security: session cookie is SameSite=Strict, so cross-site can't send it
    if not origin:
        return ALLOWED_ORIGINS[1]  # default to production origin
    return None  # reject unknown cross-origin requests


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
        "totalLoan": 1219358926154.0,
        "fundingRate": 6.98,
        "totalInvest": 1481603094800.0,
        "investYield": 8.84,
        "netSpread": 1.86,
        "netPL": 43593948337.391396,
        "tdPct": 34.3,
        "bondPct": 65.7,
        "tdAmount": 946000000000.0,
        "bondAmount": 1814203094800.0,
        "totalTSDB": 240500000000.0,
        "totalHanMuc": 1610000000000.0
    },
    "limitControls": [
        {
            "bank": "Cathay",
            "duNo": 200000000000.0,
            "hanMuc": 200000000000.0,
            "util": 100.0,
            "room": 0.0,
            "status": "danger"
        },
        {
            "bank": "Shinhan",
            "duNo": 159921586864.0,
            "hanMuc": 160000000000.0,
            "util": 100.0,
            "room": 78413136.0,
            "status": "danger"
        },
        {
            "bank": "VCB",
            "duNo": 653901174143.0,
            "hanMuc": 750000000000.0,
            "util": 87.2,
            "room": 96098825857.0,
            "status": "warning"
        },
        {
            "bank": "HSBC",
            "duNo": 111000000000.0,
            "hanMuc": 250000000000.0,
            "util": 44.4,
            "room": 139000000000.0,
            "status": "safe"
        },
        {
            "bank": "BIDV",
            "duNo": 94536165147.0,
            "hanMuc": 250000000000.0,
            "util": 37.8,
            "room": 155463834853.0,
            "status": "safe"
        }
    ],
    "loans": [
        {
            "bank": "VCB",
            "amount": 74100000000.0,
            "rate": 6.0,
            "startDate": "2025-12-22",
            "endDate": "2026-06-19",
            "status": "Outstanding"
        },
        {
            "bank": "VCB",
            "amount": 119000000000.0,
            "rate": 6.0,
            "startDate": "2026-01-05",
            "endDate": "2026-07-03",
            "status": "Outstanding"
        },
        {
            "bank": "VCB",
            "amount": 87701174143.0,
            "rate": 6.0,
            "startDate": "2026-01-15",
            "endDate": "2026-07-13",
            "status": "Outstanding"
        },
        {
            "bank": "VCB",
            "amount": 72100000000.0,
            "rate": 6.0,
            "startDate": "2026-01-20",
            "endDate": "2026-07-20",
            "status": "Outstanding"
        },
        {
            "bank": "Cathay",
            "amount": 200000000000.0,
            "rate": 7.2,
            "startDate": "2026-02-05",
            "endDate": "2026-08-04",
            "status": "Outstanding"
        },
        {
            "bank": "Shinhan",
            "amount": 143663435630.0,
            "rate": 6.9,
            "startDate": "2026-04-15",
            "endDate": "2026-10-15",
            "status": "Outstanding"
        },
        {
            "bank": "Shinhan",
            "amount": 9637371651.0,
            "rate": 6.9,
            "startDate": "2026-04-20",
            "endDate": "2026-10-20",
            "status": "Outstanding"
        },
        {
            "bank": "Shinhan",
            "amount": 6620779583.0,
            "rate": 6.9,
            "startDate": "2026-04-23",
            "endDate": "2026-10-23",
            "status": "Outstanding"
        },
        {
            "bank": "VCB",
            "amount": 124000000000.0,
            "rate": 8.0,
            "startDate": "2026-04-20",
            "endDate": "2026-10-19",
            "status": "Outstanding"
        },
        {
            "bank": "VCB",
            "amount": 177000000000.0,
            "rate": 8.0,
            "startDate": "2026-05-05",
            "endDate": "2026-11-02",
            "status": "Outstanding"
        },
        {
            "bank": "BIDV",
            "amount": 14709047762.0,
            "rate": 7.0,
            "startDate": "2026-05-05",
            "endDate": "2026-11-02",
            "status": "Outstanding"
        },
        {
            "bank": "BIDV",
            "amount": 79827117385.0,
            "rate": 7.0,
            "startDate": "2026-05-11",
            "endDate": "2026-11-06",
            "status": "Outstanding"
        },
        {
            "bank": "HSBC",
            "amount": 111000000000.0,
            "rate": 7.0,
            "startDate": "2026-06-05",
            "endDate": "2026-11-02",
            "status": "Outstanding"
        }
    ],
    "investments": [
        {
            "bank": "TCBS",
            "amount": 221128300000.0,
            "rate": 8.0,
            "type": "BOND",
            "startDate": "2025-12-16",
            "endDate": "2026-06-16",
            "status": "Outstanding"
        },
        {
            "bank": "TCBS",
            "amount": 120736438800.0,
            "rate": 8.5,
            "type": "BOND",
            "startDate": "2026-01-28",
            "endDate": "2026-07-28",
            "status": "Outstanding"
        },
        {
            "bank": "VPB",
            "amount": 100000000000.0,
            "rate": 8.3,
            "type": "TD",
            "startDate": "2026-01-28",
            "endDate": "2026-07-28",
            "status": "Outstanding"
        },
        {
            "bank": "VPB",
            "amount": 70000000000.0,
            "rate": 8.3,
            "type": "TD",
            "startDate": "2026-01-28",
            "endDate": "2026-07-28",
            "status": "Outstanding"
        },
        {
            "bank": "VHM",
            "amount": 207457534000.0,
            "rate": 9.0,
            "type": "BOND",
            "startDate": "2026-02-06",
            "endDate": "2026-08-06",
            "status": "Outstanding"
        },
        {
            "bank": "TVS",
            "amount": 150000000000.0,
            "rate": 9.0,
            "type": "BOND",
            "startDate": "2026-03-16",
            "endDate": "2026-06-16",
            "status": "Outstanding"
        },
        {
            "bank": "TVS",
            "amount": 152280822000.0,
            "rate": 9.3,
            "type": "BOND",
            "startDate": "2026-05-28",
            "endDate": "2026-11-30",
            "status": "Outstanding"
        },
        {
            "bank": "TCBS",
            "amount": 250000000000.0,
            "rate": 9.2,
            "type": "BOND",
            "startDate": "2026-06-02",
            "endDate": "2026-12-02",
            "status": "Outstanding"
        },
        {
            "bank": "VPB",
            "amount": 210000000000.0,
            "rate": 9.3,
            "type": "TD",
            "startDate": "2026-06-12",
            "endDate": "2026-12-12",
            "status": "Outstanding"
        }
    ],
    "durationMismatches": [
        {
            "investBank": "TCBS",
            "loanBank": "VCB",
            "investEnd": "2026-07-28",
            "loanEnd": "2026-07-03",
            "daysDiff": 25,
            "investAmt": 120736438800.0,
            "loanAmt": 119000000000.0
        },
        {
            "investBank": "VPB",
            "loanBank": "VCB",
            "investEnd": "2026-07-28",
            "loanEnd": "2026-07-13",
            "daysDiff": 15,
            "investAmt": 100000000000.0,
            "loanAmt": 87701174143.0
        },
        {
            "investBank": "VPB",
            "loanBank": "VCB",
            "investEnd": "2026-07-28",
            "loanEnd": "2026-07-20",
            "daysDiff": 8,
            "investAmt": 70000000000.0,
            "loanAmt": 72100000000.0
        },
        {
            "investBank": "VHM",
            "loanBank": "Cathay",
            "investEnd": "2026-08-06",
            "loanEnd": "2026-08-04",
            "daysDiff": 2,
            "investAmt": 207457534000.0,
            "loanAmt": 200000000000.0
        },
        {
            "investBank": "TVS",
            "loanBank": "Shinhan",
            "investEnd": "2026-11-30",
            "loanEnd": "2026-10-23",
            "daysDiff": 38,
            "investAmt": 152280822000.0,
            "loanAmt": 6620779583.0
        },
        {
            "investBank": "TCBS",
            "loanBank": "VCB",
            "investEnd": "2026-12-02",
            "loanEnd": "2026-10-19",
            "daysDiff": 44,
            "investAmt": 250000000000.0,
            "loanAmt": 124000000000.0
        },
        {
            "investBank": "VPB",
            "loanBank": "BIDV",
            "investEnd": "2026-12-12",
            "loanEnd": "2026-11-02",
            "daysDiff": 40,
            "investAmt": 210000000000.0,
            "loanAmt": 14709047762.0
        }
    ],
    "tsdbAnomalies": [
        {
            "bank": "BIDV",
            "amount": 87500000000.0,
            "reasons": [
                "Đã hết hạn (2025-03-20)"
            ]
        },
        {
            "bank": "VCB",
            "amount": 15000000000.0,
            "reasons": [
                "Đã hết hạn (2025-04-10)"
            ]
        },
        {
            "bank": "VCB",
            "amount": 35000000000.0,
            "reasons": [
                "Đã hết hạn (2025-06-12)"
            ]
        },
        {
            "bank": "VCB",
            "amount": 25000000000.0,
            "reasons": [
                "Đã hết hạn (2025-06-18)"
            ]
        },
        {
            "bank": "VIB",
            "amount": 85000000000.0,
            "reasons": [
                "Đã hết hạn (2025-06-16)"
            ]
        },
        {
            "bank": "Shinhan",
            "amount": 48000000000.0,
            "reasons": [
                "Đã hết hạn (2025-09-20)"
            ]
        },
        {
            "bank": "Cathay",
            "amount": 30000000000.0,
            "reasons": [
                "Đã hết hạn (2026-02-04)"
            ]
        },
        {
            "bank": "N/A",
            "amount": 30000000000.0,
            "reasons": [
                "Đã hết hạn (2026-01-28)"
            ]
        },
        {
            "bank": "N/A",
            "amount": 355500000000.0,
            "reasons": [
                "Lãi suất bằng 0 hoặc trống"
            ]
        }
    ],
    "loanByBank": [
        {
            "bank": "VCB",
            "amount": 653901174143.0
        },
        {
            "bank": "Cathay",
            "amount": 200000000000.0
        },
        {
            "bank": "Shinhan",
            "amount": 159921586864.0
        },
        {
            "bank": "BIDV",
            "amount": 94536165147.0
        },
        {
            "bank": "HSBC",
            "amount": 111000000000.0
        }
    ],
    "investByBank": [
        {
            "bank": "TCBS",
            "amount": 591864738800.0
        },
        {
            "bank": "VPB",
            "amount": 380000000000.0
        },
        {
            "bank": "VHM",
            "amount": 207457534000.0
        },
        {
            "bank": "TVS",
            "amount": 302280822000.0
        }
    ]
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
