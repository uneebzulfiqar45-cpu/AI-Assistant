import os
import httpx
from dotenv import load_dotenv
from livekit.agents import function_tool, RunContext
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(dotenv_path=BASE_DIR / ".env")

LLAMA3_WRITE_KEY = os.getenv("OPENROUTER_API_KEY_Llama3_Write")
MIXTRAL_WRITE_KEY = os.getenv("OPENROUTER_API_KEY_Mixtral_Write")

API_KEYToUse = LLAMA3_WRITE_KEY or MIXTRAL_WRITE_KEY

@function_tool
async def write_creative_content(context: RunContext, topic: str, tone: str = "friendly") -> str:
    """
    Use this tool to write a long story, compose an essay, draft an email body, or write an article.

    Args:
        topic: The overall subject matter of the writing.
        tone: The tone of the writing (e.g., 'professional', 'funny', 'friendly').
    """
    if not API_KEYToUse:
        return "Writing API keys missing from .env."

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEYToUse}",
        "Content-Type": "application/json",
        "HTTP-Referer": "zoya-agent",
        "X-Title": "Zoya Writing"
    }
    
    payload = {
        "model": "meta-llama/llama-3-8b-instruct",
        "messages": [
            {"role": "system", "content": f"You are an expert creative writer for Zoya. Write gracefully in Roman Urdu. Follow the requested tone: {tone}."},
            {"role": "user", "content": f"Please write about this topic:\n{topic}"}
        ]
    }
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Creative Writing error: {e}"
