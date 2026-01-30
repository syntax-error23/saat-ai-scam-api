# SAAT AI – Scam Detection API

SAAT AI is a real-time scam detection API that analyzes user messages and detects scams such as phishing, lottery fraud, payment scams, and impersonation attempts using large language models (LLMs).

The API is designed to be fast, conversation-aware, and easy to integrate into messaging platforms, call-center tools, and browser extensions.


## Features

- Detects scam messages with high accuracy
- Supports multiple scam categories (phishing, lottery, payment, impersonation)
- Returns confidence score and reasoning
- Generates a safe reply users can send back
- Conversation-aware (maintains short context)
- Low-latency inference using Groq


## Tech Stack

- **Backend:** Python, FastAPI
- **LLM Provider:** Groq
- **Model:** `llama-3.1-8b-instant`
- **Server:** Uvicorn
- **Version Control:** Git + GitHub



## API Endpoints

### Health Check

**GET** `/health`

Used to verify that the API is running.

**Response**
```json
{
  "status": "ok"
}
