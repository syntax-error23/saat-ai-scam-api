from fastapi import FastAPI, HTTPException, Header
from fastapi import Request
from pydantic import BaseModel
import os
import re

from llm_router import detect_scam, run_agent

app = FastAPI(
    title="SAAT AI Scam Detection API",
    version="0.1.0"
)

# API Key
API_KEY = os.getenv("SAAT_API_KEY", "DEV_SECRET_KEY")

# Memory 
MEMORY = {}
MAX_TURNS = 10

# Request schema 
class ScamRequest(BaseModel):
    conversation_id: str
    message: str

# Health check 
@app.get("/health")
def health():
    return {"status": "ok"}

# Extractor
def extract_intelligence(messages: list[dict]) -> dict:
    text = " ".join(m["content"] for m in messages)

    result = {
        "upi_ids": [],
        "phone_numbers": [],
        "bank_accounts": [],
        "urls": []
    }

    # Phone numbers
    phones = re.findall(r'\b(?:\+91[\s-]?)?[6-9]\d{9}\b', text)
    result["phone_numbers"] = list(set(phones))

    # UPI IDs
    upis = re.findall(r'\b[a-zA-Z0-9.\-_]{2,}@[a-zA-Z]{2,}\b', text)
    result["upi_ids"] = list(set(upis))

    # URLs
    urls = re.findall(r'https?://[^\s]+', text)
    result["urls"] = list(set(urls))

    # Bank accounts
    candidates = re.findall(r'\b\d{9,18}\b', text)
    for c in candidates:
        if c not in result["phone_numbers"]:
            result["bank_accounts"].append(c)

    result["bank_accounts"] = list(set(result["bank_accounts"]))

    return result

print(run_agent)


# Webhook 
@app.api_route("/webhook", methods=["GET", "POST", "HEAD", "OPTIONS"])
async def webhook_handler(
    request: Request,
    req: ScamRequest | None = None,
    x_api_key: str | None = Header(default=None, alias="X-API-Key")
):
    # ---- Preflight / tester checks ----
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return {"status": "ok"}

    # ---- Actual POST logic ----
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    cid = req.conversation_id

    if cid not in MEMORY:
        MEMORY[cid] = []

    MEMORY[cid].append({
        "role": "user",
        "content": req.message
    })
    MEMORY[cid] = MEMORY[cid][-MAX_TURNS:]

    detection = detect_scam(MEMORY[cid])

    response = {
        "is_scam": detection["is_scam"],
        "scam_type": detection["scam_type"],
        "confidence": detection["confidence"],
        "agent_reply": None,
        "extracted_intelligence": {
            "upi_ids": [],
            "phone_numbers": [],
            "bank_accounts": [],
            "urls": []
        }
    }

    if detection["is_scam"]:
        agent_reply = run_agent(MEMORY[cid], detection["scam_type"])
        MEMORY[cid].append({
            "role": "assistant",
            "content": agent_reply
        })
        MEMORY[cid] = MEMORY[cid][-MAX_TURNS:]

        response["agent_reply"] = agent_reply
        response["extracted_intelligence"] = extract_intelligence(MEMORY[cid])

    return response