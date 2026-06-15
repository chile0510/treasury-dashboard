"""
GET /api/cron/daily_report
Vercel Cron Job — sends a daily treasury summary to GTalk every morning.

Schedule: 0 1 * * 1-5 (1:00 AM UTC = 8:00 AM Vietnam, Mon-Fri)
Secured via CRON_SECRET Bearer token.
"""

import json
import os
from datetime import datetime, timezone, timedelta
from http.server import BaseHTTPRequestHandler

from lib.treasury_data import FINANCIAL_DATA
from api.gtalk.gtalk_client import send_text_message, send_template_message

CRON_SECRET = os.environ.get("CRON_SECRET", "")
# Channel "Thông báo" (broadcast)
REPORT_CHANNEL_ID = os.environ.get("GTALK_REPORT_CHANNEL", "2066321049349345281")
DASHBOARD_URL = os.environ.get("DASHBOARD_URL", "https://treasury-dashboard-sepia.vercel.app")


def _verify_cron(headers) -> bool:
    """Verify the request is from Vercel's cron scheduler."""
    if not CRON_SECRET:
        return True  # No secret configured, allow (dev mode)
    auth = headers.get("Authorization", "")
    return auth == f"Bearer {CRON_SECRET}"


def _format_vnd(num: float) -> str:
    """Format a number as a Vietnamese Dong string."""
    if abs(num) >= 1e12:
        return f"{num / 1e12:,.1f} nghìn tỷ".replace(",", ".")
    if abs(num) >= 1e9:
        val = round(num / 1e9)
        return f"{val:,} tỷ".replace(",", ".")
    return f"{num:,.0f}".replace(",", ".")


def _days_from_now(date_str: str) -> int:
    try:
        target = datetime.strptime(date_str, "%Y-%m-%d")
        return (target - datetime.now()).days
    except ValueError:
        return 999


def _generate_morning_report() -> str:
    """Generate the daily morning report text."""
    s = FINANCIAL_DATA["summary"]
    vn_tz = timezone(timedelta(hours=7))
    now = datetime.now(vn_tz)
    date_str = now.strftime("%d/%m/%Y")
    weekday_names = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]
    weekday = weekday_names[now.weekday()]

    lines = [
        f"📊 **TREASURY DAILY REPORT**",
        f"📅 {weekday}, {date_str}",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━",
        "",
        "**💰 PORTFOLIO OVERVIEW**",
        f"• Tổng dư nợ: **{_format_vnd(s['totalLoan'])}**",
        f"• Tổng đầu tư: **{_format_vnd(s['totalInvest'])}**",
        f"• Funding rate: **{s['fundingRate']}%**",
        f"• Invest yield: **{s['investYield']}%**",
        f"• Net spread: **+{s['netSpread']}%**",
        f"• Net P&L: **+{_format_vnd(s['netPL'])}**",
        "",
    ]

    # Room alerts
    danger = [lc for lc in FINANCIAL_DATA["limitControls"] if lc["status"] == "danger"]
    warning = [lc for lc in FINANCIAL_DATA["limitControls"] if lc["status"] == "warning"]

    if danger or warning:
        lines.append("**🚨 CẢNH BÁO HẠN MỨC**")
        for lc in danger:
            lines.append(f"🔴 **{lc['bank']}**: {lc['util']}% — Room: {_format_vnd(lc['room'])}")
        for lc in warning:
            lines.append(f"🟡 **{lc['bank']}**: {lc['util']}% — Room: {_format_vnd(lc['room'])}")
        lines.append("")

    # Expiring soon (within 7 days)
    expiring = []
    for item in FINANCIAL_DATA["loans"] + FINANCIAL_DATA["investments"]:
        days = _days_from_now(item["endDate"])
        if 0 < days <= 7:
            item_type = "Vay" if "type" not in item else f"ĐT ({item['type']})"
            expiring.append((days, item["bank"], item_type, item["amount"], item["endDate"]))

    if expiring:
        expiring.sort()
        lines.append("**⏰ SẮP ĐÁO HẠN (≤7 ngày)**")
        for days, bank, itype, amt, end in expiring:
            lines.append(f"⚡ **{bank}** ({itype}) — {_format_vnd(amt)} — còn **{days} ngày**")
        lines.append("")

    # Mismatch summary
    mismatches = FINANCIAL_DATA["durationMismatches"]
    if mismatches:
        high_risk = [m for m in mismatches if m["daysDiff"] > 30]
        lines.append(f"**⚠️ DURATION MISMATCH: {len(mismatches)} cặp** (🔴 cao: {len(high_risk)})")
        lines.append("")

    lines.extend([
        "━━━━━━━━━━━━━━━━━━━━━━━━",
        f"🔗 Dashboard: {DASHBOARD_URL}",
        "💬 Gõ `help` trong Chat chung để xem thêm lệnh",
    ])

    return "\n".join(lines)


class handler(BaseHTTPRequestHandler):
    server_version = "TreasuryCron"
    sys_version = ""

    def do_GET(self):
        timestamp = datetime.now(timezone.utc).isoformat()

        # Verify cron secret
        if not _verify_cron(self.headers):
            print(f"[CRON] {timestamp} | UNAUTHORIZED")
            self.send_response(401)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Unauthorized"}).encode())
            return

        print(f"[CRON] {timestamp} | DAILY_REPORT triggered")

        # Generate and send report
        report_text = _generate_morning_report()
        result = send_text_message(REPORT_CHANNEL_ID, report_text)

        print(f"[CRON] {timestamp} | REPORT sent to {REPORT_CHANNEL_ID} | result={result.get('errorCode')}")

        # Response
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({
            "ok": True,
            "report_channel": REPORT_CHANNEL_ID,
            "send_result": result.get("errorCode", "unknown"),
            "timestamp": timestamp,
        }, ensure_ascii=False).encode())

    def log_message(self, format, *args):
        pass
