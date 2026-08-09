import os
import httpx
from dotenv import load_dotenv
from livekit.agents import function_tool, RunContext
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(dotenv_path=BASE_DIR / ".env")

NEWS_API_KEY = os.getenv("NEWS_API_KEY")

@function_tool
async def get_latest_news(context: RunContext, topic: str = "technology") -> str:
    """
    Search for the latest news articles on a given topic using NewsAPI.

    Args:
        topic: The topic to search news for (e.g. 'sports', 'AI', 'Pakistan')
    """
    if not NEWS_API_KEY:
        return "News API key missing in .env configuration."

    url = f"https://newsapi.org/v2/everything?q={topic}&sortBy=publishedAt&apiKey={NEWS_API_KEY}&language=en"
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            
            articles = data.get("articles", [])
            if not articles:
                return f"'{topic}' par koi taaza news nahi mili."

            result = f"Latest news about '{topic}':\n"
            for i, article in enumerate(articles[:3]):
                title = article.get("title", "No Title")
                desc = article.get("description", "")
                result += f"{i+1}. {title}\n   {desc}\n\n"
            
            return result.strip()
    except Exception as e:
        return f"News laane mein detail error aai: {e}"
