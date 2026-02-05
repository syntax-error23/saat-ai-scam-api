from fastapi import FastAPI, HTTPException, Header, Request
from pydantic import BaseModel
import os
import re

from llm_router import detect_scam, run_agent

app = FastAPI(
    title="SAAT AI Scam Detection API",
    version="0.2.0"
)

# =========================
# CONFIG
# =========================
API_KEY = os.getenv("SAAT_API_KEY", "DEV_SECRET_KEY")
MEMORY = {}
MAX_TURNS = 10

# =========================
# ROOT + HEALTH
# =========================
@app.api_route("/", methods=["GET", "POST", "HEAD", "OPTIONS"])
async def root():
    return {"status": "ok"}

@app.get("/health")
def health():
    return {"status": "ok"}

# =========================
# INTELLIGENCE EXTRACTION
# =========================
def extract_intelligence(messages: list[dict]) -> dict:
    text = " ".join(m["content"] for m in messages)

    phone_numbers = re.findall(
        r'(?:\+91[\s-]?)?[6-9]\d{9}',
        text
    )

    upi_ids = re.findall(
        r'\b[a-zA-Z0-9.\-_]{2,}@[a-zA-Z]{2,}\b',
        text
    )

    urls = re.findall(
        r'https?://[^\s]+',
        text
    )

    bank_accounts = []
    for num in re.findall(r'\b\d{9,18}\b', text):
        if num not in phone_numbers:
            bank_accounts.append(num)

    return {
        "upi_ids": list(set(upi_ids)),
        "phone_numbers": list(set(phone_numbers)),
        "bank_accounts": list(set(bank_accounts)),
        "urls": list(set(urls))
    }

# =========================
# WEBHOOK
# =========================
@app.api_route("/webhook", methods=["GET", "POST", "HEAD", "OPTIONS"])
async def webhook(
    request: Request,
    x_api_key: str | None = Header(default=None, alias="x-api-key")
):
    # ---- Allow tester / preflight ----
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return {"status": "ok"}

    # ---- Auth ----
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # ---- Parse JSON ----
    try:
        body = await request.json()
    except:
        body = None

    # ---- Tester case (empty body) ----
    if not body:
        return {
            "status": "success",
            "reply": "hello"
        }

    # =========================
    # GUVI FORMAT HANDLING
    # =========================
    session_id = body.get("sessionId")
    message_obj = body.get("message", {})
    message_text = message_obj.get("text")

    if not session_id or not message_text:
        raise HTTPException(status_code=400, detail="Invalid request format")

    # ---- Init memory ----
    MEMORY.setdefault(session_id, [])

    # ---- Add incoming message ----
    MEMORY[session_id].append({
        "role": "user",
        "content": message_text
    })
    MEMORY[session_id] = MEMORY[session_id][-MAX_TURNS:]

    # ---- Detect scam (FAST) ----
    detection = detect_scam(MEMORY[session_id])

    # ---- Default reply (human-like but neutral) ----
    reply_text = "can you explain this?"

    # ---- If scam → activate agent ----
    if detection.get("is_scam"):
        reply_text = run_agent(
            MEMORY[session_id],
            detection.get("scam_type")
        )

        MEMORY[session_id].append({
            "role": "assistant",
            "content": reply_text
        })
        MEMORY[session_id] = MEMORY[session_id][-MAX_TURNS:]

    # =========================
    # REQUIRED RESPONSE FORMAT
    # =========================
    return {
        "status": "success",
        "reply": reply_text
    }