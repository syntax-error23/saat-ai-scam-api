# SAAT AI-Agentic AI Honeypot System for Scam Detection and Intelligence Extraction

An intelligent honeypot system that detects scam messages, takes over conversations, and extracts actionable intelligence such as phone numbers, UPI IDs, phishing links, and financial details.

Built as part of the India AI Impact Buildathon (HCL GUVI).

## Overview

Traditional scam detection systems stop at classification.

This system goes further by:
- Detecting scams  
- Engaging scammers in conversation  
- Extracting structured intelligence  
- Maintaining realistic multi-turn interactions  

## Features

- Scam Detection (hybrid: keyword + LLM fallback)  
- Agentic Honeypot Conversation System  
- Multi-turn Memory Handling  
- Goal-driven Question Strategy Engine  
- Data Extraction:
  - Phone Numbers  
  - UPI IDs  
  - URLs (phishing links)  
  - Bank Accounts  
  - Emails  
- Adaptive, non-repetitive responses  
- FastAPI-based API with webhook support  

## System Architecture

User Input
↓
Scam Detection (Rule + LLM)
↓
Memory (Conversation Context)
↓
Strategy Engine (Decides Next Question)
↓
Regex Extraction (Phone, UPI, URL, etc.)
↓
Response Generation


## How It Works

1. A suspicious message is received  
2. The system detects whether it is a scam  
3. If confirmed, the honeypot agent takes over  
4. Conversation memory stores full context  
5. The strategy engine determines missing information  
6. The system asks targeted questions  
7. Regex-based extraction captures scammer details  
8. The process repeats to maximize intelligence extraction  

## Example Output

json
{
  "status": "success",
  "reply": "where should i transfer the money",
  "is_scam": true,
  "scam_type": "phishing",
  "intel": {
    "phone_numbers": ["9876543210"],
    "upi_ids": ["scammer@upi"],
    "urls": ["https://fakebank-login.com"],
    "bank_accounts": [],
    "emails": []
  }
}


## How It Works

1. A suspicious message is received  
2. The system detects whether it is a scam  
3. If confirmed, the honeypot agent takes over  
4. Conversation memory stores full context  
5. The strategy engine determines missing information  
6. The system asks targeted questions  
7. Regex-based extraction captures scammer details  
8. The process repeats to maximize intelligence extraction  

## Example Conversation
User: You won 50 lakh lottery send OTP now
Bot: how do i claim this

User: send otp to 9876543210
Bot: how do i send the money do you have upi

User: send money to scammer@upi
Bot: can you send the link again

User: go to https://fakebank-login.com

User: You won 50 lakh lottery send OTP now
Bot: how do i claim this

User: send otp to 9876543210
Bot: how do i send the money do you have upi

User: send money to scammer@upi
Bot: can you send the link again

User: go to https://fakebank-login.com

Team

This project was developed as part of a 4-member team:

Tanmay Das
Shubham Kulkarni
Arin Pattnaik
Anushka



