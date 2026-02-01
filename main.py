from fastapi import FastAPI, HTTPException, Header, Request
from pydantic import BaseModel
import os
import re

from llm_router import detect_scam, run_agent

app = FastAPI(
    title="SAAT AI Scam Detection API",
    version="0.1.0"
)

# ROOT ROUTE 
@app.api_route("/", methods=["GET", "POST", "HEAD", "OPTIONS"])
async def root(request: Request):
    return {"status": "ok"}

# CONFIG

API_KEY = os.getenv("SAAT_API_KEY", "DEV_SECRET_KEY")
MEMORY = {}
MAX_TURNS = 10

# REQUEST SCHEMA
class ScamRequest(BaseModel):
    conversation_id: str
    message: str

# HEALTH CHECK
@app.get("/health")
def health():
    return {"status": "ok"}

# INTELLIGENCE EXTRACTOR
def extract_intelligence(messages: list[dict]) -> dict:
    text = " ".join(m["content"] for m in messages)

    result = {
        "upi_ids": [],
        "phone_numbers": [],
        "bank_accounts": [],
        "urls": []
    }

    result["phone_numbers"] = list(set(
        re.findall(r'\b(?:\+91[\s-]?)?[6-9]\d{9}\b', text)
    ))

    result["upi_ids"] = list(set(
        re.findall(r'\b[a-zA-Z0-9.\-_]{2,}@[a-zA-Z]{2,}\b', text)
    ))

    result["urls"] = list(set(
        re.findall(r'https?://[^\s]+', text)
    ))

    candidates = re.findall(r'\b\d{9,18}\b', text)
    for c in candidates:
        if c not in result["phone_numbers"]:
            result["bank_accounts"].append(c)

    result["bank_accounts"] = list(set(result["bank_accounts"]))
    return result

# HONEYPOT WEBHOOK
from fastapi import Request

@app.api_route("/webhook", methods=["GET", "POST", "HEAD", "OPTIONS"])
@app.api_route("/webhook/", methods=["GET", "POST", "HEAD", "OPTIONS"])
async def webhook_handler(
    request: Request,
    x_api_key: str | None = Header(default=None, alias="X-API-Key")
):
    # ---- Tester preflight ----
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return {"status": "ok"}

    # ---- Try to read body safely ----
    try:
        body = await request.json()
    except:
        body = None

    # ---- Tester sends EMPTY body ----
    if not body:
        return {
            "is_scam": False,
            "scam_type": "none",
            "confidence": 0.0,
            "agent_reply": None,
            "extracted_intelligence": {
                "upi_ids": [],
                "phone_numbers": [],
                "bank_accounts": [],
                "urls": []
            }
        }

    # ---- Auth ----
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    req = ScamRequest(**body)

    cid = req.conversation_id
    MEMORY.setdefault(cid, [])

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
