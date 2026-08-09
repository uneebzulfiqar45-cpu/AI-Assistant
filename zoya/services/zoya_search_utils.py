import os
import httpx
import logging
from dotenv import load_dotenv
from pathlib import Path

# Load env from parent dir
load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")

logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

async def call_openrouter_search(query: str) -> str:
    """
    Fallback search using OpenRouter's Perplexity Sonar Online model.
    Used when primary search engines (SerpAPI/Tavily) fail.
    """
    if not OPENROUTER_API_KEY:
        return "OpenRouter API Key missing in .env! Donon search engines aur fallback fail ho gaya."

    logger.info(f"Triggering OpenRouter Fallback for: {query}")
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Model with internet search capabilities
    model = "perplexity/llama-3.1-sonar-large-128k-online"
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a research assistant. Provide the most accurate and up-to-date answer based on web search."},
            {"role": "user", "content": query}
        ]
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            answer = data["choices"][0]["message"]["content"]
            return f"[FALLBACK RESULT - OpenRouter]:\n{answer}"
    except Exception as e:
        logger.error(f"OpenRouter Fallback Error: {e}")
        return f"Search fail hua aur fallback OpenRouter bhi issue kar raha hai: {e}"
