import os
import json
from groq import Groq

print("=== GROQ FILE STARTED ===")

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def detect_scam_groq(message: str):
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

    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a strict JSON-only scam detection engine."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    raw = completion.choices[0].message.content.strip()
    return json.loads(raw)


if __name__ == "__main__":
    print("=== ENTERING MAIN ===")

    test_messages = [
        "Hey are you coming to class tomorrow?",
        "Congratulations! You won a prize. Click this link and send UPI details."
    ]

    for msg in test_messages:
        print("\nMESSAGE:", msg)
        result = detect_scam_groq(msg)
        print("RESULT:", result)