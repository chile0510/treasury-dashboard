"""AI-powered intent parser using Google Gemini API.

Uses urllib.request (zero external dependencies) to call Gemini 2.0 Flash
for classifying user messages into Treasury chatbot intents.

Falls back to None on any failure so the caller can use a keyword-based parser.
"""

import json
import os
import re
import urllib.request
import urllib.error
from typing import Optional

# Gemini API configuration
_GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/"
    "models/gemini-2.0-flash:generateContent"
)
_TIMEOUT_SECONDS = 5

_SYSTEM_PROMPT = """\
You are an intent classifier for a Vietnamese Treasury Dashboard chatbot.

Classify the user message into exactly ONE of these intents:

- help: user wants to see instructions, help, or available commands (e.g. "xem hướng dẫn", "commands", "trợ giúp")
- query_summary: user asks for a portfolio overview or summary report (e.g. "tổng quan portfolio", "báo cáo tổng hợp")
- query_limit: user asks about bank credit limits (e.g. "hạn mức ngân hàng", "limit"). Extract the bank name into params.bank if mentioned.
- query_maturity: user asks about upcoming maturities (e.g. "khoản sắp đáo hạn", "maturity")
- query_spread: user asks about interest rates, spread, or yield (e.g. "lãi suất", "spread", "yield")
- query_mismatch: user asks about duration mismatch (e.g. "duration mismatch", "lệch kỳ hạn")
- query_investments: user asks about investment list, bonds, or deposits (e.g. "danh sách đầu tư", "bond", "tiền gửi")
- query_loans: user asks about loan list or outstanding debt (e.g. "danh sách khoản vay", "dư nợ")
- export_report: user wants to export or download a report (e.g. "xuất file", "export", "tải báo cáo")
- unknown: message does not match any of the above intents

Respond with ONLY a JSON object in this exact format (no markdown, no explanation):
{"intent": "<intent_name>", "params": {}}

If the user mentions a specific bank name for query_limit, include it:
{"intent": "query_limit", "params": {"bank": "<bank_name>"}}

For all other intents, params should be an empty object {}.
"""


def ai_parse_intent(user_message: str) -> Optional[tuple[str, dict]]:
    """Parse a user message into an intent using Google Gemini API.

    Sends the user message to Gemini 2.0 Flash with a system prompt that
    instructs the model to classify the message into a Treasury chatbot intent.

    Args:
        user_message: The raw text message from the user.

    Returns:
        A tuple of (intent_name, params_dict) on success, e.g.
        ("query_limit", {"bank": "VCB"}), or None if the API key is not
        configured, the API call fails, or the response cannot be parsed.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None

    url = f"{_GEMINI_ENDPOINT}?key={api_key}"

    request_body = {
        "system_instruction": {
            "parts": [{"text": _SYSTEM_PROMPT}],
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": user_message}],
            }
        ],
        "generationConfig": {
            "temperature": 0.0,
            "maxOutputTokens": 256,
        },
    }

    try:
        data = json.dumps(request_body).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=_TIMEOUT_SECONDS) as resp:
            response_body = json.loads(resp.read().decode("utf-8"))

        return _extract_intent(response_body)

    except (urllib.error.URLError, urllib.error.HTTPError):
        return None
    except (json.JSONDecodeError, KeyError, IndexError, TypeError):
        return None
    except OSError:
        return None
    except Exception:
        # Catch-all: never let this module crash the caller
        return None


def _extract_intent(response_body: dict) -> Optional[tuple[str, dict]]:
    """Extract intent and params from a Gemini API response.

    Args:
        response_body: The parsed JSON response from Gemini API.

    Returns:
        A tuple of (intent, params) or None if extraction fails.
    """
    try:
        text = response_body["candidates"][0]["content"]["parts"][0]["text"]
        text = _strip_code_fences(text.strip())
        parsed = json.loads(text)

        intent = parsed.get("intent")
        if not isinstance(intent, str) or not intent:
            return None

        params = parsed.get("params", {})
        if not isinstance(params, dict):
            params = {}

        return (intent, params)

    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        return None


def _strip_code_fences(text: str) -> str:
    """Remove markdown code fences from Gemini response text.

    Gemini sometimes wraps JSON output in ```json ... ``` blocks.
    This function strips those fences so the inner JSON can be parsed.

    Args:
        text: Raw text that may contain markdown code fences.

    Returns:
        The text with code fences removed.
    """
    # Match ```json ... ``` or ``` ... ``` (with optional language tag)
    pattern = r"^```(?:json)?\s*\n?(.*?)\n?\s*```$"
    match = re.match(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text
