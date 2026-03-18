from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import List, Optional
import os
import re

from llm_router import detect_scam, run_agent

app = FastAPI(
    title="Honeypot Scam Detection API",
    version="1.0.0"
)

# =========================
# CONFIG
# =========================
API_KEY = os.getenv("SAAT_API_KEY", "DEV_SECRET_KEY")
MEMORY = {}
MAX_TURNS = 15


# =========================
# REQUEST MODELS
# =========================
class Message(BaseModel):
    text: str

class ChatRequest(BaseModel):
    sessionId: str
    message: Message
    conversationHistory: Optional[List[dict]] = []


# =========================
# ROOT
# =========================
@app.get("/")
async def root():
    return {"status": "ok"}


# =========================
# INTELLIGENCE EXTRACTION
# =========================
def extract_intelligence(messages: list[dict]) -> dict:
    text = " ".join(m.get("content", "") for m in messages)

    phone_numbers = re.findall(r'(?:\+91[\s-]?|0)?[6-9]\d{9}', text)
    upi_ids = re.findall(r'\b[a-zA-Z0-9.\-_]{2,}@[a-zA-Z]{2,}\b', text)
    urls = re.findall(r'https?://[^\s]+', text)

    bank_accounts = []
    for num in re.findall(r'\b\d{9,18}\b', text):
        if num not in phone_numbers:
            bank_accounts.append(num)

    emails = re.findall(
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        text
    )

    return {
        "phone_numbers": list(set(phone_numbers)),
        "upi_ids": list(set(upi_ids)),
        "bank_accounts": list(set(bank_accounts)),
        "urls": list(set(urls)),
        "emails": list(set(emails))
    }


# =========================
# MAIN ENDPOINT
# =========================
@app.post("/webhook")
async def webhook(
    request: ChatRequest,
    x_api_key: str | None = Header(default=None, alias="x-api-key")
):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    body = request.dict()

    session_id = body.get("sessionId")
    message_text = body.get("message", {}).get("text")
    history = body.get("conversationHistory", [])

    if not session_id or not message_text:
        raise HTTPException(status_code=400, detail="Invalid request")

    # =========================
    # MEMORY MANAGEMENT
    # =========================
    MEMORY.setdefault(session_id, [])

    if not MEMORY[session_id] and history:
        for msg in history:
            role = "user" if msg.get("sender") == "user" else "assistant"
            MEMORY[session_id].append({
                "role": role,
                "content": msg.get("text", "")
            })

    MEMORY[session_id].append({
        "role": "user",
        "content": message_text
    })

    MEMORY[session_id] = MEMORY[session_id][-MAX_TURNS:]

    # =========================
    # DETECTION
    # =========================
    detection = detect_scam(MEMORY[session_id])

    # =========================
    # EXTRACTION
    # =========================
    intel = extract_intelligence(MEMORY[session_id])

    # =========================
    # HONEYPOT RESPONSE
    # =========================
    reply_text = run_agent(
        MEMORY[session_id],
        detection.get("scam_type"),
        mode="honeypot",
        intel=intel
    )

    MEMORY[session_id].append({
        "role": "assistant",
        "content": reply_text
    })

    MEMORY[session_id] = MEMORY[session_id][-MAX_TURNS:]

    # =========================
    # FINAL RESPONSE
    # =========================
    return {
        "status": "success",
        "reply": reply_text,
        "is_scam": detection.get("is_scam"),
        "scam_type": detection.get("scam_type"),
        "intel": intel,
        "conversation": MEMORY[session_id] 
    }
