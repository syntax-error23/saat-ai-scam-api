import requests
import json

print("=== FILE STARTED ===")

OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
MODEL = "mistral"


def detect_scam_llm(message: str):
    prompt = f"""
Respond ONLY in valid JSON.

JSON format:
{{
  "is_scam": true or false,
  "scam_type": "payment" | "phishing" | "lottery" | "impersonation" | "other" | "none",
  "confidence": number between 0 and 1,
  "reason": "short explanation"
}}

Message:
{message}
"""

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a strict JSON-only scam detection engine."},
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }

    response = requests.post(
        OLLAMA_CHAT_URL,
        json=payload,
        timeout=120  # IMPORTANT: local LLMs are slow on first run
    )

    response.raise_for_status()

    data = response.json()
    raw_text = data["message"]["content"].strip()

    return json.loads(raw_text)


print("=== ENTERING MAIN ===")

test_messages = [
    "Hey are you coming to class tomorrow?",
    "Congratulations! You won a prize. Click this link and send UPI details."
]

for msg in test_messages:
    print("\nMESSAGE:", msg)
    result = detect_scam_llm(msg)
    print("RESULT:", result)
