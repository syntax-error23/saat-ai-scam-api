from fastapi import FastAPI, HTTPException, Header, Request
import os
import re

from llm_router import detect_scam, run_agent

app = FastAPI(
    title="SAAT AI Scam Detection API",
    version="0.3.0"
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

    phone_numbers = re.findall(r'(?:\+91[\s-]?)?[6-9]\d{9}', text)
    upi_ids = re.findall(r'\b[a-zA-Z0-9.\-_]{2,}@[a-zA-Z]{2,}\b', text)
    urls = re.findall(r'https?://[^\s]+', text)

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
    # ---- Preflight / tester ----
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return {"status": "ok"}

    # ---- Auth ----
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # ---- Parse body ----
    try:
        body = await request.json()
    except:
        body = None

    # ---- Empty tester call ----
    if not body:
        return {
            "status": "success",
            "reply": "hello"
        }

    # =========================
    # GUVI REQUEST FORMAT
    # =========================
    session_id = body.get("sessionId")
    message_obj = body.get("message", {})
    message_text = message_obj.get("text")
    history = body.get("conversationHistory", [])

    if not session_id or not message_text:
        raise HTTPException(status_code=400, detail="Invalid request format")

    # =========================
    # BUILD MEMORY (PROPERLY)
    # =========================
    MEMORY.setdefault(session_id, [])

    # Add previous conversation (only once)
    if not MEMORY[session_id] and history:
        for msg in history:
            role = "assistant" if msg.get("sender") == "user" else "user"
            MEMORY[session_id].append({
                "role": role,
                "content": msg.get("text", "")
            })

    # Add current incoming message
    MEMORY[session_id].append({
        "role": "user",
        "content": message_text
    })

    MEMORY[session_id] = MEMORY[session_id][-MAX_TURNS:]

    # =========================
    # DETECTION
    # =========================
    detection = detect_scam(MEMORY[session_id])

    # Default neutral reply
    reply_text = "can you explain this?"

    # =========================
    # AGENT ACTIVATION
    # =========================
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