import os
import requests
import logging
from dotenv import load_dotenv
from livekit.agents import function_tool  # ✅ Correct decorator
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from zoya.services.zoya_search_utils import call_openrouter_search

@function_tool
async def google_search(query: str) -> str:
    """
    Search the internet using SerpAPI (Google Search engine).
    Provides titles, links, and summaries of top results.
    Fail-safe: Automatically falls back to OpenRouter if SerpAPI is down.
    """
    logger.info(f"SerpAPI Query: {query}")

    api_key = os.getenv("serpapi_API_KEY")

    if not api_key:
        logger.info("serpapi_API_KEY missing. Trying OpenRouter Fallback...")
        return await call_openrouter_search(query)

    url = "https://serpapi.com/search"
    params = {
        "api_key": api_key,
        "engine": "google",
        "q": query,
        "num": 5
    }

    try:
        logger.info("SerpAPI ko request bheji ja rahi hai...")
        response = requests.get(url, params=params, timeout=12)
        response.raise_for_status()
        
        data = response.json()
        results = data.get("organic_results", [])

        if not results:
            return "Koi results nahi mile."

        formatted = ""
        for i, item in enumerate(results[:5], start=1):
            title = item.get("title", "No title")
            link = item.get("link", "No link")
            snippet = item.get("snippet", "")
            formatted += f"{i}. {title}\n{link}\n{snippet}\n\n"
        
        return formatted.strip()
    except Exception as e:
        logger.warning(f"SerpAPI failed: {e}. Switching to OpenRouter Fallback...")
        return await call_openrouter_search(query)

@function_tool
async def get_current_datetime() -> str:
    return datetime.now().isoformat()

