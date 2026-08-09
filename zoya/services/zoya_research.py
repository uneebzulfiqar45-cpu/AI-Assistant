import os
import httpx
from dotenv import load_dotenv
from livekit.agents import function_tool, RunContext
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(dotenv_path=BASE_DIR / ".env")

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

from zoya.services.zoya_search_utils import call_openrouter_search

@function_tool
async def deep_research(context: RunContext, query: str) -> str:
    """
    Do DEEP research/internet analysis for analytics and detailed web answers using Tavily Search API.
    Use this for complex questions, fact-checking, or when you need a summarized AI answer.
    (Preferred for specialized data and summarized trends).
    Fail-safe: Automatically falls back to OpenRouter if Tavily is down.

    Args:
        query: What to research or search for.
    """
    if not TAVILY_API_KEY:
        logger.info("TAVILY_API_KEY missing. Trying OpenRouter Fallback...")
        return await call_openrouter_search(query)

    url = "https://api.tavily.com/search"
    headers = {"Content-Type": "application/json"}
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "search_depth": "advanced",
        "include_answer": True
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("answer", "Deep research completed but no clear answer was summarized. Check the results.")
    except Exception as e:
        logger.warning(f"Tavily Research failed: {e}. Switching to OpenRouter Fallback...")
        return await call_openrouter_search(query)
