import os
import httpx
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import function_tool, RunContext

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(dotenv_path=BASE_DIR / ".env")

# API Keys
GENIUS_KEY = os.getenv("genius_API_KEY_Song")
TAVILY_KEY = os.getenv("TAVILY_API_KEY")
SERPAPI_KEY = os.getenv("serpapi_API_KEY")

async def fetch_from_genius(song_name: str) -> str:
    """Fetch lyrics info from Genius API."""
    if not GENIUS_KEY: return None
    url = f"https://api.genius.com/search?q={song_name}"
    headers = {"Authorization": f"Bearer {GENIUS_KEY}"}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                hits = resp.json().get('response', {}).get('hits', [])
                if hits:
                    song = hits[0]['result']
                    # Genius API doesn't return full lyrics in JSON, 
                    # but we can provide the song title and artist found.
                    return f"Genius found: {song['full_title']}"
    except Exception:
        pass
    return None

async def fetch_from_tavily(song_name: str) -> str:
    """Search for lyrics using Tavily."""
    if not TAVILY_KEY: return None
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": TAVILY_KEY,
        "query": f"{song_name} full lyrics text",
        "search_depth": "advanced"
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                results = resp.json().get('results', [])
                if results:
                    # Collect snippets
                    snippets = "\n".join([r['content'] for r in results[:3]])
                    if len(snippets) > 50:
                        return f"Tavily Search Results:\n{snippets}"
    except Exception:
        pass
    return None

async def fetch_from_serpapi(song_name: str) -> str:
    """Search for lyrics using SerpApi."""
    if not SERPAPI_KEY: return None
    url = "https://serpapi.com/search"
    params = {
        "q": f"{song_name} lyrics",
        "api_key": SERPAPI_KEY,
        "engine": "google"
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                # SerpApi usually has a 'lyrics' box or snippets
                search_data = resp.json()
                if "lyrics" in search_data:
                    return f"Google (SerpApi) Lyrics:\n{search_data['lyrics']}"
                
                snippets = []
                for r in search_data.get('organic_results', []):
                    if 'snippet' in r: snippets.append(r['snippet'])
                if snippets:
                    return f"Google (SerpApi) Snippets:\n" + "\n".join(snippets[:2])
    except Exception:
        pass
    return None

@function_tool
async def get_song_lyrics(context: RunContext, song_name: str) -> str:
    """
    Find the lyrics of a song using Genius, Tavily, and SerpApi.
    Use this when the user says "song sunao", "gaana sunao", or "lyrics dhoondo".

    Args:
        song_name: The name of the song to find lyrics for.
    """
    print(f"[LYRICS] Deep searching for: {song_name}...")
    
    # 1. Primary: Genius (Metadata/Confirmation)
    genius_info = await fetch_from_genius(song_name)
    if genius_info:
        print(f"[LYRICS] {genius_info}")

    # 2. Main Text Source: Tavily
    lyrics = await fetch_from_tavily(song_name)
    if lyrics:
        print(f"[LYRICS] Success via Tavily.")
        return f"🎵 **Found via Tavily:**\n\n{lyrics}"

    # 3. Fallback: SerpApi
    lyrics = await fetch_from_serpapi(song_name)
    if lyrics:
        print(f"[LYRICS] Success via SerpApi.")
        return f"🎵 **Found via Google (SerpApi):**\n\n{lyrics}"

    return f"❌ Maaf kijiye Uneeb, Genius aur Search results se '{song_name}' ke mukammal lyrics nahi mil sakay."
