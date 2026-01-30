import os
import json
from groq import Groq

import re

def extract_signals(text: str) -> dict:
    upi_pattern = r"\b[\w.\-]{2,}@[a-zA-Z]{2,}\b"
    phone_pattern = r"\b(?:\+91[-\s]?)?[6-9]\d{9}\b"
    url_pattern = r"https?://[^\s]+"
    bank_acct_pattern = r"\b\d{9,18}\b"

    return {
        "upi_ids": list(set(re.findall(upi_pattern, text))),
        "phone_numbers": list(set(re.findall(phone_pattern, text))),
        "urls": list(set(re.findall(url_pattern, text))),
        "bank_accounts": list(set(re.findall(bank_acct_pattern, text))),
    }


# ---- Groq setup ----
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY not set")

client = Groq(api_key=GROQ_API_KEY)

MODEL = "llama-3.1-8b-instant"  # fast + supported


def detect_scam(messages: list[dict]) -> dict:
    """
    messages = [
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."},
        ...
    ]
    """

    system_prompt = """
You are an AI scam detection and safety assistant.

Tasks:
1. Decide if the message is a scam
2. If it IS a scam, generate a polite, safe reply the user can send
3. If it is NOT a scam, set safe_reply to null

Rules:
- Respond ONLY in valid JSON
- No markdown
- No extra keys
- Be concise and practical

JSON format:
{
  "is_scam": true or false,
  "scam_type": "payment" | "phishing" | "lottery" | "impersonation" | "other" | "none",
  "confidence": number between 0 and 1,
  "reason": "short explanation",
  "safe_reply": "message user can send" or null
}
"""

    completion = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": system_prompt},
            *messages
        ]
    )

    raw = completion.choices[0].message.content.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON from model:\n{raw}")
