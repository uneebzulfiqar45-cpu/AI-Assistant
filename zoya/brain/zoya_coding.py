import os
import httpx
from dotenv import load_dotenv
from livekit.agents import function_tool, RunContext
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(dotenv_path=BASE_DIR / ".env")

DEEPSEEK_CODER_KEY = os.getenv("OPENROUTER_API_KEY_DeepSeek_Coder")
QWEN_CODER_KEY = os.getenv("OPENROUTER_API_KEY_Qwen_Coder")
STARCODER_KEY = os.getenv("OPENROUTER_API_KEY_StarCoder")

API_KEYToUse = DEEPSEEK_CODER_KEY or QWEN_CODER_KEY or STARCODER_KEY

@function_tool
async def write_code(context: RunContext, prompt: str, language: str) -> str:
    """
    Use this tool when the user asks you to write code, design an algorithm, or fix a coding bug.

    Args:
        prompt: What specifically does the user want you to code or program?
        language: The programming language (e.g. 'python', 'javascript', 'c++')
    """
    if not API_KEYToUse:
        return "Coding API keys missing from .env."

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEYToUse}",
        "Content-Type": "application/json",
        "HTTP-Referer": "zoya-agent",
        "X-Title": "Zoya Coding"
    }
    
    payload = {
        "model": "qwen/qwen-2.5-coder-32b-instruct",
        "messages": [
            {"role": "system", "content": f"You are an expert {language} programmer. Return code snippets with clear explanations in Roman Urdu."},
            {"role": "user", "content": prompt}
        ]
    }
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Coding model error: {e}"
