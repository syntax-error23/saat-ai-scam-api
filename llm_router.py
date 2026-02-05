import os
import json
from groq import Groq

# LLM Setup (Groq)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY not set")

client = Groq(api_key=GROQ_API_KEY)

MODEL = "llama-3.1-8b-instant"

# Scam Detector
def detect_scam(messages: list[dict]) -> dict:
    """
    messages = [
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."},
        ...
    ]
    """

    # ---------- FAST HEURISTIC TRIGGER ----------
    joined = " ".join(m["content"].lower() for m in messages)

    KEYWORDS = [
        "urgent", "blocked", "verify", "otp",
        "upi", "account", "suspended", "immediately",
        "pay", "fee", "bank"
    ]

    if any(k in joined for k in KEYWORDS):
        return {
            "is_scam": True,
            "scam_type": "phishing",
            "confidence": 0.85,
            "reason": "keyword_trigger"
        }

    # ---------- LLM DETECTION ----------
    system_prompt = """
You are an AI scam detection assistant.

Your task:
Decide whether the conversation indicates a scam.

Rules:
- Respond ONLY in valid JSON
- No markdown
- No extra keys

JSON format:
{
  "is_scam": true or false,
  "scam_type": "payment" | "phishing" | "lottery" | "impersonation" | "other" | "none",
  "confidence": number between 0 and 1,
  "reason": "short explanation"
}
""".strip()

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

    try:
        return json.loads(raw)
    except Exception:
        # SAFE FALLBACK — NEVER CRASH EVALUATION
        return {
            "is_scam": True,
            "scam_type": "other",
            "confidence": 0.7,
            "reason": "model_parse_fallback"
        }


def run_agent(memory: list[dict], scam_type: str | None = None) -> str:
    """
    Very casual, human-like reply generator.
    Sounds like a real person texting, not an AI.
    """

    SYSTEM_PROMPT = """
you are a normal person texting casually.

you do not know this is a scam.
you think it *might* be real.

how you type:
- all lowercase
- short messages
- slightly informal
- no perfect grammar
- no formal tone
- commas are ok
- avoid long sentences
- 1 message only

rules:
- never mention scams, fraud, police, safety
- never accuse or sound suspicious
- never analyze
- ask just one simple follow-up
- sound a bit confused or curious
- do NOT be overly polite or excited

reply with ONLY the message text.
""".strip()

    SCAM_FOLLOWUPS = {
        "lottery": [
            "wait how does this work",
            "what do i need to do to claim it",
            "which company is this from"
        ],
        "payment": [
            "ok how do i pay",
            "where am i supposed to send it",
            "is this online or what"
        ],
        "phishing": [
            "can you send the link again",
            "what is this for exactly",
            "where does this take me"
        ],
        "impersonation": [
            "can you share your official number",
            "how do i verify this",
            "is there someone i can contact"
        ],
        "other": [
            "can you explain a bit",
            "not sure i get this",
            "what is this about"
        ]
    }

    options = SCAM_FOLLOWUPS.get(scam_type or "other", SCAM_FOLLOWUPS["other"])
    followup = options[0]

    completion = client.chat.completions.create(
        model=MODEL,
        temperature=0.8,
        max_tokens=40,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            *memory,
            {"role": "assistant", "content": followup}
        ],
        timeout=8
    )

    reply = completion.choices[0].message.content.strip().lower()

    if not reply:
        reply = "can you explain this"

    return reply
