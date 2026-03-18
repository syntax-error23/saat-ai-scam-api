import os
import json
import re
import random
from typing import List, Dict, Optional
from groq import Groq

# =========================
# LLM SETUP
# =========================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY not set")

client = Groq(api_key=GROQ_API_KEY)
MODEL = "llama-3.1-8b-instant"


# =========================
# SCAM DETECTION MODULE
# =========================
def detect_scam(messages: List[Dict]) -> Dict:
    """
    Hybrid detection:
    - fast keyword check
    - LLM fallback
    - safe output always
    """

    try:
        joined = " ".join(m.get("content", "").lower() for m in messages)

        KEYWORDS = [
            "otp", "verify", "upi", "payment", "urgent",
            "bank", "lottery", "winner", "prize",
            "blocked", "suspended", "click", "link",
            "account", "transfer", "fee"
        ]

        if any(k in joined for k in KEYWORDS):
            return {
                "is_scam": True,
                "scam_type": "phishing",
                "confidence": 0.9,
                "reason": "keyword_trigger"
            }

        # ---- LLM fallback
        system_prompt = """
Classify if this is a scam.

Return ONLY JSON:
{
  "is_scam": true or false,
  "scam_type": "phishing" | "payment" | "lottery" | "impersonation" | "other" | "none",
  "confidence": number,
  "reason": "short"
}
"""

        completion = client.chat.completions.create(
            model=MODEL,
            temperature=0,
            max_tokens=80,
            messages=[
                {"role": "system", "content": system_prompt},
                *messages
            ],
            timeout=6
        )

        raw = completion.choices[0].message.content.strip()

        try:
            return json.loads(raw)
        except:
            return {
                "is_scam": False,
                "scam_type": "none",
                "confidence": 0.5,
                "reason": "parse_fallback"
            }

    except Exception:
        return {
            "is_scam": False,
            "scam_type": "none",
            "confidence": 0.5,
            "reason": "error"
        }


# =========================
# HONEYPOT STRATEGY ENGINE
# =========================
def get_next_question(intel: Dict, last_bot_msg: str) -> Optional[str]:
    """
    Goal-driven extraction strategy
    Avoid repetition + staged extraction
    """

    # PHONE
    if not intel.get("phone_numbers"):
        if "call me" not in last_bot_msg:
            return "can you call me instead i dont understand"

    # UPI
    if not intel.get("upi_ids"):
        if "upi" not in last_bot_msg:
            return "how do i send the money do you have upi"

    # LINK
    if not intel.get("urls"):
        if "link" not in last_bot_msg:
            return "can you send the link again"

    # BANK
    if not intel.get("bank_accounts"):
        if "transfer" not in last_bot_msg:
            return "where should i transfer the money"

    return None


# =========================
# OUTPUT CLEANING
# =========================
def clean_reply(text: str) -> str:
    if not text:
        return ""

    text = text.replace("\\n", " ").replace("\n", " ")
    text = re.sub(r'[\*\#\-\_]+', '', text)
    text = re.sub(r"\s+", " ", text).strip().lower()

    if len(text) > 120:
        text = text[:120]

    return text


# =========================
# HONEYPOT AGENT
# =========================
def run_agent(
    memory: List[Dict],
    scam_type: Optional[str] = None,
    mode: str = "honeypot",
    intel: Optional[Dict] = None
) -> str:
    """
    Core honeypot agent:
    - stage-aware
    - avoids repetition
    - goal-driven extraction
    - natural conversation
    """

    try:
        # =========================
        # STEP 0: ANALYZE MEMORY
        # =========================
        user_msgs = [m for m in memory if m.get("role") == "user"]
        bot_msgs = [m for m in memory if m.get("role") == "assistant"]

        turn_count = len(user_msgs)
        last_bot_msg = bot_msgs[-1]["content"] if bot_msgs else ""

        # =========================
        # STEP 1: FIRST MESSAGE FIX
        # =========================
        if turn_count == 1:
            return "how do i claim this"

        # =========================
        # STEP 2: SMART EXTRACTION
        # =========================
        if intel:
            question = get_next_question(intel, last_bot_msg)
            if question:
                return question

        # =========================
        # STEP 3: NATURAL VARIATION
        # =========================
        fallback_options = [
            "what do i need to do",
            "i dont understand can you explain",
            "what is this about",
            "how does this work",
            "what happens next",
            "can you explain properly",
            "what should i do now"
        ]

        # avoid repeating same fallback
        safe_options = [opt for opt in fallback_options if opt not in last_bot_msg]

        if safe_options:
            return random.choice(safe_options)

        return "what is this about"

    except Exception:
        return "what is this about"
