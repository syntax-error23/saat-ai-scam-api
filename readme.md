## SAAT AI — Scam Detection & Response API

An AI-powered backend service that analyzes suspicious messages, detects potential scams, generates safe human-like responses, and extracts actionable scam indicators (UPI IDs, phone numbers, URLs, bank accounts).

Built using FastAPI + Groq LLMs, deployed as a public API.

## Problem

Online scams are increasing rapidly across SMS, WhatsApp, email, and social platforms.
Most users struggle to:

-> Identify scams confidently

-> Respond safely without escalating risk

-> Extract useful information (numbers, UPI IDs, links) for reporting

-> Most existing solutions only classify scams but do not assist users during the conversation.

## Solution

SAAT AI acts as an intelligent scam-response assistant:

-> Detects whether a message is a scam

-> Classifies the scam type

-> Generates a natural, human-like reply (without alerting the scammer)

-> Extracts structured intelligence from the conversation


## Key Features

-> Scam Detection

-> LLM-based classification

-> Confidence score + scam category

-> Human-like Response Generation

-> Casual, non-robotic replies

-> Designed to avoid alerting scammers

Intelligence Extraction:

-> UPI IDs

-> Phone numbers (India-focused)

-> URLs

-> Bank account numbers

-> Conversation Memory

-> Multi-turn context support

-> Production-ready API

-> FastAPI backend

-> Public deployment

-> Clear request/response contract

## Architecture Overview

Client / Tester
      ↓
FastAPI Backend
      ↓
Groq LLM (Detection + Agent)
      ↓
Signal Extraction

## API Endpoints

# Health Check
GET /health
Response:
{ "status": "ok" }
# Scam Analysis Webook
POST /webhook
Headers:
X-API-Key: DEV_SECRET_KEY
Content-Type: application/json
Request Body:
{
  "conversation_id": "abc123",
  "message": "You have won ₹10,00,000. Click this link to claim."
}
Response:
{
  "is_scam": true,
  "scam_type": "lottery",
  "confidence": 0.92,
  "agent_reply": "wait how does this work",
  "extracted_intelligence": {
    "upi_ids": [],
    "phone_numbers": [],
    "bank_accounts": [],
    "urls": ["http://fake-link.example"]
  }
}

## Testing and Demo
Public deployment (Render)

Compatible with hackathon endpoint tester

Supports GET / HEAD / OPTIONS preflight checks

Gracefully handles empty tester requests

Can be tested via:

Swagger UI (/docs)

curl

Postman

## Limitation
Requires user-provided messages

No direct WhatsApp interception (API-only)

No frontend UI (backend-focused prototype)

## Future Imporvements
Requires user-provided messages

No direct WhatsApp interception (API-only)

No frontend UI (backend-focused prototype)

## Tech Stack
WhatsApp / Telegram bot integration

Browser extension

Scam intelligence dashboard

Multi-language support

Persistent storage

## Authors
Shubham Kulkarni
Tanmay Das

