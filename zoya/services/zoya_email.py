import os
import httpx
from dotenv import load_dotenv
from livekit.agents import function_tool, RunContext
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(dotenv_path=BASE_DIR / ".env")

MAILERSEND_API_KEY = os.getenv("MAILERSEND_API_KEY")
MAILERSEND_FROM_EMAIL = os.getenv("MAILERSEND_FROM_EMAIL")
MAILERSEND_FROM_NAME = os.getenv("MAILERSEND_FROM_NAME")

@function_tool
async def send_email(context: RunContext, to_email: str, subject: str, message: str) -> str:
    """
    Send an email using MailerSend API. Use this when the user asks you to send an email.

    Args:
        to_email: The recipient's email address
        subject: The subject of the email
        message: The body of the email
    """
    if not MAILERSEND_API_KEY or not MAILERSEND_FROM_EMAIL:
        return "Email API keys (MailerSend) missing from .env, email could not be sent."

    url = "https://api.mailersend.com/v1/email"
    headers = {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "Authorization": f"Bearer {MAILERSEND_API_KEY}"
    }

    payload = {
        "from": {
            "email": MAILERSEND_FROM_EMAIL,
            "name": MAILERSEND_FROM_NAME or "Zoya AI"
        },
        "to": [
            {
                "email": to_email
            }
        ],
        "subject": subject,
        "text": message
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return f"✅ Email successfully '{to_email}' ko bhej di gayi hai!"
    except Exception as e:
        return f"❌ Email bhejne mein error aai: {e}"
