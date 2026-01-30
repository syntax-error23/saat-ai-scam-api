from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import json
import os

from llm_router import detect_scam, extract_signals

app = FastAPI(
    title="SAAT AI Scam Detection API",
    version="0.1.0"
)

# ---- API Key ----
API_KEY = os.getenv("SAAT_API_KEY", "DEV_SECRET_KEY")

# ---- Memory ----
MEMORY = {}
MAX_TURNS = 6

# ---- Risk tracking ----
CONF_HISTORY = {}
MAX_CONF = 5

# ---- Request schema ----
class ScamRequest(BaseModel):
    conversation_id: str
    message: str

# ---- Health check ----
@app.get("/health")
def health():
    return {"status": "ok"}

# ---- Webhook ----
@app.post("/webhook")
def webhook(
    req: ScamRequest,
    x_api_key: str = Header(..., alias="X-API-Key")
):
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

    try:
        result = detect_scam(MEMORY[cid])
        signals = extract_signals(req.message)

        result["extracted_signals"] = signals
                # ---- Risk escalation logic ----
        CONF_HISTORY.setdefault(cid, [])
        CONF_HISTORY[cid].append(result["confidence"])
        CONF_HISTORY[cid] = CONF_HISTORY[cid][-MAX_CONF:]

        avg_conf = sum(CONF_HISTORY[cid]) / len(CONF_HISTORY[cid])

        if result["confidence"] > 0.8 and avg_conf > 0.7:
            trend = "high_risk"
            action = "block_and_report"
        elif result["confidence"] > avg_conf + 0.15:
            trend = "increasing"
            action = "warn_user"
        else:
            trend = "stable"
            action = "monitor"

        result["risk_trend"] = trend
        result["recommended_action"] = action

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
def warmup():
    try:
        detect_scam([{"role": "user", "content": "Hello"}])
        print("Groq warmed up")
    except:
        pass
