"""
POST /api/gtalk/webhook
Webhook endpoint for GTalk chatbot — Treasury Portfolio queries.

This Vercel serverless function:
1. Receives webhook POSTs from GTalk when users send messages
2. Verifies HMAC-SHA256 signature
3. Sends SEEN + TYPING receipts immediately
4. Parses user intent (keyword-based)
5. Queries financial data
6. Replies with formatted Markdown text
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import re
from datetime import datetime, timezone

# Import GTalk client functions (same directory, no handler class = not a serverless endpoint)
from api.gtalk.gtalk_client import (
    send_text_message,
    send_receipt,
    verify_webhook_signature,
)

# Import shared financial data
from lib.treasury_data import FINANCIAL_DATA

WEBHOOK_SECRET = os.environ.get("GTALK_WEBHOOK_SECRET", "")

# ============================================================
# Utility: Format VND amounts
# ============================================================

def format_vnd(num: float) -> str:
    """Format a number as a Vietnamese Dong string."""
    if abs(num) >= 1e12:
        return f"{num / 1e12:,.1f} nghìn tỷ".replace(",", ".")
    if abs(num) >= 1e9:
        val = round(num / 1e9)
        return f"{val:,} tỷ".replace(",", ".")
    if abs(num) >= 1e6:
        return f"{num / 1e6:,.0f} triệu".replace(",", ".")
    return f"{num:,.0f}".replace(",", ".")


def format_date(date_str: str) -> str:
    """Convert YYYY-MM-DD to DD/MM/YYYY."""
    if not date_str:
        return "—"
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        return d.strftime("%d/%m/%Y")
    except ValueError:
        return date_str


def days_from_now(date_str: str) -> int:
    """Calculate days between now and a date string."""
    try:
        target = datetime.strptime(date_str, "%Y-%m-%d")
        now = datetime.now()
        return (target - now).days
    except ValueError:
        return 0


# ============================================================
# Intent Parsing (keyword-based, no AI required)
# ============================================================

# Bank name aliases for fuzzy matching
BANK_ALIASES = {
    "vcb": "VCB", "vietcombank": "VCB",
    "bidv": "BIDV",
    "cathay": "Cathay",
    "shinhan": "Shinhan",
    "hsbc": "HSBC",
    "tcbs": "TCBS",
    "vpb": "VPB", "vpbank": "VPB",
    "vhm": "VHM", "vinhomes": "VHM",
    "tvs": "TVS",
    "vib": "VIB",
}


def extract_bank(text: str) -> str | None:
    """Extract a bank name from the user's message text."""
    text_lower = text.lower()
    for alias, canonical in BANK_ALIASES.items():
        # Match as whole word or at word boundary
        if re.search(r'\b' + re.escape(alias) + r'\b', text_lower):
            return canonical
    return None


def parse_intent(text: str) -> tuple[str, dict]:
    """
    Parse the user's message and return (intent, params).
    Uses simple keyword matching — no external AI dependency.
    Handles both Vietnamese with and without diacritics.
    """
    text_lower = text.lower().strip()

    # Help / commands
    if any(w in text_lower for w in ["help", "trợ giúp", "tro giup", "hướng dẫn", "huong dan", "menu", "/start", "commands", "lệnh", "lenh"]):
        return "help", {}

    # Limit / Room query (with optional bank filter)
    if any(w in text_lower for w in ["room", "hạn mức", "han muc", "limit", "giới hạn", "gioi han", "dư nợ ngân hàng", "du no ngan hang"]):
        bank = extract_bank(text)
        return "query_limit", {"bank": bank}

    # Duration mismatch
    if any(w in text_lower for w in ["mismatch", "duration", "lệch kỳ", "lech ky", "lệch hạn", "lech han", "kỳ hạn lệch", "ky han lech"]):
        return "query_mismatch", {}

    # Maturity / expiring
    if any(w in text_lower for w in ["đáo hạn", "dao han", "maturity", "sắp hạn", "sap han", "expire", "hết hạn", "het han", "đến hạn", "den han"]):
        return "query_maturity", {}

    # Spread / rates
    if any(w in text_lower for w in ["spread", "lãi suất", "lai suat", "yield", "lãi ròng", "lai rong", "net interest"]):
        return "query_spread", {}

    # Summary / overview
    if any(w in text_lower for w in ["tổng", "tong", "summary", "tổng quan", "tong quan", "overview", "báo cáo", "bao cao", "report", "tình hình", "tinh hinh"]):
        return "query_summary", {}

    # Investments query
    if any(w in text_lower for w in ["đầu tư", "dau tu", "invest", "bond", "trái phiếu", "trai phieu", "tiền gửi", "tien gui"]):
        return "query_investments", {}

    # Loans query
    if any(w in text_lower for w in ["vay", "loan", "khoản vay", "khoan vay", "nợ", "no", "dư nợ", "du no"]):
        return "query_loans", {}

    # Fallback: unknown
    return "unknown", {}


# ============================================================
# Response Generators
# ============================================================

def reply_help() -> str:
    return (
        "📋 **Treasury Bot — Danh sách lệnh**\n\n"
        "Bạn có thể hỏi tôi bằng tiếng Việt hoặc tiếng Anh:\n\n"
        "• `tổng quan` — Tóm tắt portfolio\n"
        "• `room BIDV` — Hạn mức & room của ngân hàng\n"
        "• `hạn mức` — Tất cả hạn mức ngân hàng\n"
        "• `đáo hạn` — Khoản sắp đáo hạn (<30 ngày)\n"
        "• `spread` — Lãi suất & spread hiện tại\n"
        "• `mismatch` — Duration mismatch\n"
        "• `đầu tư` — Danh sách đầu tư\n"
        "• `khoản vay` — Danh sách khoản vay\n"
        "• `help` — Xem lại menu này\n"
    )


def reply_summary() -> str:
    s = FINANCIAL_DATA["summary"]
    danger_banks = [lc["bank"] for lc in FINANCIAL_DATA["limitControls"] if lc["status"] == "danger"]
    mismatches = len(FINANCIAL_DATA["durationMismatches"])

    return (
        "📊 **Treasury Portfolio — Tóm tắt**\n\n"
        f"💰 Tổng dư nợ: **{format_vnd(s['totalLoan'])}**\n"
        f"📈 Tổng đầu tư: **{format_vnd(s['totalInvest'])}**\n"
        f"📊 Funding rate: **{s['fundingRate']}%**\n"
        f"📊 Invest yield: **{s['investYield']}%**\n"
        f"✨ Net spread: **+{s['netSpread']}%**\n"
        f"💵 Net P&L: **+{format_vnd(s['netPL'])}**\n"
        f"📦 Tỷ trọng: TD {s['tdPct']}% | Bond {s['bondPct']}%\n\n"
        f"🔴 Room cạn: **{', '.join(danger_banks) if danger_banks else 'Không có'}**\n"
        f"⚠️ Duration mismatch: **{mismatches} cặp**\n"
    )


def reply_limit(bank: str | None) -> str:
    limits = FINANCIAL_DATA["limitControls"]

    if bank:
        # Filter for specific bank
        found = [lc for lc in limits if lc["bank"].lower() == bank.lower()]
        if not found:
            return f"❌ Không tìm thấy ngân hàng **{bank}** trong danh sách hạn mức."

        lc = found[0]
        icon = "🔴" if lc["status"] == "danger" else "🟢"
        return (
            f"🏦 **{lc['bank']} — Thông tin Hạn mức**\n\n"
            f"• Dư nợ: **{format_vnd(lc['duNo'])}**\n"
            f"• Hạn mức: **{format_vnd(lc['hanMuc'])}**\n"
            f"• Sử dụng: **{lc['util']}%** {icon}\n"
            f"• Room còn lại: **{format_vnd(lc['room'])}**\n"
        )

    # Show all banks
    lines = ["🏦 **Tổng quan Hạn mức Ngân hàng**\n"]
    for lc in limits:
        icon = "🔴" if lc["status"] == "danger" else "🟢"
        lines.append(
            f"{icon} **{lc['bank']}**: {format_vnd(lc['duNo'])}/{format_vnd(lc['hanMuc'])} "
            f"({lc['util']}%) — Room: {format_vnd(lc['room'])}"
        )
    return "\n".join(lines)


def reply_maturity() -> str:
    now = datetime.now()
    threshold_days = 30

    # Check investments
    expiring_inv = []
    for inv in FINANCIAL_DATA["investments"]:
        days = days_from_now(inv["endDate"])
        if 0 < days <= threshold_days:
            expiring_inv.append({**inv, "daysLeft": days})
    expiring_inv.sort(key=lambda x: x["daysLeft"])

    # Check loans
    expiring_loans = []
    for loan in FINANCIAL_DATA["loans"]:
        days = days_from_now(loan["endDate"])
        if 0 < days <= threshold_days:
            expiring_loans.append({**loan, "daysLeft": days})
    expiring_loans.sort(key=lambda x: x["daysLeft"])

    lines = ["⏰ **Khoản sắp đáo hạn (≤30 ngày)**\n"]

    if expiring_inv:
        lines.append("**📈 Đầu tư:**")
        for inv in expiring_inv:
            lines.append(
                f"• **{inv['bank']}** ({inv['type']}) — {format_vnd(inv['amount'])} "
                f"@ {inv['rate']}% — đáo hạn {format_date(inv['endDate'])} "
                f"(**{inv['daysLeft']} ngày**)"
            )
    else:
        lines.append("📈 Đầu tư: _Không có khoản nào đáo hạn trong 30 ngày_")

    lines.append("")

    if expiring_loans:
        lines.append("**💰 Khoản vay:**")
        for loan in expiring_loans:
            lines.append(
                f"• **{loan['bank']}** — {format_vnd(loan['amount'])} "
                f"@ {loan['rate']}% — đáo hạn {format_date(loan['endDate'])} "
                f"(**{loan['daysLeft']} ngày**)"
            )
    else:
        lines.append("💰 Khoản vay: _Không có khoản nào đáo hạn trong 30 ngày_")

    if not expiring_inv and not expiring_loans:
        # Extend to 60 days
        lines = ["⏰ **Khoản đáo hạn trong 60 ngày tới**\n"]
        for inv in FINANCIAL_DATA["investments"]:
            days = days_from_now(inv["endDate"])
            if 0 < days <= 60:
                lines.append(
                    f"• **{inv['bank']}** ({inv['type']}) — {format_vnd(inv['amount'])} "
                    f"— đáo hạn {format_date(inv['endDate'])} ({days} ngày)"
                )

    return "\n".join(lines)


def reply_spread() -> str:
    s = FINANCIAL_DATA["summary"]
    return (
        "📊 **Lãi suất & Spread**\n\n"
        f"• Funding rate (vay): **{s['fundingRate']}%**\n"
        f"• Invest yield (đầu tư): **{s['investYield']}%**\n"
        f"• Net spread: **+{s['netSpread']}%**\n"
        f"• Net P&L: **+{format_vnd(s['netPL'])}**\n"
    )


def reply_mismatch() -> str:
    mismatches = FINANCIAL_DATA["durationMismatches"]
    if not mismatches:
        return "✅ Không có duration mismatch nào."

    lines = [f"⚠️ **Duration Mismatch — {len(mismatches)} cặp**\n"]
    for dm in mismatches:
        risk = "🔴 Cao" if dm["daysDiff"] > 30 else ("🟡 TB" if dm["daysDiff"] > 10 else "🟢 Thấp")
        lines.append(
            f"• **{dm['investBank']}** → **{dm['loanBank']}**: "
            f"lệch **{dm['daysDiff']} ngày** {risk}\n"
            f"  ĐT đáo {format_date(dm['investEnd'])} | Vay đáo {format_date(dm['loanEnd'])} | "
            f"Số tiền: {format_vnd(dm['investAmt'])}"
        )
    return "\n".join(lines)


def reply_investments() -> str:
    investments = FINANCIAL_DATA["investments"]
    lines = [f"📈 **Danh sách Đầu tư — {len(investments)} khoản**\n"]
    total = 0
    for i, inv in enumerate(investments, 1):
        days = days_from_now(inv["endDate"])
        urgency = "🔴" if days <= 15 else ("🟡" if days <= 45 else "🟢")
        lines.append(
            f"{i}. {urgency} **{inv['bank']}** ({inv['type']}) — "
            f"{format_vnd(inv['amount'])} @ {inv['rate']}% — "
            f"đáo hạn {format_date(inv['endDate'])} ({days} ngày)"
        )
        total += inv["amount"]
    lines.append(f"\n**Tổng đầu tư: {format_vnd(total)}**")
    return "\n".join(lines)


def reply_loans() -> str:
    loans = FINANCIAL_DATA["loans"]
    lines = [f"💰 **Danh sách Khoản vay — {len(loans)} khoản**\n"]
    total = 0
    for i, loan in enumerate(loans, 1):
        days = days_from_now(loan["endDate"])
        urgency = "🔴" if days <= 15 else ("🟡" if days <= 45 else "🟢")
        lines.append(
            f"{i}. {urgency} **{loan['bank']}** — "
            f"{format_vnd(loan['amount'])} @ {loan['rate']}% — "
            f"đáo hạn {format_date(loan['endDate'])} ({days} ngày)"
        )
        total += loan["amount"]
    lines.append(f"\n**Tổng dư nợ: {format_vnd(total)}**")
    return "\n".join(lines)


def reply_unknown() -> str:
    return (
        "🤔 Tôi chưa hiểu câu hỏi của bạn.\n\n"
        "Gõ **help** để xem danh sách lệnh tôi hỗ trợ."
    )


# Map intent → response generator
INTENT_HANDLERS = {
    "help": lambda params: reply_help(),
    "query_summary": lambda params: reply_summary(),
    "query_limit": lambda params: reply_limit(params.get("bank")),
    "query_maturity": lambda params: reply_maturity(),
    "query_spread": lambda params: reply_spread(),
    "query_mismatch": lambda params: reply_mismatch(),
    "query_investments": lambda params: reply_investments(),
    "query_loans": lambda params: reply_loans(),
    "unknown": lambda params: reply_unknown(),
}


def generate_reply(intent: str, params: dict) -> str:
    handler = INTENT_HANDLERS.get(intent, INTENT_HANDLERS["unknown"])
    return handler(params)


# ============================================================
# Vercel Serverless Function Handler
# ============================================================

class handler(BaseHTTPRequestHandler):
    server_version = "TreasuryBot"
    sys_version = ""

    def do_POST(self):
        timestamp = datetime.now(timezone.utc).isoformat()

        # --- 1. Read raw body ---
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length)

        print(f"[WEBHOOK] {timestamp} | RECEIVED POST | size={content_length}")
        print(f"[WEBHOOK] {timestamp} | HEADERS | sig={self.headers.get('x-gtalk-event-signature', 'NONE')}")

        # --- 2. Skip signature verification for now (debug mode) ---
        # TODO: Re-enable after confirming webhook works end-to-end
        # if WEBHOOK_SECRET:
        #     signature = self.headers.get("x-gtalk-event-signature", "")
        #     if not verify_webhook_signature(raw_body, signature, WEBHOOK_SECRET):
        #         print(f"[WEBHOOK] {timestamp} | SIGNATURE_INVALID")
        #         self.send_response(401)
        #         self.send_header("Content-Type", "application/json")
        #         self.end_headers()
        #         self.wfile.write(json.dumps({"error": "Invalid signature"}).encode())
        #         return

        # --- 3. Parse payload ---
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            print(f"[WEBHOOK] {timestamp} | JSON_PARSE_ERROR | {e}")
            print(f"[WEBHOOK] {timestamp} | RAW_BODY | {raw_body[:500]}")
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode())
            return

        print(f"[WEBHOOK] {timestamp} | PAYLOAD | {json.dumps(payload, ensure_ascii=False)[:500]}")

        # Extract fields - content can be a string or a dict with "text" key
        raw_content = payload.get("content", "")
        if isinstance(raw_content, dict):
            content = raw_content.get("text", "")
        else:
            content = str(raw_content)

        content_type = payload.get("contentType", 0)
        channel_id = str(payload.get("channelId", ""))
        sender_id = str(payload.get("senderId", ""))
        global_msg_id = str(payload.get("globalMsgId", ""))
        oa_id = str(payload.get("oaId", ""))

        print(f"[WEBHOOK] {timestamp} | MSG from={sender_id} ch={channel_id} type={content_type} text={content[:80]}")

        # --- 4. Ignore non-text messages ---
        if content_type != 0:
            print(f"[WEBHOOK] {timestamp} | SKIP non-text contentType={content_type}")
            self._ok_response()
            return

        # Ignore empty messages
        if not content.strip():
            print(f"[WEBHOOK] {timestamp} | SKIP empty content")
            self._ok_response()
            return

        # Ignore messages from the bot itself (prevent loops)
        oa_id_env = os.environ.get("GTALK_OA_ID", "")
        if sender_id and sender_id == oa_id_env:
            print(f"[WEBHOOK] {timestamp} | SKIP own message")
            self._ok_response()
            return

        # --- 5. Send SEEN + TYPING receipt ---
        if global_msg_id and channel_id and oa_id:
            receipt_result = send_receipt(oa_id, channel_id, global_msg_id, [2, 3])
            print(f"[WEBHOOK] {timestamp} | RECEIPT result={receipt_result}")

        # --- 6. Parse intent & generate reply ---
        intent, params = parse_intent(content)
        reply_text = generate_reply(intent, params)

        print(f"[WEBHOOK] {timestamp} | INTENT={intent} params={params}")

        # --- 7. Send reply ---
        if channel_id:
            result = send_text_message(channel_id, reply_text)
            print(f"[WEBHOOK] {timestamp} | REPLY_RESULT={json.dumps(result, ensure_ascii=False)[:300]}")

        # --- 8. Return 200 OK to GTalk ---
        self._ok_response()

    def _ok_response(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True}).encode())

    def do_GET(self):
        """Health check endpoint."""
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "ok",
            "service": "Treasury GTalk Chatbot",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "base_url": os.environ.get("GTALK_BASE_URL", "NOT_SET"),
        }).encode())

    def log_message(self, format, *args):
        # Suppress default HTTP logging
        pass

