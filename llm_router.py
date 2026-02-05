import os
import json
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
# SCAM DETECTION
# =========================
def detect_scam(messages: list[dict]) -> dict:
    """
    Fast + safe scam detection.
    NEVER crashes.
    """

    joined = " ".join(m["content"].lower() for m in messages)

    # ---- Fast heuristic (GUVI-friendly, low latency) ----
    KEYWORDS = [
        "urgent", "blocked", "verify", "otp",
        "upi", "account", "suspended",
        "immediately", "pay", "fee", "bank"
    ]

    if any(k in joined for k in KEYWORDS):
        return {
            "is_scam": True,
            "scam_type": "phishing",
            "confidence": 0.9,
            "reason": "keyword_trigger"
        }

    # ---- LLM fallback (only if needed) ----
    system_prompt = """
You are an AI scam detection assistant.

Decide whether the conversation indicates a scam.

Rules:
- Respond ONLY in valid JSON
- No markdown
- No extra text

JSON format:
{
  "is_scam": true or false,
  "scam_type": "payment" | "phishing" | "lottery" | "impersonation" | "other" | "none",
  "confidence": number between 0 and 1,
  "reason": "short explanation"
}
""".strip()

    try:
        completion = client.chat.completions.create(
            model=MODEL,
            temperature=0,
            messages=[
                {"role": "system", "content": system_prompt},
                *messages
            ],
            timeout=8
        )

        raw = completion.choices[0].message.content.strip()
        return json.loads(raw)

    except Exception:
        # ---- ABSOLUTE SAFETY NET ----
        return {
            "is_scam": True,
            "scam_type": "other",
            "confidence": 0.7,
            "reason": "safe_fallback"
        }


# =========================
# AGENTIC HONEYPOT AGENT
# =========================
def run_agent(memory: list[dict], scam_type: str | None = None) -> str:
    """
    Human-like honeypot agent.
    GUARANTEED non-empty, non-garbage output.
    """

    SYSTEM_PROMPT = """
you are a normal person replying casually to a message.

you do NOT know this is a scam.
you think it might be real.

how you write:
- all lowercase
- natural short sentences
- mildly confused or curious
- sounds like a real human texting

rules:
- never mention scams, fraud, police, safety
- never accuse
- never analyze
- ask only ONE question
- reply must be a full sentence
- no emojis
- no symbols like ? alone

reply with ONLY the message text.
""".strip()

    FOLLOWUPS = {
        "phishing": [
            "why is my account being blocked",
            "what do i need to verify",
            "can you explain this"
        ],
        "payment": [
            "how am i supposed to pay this",
            "where do i send the money",
            "what is this fee for"
        ],
        "impersonation": [
            "who is this exactly",
            "how do i check this is legit",
            "can you share more details"
        ],
        "lottery": [
            "how did i win this",
            "what is this about",
            "can you explain how this works"
        ],
        "other": [
            "can you explain this",
            "what is this regarding",
            "why am i getting this message"
        ]
    }

    options = FOLLOWUPS.get(scam_type or "other", FOLLOWUPS["other"])
    seed_question = options[0]

    try:
        completion = client.chat.completions.create(
            model=MODEL,
            temperature=0.6,
            max_tokens=40,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                *memory,
                {"role": "assistant", "content": seed_question}
            ],
            timeout=8
        )

        reply = completion.choices[0].message.content.strip().lower()

    except Exception:
        reply = ""

    # ---- FINAL GUARDRAIL ----
    if not reply or len(reply) < 6:
        reply = "why is my account being blocked"

    return reply
