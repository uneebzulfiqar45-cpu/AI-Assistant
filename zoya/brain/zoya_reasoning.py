import os
import httpx
from dotenv import load_dotenv
from livekit.agents import function_tool, RunContext
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(dotenv_path=BASE_DIR / ".env")

REASONING_API_KEY = os.getenv("OPENROUTER_API_KEY_REASONING")
O1_API_KEY = os.getenv("OPENROUTER_API_KEY_O1")
R1_API_KEY = os.getenv("OPENROUTER_API_KEY_R1")

# Priority fallback based on .env
API_KEYToUse = R1_API_KEY or O1_API_KEY or REASONING_API_KEY

@function_tool
async def deep_think(context: RunContext, user_query: str) -> str:
    """
    Use this tool when the user asks a very complex question that requires deep logic, math, reasoning or advanced explanation.

    Args:
        user_query: The difficult question or problem the user needs solved.
    """
    if not API_KEYToUse:
        return "Reasoning API keys missing from .env."

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEYToUse}",
        "Content-Type": "application/json",
        "HTTP-Referer": "zoya-agent",
        "X-Title": "Zoya Reasoning"
    }
    
    # We use a reasoning model, e.g. R1 or O1
    payload = {
        "model": "deepseek/deepseek-r1",
        "messages": [
            {"role": "system", "content": "You are a logical reasoning module for Zoya. Provide extreme detail, step-by-step logic, and high accuracy. Output in Roman Urdu."},
            {"role": "user", "content": user_query}
        ]
    }
    
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Reasoning compute error: {e}"
